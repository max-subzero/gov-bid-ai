"""Commercial Pricing, Loaded Labor Rate & Prevailing Wage Compliance Engine."""

from typing import Dict, List, Optional
from govbid.models.pricing import (
    LaborCategory,
    PricingModelResult,
    StaffingRequirement,
    StatutoryWageSchedule,
    WageClassificationType,
)


class PricingLaborEngine:
    """Calculates loaded billing rates, cost fee schedules, and verifies prevailing wage compliance."""

    # Built-in statutory prevailing wage determinations (NYC Comptroller Labor Law § 220 & Federal DBA)
    DEFAULT_STATUTORY_SCHEDULES: Dict[str, StatutoryWageSchedule] = {
        "NYC-LL220-TELEMATICS-ELEC": StatutoryWageSchedule(
            schedule_id="NYC-LL220-TELEMATICS-ELEC",
            trade_title="Electrician - Telematics & Communications Line Installer",
            jurisdiction="NYC Comptroller Labor Law § 220",
            base_hourly_wage=60.50,
            fringe_hourly_rate=39.25,
            overtime_multiplier=1.5,
            effective_period="FY 2026 - 2027",
        ),
        "NYC-LL220-AUTO-DIAGNOSTIC": StatutoryWageSchedule(
            schedule_id="NYC-LL220-AUTO-DIAGNOSTIC",
            trade_title="Automotive Mechanic - Heavy Fleet Diagnostic Specialist",
            jurisdiction="NYC Comptroller Labor Law § 220",
            base_hourly_wage=48.00,
            fringe_hourly_rate=34.50,
            overtime_multiplier=1.5,
            effective_period="FY 2026 - 2027",
        ),
        "FED-DBA-COMM-TECH": StatutoryWageSchedule(
            schedule_id="FED-DBA-COMM-TECH",
            trade_title="Communications Systems Installer",
            jurisdiction="US Department of Labor Davis-Bacon Act",
            base_hourly_wage=42.00,
            fringe_hourly_rate=22.50,
            overtime_multiplier=1.5,
            effective_period="FY 2026",
        ),
    }

    def calculate_loaded_rate(self, category: LaborCategory) -> LaborCategory:
        """Calculates direct labor burdens, overhead, profit margin, and validates statutory wage floors."""
        base_cash = category.base_hourly_rate
        fringe = category.fringe_hourly_rate
        tax_burden = base_cash * (category.payroll_tax_burden_pct / 100.0)
        workers_comp = base_cash * (category.workers_comp_pct / 100.0)

        direct_cost = base_cash + fringe + tax_burden + workers_comp
        with_overhead = direct_cost * (1.0 + (category.overhead_pct / 100.0))
        loaded_rate = round(with_overhead * (1.0 + (category.profit_margin_pct / 100.0)), 2)

        statutory_floor = 0.0
        is_compliant = True

        if category.classification == WageClassificationType.PREVAILING_WAGE_TRADE:
            stat_sched = category.statutory_schedule
            # Auto-assign matching default schedule if none provided
            if not stat_sched and "electric" in category.title.lower() or "telematics" in category.title.lower():
                stat_sched = self.DEFAULT_STATUTORY_SCHEDULES.get("NYC-LL220-TELEMATICS-ELEC")

            if stat_sched:
                stat_base = stat_sched.base_hourly_wage
                stat_fringe = stat_sched.fringe_hourly_rate
                stat_tax = stat_base * (category.payroll_tax_burden_pct / 100.0)
                stat_comp = stat_base * (category.workers_comp_pct / 100.0)
                statutory_floor = round(stat_base + stat_fringe + stat_tax + stat_comp, 2)

                # Validate whether base wage or fringe fails statutory schedule
                if base_cash < stat_base or fringe < stat_fringe or loaded_rate < statutory_floor:
                    is_compliant = False

        return category.model_copy(
            update={
                "loaded_hourly_rate": loaded_rate,
                "statutory_minimum_floor": statutory_floor,
                "is_compliant": is_compliant,
            }
        )

    def build_fee_schedule(
        self,
        solicitation_number: str,
        staffing: List[StaffingRequirement],
        prevailing_wage_mandated: bool = False,
        materials_and_odc: float = 0.0,
    ) -> PricingModelResult:
        """Builds a comprehensive fee schedule across all staffing roles and evaluates wage compliance."""
        processed_staffing: List[StaffingRequirement] = []
        total_hours = 0.0
        total_labor_cost = 0.0
        compliance_alerts: List[str] = []
        all_compliant = True

        for req in staffing:
            evaluated_cat = self.calculate_loaded_rate(req.labor_category)
            subtotal = round(evaluated_cat.loaded_hourly_rate * req.total_hours, 2)

            total_hours += req.total_hours
            total_labor_cost += subtotal

            if not evaluated_cat.is_compliant:
                all_compliant = False
                sched = evaluated_cat.statutory_schedule
                ref_text = f" (Statutory Base: ${sched.base_hourly_wage:,.2f}/hr, Fringe: ${sched.fringe_hourly_rate:,.2f}/hr)" if sched else ""
                compliance_alerts.append(
                    f"STATUTORY WAGE DEFICIT: '{evaluated_cat.title}' loaded rate of ${evaluated_cat.loaded_hourly_rate:,.2f}/hr "
                    f"falls below legal statutory floor of ${evaluated_cat.statutory_minimum_floor:,.2f}/hr{ref_text}. "
                    "Submission constitutes a labor law non-responsive violation."
                )

            processed_staffing.append(
                req.model_copy(
                    update={
                        "labor_category": evaluated_cat,
                        "subtotal_labor_cost": subtotal,
                    }
                )
            )

        if prevailing_wage_mandated:
            has_trade_role = any(
                req.labor_category.classification == WageClassificationType.PREVAILING_WAGE_TRADE
                for req in processed_staffing
            )
            if not has_trade_role:
                compliance_alerts.append(
                    "RISK NOTICE: Solicitation mandates Prevailing Wage compliance, but staffing plan contains "
                    "zero PREVAILING_WAGE_TRADE labor categories. Ensure all field installation or physical hardware "
                    "maintenance is properly classified under NY Labor Law § 220 trade titles."
                )

        total_labor_cost = round(total_labor_cost, 2)
        total_price = round(total_labor_cost + materials_and_odc, 2)
        blended_rate = round(total_labor_cost / total_hours, 2) if total_hours > 0 else 0.0

        return PricingModelResult(
            solicitation_number=solicitation_number,
            prevailing_wage_mandated=prevailing_wage_mandated,
            total_billable_hours=total_hours,
            total_labor_cost=total_labor_cost,
            materials_and_odc=materials_and_odc,
            total_contract_price=total_price,
            effective_blended_hourly_rate=blended_rate,
            is_fully_compliant=all_compliant,
            staffing_breakdown=processed_staffing,
            compliance_alerts=compliance_alerts,
        )

    def generate_certified_payroll_declaration(
        self,
        result: PricingModelResult,
        vendor_name: str,
        certifying_officer: Optional[str] = None,
    ) -> str:
        """Generates an official Certified Payroll & Statutory Prevailing Wage Acknowledgment Declaration."""
        lines = [
            "=" * 78,
            "STATUTORY PREVAILING WAGE & CERTIFIED PAYROLL COMPLIANCE DECLARATION",
            "Pursuant to New York State Labor Law Article 8 (§ 220) and Article 9 (§ 230)",
            "=" * 78,
            f"DATE:             October 2026",
            f"CONTRACTOR:       {vendor_name}",
            f"SOLICITATION PIN: {result.solicitation_number}",
            f"TOTAL PROPOSAL:   ${result.total_contract_price:,.2f} ({result.total_billable_hours:,.0f} Total Billable Hours)",
            f"BLENDED RATE:     ${result.effective_blended_hourly_rate:,.2f}/hr",
            "",
            "1. STATUTORY LABOR CLASSIFICATION SCHEDULE",
        ]

        for req in result.staffing_breakdown:
            cat = req.labor_category
            badge = "[PREVAILING WAGE]" if cat.classification == WageClassificationType.PREVAILING_WAGE_TRADE else "[EXEMPT PROFESSIONAL]"
            lines.append(f"  • {badge} {cat.title}")
            lines.append(f"    Base Cash: ${cat.base_hourly_rate:,.2f}/hr | Fringe: ${cat.fringe_hourly_rate:,.2f}/hr | Loaded: ${cat.loaded_hourly_rate:,.2f}/hr")
            lines.append(f"    Allocated: {req.total_hours:,.0f} hours | Subtotal Labor: ${req.subtotal_labor_cost:,.2f}")
            if cat.statutory_schedule:
                lines.append(f"    Schedule:  {cat.statutory_schedule.jurisdiction} ({cat.statutory_schedule.schedule_id})")
            lines.append("")

        lines.extend([
            "2. CERTIFIED PAYROLL SUBMISSION MANDATE",
            "  The undersigned contractor hereby covenants, agrees, and certifies under penalty of perjury:",
            "  1. All designated trade mechanics and installers shall be compensated at rates equal to or",
            "     exceeding the statutory prevailing wage schedules published by the NYC Comptroller.",
            "  2. Weekly certified payroll records (Form WH-347 or NYC Comptroller Certified Payroll Form)",
            "     shall be submitted through the City of New York electronic certified payroll portal.",
            "  3. Zero uncertified wage classifications, illicit trainee deductions, or non-approved",
            "     independent contractor misclassifications shall be permitted.",
            "",
            f"  Authorized Representative: {vendor_name}",
            f"  Title / Officer:           {certifying_officer or 'Chief Financial Officer / Managing Principal'}",
            "=" * 78,
        ])

        return "\n".join(lines)
