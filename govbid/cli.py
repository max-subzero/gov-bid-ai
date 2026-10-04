"""Command-line interface for GovBid AI."""

import argparse
import json
import sys
from pathlib import Path
from govbid.connectors.portal_connector import PortalConnectorEngine
from govbid.engines.addendum_diff import AddendumDiffEngine
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.engines.gap_analyzer import GapAnalyzer
from govbid.engines.pricing_engine import PricingLaborEngine
from govbid.engines.proposal_grounder import ProposalGrounder
from govbid.engines.proposal_synthesizer import ProposalSynthesizerEngine
from govbid.engines.schedule_b_allocator import ScheduleBAllocator
from govbid.models.pricing import StaffingRequirement
from govbid.models.rfp import ClauseCategory
from govbid.models.vendor import VendorProfile
from govbid.parsers.rfp_parser import RfpParser


def load_vendor(vendor_path: str) -> VendorProfile:
    """Loads and validates a vendor JSON profile."""
    path = Path(vendor_path)
    if not path.exists():
        print(f"Error: Vendor profile not found at '{vendor_path}'", file=sys.stderr)
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return VendorProfile(**data)


def cmd_parse(args: argparse.Namespace) -> None:
    """Executes RFP parsing and clause detection (supports .pdf, .txt, .md)."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)

    if args.json:
        print(rfp.model_dump_json(indent=2))
        return

    print("=" * 70)
    print(f"SOLICITATION METADATA: {rfp.solicitation_number}")
    print("=" * 70)
    print(f"Title:        {rfp.title}")
    print(f"Agency:       {rfp.issuing_agency}")
    print(f"Jurisdiction: {rfp.jurisdiction}")
    print(f"Deadline:     {rfp.submission_deadline or 'Not specified'}")
    print("\nEVALUATION CRITERIA:")
    for crit in rfp.evaluation_criteria:
        print(f"  • {crit.title:35s} {crit.weight_percentage:5.1f}%")

    print(f"\nDETECTED COMPLIANCE CLAUSES ({len(rfp.clauses)} Found):")
    for clause in rfp.clauses:
        thresh = f" [{clause.threshold_value} {clause.threshold_unit}]" if clause.threshold_value else ""
        print(f"  [{clause.category.value}] {clause.title}{thresh}")
        print(f"    Reference: {clause.regulatory_reference or 'N/A'}")
        print(f"    Excerpt:   {clause.raw_excerpt[:90]}...\n")


def cmd_check(args: argparse.Namespace) -> None:
    """Runs DisqualificationGuard against vendor profile."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    guard = DisqualificationGuard()
    findings = guard.evaluate(rfp, vendor)

    if args.json:
        print(json.dumps([f.model_dump() for f in findings], indent=2))
        return

    print("=" * 70)
    print(f"DISQUALIFICATION AUDIT: {vendor.name} vs {rfp.solicitation_number}")
    print("=" * 70)
    if not findings:
        print("✓ Zero disqualification triggers detected. Bid submission is compliant.")
        return

    print(f"⚠️  {len(findings)} COMPLIANCE DEFICIENCIES DETECTED:\n")
    for f in findings:
        print(f"[{f.severity.value}] {f.title}")
        print(f"  Category:    {f.rule_category}")
        print(f"  Detail:      {f.detail}")
        print(f"  Remediation: {f.remediation_step}\n")


