"""Data models for Schedule B M/WBE Subcontractor Utilization Plans."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MwbeCertificationType(str, Enum):
    """Recognized municipal, state, and federal business enterprise certifications."""
    MBE = "MBE"       # Minority-Owned Business Enterprise
    WBE = "WBE"       # Women-Owned Business Enterprise
    MWBE = "MWBE"     # Dual Minority and Women-Owned Business Enterprise
    DBE = "DBE"       # Disadvantaged Business Enterprise (DOT / FTA)
    SDVOB = "SDVOB"   # Service-Disabled Veteran-Owned Business


class EthnicityGenderCategory(str, Enum):
    """Statutory demographic subcategories tracked under NYC Local Law 1 & PPB rules."""
    BLACK_AMERICAN = "Black American"
    HISPANIC_AMERICAN = "Hispanic American"
    ASIAN_AMERICAN = "Asian American"
    NON_MINORITY_FEMALE = "Caucasian Female"
    NATIVE_AMERICAN = "Native American"
    OTHER = "Other"


class SubcontractorAllocation(BaseModel):
    """An allocated certified M/WBE subcontractor partnership."""
    subcontractor_id: str = Field(..., description="Unique identifier for subcontractor")
    company_name: str = Field(..., description="Legal company name of certified firm")
    certification_type: MwbeCertificationType = Field(..., description="MBE, WBE, MWBE, DBE, SDVOB")
    certifying_agency: str = Field(..., description="E.g. NYC SBS, NYS Empire State Development, PANYNJ")
    ethnicity_gender: Optional[EthnicityGenderCategory] = Field(None, description="Demographic classification")
    scope_of_work: str = Field(..., description="Description of subcontracted trade or service scope")
    naics_code: Optional[str] = Field(None, description="6-digit NAICS code or NIGP commodity code")
    allocated_amount: float = Field(..., description="Dollar amount committed to subcontractor in USD")
    percentage_of_total: float = Field(default=0.0, description="Percentage of total contract bid amount")


class GoodFaithEffortRecord(BaseModel):
    """Documented outreach and good faith efforts (GFE) for partial or full waiver requests."""
    action_type: str = Field(..., description="DIRECTORY_SEARCH, DIRECT_OUTREACH, UNBUNDLED_SCOPE, or ADVERTISEMENT")
    description: str = Field(..., description="Summary of specific action undertaken")
    date_performed: str = Field(..., description="Date or date range of effort")
    firms_contacted: int = Field(default=0, description="Number of certified firms solicited")
    responses_received: int = Field(default=0, description="Number of bids or inquiries received")
    outcome: str = Field(..., description="Reason for rejection or non-selection")


class ScheduleBStatus(str, Enum):
    """Compliance state of the Schedule B Utilization Plan."""
    COMPLIANT = "COMPLIANT"                 # Meets or exceeds mandatory goal
    PARTIAL_DEFICIT = "PARTIAL_DEFICIT"     # Some allocation, but below mandatory goal
    FULL_DEFICIT = "FULL_DEFICIT"           # Zero M/WBE allocation provided
    WAIVER_REQUESTED = "WAIVER_REQUESTED"   # Accompanied by official waiver request packet


class ScheduleBPlan(BaseModel):
    """Complete Schedule B M/WBE Subcontractor Utilization Plan."""
    solicitation_number: str = Field(..., description="Solicitation PIN or RFP identifier")
    total_bid_amount: float = Field(..., description="Total proposed contract price in USD")
    mandatory_goal_percentage: float = Field(..., description="Mandatory M/WBE goal (e.g. 30.0 for 30%)")
    required_mwbe_amount: float = Field(..., description="Required M/WBE spend threshold in USD")
    actual_mwbe_amount: float = Field(..., description="Total allocated M/WBE spend in USD")
    actual_mwbe_percentage: float = Field(..., description="Total allocated M/WBE percentage")
    mbe_percentage: float = Field(default=0.0, description="Percentage committed to MBE certified firms")
    wbe_percentage: float = Field(default=0.0, description="Percentage committed to WBE certified firms")
    status: ScheduleBStatus = Field(..., description="Overall compliance status")
    allocations: List[SubcontractorAllocation] = Field(default_factory=list, description="Subcontractor lines")
    shortfall_amount: float = Field(default=0.0, description="Dollar shortfall below mandatory goal")
    shortfall_percentage: float = Field(default=0.0, description="Percentage point shortfall below goal")
    good_faith_efforts: List[GoodFaithEffortRecord] = Field(default_factory=list, description="GFE audit trail")
    waiver_justification: Optional[str] = Field(None, description="Justification for partial/full waiver")
    validation_messages: List[str] = Field(default_factory=list, description="Warnings or compliance alerts")
