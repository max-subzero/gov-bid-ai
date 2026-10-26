"""Unit tests for NYC PASSPort / FAR 52.209-5 ResponsibilityAuditor."""

import unittest
from govbid.engines.responsibility_auditor import (
    ResponsibilityAuditor,
    ResponsibilityStatus,
    VendorResponsibilityDisclosure,
)


class TestResponsibilityAuditor(unittest.TestCase):
    def setUp(self) -> None:
        self.auditor = ResponsibilityAuditor()

    def test_clean_vendor_returns_responsible_and_perfect_score(self) -> None:
        payload = {
            "vendor_id": "VEND-NYC-100",
            "vendor_name": "Metro Transit Telemetry Corp.",
            "debarment_or_suspension": False,
            "tax_liens_unresolved": False,
            "osha_or_labor_violations": 0,
            "prevailing_wage_debarment": False,
            "criminal_convictions_5yr": False,
            "conflict_of_interest_disclosed": False,
            "caution_flags_remediated": False,
            "IntegrityOfficerCertified": True,
        }
        result = self.auditor.evaluate(payload)

        self.assertEqual(result.status, ResponsibilityStatus.RESPONSIBLE.value)
        self.assertEqual(result.status, "RESPONSIBLE")
        self.assertEqual(result.integrity_score, 100.0)
        self.assertEqual(len(result.findings), 0)

    def test_remediated_caution_flags_return_conditional_responsibility(self) -> None:
        payload = {
            "vendor_id": "VEND-NYC-204",
            "vendor_name": "Tri-State Signal Systems LLC",
            "debarment_or_suspension": False,
            "tax_liens_unresolved": True,
            "osha_or_labor_violations": 1,
            "prevailing_wage_debarment": False,
            "criminal_convictions_5yr": False,
            "conflict_of_interest_disclosed": True,
            "caution_flags_remediated": True,
            "IntegrityOfficerCertified": True,
        }
        result = self.auditor.audit(payload)

        self.assertEqual(
            result.status,
            ResponsibilityStatus.CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED.value,
        )
        self.assertGreater(result.integrity_score, 0.0)
        self.assertLess(result.integrity_score, 100.0)
        codes = {f.code for f in result.findings}
        self.assertIn("RESP-TAX-004", codes)
        self.assertIn("RESP-OSHA-005", codes)
        self.assertIn("RESP-COI-006", codes)
        for finding in result.findings:
            self.assertTrue(finding.statute)
            self.assertTrue(finding.detail)
            self.assertTrue(finding.remediation)

    def test_statutory_debarment_and_prevailing_wage_disqualification(self) -> None:
        payload = VendorResponsibilityDisclosure(
            vendor_id="VEND-NYC-999",
            vendor_name="Disqualified Contractors Inc.",
            debarment_or_suspension=True,
            tax_liens_unresolved=False,
            osha_or_labor_violations=0,
            prevailing_wage_debarment=True,
            criminal_convictions_5yr=False,
            conflict_of_interest_disclosed=False,
            caution_flags_remediated=True,
            IntegrityOfficerCertified=True,
        )
        result = self.auditor.evaluate(payload)

        self.assertEqual(
            result.status,
            ResponsibilityStatus.NON_RESPONSIBLE_DISQUALIFIED.value,
        )
        self.assertEqual(result.integrity_score, 0.0)
        codes = {f.code for f in result.findings}
        self.assertIn("RESP-DEBAR-001", codes)
        self.assertIn("RESP-PWAGE-002", codes)

    def test_missing_integrity_certification_or_unremediated_crime_disqualifies(self) -> None:
        payload = {
            "vendor_id": "VEND-NYC-403",
            "vendor_name": "Unverified Bidding Entity",
            "debarment_or_suspension": False,
            "tax_liens_unresolved": False,
            "osha_or_labor_violations": 0,
            "prevailing_wage_debarment": False,
            "criminal_convictions_5yr": True,
            "conflict_of_interest_disclosed": False,
            "caution_flags_remediated": False,
            "IntegrityOfficerCertified": False,
        }
        result = self.auditor.evaluate(payload)

        self.assertEqual(result.status, "NON_RESPONSIBLE_DISQUALIFIED")
        self.assertEqual(result.integrity_score, 0.0)
        codes = {f.code for f in result.findings}
        self.assertIn("RESP-CRIM-003", codes)
        self.assertIn("RESP-CERT-007", codes)

    def test_rfc7807_problem_details_serialization(self) -> None:
        disq_result = self.auditor.evaluate(
            {
                "vendor_id": "VEND-ERR-500",
                "vendor_name": "Debarred Corp",
                "debarment_or_suspension": True,
                "IntegrityOfficerCertified": True,
            }
        )
        problem = disq_result.to_problem_details(
            instance="urn:nyc:passport:submission:2026-8841"
        )

        self.assertEqual(problem["status"], 403)
        self.assertEqual(problem["code"], "ERR_VENDOR_NON_RESPONSIBLE")
        self.assertEqual(problem["instance"], "urn:nyc:passport:submission:2026-8841")
        self.assertIn("vendor-non-responsible-disqualified", problem["type"])
        self.assertEqual(problem["responsibility_status"], "NON_RESPONSIBLE_DISQUALIFIED")
        self.assertEqual(len(problem["findings"]), 1)
        self.assertEqual(problem["findings"][0]["code"], "RESP-DEBAR-001")

        cond_result = self.auditor.evaluate(
            {
                "vendor_id": "VEND-WARN-202",
                "vendor_name": "Conditional Corp",
                "conflict_of_interest_disclosed": True,
                "caution_flags_remediated": True,
                "IntegrityOfficerCertified": True,
            }
        )
        cond_problem = cond_result.to_problem_details()
        self.assertEqual(cond_problem["status"], 422)
        self.assertEqual(cond_problem["code"], "WARN_CONDITIONAL_RESPONSIBILITY")
        self.assertEqual(
            cond_problem["responsibility_status"],
            "CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
