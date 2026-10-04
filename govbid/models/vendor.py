"""Data models for Vendor Profiles, Certifications, and Past Performance."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PastPerformanceRecord(BaseModel):
    """A verified past performance record cited in proposals."""
    record_id: str = Field(..., description="Unique ID for past contract")
    client_name: str = Field(..., description="Agency or corporate client name")
    is_government: bool = Field(True, description="Whether client is a public sector entity")
    contract_value: float = Field(..., description="Total contract value in USD")
    duration_years: float = Field(..., description="Duration of contract in years")
    domain: str = Field(..., description="Functional domain, e.g. Fleet Telematics, Cloud Infrastructure")
    summary: str = Field(..., description="Verifiable description of work performed and results delivered")
    reference_contact: Optional[str] = Field(None, description="Contact info for reference checks")


class VendorProfile(BaseModel):
    """Structured vendor capability profile for qualification and gap analysis."""
    vendor_id: str = Field(..., description="Unique identifier for vendor")
    name: str = Field(..., description="Legal company name")
    years_in_business: int = Field(..., description="Consecutive operating years")
    insurance_general_liability: float = Field(default=0.0, description="General liability coverage in USD")
    insurance_cyber_liability: float = Field(default=0.0, description="Cyber liability coverage in USD")
    bonding_capacity: float = Field(default=0.0, description="Surety bonding capacity in USD")
    is_mwbe_certified: bool = Field(default=False, description="Whether vendor is certified MBE/WBE/DBE")
    mwbe_subcontractor_network: bool = Field(default=False, description="Has established M/WBE subcontractor partners")
    prevailing_wage_compliant: bool = Field(default=True, description="Enforces prevailing wage & certified payroll")
    certifications: List[str] = Field(default_factory=list, description="List of vendor certifications")
    active_registrations: List[str] = Field(default_factory=list, description="Active registries: NYC_PASSPORT, SAM_GOV")
    past_performance: List[PastPerformanceRecord] = Field(default_factory=list, description="Verified past performance records")
