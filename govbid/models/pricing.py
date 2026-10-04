"""Data models for Commercial Pricing, Prevailing Wage Schedules, and Fee Schedules."""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class WageClassificationType(str, Enum):
    """Labor classification under federal and municipal labor law."""
    PREVAILING_WAGE_TRADE = "PREVAILING_WAGE_TRADE"  # Governed by NY Labor Law § 220/230 or Davis-Bacon/SCA
    EXEMPT_PROFESSIONAL = "EXEMPT_PROFESSIONAL"      # FLSA exempt engineering, architectural, or executive


class StatutoryWageSchedule(BaseModel):
    """Statutory prevailing wage determination issued by Comptroller or Department of Labor."""
    schedule_id: str = Field(..., description="Unique schedule code, e.g. NYC-LL220-2026-ELEC")
    trade_title: str = Field(..., description="Official trade classification name")
    jurisdiction: str = Field("NYC Comptroller", description="Issuing labor regulatory authority")
    base_hourly_wage: float = Field(..., description="Statutory minimum cash wage per hour in USD")
    fringe_hourly_rate: float = Field(..., description="Statutory supplemental / fringe benefit rate in USD")
    overtime_multiplier: float = Field(1.5, description="Overtime rate multiplier (typically 1.5x or 2.0x)")
    effective_period: str = Field(..., description="Statutory schedule fiscal year or period")


class LaborCategory(BaseModel):
    """A defined staffing role with loaded cost modeling and statutory floor validation."""
    role_id: str = Field(..., description="Unique labor role identifier")
    title: str = Field(..., description="Staffing job title")
    classification: WageClassificationType = Field(..., description="Prevailing wage trade vs exempt professional")
    statutory_schedule: Optional[StatutoryWageSchedule] = Field(None, description="Linked prevailing wage schedule if applicable")
    base_hourly_rate: float = Field(..., description="Base direct cash wage paid to worker ($/hr)")
    fringe_hourly_rate: float = Field(default=0.0, description="Supplemental fringe benefit rate ($/hr)")
    payroll_tax_burden_pct: float = Field(default=12.0, description="Mandatory FICA (7.65%), FUTA, SUI burden percentage")
    workers_comp_pct: float = Field(default=5.0, description="Workers compensation and statutory disability percentage")
    overhead_pct: float = Field(default=15.0, description="Company general & administrative (G&A) overhead percentage")
    profit_margin_pct: float = Field(default=12.0, description="Target corporate profit margin percentage")
    loaded_hourly_rate: float = Field(default=0.0, description="Final fully loaded hourly billing rate ($/hr)")
    statutory_minimum_floor: float = Field(default=0.0, description="Absolute legal minimum loaded rate ($/hr)")
    is_compliant: bool = Field(default=True, description="Whether loaded rate satisfies statutory minimums")


class StaffingRequirement(BaseModel):
    """A staffing allocation item detailing role, headcount, and billable hours."""
    role_id: str = Field(..., description="Identifier matching LaborCategory role_id")
    labor_category: LaborCategory = Field(..., description="Configured labor category model")
    headcount: int = Field(default=1, description="Number of personnel assigned")
    total_hours: float = Field(..., description="Total billable hours committed across contract term")
    subtotal_labor_cost: float = Field(default=0.0, description="Total billed labor price in USD")


class PricingModelResult(BaseModel):
    """Comprehensive fee schedule and prevailing wage compliance audit result."""
    solicitation_number: str = Field(..., description="PIN or RFP solicitation number")
    prevailing_wage_mandated: bool = Field(..., description="Whether solicitation contains prevailing wage clause")
    total_billable_hours: float = Field(..., description="Total project labor hours")
    total_labor_cost: float = Field(..., description="Sum of all loaded labor costs in USD")
    materials_and_odc: float = Field(default=0.0, description="Hardware, materials, and other direct costs (ODC) in USD")
    total_contract_price: float = Field(..., description="Total proposed contract price in USD")
    effective_blended_hourly_rate: float = Field(..., description="Weighted average loaded billing rate ($/hr)")
    is_fully_compliant: bool = Field(..., description="Zero statutory wage deficits across all roles")
    staffing_breakdown: List[StaffingRequirement] = Field(default_factory=list, description="Role-by-role labor cost items")
    compliance_alerts: List[str] = Field(default_factory=list, description="Deficit notices or statutory audit warnings")
