"""Data models for Live Procurement Portals (SAM.gov & NYC City Record) and Automated Triage."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from govbid.models.audit import DisqualificationFinding
from govbid.models.rfp import ParsedRfp


class PortalSource(str, Enum):
    """Supported public procurement portals and data sources."""
    SAM_GOV = "SAM_GOV"                    # Federal System for Award Management (api.sam.gov)
    NYC_CITY_RECORD = "NYC_CITY_RECORD"    # City of New York City Record Online (CROL)
    CUSTOM_FEED = "CUSTOM_FEED"            # User-supplied solicitation syndication feed


class ProcurementNoticeType(str, Enum):
    """Class of procurement notice published by public sector agencies."""
    SOLICITATION = "SOLICITATION"
    PRESOLICITATION = "PRESOLICITATION"
    COMBINED_SYNOPSIS = "COMBINED_SYNOPSIS"
    SOURCES_SOUGHT = "SOURCES_SOUGHT"
    AWARD_NOTICE = "AWARD_NOTICE"


class SetAsideType(str, Enum):
    """Small business and socio-economic set-aside classifications."""
    NONE_UNRESTRICTED = "Unrestricted / Full & Open"
    TOTAL_SMALL_BUSINESS = "Total Small Business Set-Aside"
    SBA_8A = "8(a) Business Development Program"
    WOSB = "Women-Owned Small Business"
    EDWOSB = "Economically Disadvantaged Women-Owned"
    SDVOSB = "Service-Disabled Veteran-Owned"
    HUBZONE = "Historically Underutilized Business Zone"
    MWBE_LOCAL = "Local M/WBE Preference / Quota"


class RawPortalOpportunity(BaseModel):
    """A normalized procurement notice ingested from a public agency feed or API."""
    notice_id: str = Field(..., description="Unique notice ID or portal identifier")
    title: str = Field(..., description="Official solicitation title")
    solicitation_number: str = Field(..., description="PIN, RFP#, or solicitation identifier")
    agency: str = Field(..., description="Issuing agency, department, or bureau")
    posted_date: str = Field(..., description="Date published on portal (ISO or date string)")
    response_deadline: Optional[str] = Field(None, description="Proposal submission deadline")
    source: PortalSource = Field(..., description="Origin portal (SAM.gov or City Record)")
    notice_type: ProcurementNoticeType = Field(default=ProcurementNoticeType.SOLICITATION)
    set_aside: SetAsideType = Field(default=SetAsideType.NONE_UNRESTRICTED)
    naics_code: Optional[str] = Field(None, description="Primary 6-digit NAICS code")
    description: str = Field(..., description="Scope of work or solicitation synopsis")
    ui_link: Optional[str] = Field(None, description="Public web URL to view procurement packet")
    attachment_urls: List[str] = Field(default_factory=list, description="Links to download RFP PDFs")


class TriageResult(BaseModel):
    """Qualification audit and fit score evaluated for an ingested opportunity."""
    opportunity: RawPortalOpportunity = Field(..., description="Ingested portal notice")
    parsed_rfp: ParsedRfp = Field(..., description="Structured RFP model parsed from notice synopsis")
    fit_score: float = Field(..., description="Computed qualification fit score (0.0 - 100.0)")
    recommendation: str = Field(..., description="GO, CONDITIONAL_GO, or NO_GO")
    is_disqualified: bool = Field(default=False, description="Whether fatal disqualification triggers exist")
    fatal_disqualifiers: List[str] = Field(default_factory=list, description="Non-remediable dealbreakers")
    remediable_actions: List[str] = Field(default_factory=list, description="Action items to achieve compliance")
    estimated_budget: Optional[float] = Field(None, description="Estimated contract budget if disclosed")


class PortalTriageReport(BaseModel):
    """Comprehensive opportunity scan and ranking report for a vendor profile."""
    scan_timestamp: str = Field(..., description="Timestamp when portal scan was executed")
    source: PortalSource = Field(..., description="Ingested portal data source")
    total_scanned: int = Field(..., description="Total procurement notices analyzed")
    qualified_count: int = Field(..., description="Opportunities meeting recommendation threshold (GO / COND_GO)")
    disqualified_count: int = Field(..., description="Opportunities rejected on fatal disqualifiers")
    ranked_opportunities: List[TriageResult] = Field(default_factory=list, description="Results ordered by fit score")
