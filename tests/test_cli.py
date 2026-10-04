"""Unit tests for GovBid CLI commands."""

import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from govbid.cli import main

FIXTURES_DIR = Path(__file__).parent / "fixtures"
RFP_PATH = str(FIXTURES_DIR / "sample_rfp.txt")
VENDOR_PATH = str(FIXTURES_DIR / "sample_vendor.json")
STAFFING_PATH = str(FIXTURES_DIR / "sample_staffing_plan.json")


class TestGovBidCLI(unittest.TestCase):
    def test_cli_parse(self) -> None:
        with patch("sys.argv", ["govbid", "parse", RFP_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("SOLICITATION METADATA: 85626P0001", out)
            self.assertIn("M/WBE Participation Goal (30.0%)", out)

    def test_cli_parse_json(self) -> None:
        with patch("sys.argv", ["govbid", "--json", "parse", RFP_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["solicitation_number"], "85626P0001")
            self.assertGreaterEqual(len(data["clauses"]), 5)

    def test_cli_check(self) -> None:
        with patch("sys.argv", ["govbid", "check", RFP_PATH, VENDOR_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("DISQUALIFICATION AUDIT", out)
            self.assertIn("Zero disqualification triggers detected", out)

    def test_cli_evaluate(self) -> None:
        with patch("sys.argv", ["govbid", "evaluate", RFP_PATH, VENDOR_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("BID QUALIFICATION AUDIT", out)
            self.assertIn("Recommendation: GO", out)

    def test_cli_outline(self) -> None:
        with patch("sys.argv", ["govbid", "outline", RFP_PATH, VENDOR_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("GROUNDED PROPOSAL OUTLINE", out)
            self.assertTrue("PAST-DCAS-01" in out or "PAST-SOKO-02" in out)


    def test_cli_diff(self) -> None:
        addendum_path = str(FIXTURES_DIR / "sample_addendum.txt")
        with patch("sys.argv", ["govbid", "diff", RFP_PATH, addendum_path]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("ADDENDUM DIFFERENTIAL AUDIT", out)
            self.assertIn("NEW SUBMISSION DEADLINE: December 1, 2026", out)
            self.assertIn("Threshold Modified", out)

    def test_cli_diff_json(self) -> None:
        addendum_path = str(FIXTURES_DIR / "sample_addendum.txt")
        with patch("sys.argv", ["govbid", "--json", "diff", RFP_PATH, addendum_path]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["solicitation_number"], "85626P0001")
            self.assertGreaterEqual(len(data["diff_items"]), 2)
            self.assertEqual(len(data["qa_pairs"]), 3)

    def test_cli_schedule_b(self) -> None:
        with patch("sys.argv", ["govbid", "schedule-b", RFP_PATH, VENDOR_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("SCHEDULE B M/WBE UTILIZATION AUDIT: 85626P0001", out)
            self.assertIn("Status:                      [COMPLIANT]", out)
            self.assertIn("Apex Telematics Wiring", out)
            self.assertIn("CipherShield Security", out)

    def test_cli_schedule_b_json(self) -> None:
        with patch("sys.argv", ["govbid", "--json", "schedule-b", RFP_PATH, VENDOR_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["solicitation_number"], "85626P0001")
            self.assertEqual(data["status"], "COMPLIANT")
            self.assertEqual(data["actual_mwbe_percentage"], 30.0)
            self.assertEqual(len(data["allocations"]), 2)

    def test_cli_price(self) -> None:
        with patch("sys.argv", ["govbid", "price", RFP_PATH, STAFFING_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            out = mock_out.getvalue()
            self.assertIn("COMMERCIAL PRICING & PREVAILING WAGE AUDIT: 85626P0001", out)
            self.assertIn("Compliance Status:           [COMPLIANT - ZERO STATUTORY DEFICITS]", out)
            self.assertIn("Field Telematics Installation Electrician", out)
            self.assertIn("Principal Cloud Solutions Architect", out)

    def test_cli_price_json(self) -> None:
        with patch("sys.argv", ["govbid", "--json", "price", RFP_PATH, STAFFING_PATH]), patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            main()
            data = json.loads(mock_out.getvalue())
            self.assertEqual(data["solicitation_number"], "85626P0001")
            self.assertTrue(data["is_fully_compliant"])
            self.assertEqual(len(data["staffing_breakdown"]), 4)
            self.assertEqual(data["total_billable_hours"], 13000.0)


if __name__ == "__main__":
    unittest.main()
