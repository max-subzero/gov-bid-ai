"""Unit tests for PricingLaborEngine and statutory wage compliance."""

import unittest
from govbid.engines.pricing_engine import PricingLaborEngine
from govbid.models.pricing import (
    LaborCategory,
    StaffingRequirement,
    StatutoryWageSchedule,
    WageClassificationType,
)


class TestPricingLaborEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PricingLaborEngine()
        self.solicitation_pin = "85626P0001"

        self.stat_sched_elec = StatutoryWageSchedule(
            schedule_id="NYC-LL220-TELEMATICS-ELEC",
            trade_title="Electrician - Telematics & Communications Line Installer",
            jurisdiction="NYC Comptroller Labor Law § 220",
            base_hourly_wage=60.50,
            fringe_hourly_rate=39.25,
            overtime_multiplier=1.5,
            effective_period="FY 2026 - 2027",
        )

        self.compliant_trade = LaborCategory(
            role_id="ROLE-ELEC-01",
            title="Field Telematics Installation Electrician",
            classification=WageClassificationType.PREVAILING_WAGE_TRADE,
            statutory_schedule=self.stat_sched_elec,
            base_hourly_rate=62.00,
            fringe_hourly_rate=40.00,
            payroll_tax_burden_pct=12.0,
            workers_comp_pct=6.0,
            overhead_pct=15.0,
            profit_margin_pct=10.0,
        )

        self.exempt_arch = LaborCategory(
            role_id="ROLE-ARCH-02",
            title="Principal Cloud Solutions Architect",
            classification=WageClassificationType.EXEMPT_PROFESSIONAL,
            base_hourly_rate=135.00,
            fringe_hourly_rate=0.0,
            payroll_tax_burden_pct=10.0,
            workers_comp_pct=1.5,
            overhead_pct=15.0,
            profit_margin_pct=15.0,
        )

    def test_calculate_loaded_rate_exempt_role(self) -> None:
        evaluated = self.engine.calculate_loaded_rate(self.exempt_arch)
        self.assertTrue(evaluated.is_compliant)
        self.assertEqual(evaluated.statutory_minimum_floor, 0.0)
        # Direct: 135 + 13.5 (10%) + 2.025 (1.5%) = 150.525
        # Overhead: 150.525 * 1.15 = 173.10375
        # Profit: 173.10375 * 1.15 = 199.07
        self.assertEqual(evaluated.loaded_hourly_rate, 199.07)

    def test_calculate_loaded_rate_prevailing_wage_compliant(self) -> None:
        evaluated = self.engine.calculate_loaded_rate(self.compliant_trade)
        self.assertTrue(evaluated.is_compliant)
        self.assertGreater(evaluated.loaded_hourly_rate, evaluated.statutory_minimum_floor)
        self.assertEqual(evaluated.loaded_hourly_rate, 143.15)
        self.assertEqual(evaluated.statutory_minimum_floor, 110.64)

    def test_calculate_loaded_rate_wage_deficit_detection(self) -> None:
        # Underpay trade mechanic ($45/hr base vs $60.50 statutory requirement)
        underpaid_trade = self.compliant_trade.model_copy(
            update={"base_hourly_rate": 45.00, "fringe_hourly_rate": 20.00}
        )
        evaluated = self.engine.calculate_loaded_rate(underpaid_trade)
        self.assertFalse(evaluated.is_compliant)

    def test_build_fee_schedule_computes_accurate_totals(self) -> None:
        req_trade = StaffingRequirement(
            role_id="ROLE-ELEC-01",
            labor_category=self.compliant_trade,
            headcount=4,
            total_hours=8000.0,
        )
        req_arch = StaffingRequirement(
            role_id="ROLE-ARCH-02",
            labor_category=self.exempt_arch,
            headcount=1,
            total_hours=1800.0,
        )

        result = self.engine.build_fee_schedule(
            solicitation_number=self.solicitation_pin,
            staffing=[req_trade, req_arch],
            prevailing_wage_mandated=True,
            materials_and_odc=1_450_000.0,
        )

        self.assertTrue(result.is_fully_compliant)
        self.assertEqual(result.total_billable_hours, 9800.0)
        # Labor: (8000 * 143.15) + (1800 * 199.07) = 1,145,200 + 358,326 = 1,503,526.0
        self.assertEqual(result.total_labor_cost, 1_503_526.0)
        self.assertEqual(result.total_contract_price, 2_953_526.0)
        self.assertAlmostEqual(result.effective_blended_hourly_rate, 153.42, places=1)
        self.assertEqual(len(result.compliance_alerts), 0)

    def test_build_fee_schedule_flags_missing_trade_when_prevailing_wage_mandated(self) -> None:
        # Prevailing wage is mandated, but vendor only staffed exempt office roles
        req_arch = StaffingRequirement(
            role_id="ROLE-ARCH-02",
            labor_category=self.exempt_arch,
            headcount=1,
            total_hours=1800.0,
        )

        result = self.engine.build_fee_schedule(
            solicitation_number=self.solicitation_pin,
            staffing=[req_arch],
            prevailing_wage_mandated=True,
        )

        self.assertTrue(any("zero PREVAILING_WAGE_TRADE" in alert for alert in result.compliance_alerts))

    def test_generate_certified_payroll_declaration(self) -> None:
        req_trade = StaffingRequirement(
            role_id="ROLE-ELEC-01",
            labor_category=self.compliant_trade,
            headcount=4,
            total_hours=8000.0,
        )
        result = self.engine.build_fee_schedule(
            solicitation_number=self.solicitation_pin,
            staffing=[req_trade],
            prevailing_wage_mandated=True,
            materials_and_odc=500_000.0,
        )

        declaration = self.engine.generate_certified_payroll_declaration(
            result=result,
            vendor_name="Soko Platform LLC",
            certifying_officer="Managing Director",
        )

        self.assertIn("STATUTORY PREVAILING WAGE & CERTIFIED PAYROLL COMPLIANCE DECLARATION", declaration)
        self.assertIn("Soko Platform LLC", declaration)
        self.assertIn("Managing Director", declaration)
        self.assertIn("85626P0001", declaration)
        self.assertIn("Form WH-347", declaration)


if __name__ == "__main__":
    unittest.main()
