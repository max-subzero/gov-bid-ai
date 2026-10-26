"""NYC PASSPort / VENDEX & Federal FAR 52.209-5 Vendor Responsibility & Integrity Auditor."""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Union


class ResponsibilityStatus(str, Enum):
    """Deterministic vendor responsibility determination outcomes."""

    RESPONSIBLE = "RESPONSIBLE"
    CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED = (
        "CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED"
    )
    NON_RESPONSIBLE_DISQUALIFIED = "NON_RESPONSIBLE_DISQUALIFIED"


@dataclass(frozen=True)
class ResponsibilityFinding:
    """Individual statutory or regulatory responsibility audit finding."""

    code: str
    severity: str
    statute: str
    detail: str
    remediation: str

    def to_dict(self) -> Dict[str, str]:
        """Serialize finding to dictionary."""
        return asdict(self)


@dataclass
class VendorResponsibilityDisclosure:
    """Normalized vendor responsibility and integrity questionnaire payload."""

    vendor_id: str = "UNKNOWN-VENDOR"
    vendor_name: str = "Unknown Vendor"
    debarment_or_suspension: bool = False
    tax_liens_unresolved: bool = False
    osha_or_labor_violations: int = 0
    prevailing_wage_debarment: bool = False
    criminal_convictions_5yr: bool = False
    conflict_of_interest_disclosed: bool = False
    caution_flags_remediated: bool = False
    IntegrityOfficerCertified: bool = True

    @classmethod
    def from_payload(
        cls, payload: Union["VendorResponsibilityDisclosure", Mapping[str, Any]]
    ) -> "VendorResponsibilityDisclosure":
        """Normalize dictionary or disclosure instance into VendorResponsibilityDisclosure."""
        if isinstance(payload, VendorResponsibilityDisclosure):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("Responsibility disclosure payload must be a Mapping or VendorResponsibilityDisclosure")

        integrity_certified = payload.get(
            "IntegrityOfficerCertified",
            payload.get("integrity_officer_certified", True),
        )
        osha_raw = payload.get("osha_or_labor_violations", 0)
        if isinstance(osha_raw, bool):
            osha_count = 1 if osha_raw else 0
        else:
            osha_count = max(0, int(osha_raw or 0))

        return cls(
            vendor_id=str(payload.get("vendor_id", "UNKNOWN-VENDOR")),
            vendor_name=str(payload.get("vendor_name", "Unknown Vendor")),
            debarment_or_suspension=bool(payload.get("debarment_or_suspension", False)),
            tax_liens_unresolved=bool(payload.get("tax_liens_unresolved", False)),
            osha_or_labor_violations=osha_count,
            prevailing_wage_debarment=bool(payload.get("prevailing_wage_debarment", False)),
            criminal_convictions_5yr=bool(payload.get("criminal_convictions_5yr", False)),
            conflict_of_interest_disclosed=bool(payload.get("conflict_of_interest_disclosed", False)),
            caution_flags_remediated=bool(payload.get("caution_flags_remediated", False)),
            IntegrityOfficerCertified=bool(integrity_certified),
        )


@dataclass
class ResponsibilityAuditResult:
    """Deterministic output of the NYC PASSPort / FAR 52.209-5 Responsibility Auditor."""

    status: str
    integrity_score: float
    findings: List[ResponsibilityFinding] = field(default_factory=list)
    vendor_id: str = "UNKNOWN-VENDOR"
    vendor_name: str = "Unknown Vendor"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_problem_details(
        self, instance: Optional[str] = None
    ) -> Dict[str, Any]:
        """Export audit result as an RFC 7807 Problem Details dictionary."""
        if self.status == ResponsibilityStatus.NON_RESPONSIBLE_DISQUALIFIED.value:
            http_status = 403
            problem_type = "https://govbid.ai/problems/vendor-non-responsible-disqualified"
            title = "Vendor Non-Responsible: Statutory Disqualification"
            code = "ERR_VENDOR_NON_RESPONSIBLE"
        elif (
            self.status
            == ResponsibilityStatus.CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED.value
        ):
            http_status = 422
            problem_type = "https://govbid.ai/problems/conditional-responsibility-rehabilitation-required"
            title = "Conditional Responsibility: Rehabilitation or COI Mitigation Required"
            code = "WARN_CONDITIONAL_RESPONSIBILITY"
        else:
            http_status = 200
            problem_type = "about:blank"
            title = "Vendor Responsibility Verified"
            code = "OK_VENDOR_RESPONSIBLE"

        lead_detail = (
            "; ".join(f"{f.code}: {f.detail}" for f in self.findings)
            if self.findings
            else "Vendor meets all FAR Subpart 9.1 and NYC PPB § 2-08 responsibility standards."
        )

        return {
            "type": problem_type,
            "title": title,
            "status": http_status,
            "detail": lead_detail,
            "instance": instance or f"urn:govbid:responsibility-audit:{self.vendor_id}",
            "code": code,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "responsibility_status": self.status,
            "integrity_score": round(self.integrity_score, 2),
            "findings": [f.to_dict() for f in self.findings],
            "timestamp": self.timestamp,
        }


