"""Unit tests for AddendumDiffEngine."""

from pathlib import Path
import unittest
from govbid.engines.addendum_diff import AddendumDiffEngine
from govbid.models.addendum import ChangeCategory, ChangeSeverity
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestAddendumDiffEngine(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "sample_rfp.txt", "r", encoding="utf-8") as f:
            base_content = f.read()
        self.base_rfp = RfpParser().parse_text(base_content)

        with open(FIXTURES_DIR / "sample_addendum.txt", "r", encoding="utf-8") as f:
            self.addendum_content = f.read()

        self.engine = AddendumDiffEngine()

    def test_diff_identifies_deadline_extension(self) -> None:
        result = self.engine.analyze_diff(self.base_rfp, self.addendum_content)
        
        self.assertIn("Addendum #1", result.addendum_identifier)
        self.assertIsNotNone(result.new_submission_deadline)
        self.assertIn("December 1, 2026", result.new_submission_deadline)
        
        deadline_diff = next(d for d in result.diff_items if d.category == ChangeCategory.DEADLINE_CHANGE)
        self.assertEqual(deadline_diff.severity, ChangeSeverity.CRITICAL)
        self.assertEqual(deadline_diff.original_value, "November 15, 2026")
        self.assertIn("December 1, 2026", deadline_diff.revised_value)

    def test_diff_identifies_insurance_threshold_modification(self) -> None:
        result = self.engine.analyze_diff(self.base_rfp, self.addendum_content)
        
        # In base RFP: $5,000,000. In addendum: $2,000,000
        ins_diff = next(d for d in result.diff_items if d.category == ChangeCategory.INSURANCE_MODIFICATION)
        self.assertEqual(ins_diff.severity, ChangeSeverity.MAJOR)
        self.assertEqual(ins_diff.original_value, "5000000.0 USD")
        self.assertEqual(ins_diff.revised_value, "2000000.0 USD")

    def test_diff_extracts_qa_pairs(self) -> None:
        result = self.engine.analyze_diff(self.base_rfp, self.addendum_content)
        
        self.assertEqual(len(result.qa_pairs), 3)
        self.assertEqual(result.qa_pairs[0].question_number, 1)
        self.assertIn("hardware installation be scheduled", result.qa_pairs[0].question)
        self.assertIn("24/7", result.qa_pairs[0].answer)
        
        self.assertIn("FedRAMP", result.qa_pairs[1].question)
        self.assertIn("GovCloud", result.qa_pairs[1].answer)

    def test_diff_executive_summary(self) -> None:
        result = self.engine.analyze_diff(self.base_rfp, self.addendum_content)
        self.assertIn("Addendum #1 incorporates", result.summary)
        self.assertIn("answers 3 bidder clarification questions", result.summary)


if __name__ == "__main__":
    unittest.main()
