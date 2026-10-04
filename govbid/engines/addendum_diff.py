"""Addendum & Amendment Differential Analysis Engine for government procurement."""

import re
from typing import Dict, List, Optional, Tuple, Union
from govbid.models.addendum import (
    AddendumAnalysisResult,
    AddendumDiffItem,
    ChangeCategory,
    ChangeSeverity,
    QaPair,
)
from govbid.models.rfp import ClauseCategory, ComplianceClause, ParsedRfp
from govbid.parsers.clause_detector import ClauseDetector
from govbid.parsers.rfp_parser import RfpParser


class AddendumDiffEngine:
    """Analyzes procurement addenda and amendments against baseline solicitations."""

    ADDENDUM_ID_PATTERN = re.compile(
        r"(?:ADDENDUM|AMENDMENT)\s*(?:NO\.?|NUMBER|#)?\s*([0-9A-Z\-]+)",
        re.IGNORECASE,
    )

    DEADLINE_CHANGE_PATTERN = re.compile(
        r"(?:proposal\s+(?:due\s+date|submission\s+deadline)|due\s+date)\s*(?:is\s+hereby\s+)?(?:extended|amended|changed|rescheduled)\s*(?:to|until)?[:\s]+([^\n\r.]+)",
        re.IGNORECASE,
    )

    QA_PATTERN = re.compile(
        r"(?:Q(?:uestion)?\s*([0-9]+)?[:\.\-\)]\s*)(.+?)(?:A(?:nswer)?|Response)[:\.\-\)]\s*(.+?)(?=(?:Q(?:uestion)?\s*[0-9]*[:\.\-\)]|\Z))",
        re.DOTALL | re.IGNORECASE,
    )

    def __init__(self) -> None:
        self.rfp_parser = RfpParser()
        self.clause_detector = ClauseDetector()

    def _find_matching_base_clause(
        self,
        add_clause: ComplianceClause,
        base_clauses: List[ComplianceClause],
    ) -> Optional[ComplianceClause]:
        """Matches an addendum clause against baseline clauses using category and semantic title overlap."""
        cat_matches = [c for c in base_clauses if c.category == add_clause.category]
        if not cat_matches:
            return None
        if len(cat_matches) == 1:
            return cat_matches[0]

        # Filter out numbers from word tokens to compare semantic titles
        digits = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
        add_words = {w for w in re.findall(r"\w+", add_clause.title.lower()) if not (w.isdigit() or w in digits)}
        best_match: Optional[ComplianceClause] = None
        best_overlap = -1

        for bc in cat_matches:
            base_words = {w for w in re.findall(r"\w+", bc.title.lower()) if not (w.isdigit() or w in digits)}
            overlap = len(add_words & base_words)
            if overlap > best_overlap:
                best_overlap = overlap
                best_match = bc

        return best_match

    def analyze_diff(
        self,
        base_rfp: Union[ParsedRfp, str],
        addendum_content: str,
    ) -> AddendumAnalysisResult:
        """Executes full differential analysis comparing an addendum to the baseline RFP."""
        if isinstance(base_rfp, str):
            base_rfp = self.rfp_parser.parse_text(base_rfp)

        # 1. Identify Addendum Number
        add_match = self.ADDENDUM_ID_PATTERN.search(addendum_content)
        addendum_id = f"Addendum #{add_match.group(1)}" if add_match else "Addendum / Amendment"

        diff_items: List[AddendumDiffItem] = []
        diff_count = 1

        # 2. Check for Proposal Due Date / Deadline Extensions
        new_deadline: Optional[str] = None
        deadline_match = self.DEADLINE_CHANGE_PATTERN.search(addendum_content)
        if deadline_match:
            new_deadline = deadline_match.group(1).strip()
            diff_items.append(
                AddendumDiffItem(
                    diff_id=f"DIFF-{diff_count:03d}",
                    category=ChangeCategory.DEADLINE_CHANGE,
                    severity=ChangeSeverity.CRITICAL,
                    title="Proposal Submission Deadline Extended",
                    original_value=base_rfp.submission_deadline or "Initial Deadline",
                    revised_value=new_deadline,
                    explanation=f"Proposal submission deadline has been officially updated to '{new_deadline}'.",
                    raw_excerpt=addendum_content[deadline_match.start() : min(len(addendum_content), deadline_match.end() + 60)].strip(),
                )
            )
            diff_count += 1

        # 3. Detect Modified or New Clauses in Addendum
        addendum_clauses = self.clause_detector.detect_clauses(addendum_content)

        for add_clause in addendum_clauses:
            base_clause = self._find_matching_base_clause(add_clause, base_rfp.clauses)
            if base_clause:
                # Check if threshold changed
                if add_clause.threshold_value is not None and base_clause.threshold_value is not None:
                    if add_clause.threshold_value != base_clause.threshold_value:
                        category = (
                            ChangeCategory.MWBE_GOAL_CHANGE
                            if add_clause.category == ClauseCategory.MWBE_SUBCONTRACTING
                            else ChangeCategory.INSURANCE_MODIFICATION
                        )
                        diff_items.append(
                            AddendumDiffItem(
                                diff_id=f"DIFF-{diff_count:03d}",
                                category=category,
                                severity=ChangeSeverity.MAJOR,
                                title=f"Threshold Modified: {add_clause.title}",
                                original_value=f"{base_clause.threshold_value} {base_clause.threshold_unit or ''}".strip(),
                                revised_value=f"{add_clause.threshold_value} {add_clause.threshold_unit or ''}".strip(),
                                explanation=(
                                    f"Requirement adjusted from {base_clause.threshold_value} to {add_clause.threshold_value}. "
                                    "Update proposal financial models and subcontractor allocations accordingly."
                                ),
                                raw_excerpt=add_clause.raw_excerpt,
                            )
                        )
                        diff_count += 1
            else:
                # Entirely new clause introduced in addendum
                diff_items.append(
                    AddendumDiffItem(
                        diff_id=f"DIFF-{diff_count:03d}",
                        category=ChangeCategory.NEW_MANDATORY_CLAUSE,
                        severity=ChangeSeverity.CRITICAL if add_clause.mandatory else ChangeSeverity.MAJOR,
                        title=f"New Requirement Introduced: {add_clause.title}",
                        original_value="None (Not present in baseline RFP)",
                        revised_value=add_clause.title,
                        explanation=f"Addendum adds mandatory compliance condition: {add_clause.description}",
                        raw_excerpt=add_clause.raw_excerpt,
                    )
                )
                diff_count += 1

        # 4. Extract Bidder Question & Answer (Q&A) Pairs
        qa_pairs: List[QaPair] = []
        qa_counter = 1
        for match in self.QA_PATTERN.finditer(addendum_content):
            q_num_raw = match.group(1)
            q_num = int(q_num_raw) if q_num_raw else qa_counter
            q_text = " ".join(match.group(2).split()).strip()
            a_text = " ".join(match.group(3).split()).strip()

            qa_pairs.append(
                QaPair(
                    question_number=q_num,
                    question=q_text,
                    answer=a_text,
                )
            )
            qa_counter += 1

        # 5. Build Executive Summary
        critical_count = sum(1 for d in diff_items if d.severity == ChangeSeverity.CRITICAL)
        summary = (
            f"{addendum_id} incorporates {len(diff_items)} contractual modifications "
            f"({critical_count} critical) and answers {len(qa_pairs)} bidder clarification questions."
        )

        return AddendumAnalysisResult(
            solicitation_number=base_rfp.solicitation_number,
            addendum_identifier=addendum_id,
            new_submission_deadline=new_deadline,
            diff_items=diff_items,
            qa_pairs=qa_pairs,
            summary=summary,
        )
