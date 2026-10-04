"""Data models for RFP Addenda, Amendments, and Differential Analysis."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ChangeSeverity(str, Enum):
    CRITICAL = "CRITICAL"          # Deadline change, new disqualifier, scope expansion
    MAJOR = "MAJOR"                # Substantial threshold shift, bonding change
    MINOR = "MINOR"                # Minor date/administrative adjustment
    INFORMATIONAL = "INFORMATIONAL"# Standard clarification or vendor Q&A item


class ChangeCategory(str, Enum):
    DEADLINE_CHANGE = "DEADLINE_CHANGE"
    INSURANCE_MODIFICATION = "INSURANCE_MODIFICATION"
    MWBE_GOAL_CHANGE = "MWBE_GOAL_CHANGE"
    NEW_MANDATORY_CLAUSE = "NEW_MANDATORY_CLAUSE"
    CLAUSE_RESCISSION = "CLAUSE_RESCISSION"
    SCOPE_CLARIFICATION = "SCOPE_CLARIFICATION"
    ADMINISTRATIVE = "ADMINISTRATIVE"


class AddendumDiffItem(BaseModel):
    """An individual identified change between the baseline RFP and an Addendum/Amendment."""
    diff_id: str = Field(..., description="Unique deterministic identifier for change")
    category: ChangeCategory = Field(..., description="Functional change category")
    severity: ChangeSeverity = Field(..., description="Impact severity of change")
    title: str = Field(..., description="Short title describing change")
    original_value: Optional[str] = Field(None, description="Previous value or requirement from baseline")
    revised_value: Optional[str] = Field(None, description="Updated value or requirement in addendum")
    explanation: str = Field(..., description="Actionable summary of change and strategic impact")
    raw_excerpt: str = Field(..., description="Verbatim text from addendum")


class QaPair(BaseModel):
    """A vendor question and agency response extracted from an Addendum."""
    question_number: int = Field(..., description="Sequential question number (e.g. 1 for Q1)")
    question: str = Field(..., description="Bidder inquiry text")
    answer: str = Field(..., description="Official agency response text")


class AddendumAnalysisResult(BaseModel):
    """Complete differential analysis between an RFP and a subsequent Addendum."""
    solicitation_number: str = Field(..., description="Base RFP PIN or solicitation number")
    addendum_identifier: str = Field(..., description="E.g. Addendum #1, Amendment 0002")
    new_submission_deadline: Optional[str] = Field(None, description="Updated proposal deadline if extended")
    diff_items: List[AddendumDiffItem] = Field(default_factory=list, description="List of identified contractual changes")
    qa_pairs: List[QaPair] = Field(default_factory=list, description="Extracted bidder Q&A pairs")
    summary: str = Field(..., description="Executive summary of addendum impact")