def cmd_evaluate(args: argparse.Namespace) -> None:
    """Runs full Gap Analysis and produces Go/No-Go score."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    analyzer = GapAnalyzer()
    result = analyzer.analyze(rfp, vendor)

    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print("=" * 70)
    print(f"BID QUALIFICATION AUDIT: {result.solicitation_number}")
    print("=" * 70)
    print(f"Vendor:         {result.vendor_name}")
    print(f"Recommendation: {result.recommendation}")
    print(f"Fit Score:      {result.fit_score} / 100.0\n")

    if result.disqualifiers:
        print(f"CRITICAL DISQUALIFICATION RISKS ({len(result.disqualifiers)}):")
        for d in result.disqualifiers:
            print(f"  ❌ [{d.severity.value}] {d.title}: {d.remediation_step}")
        print()

    if result.competency_gaps:
        print("COMPETENCY GAPS:")
        for g in result.competency_gaps:
            print(f"  ⚠️  {g}")
        print()

    if result.competitive_strengths:
        print("COMPETITIVE ADVANTAGES:")
        for s in result.competitive_strengths:
            print(f"  ✓ {s}")
    print("=" * 70)


def cmd_outline(args: argparse.Namespace) -> None:
    """Synthesizes proposal outline grounded in past performance."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    grounder = ProposalGrounder()
    outline = grounder.generate_grounded_outline(rfp, vendor)

    if args.json:
        print(json.dumps(outline, indent=2))
        return

    print("=" * 70)
    print(f"GROUNDED PROPOSAL OUTLINE: {rfp.solicitation_number}")
    print("=" * 70)
    for section, citations in outline.items():
        print(f"\nSECTION: {section}")
        for c in citations:
            print(f"  • {c}")


def cmd_diff(args: argparse.Namespace) -> None:
    """Executes differential analysis comparing an Addendum to the baseline RFP."""
    parser = RfpParser()
    base_rfp = parser.parse_file(args.base_rfp)

    # Read addendum content (support .pdf and .txt)
    add_path = Path(args.addendum_file)
    if not add_path.exists():
        print(f"Error: Addendum file not found at '{args.addendum_file}'", file=sys.stderr)
        sys.exit(1)

    if add_path.suffix.lower() == ".pdf":
        from govbid.parsers.pdf_extractor import PdfExtractor
        addendum_content = PdfExtractor().extract_text_from_file(args.addendum_file)
    else:
        with open(add_path, "r", encoding="utf-8") as f:
            addendum_content = f.read()

    engine = AddendumDiffEngine()
    result = engine.analyze_diff(base_rfp, addendum_content)

    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print("=" * 70)
    print(f"ADDENDUM DIFFERENTIAL AUDIT: {result.solicitation_number} - {result.addendum_identifier}")
    print("=" * 70)
    print(f"Summary: {result.summary}\n")

    if result.new_submission_deadline:
        print(f"📅 NEW SUBMISSION DEADLINE: {result.new_submission_deadline}\n")

    if result.diff_items:
        print(f"CONTRACTUAL MODIFICATIONS ({len(result.diff_items)}):")
        for item in result.diff_items:
            print(f"  [{item.severity.value}] {item.title}")
            if item.original_value and item.revised_value:
                print(f"    Original: {item.original_value}")
                print(f"    Revised:  {item.revised_value}")
            print(f"    Impact:   {item.explanation}\n")

    if result.qa_pairs:
        print(f"BIDDER QUESTIONS & OFFICIAL RESPONSES ({len(result.qa_pairs)}):")
        for qa in result.qa_pairs:
            print(f"  Q{qa.question_number}: {qa.question}")
            print(f"  A{qa.question_number}: {qa.answer}\n")
    print("=" * 70)


