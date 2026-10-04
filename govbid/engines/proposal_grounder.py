"""Grounded proposal synthesizer and RAG Triad hallucination auditor."""

import re
from typing import Dict, List, Tuple
from govbid.models.rfp import ParsedRfp
from govbid.models.vendor import PastPerformanceRecord, VendorProfile


class ProposalGrounder:
    """Verifies that all technical claims and experience narratives are grounded in verified past performance."""

    CLAIM_NUMBER_PATTERN = re.compile(r"\b([0-9]{1,3}(?:,[0-9]{3})+|\$[0-9]+(?:\.[0-9]+)?(?:\s*(?:million|m|k))?)\b", re.IGNORECASE)

    def evaluate_groundedness(
        self, draft_text: str, vendor: VendorProfile
    ) -> Tuple[float, List[str]]:
        """Evaluates whether statements in a draft proposal are grounded in verified vendor records.
        
        Returns:
            Tuple of (groundedness_score: 0.0 - 1.0, ungrounded_assertions: List[str])
        """
        ungrounded: List[str] = []
        sentences = [s.strip() for s in draft_text.split(".") if len(s.strip()) > 20]
        
        if not sentences:
            return (1.0, [])

        verified_text = " ".join([
            f"{p.client_name} {p.domain} {p.summary} ${p.contract_value:,.0f} {p.duration_years} years"
            for p in vendor.past_performance
        ]).lower()

        grounded_count = 0
        for sentence in sentences:
            s_lower = sentence.lower()
            # Extract keywords or metrics
            keywords = [w for w in re.findall(r"\b[a-zA-Z]{5,}\b", s_lower) if w not in {"proposer", "contractor", "services", "system", "provide", "solution"}]
            
            # Check overlap against verified records
            overlap = [kw for kw in keywords if kw in verified_text]
            if len(keywords) > 0 and len(overlap) / len(keywords) >= 0.25:
                grounded_count += 1
            else:
                # Potential hallucination or unverified claim
                ungrounded.append(sentence)

        groundedness_score = round(grounded_count / len(sentences), 2)
        return (groundedness_score, ungrounded)

    def generate_grounded_outline(
        self, rfp: ParsedRfp, vendor: VendorProfile
    ) -> Dict[str, List[str]]:
        """Synthesizes proposal section outlines with citations to verified past performance records."""
        outline: Dict[str, List[str]] = {}

        for criterion in rfp.evaluation_criteria:
            matching_records: List[PastPerformanceRecord] = []
            crit_lower = criterion.title.lower()

            for record in vendor.past_performance:
                if any(word in record.domain.lower() or word in record.summary.lower() for word in crit_lower.split()):
                    matching_records.append(record)

            points: List[str] = []
            if matching_records:
                for rec in matching_records:
                    points.append(
                        f"Demonstrated Competency: Reference Contract [{rec.record_id}] for {rec.client_name} "
                        f"(${rec.contract_value:,.0f}, {rec.duration_years} yrs): {rec.summary}"
                    )
            else:
                points.append(
                    "Standard Corporate Methodology: Propose proprietary execution framework with subcontractor support."
                )

            outline[f"{criterion.title} ({criterion.weight_percentage}%)"] = points

        return outline
