"""Schedule B M/WBE Subcontractor Utilization Plan & Waiver Allocation Engine."""

from typing import Dict, List, Optional
from govbid.models.mwbe import (
    GoodFaithEffortRecord,
    MwbeCertificationType,
    ScheduleBPlan,
    ScheduleBStatus,
    SubcontractorAllocation,
)


class ScheduleBAllocator:
    """Computes, validates, and optimizes Schedule B M/WBE subcontractor utilization plans."""

    RECOGNIZED_AGENCIES = {
        "NYC SBS",
        "NEW YORK CITY DEPARTMENT OF SMALL BUSINESS SERVICES",
        "NYS ESD",
        "NEW YORK STATE EMPIRE STATE DEVELOPMENT",
        "PANYNJ",
        "PORT AUTHORITY OF NY & NJ",
        "SBA",
        "MTA",
    }

    def calculate_plan(
        self,
        solicitation_number: str,
        total_bid_amount: float,
        mandatory_goal_percentage: float,
        allocations: List[SubcontractorAllocation],
        good_faith_efforts: Optional[List[GoodFaithEffortRecord]] = None,
        waiver_justification: Optional[str] = None,
    ) -> ScheduleBPlan:
        """Calculates a comprehensive Schedule B Utilization Plan and validates compliance."""
        if total_bid_amount <= 0:
            raise ValueError("Total bid amount must be strictly greater than $0.00")
        if mandatory_goal_percentage < 0 or mandatory_goal_percentage > 100:
            raise ValueError("Mandatory M/WBE goal percentage must be between 0.0% and 100.0%")

        gfe_list = good_faith_efforts or []
        validation_messages: List[str] = []

        # 1. Calculate Required Dollar Threshold
        required_mwbe_amount = round(total_bid_amount * (mandatory_goal_percentage / 100.0), 2)

        # 2. Process and Validate Allocations
        processed_allocations: List[SubcontractorAllocation] = []
        actual_mwbe_amount = 0.0
        mbe_amount = 0.0
        wbe_amount = 0.0

        for alloc in allocations:
            if alloc.allocated_amount <= 0:
                validation_messages.append(
                    f"Subcontractor '{alloc.company_name}' has non-positive allocation: ${alloc.allocated_amount:,.2f}"
                )
                continue

            pct = round((alloc.allocated_amount / total_bid_amount) * 100.0, 2)
            updated_alloc = alloc.model_copy(update={"percentage_of_total": pct})
            processed_allocations.append(updated_alloc)

            actual_mwbe_amount += alloc.allocated_amount

            # Track demographic splits
            if alloc.certification_type in [MwbeCertificationType.MBE, MwbeCertificationType.MWBE]:
                mbe_amount += alloc.allocated_amount
            if alloc.certification_type in [MwbeCertificationType.WBE, MwbeCertificationType.MWBE]:
                wbe_amount += alloc.allocated_amount

            # Verify certifying authority
            agency_clean = alloc.certifying_agency.strip().upper()
            if not any(rec in agency_clean for rec in self.RECOGNIZED_AGENCIES):
                validation_messages.append(
                    f"Subcontractor '{alloc.company_name}' cites unrecognized certification agency: '{alloc.certifying_agency}'. "
                    "Ensure certification is officially recognized under NYC Local Law 1 or NYS ESD."
                )

        actual_mwbe_amount = round(actual_mwbe_amount, 2)
        actual_mwbe_percentage = round((actual_mwbe_amount / total_bid_amount) * 100.0, 2)
        mbe_percentage = round((mbe_amount / total_bid_amount) * 100.0, 2)
        wbe_percentage = round((wbe_amount / total_bid_amount) * 100.0, 2)

        # 3. Determine Shortfalls and Compliance Status
        shortfall_amount = max(0.0, round(required_mwbe_amount - actual_mwbe_amount, 2))
        shortfall_percentage = max(0.0, round(mandatory_goal_percentage - actual_mwbe_percentage, 2))

        if actual_mwbe_percentage >= mandatory_goal_percentage:
            status = ScheduleBStatus.COMPLIANT
        elif waiver_justification or len(gfe_list) > 0:
            status = ScheduleBStatus.WAIVER_REQUESTED
            validation_messages.append(
                f"Schedule B M/WBE deficit detected ({shortfall_percentage:.1f}% shortfall). "
                "Accompanied by Good Faith Efforts (GFE) waiver request packet."
            )
        elif actual_mwbe_amount > 0:
            status = ScheduleBStatus.PARTIAL_DEFICIT
            validation_messages.append(
                f"CRITICAL DISQUALIFIER: Subcontractor allocation of {actual_mwbe_percentage:.1f}% falls short of "
                f"mandatory {mandatory_goal_percentage:.1f}% goal by ${shortfall_amount:,.2f} ({shortfall_percentage:.1f}%). "
                "Bid will be administratively rejected as non-responsive without an approved Schedule B waiver."
            )
        else:
            status = ScheduleBStatus.FULL_DEFICIT
            validation_messages.append(
                f"FATAL DISQUALIFIER: Zero M/WBE subcontractor participation provided for mandatory {mandatory_goal_percentage:.1f}% goal. "
                "Automatic non-responsive rejection pursuant to NYC PPB rules and Administrative Code § 6-129."
            )

        return ScheduleBPlan(
            solicitation_number=solicitation_number,
            total_bid_amount=total_bid_amount,
            mandatory_goal_percentage=mandatory_goal_percentage,
            required_mwbe_amount=required_mwbe_amount,
            actual_mwbe_amount=actual_mwbe_amount,
            actual_mwbe_percentage=actual_mwbe_percentage,
            mbe_percentage=mbe_percentage,
            wbe_percentage=wbe_percentage,
            status=status,
            allocations=processed_allocations,
            shortfall_amount=shortfall_amount,
            shortfall_percentage=shortfall_percentage,
            good_faith_efforts=gfe_list,
            waiver_justification=waiver_justification,
            validation_messages=validation_messages,
        )

    def recommend_allocations(
        self,
        solicitation_number: str,
        total_bid_amount: float,
        mandatory_goal_percentage: float,
        candidates: List[SubcontractorAllocation],
    ) -> ScheduleBPlan:
        """Intelligently calculates allocations across candidate M/WBE partners to satisfy the mandatory goal."""
        if not candidates:
            return self.calculate_plan(
                solicitation_number=solicitation_number,
                total_bid_amount=total_bid_amount,
                mandatory_goal_percentage=mandatory_goal_percentage,
                allocations=[],
            )

        required_target = round(total_bid_amount * (mandatory_goal_percentage / 100.0), 2)
        # Evenly distribute the required target across qualified candidate subcontractors
        per_sub_target = round(required_target / len(candidates), 2)
        allocated_so_far = 0.0

        sized_allocations: List[SubcontractorAllocation] = []
        for i, sub in enumerate(candidates):
            if i == len(candidates) - 1:
                # Assign remainder to final subcontractor to guarantee zero rounding discrepancy
                amount = round(required_target - allocated_so_far, 2)
            else:
                amount = per_sub_target
                allocated_so_far += amount

            pct = round((amount / total_bid_amount) * 100.0, 2)
            sized_allocations.append(
                sub.model_copy(update={"allocated_amount": amount, "percentage_of_total": pct})
            )

        return self.calculate_plan(
            solicitation_number=solicitation_number,
            total_bid_amount=total_bid_amount,
            mandatory_goal_percentage=mandatory_goal_percentage,
            allocations=sized_allocations,
        )

    def generate_waiver_memo(
        self,
        plan: ScheduleBPlan,
        vendor_name: str,
        proposer_contact: Optional[str] = None,
    ) -> str:
        """Generates an official NYC PPB Part III Schedule B Pre-Bid Waiver Request Memorandum."""
        lines = [
            "=" * 78,
            "SCHEDULE B PART III: REQUEST FOR PRE-BID M/WBE PARTICIPATION GOAL WAIVER",
            "Pursuant to NYC Administrative Code § 6-129 and City PPB Rules",
            "=" * 78,
            f"DATE:             October 2026",
            f"TO:               Agency Chief Contracting Officer (ACCO)",
            f"FROM:             {vendor_name}",
            f"SOLICITATION PIN: {plan.solicitation_number}",
            f"TOTAL PROPOSAL:   ${plan.total_bid_amount:,.2f}",
            "",
            "1. WAIVER REQUEST SUMMARY",
            f"  Mandatory Solicitation M/WBE Goal:    {plan.mandatory_goal_percentage:.1f}% (${plan.required_mwbe_amount:,.2f})",
            f"  Proposed Vendor M/WBE Commitment:    {plan.actual_mwbe_percentage:.1f}% (${plan.actual_mwbe_amount:,.2f})",
            f"  Requested Net Goal Waiver:           {plan.shortfall_percentage:.1f}% (${plan.shortfall_amount:,.2f})",
            "",
            "2. STATUTORY JUSTIFICATION FOR WAIVER REQUEST",
            f"  {plan.waiver_justification or 'Vendor has conducted exhaustive market outreach but documented genuine market unavailability for specialized sub-trades.'}",
            "",
            "3. DOCUMENTED GOOD FAITH EFFORTS (GFE) OUTREACH LOG",
        ]

        if plan.good_faith_efforts:
            for i, gfe in enumerate(plan.good_faith_efforts, 1):
                lines.append(f"  Effort #{i}: [{gfe.action_type}] on {gfe.date_performed}")
                lines.append(f"    Action:    {gfe.description}")
                lines.append(f"    Outreach:  {gfe.firms_contacted} certified firms solicited | {gfe.responses_received} inquiries received")
                lines.append(f"    Outcome:   {gfe.outcome}")
                lines.append("")
        else:
            lines.append("  [WARNING] Zero Good Faith Efforts logs attached. Agency waiver approval requires verified outreach logs.")
            lines.append("")

        lines.extend([
            "4. VENDOR CERTIFICATION",
            "  I hereby certify that the statements made herein and in the attached Good Faith Efforts documentation",
            "  are true, accurate, and complete to the best of my knowledge under penalty of non-responsiveness.",
            "",
            f"  Authorized Representative: {vendor_name}",
            f"  Contact:                   {proposer_contact or 'Legal & Compliance Officer'}",
            "=" * 78,
        ])

        return "\n".join(lines)
