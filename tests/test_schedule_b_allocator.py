"""Unit tests for ScheduleBAllocator engine."""

import unittest
from govbid.engines.schedule_b_allocator import ScheduleBAllocator
from govbid.models.mwbe import (
    EthnicityGenderCategory,
    GoodFaithEffortRecord,
    MwbeCertificationType,
    ScheduleBStatus,
    SubcontractorAllocation,
)


class TestScheduleBAllocator(unittest.TestCase):
    def setUp(self) -> None:
        self.allocator = ScheduleBAllocator()
        self.solicitation_pin = "85626P0001"
        self.total_bid = 4_500_000.0
        self.goal_pct = 30.0

        self.sub_mbe = SubcontractorAllocation(
            subcontractor_id="SUB-01",
            company_name="Apex Telematics Wiring LLC",
            certification_type=MwbeCertificationType.MBE,
            certifying_agency="NYC SBS",
            ethnicity_gender=EthnicityGenderCategory.HISPANIC_AMERICAN,
            scope_of_work="Fleet hardware wiring",
            naics_code="238210",
            allocated_amount=900_000.0,
        )

        self.sub_wbe = SubcontractorAllocation(
            subcontractor_id="SUB-02",
            company_name="CipherShield Security Inc.",
            certification_type=MwbeCertificationType.WBE,
            certifying_agency="NYS ESD",
            ethnicity_gender=EthnicityGenderCategory.NON_MINORITY_FEMALE,
            scope_of_work="Cybersecurity pen testing",
            naics_code="541512",
            allocated_amount=450_000.0,
        )

    def test_plan_compliant_meets_exact_goal(self) -> None:
        plan = self.allocator.calculate_plan(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=self.total_bid,
            mandatory_goal_percentage=self.goal_pct,
            allocations=[self.sub_mbe, self.sub_wbe],
        )

        self.assertEqual(plan.status, ScheduleBStatus.COMPLIANT)
        self.assertEqual(plan.required_mwbe_amount, 1_350_000.0)
        self.assertEqual(plan.actual_mwbe_amount, 1_350_000.0)
        self.assertEqual(plan.actual_mwbe_percentage, 30.0)
        self.assertEqual(plan.mbe_percentage, 20.0)
        self.assertEqual(plan.wbe_percentage, 10.0)
        self.assertEqual(plan.shortfall_amount, 0.0)
        self.assertEqual(plan.shortfall_percentage, 0.0)
        self.assertEqual(len(plan.allocations), 2)

    def test_plan_partial_deficit_flags_disqualification(self) -> None:
        # $6M contract requires $1.8M (30%). Allocating $1.35M leaves a $450k (7.5%) deficit.
        plan = self.allocator.calculate_plan(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=6_000_000.0,
            mandatory_goal_percentage=self.goal_pct,
            allocations=[self.sub_mbe, self.sub_wbe],
        )

        self.assertEqual(plan.status, ScheduleBStatus.PARTIAL_DEFICIT)
        self.assertEqual(plan.required_mwbe_amount, 1_800_000.0)
        self.assertEqual(plan.actual_mwbe_amount, 1_350_000.0)
        self.assertEqual(plan.actual_mwbe_percentage, 22.5)
        self.assertEqual(plan.shortfall_amount, 450_000.0)
        self.assertEqual(plan.shortfall_percentage, 7.5)
        self.assertTrue(any("CRITICAL DISQUALIFIER" in msg for msg in plan.validation_messages))

    def test_plan_full_deficit_zero_allocations(self) -> None:
        plan = self.allocator.calculate_plan(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=self.total_bid,
            mandatory_goal_percentage=self.goal_pct,
            allocations=[],
        )

        self.assertEqual(plan.status, ScheduleBStatus.FULL_DEFICIT)
        self.assertEqual(plan.actual_mwbe_amount, 0.0)
        self.assertEqual(plan.shortfall_percentage, 30.0)
        self.assertTrue(any("FATAL DISQUALIFIER" in msg for msg in plan.validation_messages))

    def test_plan_waiver_with_good_faith_efforts(self) -> None:
        gfe = GoodFaithEffortRecord(
            action_type="DIRECTORY_SEARCH",
            description="Searched NYC SBS Online Directory for certified OBD-II harness suppliers",
            date_performed="2026-10-01",
            firms_contacted=14,
            responses_received=2,
            outcome="No certified firm had required ISO-9001 automotive hardware tooling",
        )

        plan = self.allocator.calculate_plan(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=6_000_000.0,
            mandatory_goal_percentage=self.goal_pct,
            allocations=[self.sub_mbe],  # $900k = 15.0% vs 30% goal
            good_faith_efforts=[gfe],
            waiver_justification="Specialized hardware components proprietary to OEM with no certified M/WBE sources.",
        )

        self.assertEqual(plan.status, ScheduleBStatus.WAIVER_REQUESTED)
        self.assertEqual(plan.shortfall_percentage, 15.0)

        # Generate formal memorandum
        memo = self.allocator.generate_waiver_memo(
            plan=plan,
            vendor_name="Soko Platform LLC",
            proposer_contact="compliance@sokoads.com",
        )
        self.assertIn("SCHEDULE B PART III", memo)
        self.assertIn("Soko Platform LLC", memo)
        self.assertIn("Requested Net Goal Waiver:           15.0%", memo)
        self.assertIn("DIRECTORY_SEARCH", memo)
        self.assertIn("ISO-9001", memo)

    def test_recommend_allocations_distributes_target_evenly(self) -> None:
        # $6M contract with 30% goal = $1.8M target across 2 candidates = $900k each
        candidates = [self.sub_mbe, self.sub_wbe]
        plan = self.allocator.recommend_allocations(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=6_000_000.0,
            mandatory_goal_percentage=self.goal_pct,
            candidates=candidates,
        )

        self.assertEqual(plan.status, ScheduleBStatus.COMPLIANT)
        self.assertEqual(plan.actual_mwbe_amount, 1_800_000.0)
        self.assertEqual(plan.actual_mwbe_percentage, 30.0)
        self.assertEqual(plan.allocations[0].allocated_amount, 900_000.0)
        self.assertEqual(plan.allocations[1].allocated_amount, 900_000.0)

    def test_unrecognized_agency_warning(self) -> None:
        unverified_sub = SubcontractorAllocation(
            subcontractor_id="SUB-99",
            company_name="Local Chamber Partner",
            certification_type=MwbeCertificationType.MBE,
            certifying_agency="Independent Chamber of Commerce",
            scope_of_work="Marketing collateral",
            allocated_amount=1_350_000.0,
        )
        plan = self.allocator.calculate_plan(
            solicitation_number=self.solicitation_pin,
            total_bid_amount=self.total_bid,
            mandatory_goal_percentage=self.goal_pct,
            allocations=[unverified_sub],
        )

        self.assertTrue(any("unrecognized certification agency" in msg for msg in plan.validation_messages))

    def test_invalid_inputs_raise_errors(self) -> None:
        with self.assertRaises(ValueError):
            self.allocator.calculate_plan(
                solicitation_number="PIN1",
                total_bid_amount=0.0,
                mandatory_goal_percentage=30.0,
                allocations=[],
            )

        with self.assertRaises(ValueError):
            self.allocator.calculate_plan(
                solicitation_number="PIN1",
                total_bid_amount=1_000_000.0,
                mandatory_goal_percentage=150.0,
                allocations=[],
            )


if __name__ == "__main__":
    unittest.main()