def cmd_schedule_b(args: argparse.Namespace) -> None:
    """Executes Schedule B M/WBE Subcontractor Utilization Plan calculation and audit."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)
    vendor = load_vendor(args.vendor_file)

    # 1. Detect M/WBE Subcontracting Goal in RFP
    mwbe_clause = next(
        (c for c in rfp.clauses if c.category == ClauseCategory.MWBE_SUBCONTRACTING),
        None,
    )
    goal_pct = mwbe_clause.threshold_value if mwbe_clause and mwbe_clause.threshold_value is not None else 30.0

    # 2. Determine Total Bid Amount
    bid_amount = args.bid_amount if args.bid_amount else (rfp.estimated_budget or 4_500_000.0)

    allocator = ScheduleBAllocator()

    if args.recommend and vendor.candidate_subcontractors:
        plan = allocator.recommend_allocations(
            solicitation_number=rfp.solicitation_number,
            total_bid_amount=bid_amount,
            mandatory_goal_percentage=goal_pct,
            candidates=vendor.candidate_subcontractors,
        )
    else:
        plan = allocator.calculate_plan(
            solicitation_number=rfp.solicitation_number,
            total_bid_amount=bid_amount,
            mandatory_goal_percentage=goal_pct,
            allocations=vendor.candidate_subcontractors,
            waiver_justification=args.waiver_reason,
        )

    if args.json:
        print(plan.model_dump_json(indent=2))
        return

    print("=" * 72)
    print(f"SCHEDULE B M/WBE UTILIZATION AUDIT: {plan.solicitation_number}")
    print("=" * 72)
    print(f"Status:                      [{plan.status.value}]")
    print(f"Total Proposed Bid:          ${plan.total_bid_amount:,.2f}")
    print(f"Mandatory M/WBE Goal:        {plan.mandatory_goal_percentage:.1f}% (${plan.required_mwbe_amount:,.2f})")
    print(f"Total M/WBE Committed:       {plan.actual_mwbe_percentage:.1f}% (${plan.actual_mwbe_amount:,.2f})")
    print(f"  • MBE Share:               {plan.mbe_percentage:.1f}%")
    print(f"  • WBE Share:               {plan.wbe_percentage:.1f}%")
    if plan.shortfall_amount > 0:
        print(f"Shortfall Below Goal:        ${plan.shortfall_amount:,.2f} ({plan.shortfall_percentage:.1f}%)")
    print()

    print(f"SUBCONTRACTOR ALLOCATIONS ({len(plan.allocations)}):")
    if plan.allocations:
        for alloc in plan.allocations:
            print(f"  • [{alloc.certification_type.value} - {alloc.certifying_agency}] {alloc.company_name}")
            print(f"    Amount: ${alloc.allocated_amount:,.2f} ({alloc.percentage_of_total:.1f}% of total contract)")
            print(f"    Scope:  {alloc.scope_of_work}")
            if alloc.naics_code:
                print(f"    NAICS:  {alloc.naics_code}")
            print()
    else:
        print("  None declared in vendor profile.\n")

    if plan.validation_messages:
        print("COMPLIANCE & RISK ALERTS:")
        for msg in plan.validation_messages:
            print(f"  ⚠️  {msg}")
        print()

    if args.waiver_memo or (plan.shortfall_amount > 0 and args.waiver_reason):
        print(allocator.generate_waiver_memo(plan, vendor.name))

    print("=" * 72)


def cmd_price(args: argparse.Namespace) -> None:
    """Executes commercial pricing, labor rate loading, and prevailing wage compliance audit."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)

    # Check prevailing wage mandate in RFP
    prevailing_wage_mandated = any(
        c.category == ClauseCategory.PREVAILING_WAGE for c in rfp.clauses
    )

    # Load staffing plan JSON
    plan_path = Path(args.staffing_file)
    if not plan_path.exists():
        print(f"Error: Staffing plan file not found at '{args.staffing_file}'", file=sys.stderr)
        sys.exit(1)

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_data = json.load(f)

    materials_and_odc = float(plan_data.get("materials_and_odc", 0.0))
    staffing_items = [StaffingRequirement(**item) for item in plan_data.get("staffing", [])]

    engine = PricingLaborEngine()
    result = engine.build_fee_schedule(
        solicitation_number=rfp.solicitation_number,
        staffing=staffing_items,
        prevailing_wage_mandated=prevailing_wage_mandated,
        materials_and_odc=materials_and_odc,
    )

    if args.json:
        print(result.model_dump_json(indent=2))
        return

    print("=" * 74)
    print(f"COMMERCIAL PRICING & PREVAILING WAGE AUDIT: {result.solicitation_number}")
    print("=" * 74)
    status_str = "[COMPLIANT - ZERO STATUTORY DEFICITS]" if result.is_fully_compliant else "[NON-COMPLIANT - WAGE DEFICITS DETECTED]"
    wage_badge = "MANDATORY (NY Labor Law § 220 / Davis-Bacon)" if result.prevailing_wage_mandated else "NOT MANDATED"
    print(f"Prevailing Wage Requirement: {wage_badge}")
    print(f"Compliance Status:           {status_str}")
    print(f"Total Evaluated Bid Price:   ${result.total_contract_price:,.2f}")
    print(f"  • Total Labor Subtotal:    ${result.total_labor_cost:,.2f} ({result.total_billable_hours:,.0f} Total Billable Hours)")
    print(f"  • Materials & Direct ODC:  ${result.materials_and_odc:,.2f}")
    print(f"  • Blended Labor Rate:      ${result.effective_blended_hourly_rate:,.2f}/hr")
    print()

    print(f"STAFFING FEE SCHEDULE BREAKDOWN ({len(result.staffing_breakdown)} Roles):")
    for req in result.staffing_breakdown:
        cat = req.labor_category
        stat_badge = " [PREVAILING WAGE]" if cat.classification.value == "PREVAILING_WAGE_TRADE" else " [EXEMPT]"
        comp_badge = "✓" if cat.is_compliant else "⚠️ DEFICIT"
        print(f"  • {comp_badge} {cat.title}{stat_badge}")
        print(f"    Rate:      ${cat.loaded_hourly_rate:,.2f}/hr (Base: ${cat.base_hourly_rate:,.2f} + Fringe: ${cat.fringe_hourly_rate:,.2f})")
        if cat.statutory_minimum_floor > 0:
            print(f"    Floor:     Legal Minimum Floor is ${cat.statutory_minimum_floor:,.2f}/hr")
        print(f"    Subtotal:  ${req.subtotal_labor_cost:,.2f} ({req.headcount} staff × {req.total_hours:,.0f} hrs)")
        print()

    if result.compliance_alerts:
        print("COMPLIANCE & LABOR LAW RISK ALERTS:")
        for alert in result.compliance_alerts:
            print(f"  ⚠️  {alert}")
        print()

    if args.certified_payroll:
        vendor_name = args.vendor_name or "Prime Proposal Bidder"
        print(engine.generate_certified_payroll_declaration(result, vendor_name=vendor_name))

    print("=" * 74)


