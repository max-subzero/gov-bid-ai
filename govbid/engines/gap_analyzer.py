"""Gap Analyzer and Go/No-Go Decision Engine for procurement bids."""

from datetime import datetime, timezone
from typing import List
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.models.audit import GapAnalysisResult
from govbid.models.rfp import ParsedRfp
from govbid.models.vendor import VendorProfile


class GapAnalyzer:
    """Computes quantitative bidder qualification scores and Go/No-Go bid recommendations."""

    def __init__(self) -> None:
        self.disq_guard = DisqualificationGuard()

    def analyze(self, rfp: ParsedRfp, vendor: VendorProfile) -> GapAnalysisResult:
        """Executes full gap analysis between solicitation requirements and vendor profile."""
        disqualifiers = self.disq_guard.evaluate(rfp, vendor)

        competency_gaps: List[str] = []
        strengths: List[str] = []
        score = 100.0

        # Deduct heavily for critical disqualifiers
        critical_count = sum(1 for d in disqualifiers if d.severity == "CRITICAL")
        high_count = sum(1 for d in disqualifiers if d.severity == "HIGH")

        score -= critical_count * 25.0
        score -= high_count * 10.0

        # Evaluate Past Performance Volume & Relevance
        total_contract_value = sum(p.contract_value for p in vendor.past_performance)
        has_govt_experience = any(p.is_government for p in vendor.past_performance)

        if not has_govt_experience and rfp.jurisdiction in ["MUNICIPAL", "FEDERAL"]:
            competency_gaps.append("Lacks prior prime public sector / government contract performance.")
            score -= 15.0
        else:
            strengths.append(f"Demonstrated public sector contract experience across {len([p for p in vendor.past_performance if p.is_government])} prior engagements.")

        if total_contract_value > 5_000_000:
            strengths.append(f"Strong aggregate past performance portfolio (${total_contract_value:,.0f}).")
        elif total_contract_value < 1_000_000:
            competency_gaps.append(f"Aggregate past contract volume (${total_contract_value:,.0f}) may weaken financial capacity scoring.")
            score -= 10.0

        # Check Certifications
        if vendor.is_mwbe_certified:
            strengths.append("Certified M/WBE entity providing preferred scoring incentives under municipal rules.")
        elif vendor.mwbe_subcontractor_network:
            strengths.append("Established M/WBE subcontractor network satisfying Local Law participation goals.")

        # Determine Recommendation
        score = max(0.0, min(100.0, score))
        if critical_count > 0:
            # Check if critical items are remediable (e.g. insurance binder, PASSPort enrollment)
            all_remediable = all(d.rule_category in ["INSURANCE", "REGISTRATION", "MWBE_COMPLIANCE"] for d in disqualifiers)
            if all_remediable and score >= 40.0:
                recommendation = "CONDITIONAL_GO"
            else:
                recommendation = "NO_GO"
        elif score >= 75.0:
            recommendation = "GO"
        elif score >= 50.0:
            recommendation = "CONDITIONAL_GO"
        else:
            recommendation = "NO_GO"

        return GapAnalysisResult(
            solicitation_number=rfp.solicitation_number,
            vendor_name=vendor.name,
            recommendation=recommendation,
            fit_score=round(score, 1),
            disqualifiers=disqualifiers,
            competency_gaps=competency_gaps,
            competitive_strengths=strengths,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
