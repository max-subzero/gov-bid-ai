"""Data models for Disqualification Findings, Gap Analysis, and RFC 7807 problem details."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"  # Immediate legal/administrative disqualification
    HIGH = "HIGH"          # Significant point deduction or cure notice hazard
    MEDIUM = "MEDIUM"      # Moderate risk, requires clarification
    LOW = "LOW"            # Informational / minor recommendation


class DisqualificationFinding(BaseModel):
    """An identified disqualification risk or compliance deficiency."""
    finding_id: str = Field(..., description="Unique deterministic identifier")
    severity: FindingSeverity = Field(..., description="Severity level")
    rule_category: str = Field(..., description="E.g. INSURANCE, MWBE, REGISTRATION")
    title: str = Field(..., description="Clear, concise finding title")
    detail: str = Field(..., description="Explanatory details of non-compliance")
    disqualification_risk: bool = Field(True, description="True if causes non-responsive rejection")
    remediation_step: str = Field(..., description="Actionable cure or mitigation strategy")
    clause_ref: Optional[str] = Field(None, description="Referenced clause ID in solicitation")


class GapAnalysisResult(BaseModel):
    """Holistic Go/No-Go bid assessment and qualification score."""
    solicitation_number: str = Field(..., description="Target solicitation identifier")
    vendor_name: str = Field(..., description="Vendor evaluated")
    recommendation: str = Field(..., description="GO, CONDITIONAL_GO, or NO_GO")
    fit_score: float = Field(..., description="Overall qualification score (0.0 - 100.0)")
    disqualifiers: List[DisqualificationFinding] = Field(default_factory=list, description="Disqualification risks")
    competency_gaps: List[str] = Field(default_factory=list, description="Missing competencies or certifications")
    competitive_strengths: List[str] = Field(default_factory=list, description="Key differentiators and high-scoring areas")
    timestamp: str = Field(..., description="ISO 8601 audit timestamp")


class ProblemDetails(BaseModel):
    """RFC 7807 Problem Details representation for structured errors."""
    type: str = Field("about:blank", description="URI reference identifying problem type")
    title: str = Field(..., description="Short, human-readable summary of problem")
    status: int = Field(..., description="HTTP status code")
    detail: str = Field(..., description="Human-readable explanation specific to this occurrence")
    instance: Optional[str] = Field(None, description="URI reference identifying specific occurrence")
    code: str = Field(..., description="Machine-readable error code")
    timestamp: str = Field(..., description="ISO 8601 error generation timestamp")
