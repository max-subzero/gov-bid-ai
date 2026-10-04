"""Unit tests for GapAnalyzer."""

import json
from pathlib import Path
import unittest
from govbid.engines.gap_analyzer import GapAnalyzer
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGapAnalyzer(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "sample_rfp.txt", "r", encoding="utf-8") as f:
            content = f.read()
        self.rfp = RfpParser().parse_text(content)

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.vendor = VendorProfile(**data)
        self.analyzer = GapAnalyzer()

    def test_analyzer_recommends_go_for_qualified_vendor(self) -> None:
        result = self.analyzer.analyze(self.rfp, self.vendor)
        self.assertEqual(result.recommendation, "GO")
        self.assertGreaterEqual(result.fit_score, 80.0)
        self.assertEqual(len(result.disqualifiers), 0)
        self.assertTrue(any("public sector contract experience" in s for s in result.competitive_strengths))

    def test_analyzer_recommends_conditional_go_for_insurance_deficit(self) -> None:
        self.vendor.insurance_general_liability = 2_000_000.0
        result = self.analyzer.analyze(self.rfp, self.vendor)
        
        self.assertEqual(result.recommendation, "CONDITIONAL_GO")
        self.assertEqual(len(result.disqualifiers), 1)
        self.assertEqual(result.disqualifiers[0].rule_category, "INSURANCE")

    def test_analyzer_recommends_no_go_for_low_experience(self) -> None:
        self.vendor.years_in_business = 1
        self.vendor.past_performance = []
        result = self.analyzer.analyze(self.rfp, self.vendor)
        
        self.assertEqual(result.recommendation, "NO_GO")
        self.assertLessEqual(result.fit_score, 50.0)


if __name__ == "__main__":
    unittest.main()
