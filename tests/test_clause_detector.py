"""Unit tests for ClauseDetector."""

import unittest
from govbid.models.rfp import ClauseCategory
from govbid.parsers.clause_detector import ClauseDetector


class TestClauseDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = ClauseDetector()

    def test_detect_mwbe_goal(self) -> None:
        text = "Proposers must satisfy a mandatory M/WBE subcontracting goal of 30% under Local Law 1."
        clauses = self.detector.detect_clauses(text)
        
        self.assertGreaterEqual(len(clauses), 1)
        mwbe_clauses = [c for c in clauses if c.category == ClauseCategory.MWBE_SUBCONTRACTING]
        self.assertEqual(len(mwbe_clauses), 1)
        self.assertEqual(mwbe_clauses[0].threshold_value, 30.0)
        self.assertEqual(mwbe_clauses[0].threshold_unit, "%")
        self.assertTrue(mwbe_clauses[0].mandatory)

    def test_detect_prevailing_wage(self) -> None:
        text = "Field technicians are subject to certified payroll and NY Labor Law Section 220 prevailing wage."
        clauses = self.detector.detect_clauses(text)
        
        wage_clauses = [c for c in clauses if c.category == ClauseCategory.PREVAILING_WAGE]
        self.assertEqual(len(wage_clauses), 1)
        self.assertIn("Prevailing Wage", wage_clauses[0].title)

    def test_detect_insurance_thresholds(self) -> None:
        text = (
            "Contractor must provide Commercial General Liability of $5,000,000 "
            "and Cyber Liability Insurance of $2,000,000."
        )
        clauses = self.detector.detect_clauses(text)
        
        gl = next(c for c in clauses if "General Liability" in c.title)
        cyber = next(c for c in clauses if "Cyber Liability" in c.title)
        
        self.assertEqual(gl.threshold_value, 5_000_000.0)
        self.assertEqual(gl.threshold_unit, "USD")
        self.assertEqual(cyber.threshold_value, 2_000_000.0)
        self.assertEqual(cyber.threshold_unit, "USD")

    def test_detect_experience_and_registrations(self) -> None:
        text = "Proposers must have a minimum of 5 years of prior experience and active NYC PASSPort enrollment."
        clauses = self.detector.detect_clauses(text)
        
        exp = next(c for c in clauses if c.category == ClauseCategory.EXPERIENCE_THRESHOLD)
        passport = next(c for c in clauses if "PASSPort" in c.title)
        
        self.assertEqual(exp.threshold_value, 5.0)
        self.assertTrue(passport.mandatory)


if __name__ == "__main__":
    unittest.main()