def cmd_scan(args: argparse.Namespace) -> None:
    """Ingests procurement portal feeds and executes automated pre-flight opportunity triage."""
    vendor = load_vendor(args.vendor_file)

    feed_path = Path(args.feed_file)
    if not feed_path.exists():
        print(f"Error: Feed file not found at '{args.feed_file}'", file=sys.stderr)
        sys.exit(1)

    with open(feed_path, "r", encoding="utf-8") as f:
        feed_data = json.load(f)

    engine = PortalConnectorEngine()

    # Determine source format
    if args.source == "city_record" or (isinstance(feed_data, list) and len(feed_data) > 0 and "pin" in feed_data[0]):
        opportunities = engine.parse_city_record_feed(feed_data)
    else:
        opportunities = engine.parse_sam_gov_feed(feed_data)

    report = engine.triage_opportunities(
        opportunities=opportunities,
        vendor=vendor,
        min_fit_score=args.min_score,
    )

    if args.json:
        print(report.model_dump_json(indent=2))
        return

    print("=" * 76)
    print(f"PORTAL OPPORTUNITIES SCAN & TRIAGE REPORT: {report.source.value}")
    print("=" * 76)
    print(f"Scan Execution Time:       {report.scan_timestamp}")
    print(f"Total Solicitations Scanned: {report.total_scanned}")
    print(f"Qualified Opportunities:   {report.qualified_count} (GO / CONDITIONAL_GO)")
    print(f"Disqualified / High Risk:  {report.disqualified_count} (Fatal Disqualifiers)")
    print()

    print(f"RANKED OPPORTUNITY PIPELINE ({len(report.ranked_opportunities)} Matching Threshold):")
    for i, res in enumerate(report.ranked_opportunities, 1):
        opp = res.opportunity
        rec_badge = f"[{res.recommendation} - {res.fit_score:.1f}/100]"
        print(f"#{i} {rec_badge} {opp.title}")
        print(f"   PIN/Notice:  {opp.solicitation_number} | Agency: {opp.agency}")
        print(f"   Set-Aside:   {opp.set_aside.value}")
        if opp.response_deadline:
            print(f"   Deadline:    {opp.response_deadline}")
        if opp.ui_link:
            print(f"   Portal URL:  {opp.ui_link}")

        if res.fatal_disqualifiers:
            print("   🚨 FATAL DISQUALIFIERS:")
            for disq in res.fatal_disqualifiers:
                print(f"      • {disq}")

        if res.remediable_actions and res.recommendation != "GO":
            print("   🔧 REMEDIATION ACTIONS REQUIRED:")
            for act in res.remediable_actions[:2]:
                print(f"      • {act}")
        print()

    print("=" * 76)


