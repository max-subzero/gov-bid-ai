"""Command-line interface for GovBid AI."""

import argparse
import json
import sys
from pathlib import Path
from govbid.engines.disqualification_guard import DisqualificationGuard
from govbid.engines.gap_analyzer import GapAnalyzer
from govbid.engines.proposal_grounder import ProposalGrounder
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


def load_rfp(rfp_path: str) -> str:
    """Reads raw RFP text or document content."""
    path = Path(rfp_path)
    if not path.exists():
        print(f"Error: RFP file not found at '{rfp_path}'", file=sys.stderr)
        sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def cmd_parse(args: argparse.Namespace) -> None:
    """Executes RFP parsing and clause detection."""
    content = load_rfp(args.rfp_file)
    parser = RfpParser()
    rfp = parser.parse_text(content)

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
    content = load_rfp(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    parser = RfpParser()
    rfp = parser.parse_text(content)
    
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
    content = load_rfp(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    parser = RfpParser()
    rfp = parser.parse_text(content)
    
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
    content = load_rfp(args.rfp_file)
    vendor = load_vendor(args.vendor_file)
    
    parser = RfpParser()
    rfp = parser.parse_text(content)
    
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


def main() -> None:
    """CLI entrypoint dispatcher."""
    parser = argparse.ArgumentParser(
        prog="govbid",
        description="GovBid AI: Government Contract & RFP Compliance Intelligence Platform",
    )
    parser.add_argument("--json", action="store_true", help="Output results as structured JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: parse
    p_parse = subparsers.add_parser("parse", help="Parse RFP and extract compliance clauses")
    p_parse.add_argument("rfp_file", help="Path to raw RFP text/solicitation file")
    p_parse.set_defaults(func=cmd_parse)

    # Subcommand: check
    p_check = subparsers.add_parser("check", help="Run Disqualification Guard check")
    p_check.add_argument("rfp_file", help="Path to RFP file")
    p_check.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_check.set_defaults(func=cmd_check)

    # Subcommand: evaluate
    p_eval = subparsers.add_parser("evaluate", help="Execute full Gap Analysis & Go/No-Go recommendation")
    p_eval.add_argument("rfp_file", help="Path to RFP file")
    p_eval.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_eval.set_defaults(func=cmd_evaluate)

    # Subcommand: outline
    p_outline = subparsers.add_parser("outline", help="Synthesize grounded proposal outline with citations")
    p_outline.add_argument("rfp_file", help="Path to RFP file")
    p_outline.add_argument("vendor_file", help="Path to vendor profile JSON")
    p_outline.set_defaults(func=cmd_outline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
