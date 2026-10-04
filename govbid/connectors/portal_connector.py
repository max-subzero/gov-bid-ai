"""Connectors and triage engine for SAM.gov Opportunities and NYC City Record."""

import datetime
import json
from typing import Any, Dict, List, Optional, Union
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.engines.gap_analyzer import GapAnalyzer
from govbid.models.audit import FindingSeverity
from govbid.models.portal import (
    PortalSource,
    PortalTriageReport,
    ProcurementNoticeType,
    RawPortalOpportunity,
    SetAsideType,
    TriageResult,
)
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser


class PortalConnectorEngine:
    """Ingests public procurement portal feeds and executes automated pre-flight bid triage."""

    def __init__(self) -> None:
        self.rfp_parser = RfpParser()
        self.disq_guard = DisqualificationGuard()
        self.gap_analyzer = GapAnalyzer()

    def parse_sam_gov_feed(self, data: Union[str, Dict[str, Any]]) -> List[RawPortalOpportunity]:
        """Parses a standard SAM.gov Opportunities API v2 JSON response into normalized models."""
        payload = json.loads(data) if isinstance(data, str) else data
        items = payload.get("opportunitiesData") or payload.get("data") or []
        if isinstance(payload, list):
            items = payload

        opportunities: List[RawPortalOpportunity] = []
        for raw in items:
            notice_id = str(raw.get("noticeId") or raw.get("id") or "UNKNOWN-NOTICE")
            title = raw.get("title") or "Untitled Federal Solicitation"
            sol_num = raw.get("solicitationNumber") or notice_id
            agency = raw.get("fullParentPathName") or raw.get("department") or raw.get("agency") or "Federal Agency"
            posted = raw.get("postedDate") or raw.get("publishedDate") or "2026-10-01"
            deadline = raw.get("responseDeadLine") or raw.get("archiveDate")
            desc = raw.get("description") or title

            # Detect set-aside
            raw_set_aside = str(raw.get("typeOfSetAside") or raw.get("typeOfSetAsideDescription") or "").upper()
            if "8(A)" in raw_set_aside or "8A" in raw_set_aside:
                set_aside = SetAsideType.SBA_8A
            elif "WOSB" in raw_set_aside:
                set_aside = SetAsideType.WOSB
            elif "SDVOSB" in raw_set_aside:
                set_aside = SetAsideType.SDVOSB
            elif "SBA" in raw_set_aside or "SMALL" in raw_set_aside:
                set_aside = SetAsideType.TOTAL_SMALL_BUSINESS
            else:
                set_aside = SetAsideType.NONE_UNRESTRICTED

            # Detect notice type
            raw_type = str(raw.get("type") or raw.get("noticeType") or "").upper()
            if "PRESOL" in raw_type:
                notice_type = ProcurementNoticeType.PRESOLICITATION
            elif "COMBINE" in raw_type:
                notice_type = ProcurementNoticeType.COMBINED_SYNOPSIS
            elif "SOURCES" in raw_type:
                notice_type = ProcurementNoticeType.SOURCES_SOUGHT
            elif "AWARD" in raw_type:
                notice_type = ProcurementNoticeType.AWARD_NOTICE
            else:
                notice_type = ProcurementNoticeType.SOLICITATION

            ui_link = raw.get("uiLink") or f"https://sam.gov/opp/{notice_id}/view"
            attachments = raw.get("resourceLinks") or []

            opportunities.append(
                RawPortalOpportunity(
                    notice_id=notice_id,
                    title=title,
                    solicitation_number=sol_num,
                    agency=agency,
                    posted_date=posted,
                    response_deadline=deadline,
                    source=PortalSource.SAM_GOV,
                    notice_type=notice_type,
                    set_aside=set_aside,
                    naics_code=str(raw.get("naicsCode") or "") or None,
                    description=desc,
                    ui_link=ui_link,
                    attachment_urls=attachments if isinstance(attachments, list) else [attachments],
                )
            )

        return opportunities

    def parse_city_record_feed(self, data: Union[str, Dict[str, Any], List[Dict[str, Any]]]) -> List[RawPortalOpportunity]:
        """Parses City of New York City Record Online (CROL) / OpenData JSON feed."""
        if isinstance(data, str):
            payload = json.loads(data)
        else:
            payload = data

        items = payload if isinstance(payload, list) else payload.get("data") or payload.get("rows") or []

        opportunities: List[RawPortalOpportunity] = []
        for raw in items:
            pin = str(raw.get("pin") or raw.get("request_id") or "UNKNOWN-PIN")
            title = raw.get("short_title") or raw.get("solicitation_name") or "NYC Municipal Procurement"
            agency = raw.get("agency_name") or "City of New York"
            posted = raw.get("publish_date") or raw.get("start_date") or "2026-10-01"
            deadline = raw.get("due_date")
            desc = raw.get("additional_description") or raw.get("description") or title

            opportunities.append(
                RawPortalOpportunity(
                    notice_id=pin,
                    title=title,
                    solicitation_number=pin,
                    agency=agency,
                    posted_date=posted,
                    response_deadline=deadline,
                    source=PortalSource.NYC_CITY_RECORD,
                    notice_type=ProcurementNoticeType.SOLICITATION,
                    set_aside=SetAsideType.MWBE_LOCAL,
                    naics_code=str(raw.get("naics_code") or "") or None,
                    description=desc,
                    ui_link=raw.get("url") or f"https://a856-cityrecord.nyc.gov/RequestDetail/{pin}",
                    attachment_urls=[],
                )
            )

        return opportunities

    def triage_opportunities(
        self,
        opportunities: List[RawPortalOpportunity],
        vendor: VendorProfile,
        min_fit_score: float = 0.0,
    ) -> PortalTriageReport:
        """Evaluates, scores, and ranks inbound portal opportunities against vendor qualifications."""
        ranked_results: List[TriageResult] = []
        qualified_count = 0
        disqualified_count = 0

        for opp in opportunities:
            # Construct synthetic solicitation packet text from notice metadata & description
            packet_text = (
                f"SOLICITATION TITLE: {opp.title}\n"
                f"PIN: {opp.solicitation_number}\n"
                f"ISSUED BY: {opp.agency}\n"
                f"PROPOSAL DUE DATE: {opp.response_deadline or 'Open'}\n\n"
                f"DESCRIPTION:\n{opp.description}\n"
            )

            # Parse clauses and structure
            rfp = self.rfp_parser.parse_text(packet_text)
            rfp.solicitation_number = opp.solicitation_number
            rfp.title = opp.title
            rfp.issuing_agency = opp.agency

            # Evaluate disqualifications and fit score
            disq_findings = self.disq_guard.evaluate(rfp, vendor)
            gap_analysis = self.gap_analyzer.analyze(rfp, vendor)

            fatal_disqualifiers: List[str] = []
            remediable_actions: List[str] = []

            for finding in disq_findings:
                if finding.rule_category in ["EXPERIENCE", "PREVAILING_WAGE"] and finding.severity == FindingSeverity.CRITICAL:
                    fatal_disqualifiers.append(f"[{finding.rule_category}] {finding.title}: {finding.detail}")
                else:
                    remediable_actions.append(f"[{finding.rule_category}] {finding.remediation_step}")

            rec_val = str(gap_analysis.recommendation.value if hasattr(gap_analysis.recommendation, "value") else gap_analysis.recommendation)
            is_disqualified = len(fatal_disqualifiers) > 0 or rec_val == "NO_GO"

            if is_disqualified:
                disqualified_count += 1
            else:
                qualified_count += 1

            if gap_analysis.fit_score >= min_fit_score:
                ranked_results.append(
                    TriageResult(
                        opportunity=opp,
                        parsed_rfp=rfp,
                        fit_score=gap_analysis.fit_score,
                        recommendation=rec_val,
                        is_disqualified=is_disqualified,
                        fatal_disqualifiers=fatal_disqualifiers,
                        remediable_actions=remediable_actions,
                        estimated_budget=rfp.estimated_budget,
                    )
                )

        # Sort descending by fit score
        ranked_results.sort(key=lambda r: r.fit_score, reverse=True)

        source = opportunities[0].source if opportunities else PortalSource.CUSTOM_FEED
        scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return PortalTriageReport(
            scan_timestamp=scan_time,
            source=source,
            total_scanned=len(opportunities),
            qualified_count=qualified_count,
            disqualified_count=disqualified_count,
            ranked_opportunities=ranked_results,
        )
