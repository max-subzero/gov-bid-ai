"""Unit tests for DisqualificationGuard."""

import json
from pathlib import Path
import unittest
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDisqualificationGuard(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "sample_rfp.txt", "r", encoding="utf-8") as f:
            content = f.read()
        self.rfp = RfpParser().parse_text(content)

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.vendor = VendorProfile(**data)
        self.guard = DisqualificationGuard()

    def test_guard_passes_fully_qualified_vendor(self) -> None:
        findings = self.guard.evaluate(self.rfp, self.vendor)
        self.assertEqual(len(findings), 0)

    def test_guard_flags_insurance_deficit(self) -> None:
        self.vendor.insurance_general_liability = 1_000_000.0
        findings = self.guard.evaluate(self.rfp, self.vendor)
        
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].rule_category, "INSURANCE")
        self.assertIn("General Liability", findings[0].title)
        self.assertIn("Deficit: $4,000,000", findings[0].detail)

    def test_guard_flags_missing_passport_registration(self) -> None:
        self.vendor.active_registrations = []
        findings = self.guard.evaluate(self.rfp, self.vendor)
        
        passport_finding = next(f for f in findings if f.rule_category == "REGISTRATION")
        self.assertIn("NYC PASSPort", passport_finding.title)
        self.assertTrue(passport_finding.disqualification_risk)

    def test_guard_flags_experience_deficit(self) -> None:
        self.vendor.years_in_business = 2  # RFP requires 5
        findings = self.guard.evaluate(self.rfp, self.vendor)
        
        exp_finding = next(f for f in findings if f.rule_category == "EXPERIENCE")
        self.assertIn("Below Minimum Proposer Threshold", exp_finding.title)
        self.assertEqual(exp_finding.severity, "CRITICAL")


if __name__ == "__main__":
    unittest.main()
