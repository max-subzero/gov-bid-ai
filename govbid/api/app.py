"""FastAPI Application providing the GovBid AI Enterprise REST API & Interactive Console."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from govbid import __version__
from govbid.api.console_html import CONSOLE_HTML
from govbid.api.schemas import (
    CheckRequest,
    CheckResponse,
    DiffRequest,
    DraftRequest,
    EvaluateRequest,
    HealthResponse,
    ParseRequest,
    PricingRequest,
    PricingResponse,
    ScheduleBRequest,
    TriageRequest,
)
from govbid.connectors.portal_connector import PortalConnectorEngine
from govbid.engines.addendum_diff import AddendumDiffEngine
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.engines.gap_analyzer import GapAnalyzer
from govbid.engines.pricing_engine import PricingLaborEngine
from govbid.engines.proposal_synthesizer import ProposalSynthesizerEngine
from govbid.engines.schedule_b_allocator import ScheduleBAllocator
from govbid.models.addendum import AddendumAnalysisResult
from govbid.models.audit import GapAnalysisResult
from govbid.models.mwbe import ScheduleBPlan
from govbid.models.portal import PortalSource, PortalTriageReport
from govbid.models.proposal import ProposalDraft
from govbid.models.rfp import ParsedRfp
from govbid.parsers.rfp_parser import RfpParser

FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"


def create_app() -> FastAPI:
    """Creates and configures the GovBid FastAPI application."""
    app = FastAPI(
        title="GovBid AI REST API",
        description="Enterprise Procurement Compliance, Disqualification Defense, and Opportunity Triage Platform",
        version=__version__,
    )

    # RFC 7807 Structured Problem Details Exception Handlers (Working Agreement 14)
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": str(exc.detail),
                "code": f"HTTP_{exc.status_code}",
                "details": getattr(exc, "details", None),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Request validation failed",
                "code": "UNPROCESSABLE_ENTITY",
                "details": exc.errors(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "code": "INTERNAL_SERVER_ERROR",
                "details": str(exc),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    # Health Check
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            version=__version__,
            service="GovBid AI Compliance & Opportunity Triage Platform",
        )

    # Interactive Console
    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/console")

    @app.get("/console", response_class=HTMLResponse, tags=["Console"])
    async def console() -> HTMLResponse:
        return HTMLResponse(content=CONSOLE_HTML)

    # Sample Feeds & Fixtures for Interactive Testing
    @app.get("/api/v1/sample/sam-gov", tags=["Samples"])
    async def sample_sam_gov() -> Dict[str, Any]:
        sam_path = FIXTURES_DIR / "sample_sam_gov_feed.json"
        if sam_path.exists():
            with open(sam_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"opportunitiesData": []}

    @app.get("/api/v1/sample/city-record", tags=["Samples"])
    async def sample_city_record() -> List[Dict[str, Any]]:
        city_path = FIXTURES_DIR / "sample_city_record_feed.json"
        if city_path.exists():
            with open(city_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    # API v1: Parse RFP
    @app.post("/api/v1/parse", response_model=ParsedRfp, tags=["Procurement"])
    async def parse_solicitation(req: ParseRequest) -> ParsedRfp:
        parser = RfpParser()
        try:
            return parser.parse_text(req.text)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse solicitation: {str(e)}")

    # API v1: Disqualification Pre-Flight Check
    @app.post("/api/v1/check", response_model=CheckResponse, tags=["Compliance"])
    async def check_disqualification(req: CheckRequest) -> CheckResponse:
        if req.rfp is not None:
            rfp = req.rfp
        elif req.rfp_text:
            parser = RfpParser()
            rfp = parser.parse_text(req.rfp_text)
        else:
            raise HTTPException(status_code=400, detail="Either 'rfp' or 'rfp_text' must be provided.")

        guard = DisqualificationGuard()
        findings = guard.evaluate(rfp, req.vendor)
        fatal_count = sum(1 for f in findings if f.severity.value == "FATAL" or f.severity.value == "CRITICAL")
        return CheckResponse(
            solicitation_number=rfp.solicitation_number,
            is_compliant=(fatal_count == 0),
            findings_count=len(findings),
            findings=findings,
        )

    # API v1: Quantitative Fit Scoring (Go / No-Go)
    @app.post("/api/v1/evaluate", response_model=GapAnalysisResult, tags=["Compliance"])
    async def evaluate_fit(req: EvaluateRequest) -> GapAnalysisResult:
        if req.rfp is not None:
            rfp = req.rfp
        elif req.rfp_text:
            parser = RfpParser()
            rfp = parser.parse_text(req.rfp_text)
        else:
            raise HTTPException(status_code=400, detail="Either 'rfp' or 'rfp_text' must be provided.")

        analyzer = GapAnalyzer()
        return analyzer.analyze(rfp, req.vendor)

    # API v1: Addendum / Amendment Differential
    @app.post("/api/v1/diff", response_model=AddendumAnalysisResult, tags=["Procurement"])
    async def diff_addendum(req: DiffRequest) -> AddendumAnalysisResult:
        engine = AddendumDiffEngine()
        return engine.analyze_diff(
            base_rfp=req.base_text,
            addendum_content=req.addendum_text,
        )

    # API v1: Schedule B M/WBE Allocator
    @app.post("/api/v1/schedule-b", response_model=ScheduleBPlan, tags=["Subcontracting"])
    async def schedule_b(req: ScheduleBRequest) -> ScheduleBPlan:
        allocator = ScheduleBAllocator()
        if req.recommend and req.candidates:
            return allocator.recommend_allocations(
                solicitation_number=req.solicitation_number,
                total_bid_amount=req.total_bid_amount,
                mandatory_goal_percentage=req.mandatory_goal_percentage,
                candidates=req.candidates,
            )
        else:
            return allocator.calculate_plan(
                solicitation_number=req.solicitation_number,
                total_bid_amount=req.total_bid_amount,
                mandatory_goal_percentage=req.mandatory_goal_percentage,
                allocations=req.allocations or [],
                waiver_justification=req.waiver_justification,
            )

    # API v1: Commercial Pricing & Prevailing Wage Modeler
    @app.post("/api/v1/pricing", response_model=PricingResponse, tags=["Pricing"])
    async def pricing(req: PricingRequest) -> PricingResponse:
        engine = PricingLaborEngine()
        model_result = engine.build_fee_schedule(
            solicitation_number=req.solicitation_number,
            staffing=req.staffing,
            prevailing_wage_mandated=req.prevailing_wage_mandated,
            materials_and_odc=req.materials_and_odc,
        )
        declaration = None
        if req.generate_certified_payroll:
            declaration = engine.generate_certified_payroll_declaration(
                result=model_result,
                vendor_name=req.vendor_name or "Prime Proposal Bidder",
            )
        return PricingResponse(
            model_result=model_result,
            certified_payroll_declaration=declaration,
        )

    # API v1: Portal Opportunities Ingestion & Automated Triage
    @app.post("/api/v1/triage", response_model=PortalTriageReport, tags=["Portals"])
    async def triage_portal_feed(req: TriageRequest) -> PortalTriageReport:
        engine = PortalConnectorEngine()
        feed_data = req.feed_data

        # Determine parser from source or structure
        if req.source == PortalSource.NYC_CITY_RECORD or (isinstance(feed_data, list) and len(feed_data) > 0 and "pin" in feed_data[0]):
            opportunities = engine.parse_city_record_feed(feed_data)
        elif req.source == PortalSource.SAM_GOV or (isinstance(feed_data, dict) and "opportunitiesData" in feed_data):
            opportunities = engine.parse_sam_gov_feed(feed_data)
        elif isinstance(feed_data, list):
            opportunities = engine.parse_city_record_feed(feed_data)
        elif isinstance(feed_data, dict):
            opportunities = engine.parse_sam_gov_feed(feed_data)
        else:
            raise HTTPException(status_code=400, detail="Unrecognized feed data format.")

        return engine.triage_opportunities(
            opportunities=opportunities,
            vendor=req.vendor,
            min_fit_score=req.min_score,
        )

    # API v1: Grounded Proposal Prose Synthesizer
    @app.post("/api/v1/draft", response_model=ProposalDraft, tags=["Proposals"])
    async def draft_proposal(req: DraftRequest) -> ProposalDraft:
        if req.rfp is not None:
            rfp = req.rfp
        elif req.rfp_text:
            parser = RfpParser()
            rfp = parser.parse_text(req.rfp_text)
        else:
            raise HTTPException(status_code=400, detail="Either 'rfp' or 'rfp_text' must be provided.")

        synthesizer = ProposalSynthesizerEngine()
        return synthesizer.synthesize_proposal(
            rfp=rfp,
            vendor=req.vendor,
            staffing_plan=req.staffing,
            total_bid_amount=req.total_bid_amount,
            materials_and_odc=req.materials_and_odc,
            waiver_reason=req.waiver_reason,
        )

    return app


app = create_app()
