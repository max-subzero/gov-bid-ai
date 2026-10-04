"""Request and response schemas for the GovBid REST API."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

from govbid.models.audit import DisqualificationFinding, GapAnalysisResult
from govbid.models.mwbe import ScheduleBPlan, SubcontractorAllocation
from govbid.models.portal import PortalSource, PortalTriageReport, RawPortalOpportunity
from govbid.models.pricing import PricingModelResult, StaffingRequirement
from govbid.models.rfp import ParsedRfp
from govbid.models.vendor import VendorProfile


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(default="ok", description="Service health state")
    version: str = Field(..., description="Platform version string")
    service: str = Field(..., description="Service identity description")


class ParseRequest(BaseModel):
    """Payload for parsing raw solicitation text."""
    text: str = Field(..., description="Raw text of the RFP/solicitation document")
    filename: Optional[str] = Field(default="document.txt", description="Originating filename or identifier")


class CheckRequest(BaseModel):
    """Payload for pre-flight disqualification defense audit."""
    rfp_text: Optional[str] = Field(default=None, description="Raw solicitation text (if RFP not pre-parsed)")
    rfp: Optional[ParsedRfp] = Field(default=None, description="Pre-parsed RFP schema")
    vendor: VendorProfile = Field(..., description="Vendor profile and qualification capabilities")


class CheckResponse(BaseModel):
    """Audit response from disqualification check."""
    solicitation_number: str = Field(..., description="Solicitation identifier")
    is_compliant: bool = Field(..., description="True if zero fatal disqualifiers exist")
    findings_count: int = Field(..., description="Total number of findings detected")
    findings: List[DisqualificationFinding] = Field(default_factory=list, description="List of disqualification findings")


class EvaluateRequest(BaseModel):
    """Payload for quantitative fit scoring and Go/No-Go evaluation."""
    rfp_text: Optional[str] = Field(default=None, description="Raw solicitation text (if RFP not pre-parsed)")
    rfp: Optional[ParsedRfp] = Field(default=None, description="Pre-parsed RFP schema")
    vendor: VendorProfile = Field(..., description="Vendor profile and qualification capabilities")


class DiffRequest(BaseModel):
    """Payload for analyzing solicitation addendum differential."""
    base_text: str = Field(..., description="Baseline RFP or original solicitation text")
    addendum_text: str = Field(..., description="Addendum or amendment text")
    solicitation_number: Optional[str] = Field(default="SOLICITATION-01", description="Solicitation identifier")
    addendum_id: Optional[str] = Field(default="ADDENDUM-01", description="Addendum notice identifier")


class ScheduleBRequest(BaseModel):
    """Payload for Schedule B M/WBE subcontracting calculations."""
    solicitation_number: str = Field(..., description="Solicitation identifier")
    total_bid_amount: float = Field(..., gt=0, description="Total proposal bid amount in USD")
    mandatory_goal_percentage: float = Field(default=30.0, ge=0.0, le=100.0, description="Required M/WBE goal percentage")
    allocations: Optional[List[SubcontractorAllocation]] = Field(default=None, description="Explicit subcontractor allocations")
    candidates: Optional[List[SubcontractorAllocation]] = Field(default=None, description="Candidate partners for auto-recommendation")
    recommend: bool = Field(default=False, description="If true, calculates balanced distribution across candidates")
    waiver_justification: Optional[str] = Field(default=None, description="Statutory justification for pre-bid waiver request")


class PricingRequest(BaseModel):
    """Payload for commercial pricing and prevailing wage fee schedule modeling."""
    solicitation_number: str = Field(..., description="Solicitation identifier")
    staffing: List[StaffingRequirement] = Field(..., description="List of staffing requirements and labor roles")
    prevailing_wage_mandated: bool = Field(default=False, description="Whether prevailing wage trade floors are mandated")
    materials_and_odc: float = Field(default=0.0, ge=0.0, description="Materials and Other Direct Costs (ODC)")
    vendor_name: Optional[str] = Field(default=None, description="Prime contractor legal name for certified payroll")
    generate_certified_payroll: bool = Field(default=False, description="Whether to generate Certified Payroll Declaration")


class PricingResponse(BaseModel):
    """Response containing fee schedule audit and optional certified payroll declaration."""
    model_result: PricingModelResult = Field(..., description="Computed pricing and wage audit breakdown")
    certified_payroll_declaration: Optional[str] = Field(default=None, description="Formal declaration text if requested")


class TriageRequest(BaseModel):
    """Payload for portal feed ingestion and automated triage."""
    feed_data: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="Raw SAM.gov or City Record JSON feed data")
    vendor: VendorProfile = Field(..., description="Vendor qualification profile")
    source: Optional[PortalSource] = Field(default=None, description="Portal feed source format (auto-detected if omitted)")
    min_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Minimum fit score threshold")
