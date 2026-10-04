"""Parser for government procurement solicitations and RFPs."""

import re
from typing import Dict, List, Optional
from govbid.models.rfp import EvaluationCriteria, ParsedRfp
from govbid.parsers.clause_detector import ClauseDetector


class RfpParser:
    """Parses raw RFP documents, extracts metadata, evaluation rubrics, and compliance clauses."""

    TITLE_PATTERN = re.compile(r"(?:RFP|SOLICITATION|PROJECT\s+TITLE)[:\s]+([^\n\r]+)", re.IGNORECASE)
    PIN_PATTERN = re.compile(r"(?:PIN|SOLICITATION\s+(?:NO|NUMBER)|RFP\s+#)[:\s]+([A-Z0-9\-_]+)", re.IGNORECASE)
    AGENCY_PATTERN = re.compile(
        r"(?:ISSUED\s+BY|AGENCY|DEPARTMENT)[:\s]+([^\n\r]+)", re.IGNORECASE
    )
    DEADLINE_PATTERN = re.compile(
        r"(?:PROPOSAL\s+DUE\s+DATE|SUBMISSION\s+DEADLINE|DUE\s+DATE)[:\s]+([^\n\r]+)",
        re.IGNORECASE,
    )
    CRITERIA_PATTERN = re.compile(
        r"[-*•]?\s*([^:\n\r]+)[:\-]\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*(?:%|points|pts)",
        re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.detector = ClauseDetector()

    def parse_text(self, content: str) -> ParsedRfp:
        """Parses raw text of a solicitation document into a structured ParsedRfp model."""
        # 1. Extract Solicitation Metadata
        title_match = self.TITLE_PATTERN.search(content)
        title = title_match.group(1).strip() if title_match else "Government Procurement Solicitation"

        pin_match = self.PIN_PATTERN.search(content)
        solicitation_number = pin_match.group(1).strip() if pin_match else "RFP-UNASSIGNED"

        agency_match = self.AGENCY_PATTERN.search(content)
        issuing_agency = agency_match.group(1).strip() if agency_match else "Municipal Agency"

        deadline_match = self.DEADLINE_PATTERN.search(content)
        deadline = deadline_match.group(1).strip() if deadline_match else None

        # Determine jurisdiction
        jurisdiction = "MUNICIPAL"
        upper_text = content.upper()
        if "SAM.GOV" in upper_text or "FAR " in upper_text or "DEFENSE" in upper_text or "DEPARTMENT OF DEFENSE" in upper_text:
            jurisdiction = "FEDERAL"
        elif "NEW YORK STATE" in upper_text or "NYS OGS" in upper_text:
            jurisdiction = "STATE"

        # 2. Extract Evaluation Criteria Rubric
        evaluation_criteria: List[EvaluationCriteria] = []
        crit_id = 1
        for match in self.CRITERIA_PATTERN.finditer(content):
            crit_name = match.group(1).strip()
            pts = float(match.group(2))
            if 5.0 <= pts <= 100.0:  # Reasonable point or percentage weights
                evaluation_criteria.append(
                    EvaluationCriteria(
                        criterion_id=f"CRIT-{crit_id:02d}",
                        title=crit_name,
                        weight_percentage=pts,
                        description=f"Evaluation factor weighted at {pts}%",
                    )
                )
                crit_id += 1

        # 3. Detect Compliance Clauses
        clauses = self.detector.detect_clauses(content)

        return ParsedRfp(
            title=title,
            solicitation_number=solicitation_number,
            issuing_agency=issuing_agency,
            jurisdiction=jurisdiction,
            submission_deadline=deadline,
            clauses=clauses,
            evaluation_criteria=evaluation_criteria,
            raw_sections={"body": content},
        )
