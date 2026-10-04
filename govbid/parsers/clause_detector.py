"""Deterministic clause detector for government procurement solicitations."""

import re
from typing import List, Optional
from govbid.models.rfp import ClauseCategory, ComplianceClause


class ClauseDetector:
    """Detects and categorizes compliance obligations and legal disqualification triggers."""

    # Regex patterns for high-risk procurement clauses
    MWBE_PATTERN = re.compile(
        r"(?:M/WBE|MWBE|minority\s+and\s+women-owned|subcontracting)\s+goal(?:s)?\s*(?:of|is|:|is\s+(?:hereby\s+)?(?:reduced|increased|amended|changed)\s+to)?\s*([0-9]{1,2}(?:\.[0-9]+)?)\s*%",
        re.IGNORECASE,
    )
    
    PREVAILING_WAGE_PATTERN = re.compile(
        r"(?:prevailing\s+wage|labor\s+law\s+(?:section\s+)?220|labor\s+law\s+(?:section\s+)?230|davis[- ]bacon|certified\s+payroll)",
        re.IGNORECASE,
    )
    
    LIABILITY_INSURANCE_PATTERN = re.compile(
        r"(?:commercial\s+general\s+liability|general\s+liability|liability\s+coverage)(?:\s+(?:insurance|coverage))?\s*(?:of|in\s+the\s+amount\s+of|minimum\s+of|is\s+(?:hereby\s+)?(?:reduced|increased|amended|changed)\s+to|to)?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(million|\bm\b)?",
        re.IGNORECASE,
    )
    
    CYBER_INSURANCE_PATTERN = re.compile(
        r"(?:cyber\s+liability|network\s+security\s+and\s+privacy|cyber\s+insurance)(?:\s+(?:insurance|coverage))?\s*(?:of|in\s+the\s+amount\s+of|minimum\s+of|is\s+(?:hereby\s+)?(?:reduced|increased|amended|changed)\s+to|to)?\s*\$?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(million|\bm\b)?",
        re.IGNORECASE,
    )

    @staticmethod
    def _parse_insurance_val(raw_num: str, mult_match: Optional[str]) -> float:
        val = float(raw_num.replace(",", "").strip())
        if mult_match and mult_match.lower() in ["million", "m"]:
            val *= 1_000_000
        elif val < 100:  # e.g. "$5" representing 5 million
            val *= 1_000_000
        return val
    
    EXPERIENCE_PATTERN = re.compile(
        r"(?:minimum\s+(?:of\s+)?|at\s+least\s+)([0-9]+)\s+(?:consecutive\s+)?years\s+(?:of\s+)?(?:prior\s+)?experience",
        re.IGNORECASE,
    )
    
    LIQUIDATED_DAMAGES_PATTERN = re.compile(
        r"liquidated\s+damages\s*(?:of|in\s+the\s+amount\s+of|at)?\s*\$?\s*([0-9,]+)\s*(?:per\s+(?:calendar\s+)?day)?",
        re.IGNORECASE,
    )
    
    PASSPORT_PATTERN = re.compile(
        r"(?:passport|pass-port|vendex|city\s+of\s+new\s+york\s+procurement\s+and\s+sourcing\s+solutions)",
        re.IGNORECASE,
    )
    
    SAM_GOV_PATTERN = re.compile(
        r"(?:sam\.gov|system\s+for\s+award\s+management|active\s+sam\s+registration|cage\s+code)",
        re.IGNORECASE,
    )

    def detect_clauses(self, text: str) -> List[ComplianceClause]:
        """Analyzes raw solicitation text and returns all detected compliance clauses."""
        clauses: List[ComplianceClause] = []
        clause_counter = 1

        # 1. M/WBE Subcontracting Goals
        for match in self.MWBE_PATTERN.finditer(text):
            pct_val = float(match.group(1))
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-MWBE-{clause_counter:03d}",
                    category=ClauseCategory.MWBE_SUBCONTRACTING,
                    title=f"M/WBE Participation Goal ({pct_val}%)",
                    description=f"Solicitation mandates a minimum M/WBE subcontracting goal of {pct_val}%.",
                    threshold_value=pct_val,
                    threshold_unit="%",
                    mandatory=True,
                    regulatory_reference="NYC Administrative Code § 6-129 / Local Law 1",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1

        # 2. Prevailing Wage Mandates
        for match in self.PREVAILING_WAGE_PATTERN.finditer(text):
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-WAGE-{clause_counter:03d}",
                    category=ClauseCategory.PREVAILING_WAGE,
                    title="Mandatory Prevailing Wage & Certified Payroll",
                    description="Work performed under this contract is subject to prevailing wage schedules and certified payroll submission.",
                    threshold_value=None,
                    threshold_unit=None,
                    mandatory=True,
                    regulatory_reference="NY State Labor Law Article 8, § 220 / Davis-Bacon",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1
            break  # Prevent duplicate prevailing wage flags

        # 3. Commercial General Liability Insurance
        for match in self.LIABILITY_INSURANCE_PATTERN.finditer(text):
            val = self._parse_insurance_val(match.group(1), match.group(2))
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-INS-GL-{clause_counter:03d}",
                    category=ClauseCategory.BONDING_INSURANCE,
                    title=f"General Liability Insurance (${val:,.0f})",
                    description=f"Contractor must maintain commercial general liability insurance of at least ${val:,.0f} per occurrence.",
                    threshold_value=val,
                    threshold_unit="USD",
                    mandatory=True,
                    regulatory_reference="Standard NYC Agency Insurance Schedule",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1
            break

        # 4. Cyber Liability Insurance
        for match in self.CYBER_INSURANCE_PATTERN.finditer(text):
            val = self._parse_insurance_val(match.group(1), match.group(2))
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-INS-CYBER-{clause_counter:03d}",
                    category=ClauseCategory.BONDING_INSURANCE,
                    title=f"Cyber Liability Insurance (${val:,.0f})",
                    description=f"Contractor must maintain network security and cyber liability coverage of at least ${val:,.0f}.",
                    threshold_value=val,
                    threshold_unit="USD",
                    mandatory=True,
                    regulatory_reference="NYC Cyber Security Standards / DoITT",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1
            break

        # 5. Minimum Experience Threshold
        for match in self.EXPERIENCE_PATTERN.finditer(text):
            years = float(match.group(1))
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-EXP-{clause_counter:03d}",
                    category=ClauseCategory.EXPERIENCE_THRESHOLD,
                    title=f"Minimum Operating Experience ({int(years)} Years)",
                    description=f"Proposers must demonstrate at least {int(years)} consecutive years of prior enterprise experience.",
                    threshold_value=years,
                    threshold_unit="years",
                    mandatory=True,
                    regulatory_reference="Minimum Proposer Qualifications",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1
            break

        # 6. Liquidated Damages
        for match in self.LIQUIDATED_DAMAGES_PATTERN.finditer(text):
            raw_num = match.group(1).replace(",", "")
            val = float(raw_num)
            start, end = max(0, match.start() - 100), min(len(text), match.end() + 100)
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-LIQ-DAMAGES-{clause_counter:03d}",
                    category=ClauseCategory.LIQUIDATED_DAMAGES,
                    title=f"Liquidated Damages (${val:,.0f}/day)",
                    description=f"Failure to meet project milestones incurs liquidated damages of ${val:,.0f} per calendar day.",
                    threshold_value=val,
                    threshold_unit="USD/day",
                    mandatory=False,
                    regulatory_reference="General Contract Provisions",
                    raw_excerpt=text[start:end].strip(),
                )
            )
            clause_counter += 1
            break

        # 7. Mandatory Registry: NYC PASSPort
        if self.PASSPORT_PATTERN.search(text):
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-REG-PASSPORT-{clause_counter:03d}",
                    category=ClauseCategory.MANDATORY_SUBMISSION_FORM,
                    title="Mandatory NYC PASSPort Account Enrollment",
                    description="Proposers must have an active, verified account in the NYC PASSPort procurement system.",
                    threshold_value=None,
                    threshold_unit=None,
                    mandatory=True,
                    regulatory_reference="NYC Procurement Policy Board (PPB) Rules",
                    raw_excerpt="Proposers must be registered with the City of New York PASSPort system prior to award.",
                )
            )
            clause_counter += 1

        # 8. Mandatory Registry: SAM.gov
        if self.SAM_GOV_PATTERN.search(text):
            clauses.append(
                ComplianceClause(
                    clause_id=f"CLAUSE-REG-SAM-{clause_counter:03d}",
                    category=ClauseCategory.MANDATORY_SUBMISSION_FORM,
                    title="Mandatory Active SAM.gov Registration",
                    description="Contractor must maintain an active Unique Entity Identifier (UEI) and CAGE code in SAM.gov.",
                    threshold_value=None,
                    threshold_unit=None,
                    mandatory=True,
                    regulatory_reference="FAR 52.204-7 System for Award Management",
                    raw_excerpt="Offerors must be registered in the System for Award Management (SAM) prior to award.",
                )
            )
            clause_counter += 1

        return clauses
