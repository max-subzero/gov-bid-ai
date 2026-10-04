"""Data models for Parsed RFPs and Compliance Clauses."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ClauseCategory(str, Enum):
    MWBE_SUBCONTRACTING = "MWBE_SUBCONTRACTING"
    PREVAILING_WAGE = "PREVAILING_WAGE"
    BONDING_INSURANCE = "BONDING_INSURANCE"
    EXPERIENCE_THRESHOLD = "EXPERIENCE_THRESHOLD"
    LIQUIDATED_DAMAGES = "LIQUIDATED_DAMAGES"
    MANDATORY_SUBMISSION_FORM = "MANDATORY_SUBMISSION_FORM"
    CERTIFICATION_REQUIRED = "CERTIFICATION_REQUIRED"
    OTHER = "OTHER"


class ComplianceClause(BaseModel):
    """A detected mandatory or restrictive compliance requirement in a solicitation."""
    clause_id: str = Field(..., description="Unique deterministic identifier for clause")
    category: ClauseCategory = Field(..., description="Classification category")
    title: str = Field(..., description="Human-readable title of compliance rule")
    description: str = Field(..., description="Full description or excerpt of the clause")
    threshold_value: Optional[float] = Field(None, description="Extracted numerical threshold, e.g. 30.0 for 30%")
    threshold_unit: Optional[str] = Field(None, description="Unit for threshold, e.g. '%', 'USD', 'years'")
    mandatory: bool = Field(True, description="Whether failure to satisfy clause triggers disqualification")
    regulatory_reference: Optional[str] = Field(None, description="E.g. NYC Labor Law 220, FAR 52.219-9, Davis-Bacon")
    raw_excerpt: str = Field(..., description="Verbatim text extracted from document")


class EvaluationCriteria(BaseModel):
    """An official evaluation criterion used by agency evaluators to score bids."""
    criterion_id: str = Field(..., description="Criterion identifier")
    title: str = Field(..., description="Criterion name, e.g. Technical Approach")
    weight_percentage: float = Field(..., description="Point or percentage weight in scoring rubric")
    description: str = Field(..., description="Scoring expectations and requirements")


class ParsedRfp(BaseModel):
    """Structured representation of an ingested government solicitation packet."""
    title: str = Field(..., description="Solicitation title")
    solicitation_number: str = Field(..., description="PIN, RFP#, or solicitation identifier")
    issuing_agency: str = Field(..., description="Issuing agency (e.g. NYC DCAS, GSA, DoD)")
    jurisdiction: str = Field("MUNICIPAL", description="MUNICIPAL, STATE, or FEDERAL")
    estimated_budget: Optional[float] = Field(None, description="Estimated contract budget if disclosed")
    submission_deadline: Optional[str] = Field(None, description="ISO timestamp or date string")
    clauses: List[ComplianceClause] = Field(default_factory=list, description="Extracted compliance constraints")
    evaluation_criteria: List[EvaluationCriteria] = Field(default_factory=list, description="Scoring criteria")
    raw_sections: Dict[str, str] = Field(default_factory=dict, description="Raw text mapped by section header")
