"""Unit tests for GovBid AI Enterprise REST API & Interactive Console."""

import json
from pathlib import Path
import unittest
from fastapi.testclient import TestClient

from govbid.api.app import app
from govbid import __version__

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestGovBidAPI(unittest.TestCase):
    """Test suite for FastAPI endpoints."""

    def setUp(self) -> None:
        self.client = TestClient(app)
        with open(FIXTURES_DIR / "sample_rfp.txt", "r", encoding="utf-8") as f:
            self.sample_rfp_text = f.read()

        with open(FIXTURES_DIR / "sample_vendor.json", "r", encoding="utf-8") as f:
            self.sample_vendor = json.load(f)

        with open(FIXTURES_DIR / "sample_staffing_plan.json", "r", encoding="utf-8") as f:
            self.sample_staffing = json.load(f)

        with open(FIXTURES_DIR / "sample_addendum.txt", "r", encoding="utf-8") as f:
            self.sample_addendum_text = f.read()

        with open(FIXTURES_DIR / "sample_sam_gov_feed.json", "r", encoding="utf-8") as f:
            self.sample_sam_feed = json.load(f)

        with open(FIXTURES_DIR / "sample_city_record_feed.json", "r", encoding="utf-8") as f:
            self.sample_city_feed = json.load(f)

    def test_health_check(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["version"], __version__)
        self.assertIn("GovBid AI", data["service"])

    def test_console_and_redirect(self) -> None:
        # Test root redirect
        res_root = self.client.get("/", follow_redirects=False)
        self.assertEqual(res_root.status_code, 307)
        self.assertEqual(res_root.headers["location"], "/console")

        # Test console HTML
        res_console = self.client.get("/console")
        self.assertEqual(res_console.status_code, 200)
        self.assertIn("text/html", res_console.headers["content-type"])
        self.assertIn("GovBid AI", res_console.text)
        self.assertIn("James Ambenge", res_console.text)

    def test_sample_feed_endpoints(self) -> None:
        res_sam = self.client.get("/api/v1/sample/sam-gov")
        self.assertEqual(res_sam.status_code, 200)
        self.assertIn("opportunitiesData", res_sam.json())

        res_city = self.client.get("/api/v1/sample/city-record")
        self.assertEqual(res_city.status_code, 200)
        self.assertIsInstance(res_city.json(), list)

    def test_api_parse_solicitation(self) -> None:
        response = self.client.post(
            "/api/v1/parse",
            json={"text": self.sample_rfp_text, "filename": "sample_rfp.txt"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["solicitation_number"], "85626P0001")
        self.assertGreaterEqual(len(data["clauses"]), 5)

    def test_api_check_disqualification(self) -> None:
        response = self.client.post(
            "/api/v1/check",
            json={"rfp_text": self.sample_rfp_text, "vendor": self.sample_vendor},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["solicitation_number"], "85626P0001")
        self.assertTrue(data["is_compliant"])
        self.assertEqual(data["findings_count"], 0)

    def test_api_evaluate_fit(self) -> None:
        response = self.client.post(
            "/api/v1/evaluate",
            json={"rfp_text": self.sample_rfp_text, "vendor": self.sample_vendor},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["recommendation"], "GO")
        self.assertGreaterEqual(data["fit_score"], 80.0)

    def test_api_diff_addendum(self) -> None:
        response = self.client.post(
            "/api/v1/diff",
            json={
                "base_text": self.sample_rfp_text,
                "addendum_text": self.sample_addendum_text,
                "solicitation_number": "85626P0001",
                "addendum_id": "ADDENDUM-01",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["solicitation_number"], "85626P0001")
        self.assertIn("December 1, 2026", data["new_submission_deadline"])
        self.assertEqual(len(data["qa_pairs"]), 3)

    def test_api_schedule_b_recommend(self) -> None:
        response = self.client.post(
            "/api/v1/schedule-b",
            json={
                "solicitation_number": "85626P0001",
                "total_bid_amount": 4500000.0,
                "mandatory_goal_percentage": 30.0,
                "candidates": self.sample_vendor["candidate_subcontractors"],
                "recommend": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "COMPLIANT")
        self.assertEqual(data["actual_mwbe_percentage"], 30.0)
        self.assertEqual(len(data["allocations"]), 2)

    def test_api_pricing_and_certified_payroll(self) -> None:
        response = self.client.post(
            "/api/v1/pricing",
            json={
                "solicitation_number": "85626P0001",
                "staffing": self.sample_staffing["staffing"],
                "prevailing_wage_mandated": True,
                "materials_and_odc": 350000.0,
                "vendor_name": "Soko Platform LLC",
                "generate_certified_payroll": True,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        model_result = data["model_result"]
        self.assertTrue(model_result["is_fully_compliant"])
        self.assertEqual(model_result["total_billable_hours"], 13000.0)
        self.assertIsNotNone(data["certified_payroll_declaration"])
        self.assertIn("STATUTORY PREVAILING WAGE & CERTIFIED PAYROLL COMPLIANCE DECLARATION", data["certified_payroll_declaration"])

    def test_api_portal_triage(self) -> None:
        response = self.client.post(
            "/api/v1/triage",
            json={
                "feed_data": self.sample_sam_feed,
                "vendor": self.sample_vendor,
                "min_score": 0.0,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_scanned"], 3)
        self.assertEqual(data["qualified_count"], 2)
        self.assertEqual(data["disqualified_count"], 1)

    def test_api_draft_proposal(self) -> None:
        response = self.client.post(
            "/api/v1/draft",
            json={
                "rfp_text": self.sample_rfp_text,
                "vendor": self.sample_vendor,
                "staffing": self.sample_staffing["staffing"],
                "total_bid_amount": 4500000.0,
                "materials_and_odc": 350000.0,
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["solicitation_number"], "85626P0001")
        self.assertEqual(len(data["sections"]), 5)
        self.assertGreaterEqual(data["total_words"], 500)
        self.assertGreaterEqual(data["total_citations"], 5)
        self.assertIn("FORMAL PROPOSAL RESPONSE", data["full_markdown"])

    def test_rfc7807_validation_error_format(self) -> None:
        # Missing required 'text' field in ParseRequest
        response = self.client.post("/api/v1/parse", json={})
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertEqual(data["code"], "UNPROCESSABLE_ENTITY")
        self.assertIn("error", data)
        self.assertIn("details", data)
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()
