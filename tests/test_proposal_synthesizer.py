"""Unit tests for ProposalSynthesizerEngine."""

import json
from pathlib import Path
import unittest

from govbid.engines.proposal_synthesizer import ProposalSynthesizerEngine
from govbid.models.pricing import StaffingRequirement
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestProposalSynthesizer(unittest.TestCase):
    """Test suite for Grounded Proposal Prose Synthesizer Engine."""

    def setUp(self) -> None:
        self.parser = RfpParser()
        self.rfp = self.parser.parse_file(str(FIXTURES_DIR / "sample_rfp.txt"))

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            self.vendor = VendorProfile(**json.load(f))

        with open(FIXTURES_DIR / "sample_staffing_plan.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.staffing = [StaffingRequirement(**s) for s in data["staffing"]]

        self.engine = ProposalSynthesizerEngine()

    def test_synthesize_proposal_full_draft(self) -> None:
        draft = self.engine.synthesize_proposal(
            rfp=self.rfp,
            vendor=self.vendor,
            staffing_plan=self.staffing,
            total_bid_amount=4_500_000.0,
            materials_and_odc=350_000.0,
        )

        self.assertEqual(draft.solicitation_number, "85626P0001")
        self.assertIn("Soko Platform", draft.vendor_name)
        self.assertEqual(len(draft.sections), 5)

        section_ids = [s.section_id for s in draft.sections]
        self.assertIn("SEC-01-EXECUTIVE-SUMMARY", section_ids)
        self.assertIn("SEC-02-TECHNICAL-APPROACH", section_ids)
        self.assertIn("SEC-03-PAST-PERFORMANCE", section_ids)
        self.assertIn("SEC-04-SCHEDULE-B-MWBE", section_ids)
        self.assertIn("SEC-05-COMMERCIAL-COST", section_ids)

        self.assertGreaterEqual(draft.total_citations, 5)
        self.assertGreaterEqual(draft.total_words, 400)
        self.assertIn("FORMAL PROPOSAL RESPONSE", draft.full_markdown)
        self.assertIn("James Ambenge", draft.full_markdown)
        self.assertIn("85626P0001", draft.full_markdown)
        self.assertIn("PAST-DCAS-01", draft.full_markdown)
        self.assertIn("PAST-SOKO-02", draft.full_markdown)
        self.assertIn("Apex Telematics", draft.full_markdown)
        self.assertIn("CipherShield Security", draft.full_markdown)

    def test_synthesize_proposal_without_staffing_plan(self) -> None:
        draft = self.engine.synthesize_proposal(
            rfp=self.rfp,
            vendor=self.vendor,
            staffing_plan=None,
        )
        self.assertEqual(len(draft.sections), 5)
        self.assertGreaterEqual(draft.total_words, 300)
        self.assertIn("NY State Labor Law Section 220", draft.full_markdown)


if __name__ == "__main__":
    unittest.main()
