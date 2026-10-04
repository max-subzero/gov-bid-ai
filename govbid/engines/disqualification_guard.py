"""Adversarial Disqualification Guard for government procurement bids."""

from typing import List
from govbid.models.audit import DisqualificationFinding, FindingSeverity
from govbid.models.rfp import ClauseCategory, ParsedRfp
from govbid.models.vendor import VendorProfile


class DisqualificationGuard:
    """Pre-flight adversarial compliance engine that flags legal and administrative dealbreakers."""

    def evaluate(self, rfp: ParsedRfp, vendor: VendorProfile) -> List[DisqualificationFinding]:
        """Evaluates vendor profile against mandatory RFP clauses and returns findings."""
        findings: List[DisqualificationFinding] = []
        finding_count = 1

        for clause in rfp.clauses:
            # 1. Commercial General Liability Insurance Deficit
            if clause.category == ClauseCategory.BONDING_INSURANCE and "general liability" in clause.title.lower():
                req_val = clause.threshold_value or 0.0
                if vendor.insurance_general_liability < req_val:
                    deficit = req_val - vendor.insurance_general_liability
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="INSURANCE",
                            title="General Liability Insurance Below Mandated Limit",
                            detail=(
                                f"RFP requires minimum ${req_val:,.0f} General Liability coverage. "
                                f"Vendor profile indicates ${vendor.insurance_general_liability:,.0f} (Deficit: ${deficit:,.0f})."
                            ),
                            disqualification_risk=True,
                            remediation_step=f"Execute an insurance binder rider increasing General Liability limit to ${req_val:,.0f} prior to proposal submission.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 2. Cyber Liability Insurance Deficit
            elif clause.category == ClauseCategory.BONDING_INSURANCE and "cyber" in clause.title.lower():
                req_val = clause.threshold_value or 0.0
                if vendor.insurance_cyber_liability < req_val:
                    deficit = req_val - vendor.insurance_cyber_liability
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="INSURANCE",
                            title="Cyber Liability Insurance Below Mandated Limit",
                            detail=(
                                f"RFP mandates ${req_val:,.0f} Cyber Liability coverage. "
                                f"Vendor profile indicates ${vendor.insurance_cyber_liability:,.0f} (Deficit: ${deficit:,.0f})."
                            ),
                            disqualification_risk=True,
                            remediation_step=f"Bind a Network Security & Cyber Liability policy of at least ${req_val:,.0f} with municipality named as additional insured.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 3. Minimum Experience Threshold Deficit
            elif clause.category == ClauseCategory.EXPERIENCE_THRESHOLD:
                req_years = int(clause.threshold_value or 0)
                if vendor.years_in_business < req_years:
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="EXPERIENCE",
                            title="Vendor Operating Years Below Minimum Proposer Threshold",
                            detail=(
                                f"Solicitation requires at least {req_years} consecutive years of enterprise experience. "
                                f"Vendor has {vendor.years_in_business} operating years."
                            ),
                            disqualification_risk=True,
                            remediation_step="Form a Joint Venture (JV) or Prime-Subcontractor consortium with a firm possessing requisite historical tenure.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 4. M/WBE Subcontracting Plan Requirement
            elif clause.category == ClauseCategory.MWBE_SUBCONTRACTING:
                goal_pct = clause.threshold_value or 0.0
                if not vendor.is_mwbe_certified and not vendor.mwbe_subcontractor_network:
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.HIGH,
                            rule_category="MWBE_COMPLIANCE",
                            title="Missing M/WBE Subcontracting Utilization Plan",
                            detail=(
                                f"Solicitation mandates {goal_pct:.1f}% M/WBE participation. "
                                "Vendor is not M/WBE certified and has not declared verified M/WBE subcontractor partners."
                            ),
                            disqualification_risk=True,
                            remediation_step=f"Partner with certified M/WBE vendors to satisfy the {goal_pct:.1f}% subcontracting quota or submit formal Schedule B waiver request.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 5. Mandatory Prevailing Wage & Certified Payroll
            elif clause.category == ClauseCategory.PREVAILING_WAGE:
                if not vendor.prevailing_wage_compliant:
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="PREVAILING_WAGE",
                            title="Vendor Not Certified for Prevailing Wage / Certified Payroll",
                            detail="Work involves trade classifications governed by NY Labor Law § 220 / Davis-Bacon.",
                            disqualification_risk=True,
                            remediation_step="Adopt certified payroll software integration and execute compliance declaration acknowledging statutory wage rates.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 6. Mandatory Registration: NYC PASSPort
            elif "passport" in clause.title.lower():
                if "NYC_PASSPORT" not in vendor.active_registrations:
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="REGISTRATION",
                            title="Missing Active NYC PASSPort Account Enrollment",
                            detail="City of New York PPB Rules prohibit contract award to vendors lacking active PASSPort registration.",
                            disqualification_risk=True,
                            remediation_step="Complete NYC PASSPort enrollment and submit commodity code disclosures prior to RFP submission deadline.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

            # 7. Mandatory Registration: SAM.gov
            elif "sam.gov" in clause.title.lower():
                if "SAM_GOV" not in vendor.active_registrations:
                    findings.append(
                        DisqualificationFinding(
                            finding_id=f"DISQ-{finding_count:03d}",
                            severity=FindingSeverity.CRITICAL,
                            rule_category="REGISTRATION",
                            title="Missing Active SAM.gov Unique Entity Identifier (UEI)",
                            detail="Federal solicitation mandates verified active SAM.gov entity status and valid CAGE code.",
                            disqualification_risk=True,
                            remediation_step="Activate SAM.gov registration and obtain Unique Entity Identifier (UEI) immediately.",
                            clause_ref=clause.clause_id,
                        )
                    )
                    finding_count += 1

        return findings
