"""Unit tests for PortalConnectorEngine and automated opportunity triage."""

import json
from pathlib import Path
import unittest
from govbid.connectors.portal_connector import PortalConnectorEngine
from govbid.models.portal import PortalSource, SetAsideType
from govbid.models.vendor import VendorProfile

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestPortalConnectorEngine(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = PortalConnectorEngine()

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            self.vendor = VendorProfile(**json.load(f))

        with open(FIXTURES_DIR / "sample_sam_gov_feed.json", "r", encoding="utf-8") as f:
            self.sam_feed_raw = json.load(f)

        with open(FIXTURES_DIR / "sample_city_record_feed.json", "r", encoding="utf-8") as f:
            self.city_feed_raw = json.load(f)

    def test_parse_sam_gov_feed(self) -> None:
        opps = self.engine.parse_sam_gov_feed(self.sam_feed_raw)
        self.assertEqual(len(opps), 3)

        opp1 = opps[0]
        self.assertEqual(opp1.notice_id, "fed-sam-opp-001")
        self.assertEqual(opp1.solicitation_number, "W911NF-26-R-0042")
        self.assertEqual(opp1.source, PortalSource.SAM_GOV)
        self.assertEqual(opp1.set_aside, SetAsideType.TOTAL_SMALL_BUSINESS)
        self.assertIn("DEPT OF DEFENSE", opp1.agency)
        self.assertEqual(opp1.naics_code, "541512")
        self.assertEqual(len(opp1.attachment_urls), 1)

    def test_parse_city_record_feed(self) -> None:
        opps = self.engine.parse_city_record_feed(self.city_feed_raw)
        self.assertEqual(len(opps), 2)

        opp1 = opps[0]
        self.assertEqual(opp1.notice_id, "85626P0001")
        self.assertEqual(opp1.solicitation_number, "85626P0001")
        self.assertEqual(opp1.source, PortalSource.NYC_CITY_RECORD)
        self.assertIn("DCAS", opp1.agency)
        self.assertIn("Fleet Telematics", opp1.title)

    def test_triage_opportunities_ranks_and_flags_fatal_disqualifiers(self) -> None:
        opps = self.engine.parse_sam_gov_feed(self.sam_feed_raw)
        report = self.engine.triage_opportunities(opps, self.vendor)

        self.assertEqual(report.total_scanned, 3)
        self.assertEqual(report.qualified_count, 2)
        self.assertEqual(report.disqualified_count, 1)

        # Ranked list should have highest fit score first
        top_opp = report.ranked_opportunities[0]
        self.assertEqual(top_opp.opportunity.notice_id, "fed-sam-opp-001")
        self.assertEqual(top_opp.recommendation, "GO")
        self.assertEqual(top_opp.fit_score, 100.0)
        self.assertFalse(top_opp.is_disqualified)

        # Disqualified treasury notice (requires 15 yrs, vendor has 6)
        disq_opp = next(
            r for r in report.ranked_opportunities if r.opportunity.notice_id == "fed-sam-opp-002"
        )
        self.assertTrue(disq_opp.is_disqualified)
        self.assertEqual(disq_opp.recommendation, "NO_GO")
        self.assertTrue(any("EXPERIENCE" in d for d in disq_opp.fatal_disqualifiers))

    def test_triage_min_score_filter(self) -> None:
        opps = self.engine.parse_sam_gov_feed(self.sam_feed_raw)
        # Filter strictly above 75 fit score
        report = self.engine.triage_opportunities(opps, self.vendor, min_fit_score=75.0)

        # Only the 2 qualified opportunities should be present
        self.assertEqual(len(report.ranked_opportunities), 2)
        for r in report.ranked_opportunities:
            self.assertGreaterEqual(r.fit_score, 75.0)

    def test_empty_feed_returns_empty_report(self) -> None:
        report = self.engine.triage_opportunities([], self.vendor)
        self.assertEqual(report.total_scanned, 0)
        self.assertEqual(len(report.ranked_opportunities), 0)


if __name__ == "__main__":
    unittest.main()