def cmd_draft(args: argparse.Namespace) -> None:
    """Synthesizes a complete grounded government proposal response document."""
    parser = RfpParser()
    rfp = parser.parse_file(args.rfp_file)
    vendor = load_vendor(args.vendor_file)

    staffing_items = None
    if args.staffing_file:
        plan_path = Path(args.staffing_file)
        if plan_path.exists():
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            staffing_items = [StaffingRequirement(**item) for item in plan_data.get("staffing", [])]

    synthesizer = ProposalSynthesizerEngine()
    draft = synthesizer.synthesize_proposal(
        rfp=rfp,
        vendor=vendor,
        staffing_plan=staffing_items,
        total_bid_amount=args.bid_amount,
        materials_and_odc=args.materials_odc,
        waiver_reason=args.waiver_reason,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(draft.full_markdown)
        print(f"Proposal draft successfully written to '{args.output}'.")

    if args.json:
        print(draft.model_dump_json(indent=2))
        return

    if not args.output:
        print("=" * 76)
        print(f"SYNTHESIZED PROPOSAL RESPONSE: {draft.solicitation_number} — {draft.solicitation_title}")
        print("=" * 76)
        print(f"Prime Contractor:    {draft.vendor_name}")
        print(f"Issuing Agency:      {draft.issuing_agency}")
        print(f"Groundedness Score:  {draft.groundedness_score * 100:.1f}% (RAG Triad Verification)")
        print(f"Total Word Count:    {draft.total_words:,} words across {len(draft.sections)} sections")
        print(f"Empirical Citations: {draft.total_citations} verified past performance & statutory citations")
        status_badge = "[SUBMISSION READY]" if draft.is_submission_ready else "[ACTION REQUIRED - LOW GROUNDEDNESS]"
        print(f"Readiness Status:    {status_badge}")
        print()
        for sec in draft.sections:
            print(f"[{sec.section_id}] {sec.title} ({sec.word_count} words)")
            if sec.citations:
                print(f"   Citations: {', '.join(sec.citations[:4])}")
        print("=" * 76)


def cmd_serve(args: argparse.Namespace) -> None:
    """Launches the GovBid AI Enterprise REST API & Interactive Console server."""
    try:
        import uvicorn
    except ImportError:
        print("Error: 'uvicorn' is required to run the server. Install via 'pip install uvicorn'.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting GovBid AI REST API & Console on http://{args.host}:{args.port}")
    print(f"Interactive Web Console: http://{args.host}:{args.port}/console")
    print(f"OpenAPI Documentation:   http://{args.host}:{args.port}/docs")
    uvicorn.run("govbid.api.app:app", host=args.host, port=args.port, reload=args.reload)


def main() -> None:
    """CLI entrypoint dispatcher."""
    parser = argparse.ArgumentParser(
        prog="govbid",
        description="GovBid AI: Government Contract & RFP Compliance Intelligence Platform",
    )
    parser.add_argument("--json", action="store_true", help="Output results as structured JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: parse
    p_parse = subparsers.add_parser("parse", help="Parse RFP (.pdf, .txt) and extract compliance clauses")
    p_parse.add_argument("rfp_file", help="Path to RFP solicitation file (.pdf, .txt, .md)")
    p_parse.set_defaults(func=cmd_parse)

    # Subcommand: check
    p_check = subparsers.add_parser("check", help="Run Disqualification Guard check")
    p_check.add_argument("rfp_file", help="Path to RFP file (.pdf, .txt)")
    p_check.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_check.set_defaults(func=cmd_check)

    # Subcommand: evaluate
    p_eval = subparsers.add_parser("evaluate", help="Execute full Gap Analysis & Go/No-Go recommendation")
    p_eval.add_argument("rfp_file", help="Path to RFP file (.pdf, .txt)")
    p_eval.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_eval.set_defaults(func=cmd_evaluate)

    # Subcommand: outline
    p_outline = subparsers.add_parser("outline", help="Synthesize grounded proposal outline with citations")
    p_outline.add_argument("rfp_file", help="Path to RFP file (.pdf, .txt)")
    p_outline.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_outline.set_defaults(func=cmd_outline)

    # Subcommand: diff
    p_diff = subparsers.add_parser("diff", help="Analyze Addendum / Amendment differential against baseline RFP")
    p_diff.add_argument("base_rfp", help="Path to baseline RFP file (.pdf, .txt)")
    p_diff.add_argument("addendum_file", help="Path to addendum/amendment file (.pdf, .txt)")
    p_diff.set_defaults(func=cmd_diff)

    # Subcommand: schedule-b
    p_sched = subparsers.add_parser("schedule-b", help="Calculate and validate Schedule B M/WBE utilization plan")
    p_sched.add_argument("rfp_file", help="Path to RFP solicitation file (.pdf, .txt)")
    p_sched.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_sched.add_argument("--bid-amount", type=float, default=None, help="Total proposal bid amount in USD")
    p_sched.add_argument("--recommend", action="store_true", help="Auto-calculate allocations across candidate subcontractors")
    p_sched.add_argument("--waiver-reason", type=str, default=None, help="Statutory justification for pre-bid waiver request")
    p_sched.add_argument("--waiver-memo", action="store_true", help="Generate formal Schedule B Part III Waiver Memorandum")
    p_sched.set_defaults(func=cmd_schedule_b)

    # Subcommand: price
    p_price = subparsers.add_parser("price", help="Calculate loaded labor rates and audit prevailing wage compliance")
    p_price.add_argument("rfp_file", help="Path to RFP solicitation file (.pdf, .txt)")
    p_price.add_argument("staffing_file", help="Path to staffing plan JSON")
    p_price.add_argument("--vendor-name", type=str, default=None, help="Contractor company name for certified payroll declaration")
    p_price.add_argument("--certified-payroll", action="store_true", help="Generate formal Certified Payroll Compliance Declaration")
    p_price.set_defaults(func=cmd_price)

    # Subcommand: scan
    p_scan = subparsers.add_parser("scan", help="Scan and triage live portal opportunities feed")
    p_scan.add_argument("feed_file", help="Path to portal opportunities JSON feed file")
    p_scan.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_scan.add_argument("--source", choices=["auto", "sam_gov", "city_record"], default="auto", help="Portal source format")
    p_scan.add_argument("--min-score", type=float, default=0.0, help="Minimum fit score threshold to display")
    p_scan.set_defaults(func=cmd_scan)

    # Subcommand: draft
    p_draft = subparsers.add_parser("draft", help="Synthesize complete grounded proposal response")
    p_draft.add_argument("rfp_file", help="Path to RFP solicitation file (.pdf, .txt)")
    p_draft.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_draft.add_argument("--staffing-file", default=None, help="Path to staffing plan JSON")
    p_draft.add_argument("--bid-amount", type=float, default=None, help="Total proposal bid amount in USD")
    p_draft.add_argument("--materials-odc", type=float, default=0.0, help="Materials and Other Direct Costs in USD")
    p_draft.add_argument("--waiver-reason", type=str, default=None, help="Statutory justification for pre-bid waiver request")
    p_draft.add_argument("--output", "-o", type=str, default=None, help="Output markdown file path to save full proposal")
    p_draft.set_defaults(func=cmd_draft)

    # Subcommand: serve
    p_serve = subparsers.add_parser("serve", help="Launch Enterprise REST API & Interactive Console server")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
    p_serve.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload on code change")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