class ResponsibilityAuditor:
    """
    NYC PASSPort Vendor Questionnaire / VENDEX / Federal FAR 52.209-5
    Responsibility & Integrity Certification Auditor.
    """

    def evaluate(
        self,
        payload: Union[VendorResponsibilityDisclosure, Mapping[str, Any]],
    ) -> ResponsibilityAuditResult:
        """Evaluate vendor responsibility disclosure payload and return deterministic audit result."""
        disclosure = VendorResponsibilityDisclosure.from_payload(payload)
        findings: List[ResponsibilityFinding] = []
        score = 100.0
        has_fatal_bar = False
        has_conditional_flag = False

        # 1. Federal / Municipal Debarment or Suspension (FAR 52.209-5 / SAM.gov Exclusions)
        if disclosure.debarment_or_suspension:
            has_fatal_bar = True
            score -= 60.0
            findings.append(
                ResponsibilityFinding(
                    code="RESP-DEBAR-001",
                    severity="CRITICAL",
                    statute="FAR 9.405 / FAR 52.209-5(a)(1)(i)(A) / NYC PPB Rule § 2-08",
                    detail=(
                        "Vendor or its principals are presently debarred, suspended, proposed for "
                        "debarment, or declared ineligible for contract award by a public agency."
                    ),
                    remediation=(
                        "Ineligible for contract award during active exclusion period; obtain formal "
                        "SAM.gov / PASSPort exclusion termination or agency head compelling-reason waiver."
                    ),
                )
            )

        # 2. Prevailing Wage Debarment (NY Labor Law § 220-b / Davis-Bacon 40 U.S.C. § 3144)
        if disclosure.prevailing_wage_debarment:
            has_fatal_bar = True
            score -= 60.0
            findings.append(
                ResponsibilityFinding(
                    code="RESP-PWAGE-002",
                    severity="CRITICAL",
                    statute="NY Labor Law § 220-b(3)(b) / 40 U.S.C. § 3144 (Davis-Bacon Act)",
                    detail=(
                        "Vendor has been determined willful violator of prevailing wage laws and is "
                        "statutorily barred from bidding on public work contracts."
                    ),
                    remediation=(
                        "Statutory 5-year bidding prohibition applies under NYLL § 220-b; cannot be cured "
                        "without judicial vacatur or expiration of debarment term."
                    ),
                )
            )

        # 3. Criminal Convictions within 5 Years (Fraud, Bribery, Bid Rigging, Embezzlement)
        if disclosure.criminal_convictions_5yr:
            if disclosure.caution_flags_remediated:
                has_conditional_flag = True
                score -= 25.0
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-CRIM-003",
                        severity="HIGH",
                        statute="FAR 52.209-5(a)(1)(i)(B) / NYC Charter § 335 / PPB § 2-08(e)",
                        detail=(
                            "Criminal conviction within preceding 5 years disclosed with documented "
                            "ethics rehabilitation, principal severance, and independent monitor agreement."
                        ),
                        remediation=(
                            "Submit executed Corporate Integrity Agreement (CIA) and NYC DOI / CCPO "
                            "Determination of Rehabilitation prior to contract registration."
                        ),
                    )
                )
            else:
                has_fatal_bar = True
                score -= 55.0
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-CRIM-003",
                        severity="CRITICAL",
                        statute="FAR 52.209-5(a)(1)(i)(B) / NYC Charter § 335 / PPB § 2-08(e)",
                        detail=(
                            "Unremediated criminal conviction within preceding 5 years involving fraud, "
                            "bribery, antitrust bid-rigging, embezzlement, or public contract offenses."
                        ),
                        remediation=(
                            "Execute formal rehabilitation protocol with Department of Investigation (DOI) "
                            "and sever culpable principals prior to re-qualification."
                        ),
                    )
                )

        # 4. Unresolved Federal, State, or Municipal Tax Liens / Delinquencies
        if disclosure.tax_liens_unresolved:
            if disclosure.caution_flags_remediated:
                has_conditional_flag = True
                score -= 15.0
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-TAX-004",
                        severity="MEDIUM",
                        statute="FAR 52.209-5(a)(1)(i)(D) / NYC Admin. Code § 11-04 / PASSPort Tax Clearance",
                        detail=(
                            "Tax lien disclosed with active installment payment agreement or escrow cure "
                            "pending final Department of Finance / IRS clearance certificate."
                        ),
                        remediation=(
                            "Upload executed IRS / NYS DTF / NYC DOF installment compliance stipulation "
                            "into PASSPort Vendor Questionnaire."
                        ),
                    )
                )
            else:
                has_fatal_bar = True
                score -= 45.0
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-TAX-004",
                        severity="CRITICAL",
                        statute="FAR 52.209-5(a)(1)(i)(D) / NYC Admin. Code § 11-04 / PASSPort Tax Clearance",
                        detail=(
                            "Unresolved delinquent federal, state, or municipal tax liens exceeding "
                            "statutory threshold without an approved payment stipulation."
                        ),
                        remediation=(
                            "Satisfy outstanding tax warrants in full or execute a binding payment plan "
                            "with the taxing authority prior to responsibility determination."
                        ),
                    )
                )

        # 5. OSHA or Labor Law Citations / Violations
        if disclosure.osha_or_labor_violations > 0:
            count = disclosure.osha_or_labor_violations
            if count >= 3 and not disclosure.caution_flags_remediated:
                has_fatal_bar = True
                score -= 40.0
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-OSHA-005",
                        severity="CRITICAL",
                        statute="29 U.S.C. § 654 (OSHA) / NYC PPB Rule § 2-08(b)(2)",
                        detail=(
                            f"Vendor disclosed {count} unresolved OSHA/labor safety violations indicating "
                            "persistent pattern of workplace safety non-compliance without remediation."
                        ),
                        remediation=(
                            "Abate all open OSHA citations, pay assessed penalties, and implement third-party "
                            "certified site safety management plan."
                        ),
                    )
                )
            else:
                has_conditional_flag = True
                penalty = min(25.0, 10.0 * count if not disclosure.caution_flags_remediated else 8.0 * count)
                score -= penalty
                findings.append(
                    ResponsibilityFinding(
                        code="RESP-OSHA-005",
                        severity="HIGH" if not disclosure.caution_flags_remediated else "MEDIUM",
                        statute="29 U.S.C. § 654 (OSHA) / NYC PPB Rule § 2-08(b)(2)",
                        detail=(
                            f"Vendor disclosed {count} historical OSHA/labor safety caution flag(s); "
                            f"remediation status: {'documented' if disclosure.caution_flags_remediated else 'pending verification'}."
                        ),
                        remediation=(
                            "File OSHA abatement verification logs and Corrective Action Plan (CAP) "
                            "with the Agency Chief Contracting Officer (ACCO)."
                        ),
                    )
                )

        # 6. Organizational or Personal Conflict of Interest (COI)
        if disclosure.conflict_of_interest_disclosed:
            has_conditional_flag = True
            score -= 10.0 if disclosure.caution_flags_remediated else 20.0
            findings.append(
                ResponsibilityFinding(
                    code="RESP-COI-006",
                    severity="MEDIUM" if disclosure.caution_flags_remediated else "HIGH",
                    statute="FAR Subpart 9.5 / NYC Charter Chapter 68 (Conflicts of Interest Board)",
                    detail=(
                        "Organizational or key personnel Conflict of Interest (COI) disclosed in "
                        "PASSPort / FAR 9.5 questionnaire requiring ethical firewall review."
                    ),
                    remediation=(
                        "Submit an Organizational Conflict of Interest (OCI) Mitigation Plan and obtain "
                        "NYC COIB waiver or Contracting Officer clearance."
                    ),
                )
            )

        # 7. Missing Integrity Officer / Principal Certification Signature
        if not disclosure.IntegrityOfficerCertified:
            has_fatal_bar = True
            score -= 50.0
            findings.append(
                ResponsibilityFinding(
                    code="RESP-CERT-007",
                    severity="CRITICAL",
                    statute="FAR 52.209-5 / NYC PASSPort Vendor Certification Rule (PPB § 2-08)",
                    detail=(
                        "Vendor questionnaire lacks mandatory sworn attestation by Chief Executive Officer, "
                        "Chief Compliance/Integrity Officer, or authorized corporate principal."
                    ),
                    remediation=(
                        "Execute notarized/digital PASSPort Certificate of No Change or full Principal "
                        "Responsibility Certification under penalty of perjury."
                    ),
                )
            )

        clamped_score = max(0.0, min(100.0, round(score, 2)))

        if has_fatal_bar:
            status = ResponsibilityStatus.NON_RESPONSIBLE_DISQUALIFIED.value
        elif has_conditional_flag:
            status = (
                ResponsibilityStatus.CONDITIONAL_RESPONSIBILITY_REHABILITATION_REQUIRED.value
            )
        else:
            status = ResponsibilityStatus.RESPONSIBLE.value

        return ResponsibilityAuditResult(
            status=status,
            integrity_score=clamped_score,
            findings=findings,
            vendor_id=disclosure.vendor_id,
            vendor_name=disclosure.vendor_name,
        )

    def audit(
        self,
        payload: Union[VendorResponsibilityDisclosure, Mapping[str, Any]],
    ) -> ResponsibilityAuditResult:
        """Alias for evaluate() to support both audit() and evaluate() caller conventions."""
        return self.evaluate(payload)
