"""Unit tests for ProposalGrounder."""

import json
from pathlib import Path
import unittest
from govbid.engines.proposal_grounder import ProposalGrounder
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestProposalGrounder(unittest.TestCase):
    def setUp(self) -> None:
        with open(FIXTURES_DIR / "sample_rfp.txt", "r", encoding="utf-8") as f:
            content = f.read()
        self.rfp = RfpParser().parse_text(content)

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.vendor = VendorProfile(**data)
        self.grounder = ProposalGrounder()

    def test_grounder_scores_verified_claims_high(self) -> None:
        grounded_draft = (
            "Our team has demonstrated experience with City of New York DCAS deploying fleet telematics and compliance reporting. "
            "We managed compliance exception reporting across municipal vehicles and reconciled expenditures."
        )
        score, ungrounded = self.grounder.evaluate_groundedness(grounded_draft, self.vendor)
        self.assertGreaterEqual(score, 0.7)
        self.assertEqual(len(ungrounded), 0)

    def test_grounder_flags_hallucinated_claims(self) -> None:
        hallucinated_draft = (
            "We previously built orbital rocket launch telemetry systems for NASA aerospace spacecraft. "
            "Additionally we developed pharmaceutical biotechnology vaccine distribution pipelines."
        )
        score, ungrounded = self.grounder.evaluate_groundedness(hallucinated_draft, self.vendor)
        self.assertLessEqual(score, 0.3)
        self.assertGreater(len(ungrounded), 0)

    def test_grounder_generates_outline_with_citations(self) -> None:
        outline = self.grounder.generate_grounded_outline(self.rfp, self.vendor)
        self.assertEqual(len(outline), len(self.rfp.evaluation_criteria))
        all_points = " ".join([p for points in outline.values() for p in points])
        self.assertTrue("PAST-DCAS-01" in all_points or "PAST-SOKO-02" in all_points)


if __name__ == "__main__":
    unittest.main()
