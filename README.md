<div align="center">

# GovBid AI
### Government Contract & RFP Compliance Intelligence Platform
**Automated Disqualification Defense, Bid Qualification Scoring & Grounded Proposal Synthesis**

[![CI](https://github.com/max-subzero/gov-bid-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/max-subzero/gov-bid-ai/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#)
[![Standards](https://img.shields.io/badge/standards-NYC%20PPB%20%7C%20FAR%20%7C%20Davis--Bacon-orange.svg)](#)

<p align="center">
  <em>Protecting public sector contractors from administrative disqualification and scoring higher on municipal, state, and federal procurements.</em>
</p>

---

</div>

## 📌 Executive Overview

Responding to government Requests for Proposals (RFPs), Requests for Quotations (RFQs), and Invitations for Bids (IFBs) represents a high-stakes, multi-billion-dollar enterprise endeavor. However, government procurement portals (**NYC PASSPort**, **City Record**, **SAM.gov**) publish solicitations filled with dense regulatory riders, prevailing wage schedules, bonding minimums, and strict mandatory requirements.

**Over 30% of bidder submissions are disqualified on administrative technicalities before evaluators even score their technical approach.** Generic LLMs fail in this domain because they hallucinate compliance capabilities and do not understand statutory municipal procurement rules.

**GovBid AI** is an enterprise compliance intelligence platform engineered to act as an automated **Chief Procurement Officer and Compliance Defense Auditor in a Box**. It ingests solicitation packets, performs deterministic clause extraction, executes pre-flight disqualification audits, scores bidder qualification fit, and synthesizes proposal outlines strictly grounded in verified past performance.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Ingestion["1. Solicitation & Addendum Ingest"]
        A["Raw RFP / Addendum<br/><code>PDF / DOCX / Text</code>"] --> P["PdfExtractor<br/><code>Native pypdf Stream Extraction</code>"]
        P --> B["RfpParser"]
        B --> C["ClauseDetector<br/><code>Deterministic Regex & Rules</code>"]
        C --> D["ParsedRfp Schema<br/><code>Metadata, Rubric, Clauses</code>"]
    end

    subgraph Addendum["2. Addendum Differential Analysis"]
        D --> AD["AddendumDiffEngine<br/><code>Deadline & Clause Deltas</code>"]
        ADD["Addendum File<br/><code>PDF / Text</code>"] --> AD
        AD --> AR["Addendum Analysis<br/><code>Critical Changes & Q&A Pairs</code>"]
    end

    subgraph Defense["3. Disqualification & Gap Analysis"]
        D --> E["DisqualificationGuard"]
        V["VendorProfile JSON<br/><code>Insurance, Tenure, Registrations</code>"] --> E
        E --> F["GapAnalyzer<br/><code>Go / No-Go Fit Score (0-100)</code>"]
        F --> G["Disqualification Report<br/><code>RFC 7807 Remediation Steps</code>"]
    end

    subgraph Proposal["4. Grounded Proposal Synthesis"]
        D --> H["ProposalSynthesizerEngine"]
        V --> H
        H --> I["RAG Groundedness Evaluator<br/><code>Zero Hallucination Filter</code>"]
        I --> J["5-Section Proposal Response<br/><code>Grounded Citations & Markdown</code>"]
    end

    subgraph Mwbe["5. Schedule B M/WBE Subcontractor Allocator"]
        D --> SB["ScheduleBAllocator"]
        V --> SB
        SB --> SBP["Schedule B Plan<br/><code>MBE/WBE Splits & Validation</code>"]
        SB --> WM["Part III Waiver Memo<br/><code>GFE Outreach Justification</code>"]
    end

    subgraph Pricing["6. Commercial Pricing & Wage Compliance"]
        D --> PE["PricingLaborEngine"]
        SP["StaffingPlan JSON<br/><code>Roles, Wages, Hours</code>"] --> PE
        PE --> FS["Fee Schedule<br/><code>Loaded Rates & Margins</code>"]
        PE --> CPD["Certified Payroll Declaration<br/><code>LL 220 / Davis-Bacon Rider</code>"]
    end
```

---

## ⚡ Core Capabilities

### 1. Deterministic Clause Extraction (`ClauseDetector`)
Scans solicitation text for mandatory requirements and regulatory thresholds:
- **M/WBE Participation Goals**: Detects subcontracting quotas under NYC Local Law 1 and Federal FAR 52.219-9.
- **Prevailing Wage & Certified Payroll**: Identifies statutory trade mandates under NY State Labor Law § 220 / Davis-Bacon Act.
- **Bonding & Insurance Ceilings**: Extracts Commercial General Liability, Cyber Liability, and surety bonding limits.
- **Operating Experience Thresholds**: Extracts minimum required consecutive years of prior enterprise experience.
- **Mandatory Portal Enrollments**: Enforces active account checks for **NYC PASSPort**, **SAM.gov** (CAGE / UEI), and **VENDEX**.

### 2. Adversarial Disqualification Defense (`DisqualificationGuard`)
Audits vendor capability profiles against the extracted solicitation clauses before submission:
- Identifies insurance policy deficits and provides exact rider requirements.
- Flags missing M/WBE utilization plans or Schedule B waiver requirements.
- Alerts on missing portal enrollments with actionable remediation steps.

### 3. Quantitative Fit Scoring & Go/No-Go Decision Engine (`GapAnalyzer`)
Computes an objective qualification fit score ($0.0 - 100.0$) and delivers actionable procurement recommendations:
- **`GO`**: Score $\ge 75.0$ with zero critical disqualifiers.
- **`CONDITIONAL_GO`**: Remediable deficiencies detected (e.g. obtain insurance binder, enroll in PASSPort).
- **`NO_GO`**: Unremediable statutory disqualifiers (e.g. insufficient historical operating years).

### 4. RAG Triad Groundedness Synthesizer (`ProposalGrounder`)
Eliminates AI hallucinations by ensuring every proposal section maps directly to verified vendor past performance records:
- Scores narrative groundedness ($0.0 - 1.0$) against empirical past contract values, durations, and agency clients.
- Generates proposal outlines with verifiable citations to specific contract IDs.

### 5. Native Solicitation PDF Ingestion (`PdfExtractor`)
Directly ingests complex municipal and federal procurement packets in native `.pdf` format:
- Stream-based text extraction powered by `pypdf`.
- Automatic stripping of page headers, footers, and null byte artifacts.
- Metadata extraction (title, author, creation timestamp, page counts).

### 6. Addendum & Amendment Differential Analysis (`AddendumDiffEngine`)
Tracks post-issuance solicitation modifications and addenda:
- **Deadline Extensions**: Detects changes to proposal due dates and computes schedule shifts.
- **Contractual Threshold Deltas**: Automatically compares modified insurance limits, bonding tiers, and M/WBE quotas against baseline requirements.
- **Q&A Clarification Extraction**: Parses official agency responses to bidder inquiries into structured Question/Answer pairs.

### 7. Schedule B M/WBE Allocator & Pre-Bid Waiver Engine (`ScheduleBAllocator`)
Automates municipal and state subcontractor compliance under NYC Local Law 1 and PPB rules:
- **Goal Calculation & Sizing**: Computes exact required M/WBE spend against proposed contract values.
- **Demographic Split Tracking**: Automatically calculates MBE vs. WBE utilization percentages.
- **Agency Accreditation Verification**: Validates certifying agencies against recognized authorities (NYC SBS, NYS ESD, PANYNJ, SBA).
- **Intelligent Allocation Sizing (`--recommend`)**: Distributes mandatory targets evenly across qualified candidate partners.
- **Statutory Waiver Memo Generator**: Scaffolds formal Schedule B Part III Pre-Bid Waiver Request memorandums complete with Good Faith Efforts (GFE) outreach logs.

### 8. Commercial Pricing & Prevailing Wage Labor Modeler (`PricingLaborEngine`)
Audits cost volumes, staffing plans, and statutory labor rate compliance:
- **Statutory Wage Floor Validation**: Enforces minimum direct cash wages and supplemental fringe benefit rates under NY Labor Law § 220 / § 230 and Federal Davis-Bacon Act (DBA).
- **Fully Loaded Rate Calculation**: Models direct labor, mandatory payroll taxes (FICA/FUTA/SUI), workers' compensation, general overhead (G&A), and corporate profit margins.
- **Under-Pricing & Non-Responsive Deficit Detection**: Flags when proposed labor rates violate statutory floors, preventing illegal wage submissions and administrative disqualification.
- **Certified Payroll Compliance Declaration**: Auto-generates the mandatory Certified Payroll & Wage Acknowledgment Declaration rider.

### 9. Live Portal Ingestion & Automated Opportunity Triage (`PortalConnectorEngine`)
Ingests real-time procurement feeds from municipal and federal portals, executing automated pre-flight triage before proposal resource allocation:
- **SAM.gov Opportunities API v2**: Ingests federal solicitations, presolicitations, combined synopses, and small business set-asides (8(a), WOSB, SDVOSB, HUBZone).
- **NYC City Record Online (CROL) & OpenData**: Ingests municipal bids, RFPs, and PIN notices from New York City contracting agencies.
- **Automated Opportunity Triage**: Instantly pipes incoming notices into `DisqualificationGuard` and `GapAnalyzer` to calculate fit scores and categorize bids into qualified and disqualified buckets.
- **Ranked Opportunity Pipeline**: Filters opportunities against customizable qualification thresholds, exposing fatal barriers and required remediation actions.

### 10. Enterprise REST API & Interactive Bid Console (`govbid.api`)
Exposes all intelligence engines via a production-grade FastAPI microservice and single-page interactive browser console:
- **REST Endpoints (`/api/v1`)**: RFC 7807 problem details error handling across `/parse`, `/check`, `/evaluate`, `/diff`, `/schedule-b`, `/pricing`, `/triage`, and `/draft`.
- **Interactive Bid Console (`/console`)**: Zero-dependency, single-page dark-mode web application for browser-based RFP evaluation, real-time Schedule B sizing, portal feed triage, and proposal drafting.
- **Automated OpenAPI / Swagger Docs**: Live interactive API contract explorer and JSON schema documentation at `/docs` and `/redoc`.

### 11. Grounded Proposal Prose Synthesizer (`ProposalSynthesizerEngine`)
Automates the generation of publication-ready, 5-section government contract proposal response documents strictly grounded in verified past performance and compliance determinations:
- **Section 1: Executive Summary & Statement of Understanding**: Cites active municipal (NYC PASSPort) and federal (SAM.gov) registry standing, general liability coverage, cyber risk binders, and bonding backing.
- **Section 2: Technical Approach, Architecture & Scope of Work**: Tailors systems architecture, edge ingestion, data streams, and SLA commitments against solicitation evaluation criteria under NIST SP 800-53 and SOC 2 Type II controls.
- **Section 3: Organizational Qualifications & Verified Past Performance**: Embeds empirical case studies with verified contract identifiers, values, performance durations, and agency client references.
- **Section 4: Subcontractor Utilization Plan & Schedule B M/WBE Compliance**: Incorporates pre-vetted certified M/WBE subcontractor allocations, scope descriptions, and demographic splits under NYC Local Law 1 (or Part III Pre-Bid Waiver justifications).
- **Section 5: Commercial Cost Proposal & Certified Payroll Compliance**: Integrates fully loaded staffing fee schedules, billable hour distributions, blended hourly rates, and the statutory Certified Payroll Declaration (NY Labor Law § 220 / Davis-Bacon Act).
- **RAG Triad Groundedness Audit**: Continuously scores factual faithfulness ($0.0 - 1.0$) across synthesized claims, flagging ungrounded assertions and displaying submission readiness badges.

---

## 🚀 Installation & Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/max-subzero/gov-bid-ai.git
cd gov-bid-ai

# Install dependencies
pip install .
```

### CLI Commands

#### 1. Parse RFP (.pdf or .txt) and Extract Compliance Clauses
```bash
govbid parse tests/fixtures/sample_rfp.txt
# or native PDF:
govbid parse solicitation_packet.pdf
```

#### 2. Run Pre-Flight Disqualification Audit
```bash
govbid check tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json
```

#### 3. Evaluate Bidder Fit & Generate Go/No-Go Score
```bash
govbid evaluate tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json
```

#### 4. Analyze Addendum / Amendment Differential
```bash
govbid diff tests/fixtures/sample_rfp.txt tests/fixtures/sample_addendum.txt
```

#### 5. Calculate & Audit Schedule B M/WBE Subcontractor Plan
```bash
govbid schedule-b tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json
# Auto-size candidate subcontractors to meet exact goal:
govbid schedule-b tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json --recommend
# Generate pre-bid waiver request memo:
govbid schedule-b tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json --waiver-reason "Sole-source hardware" --waiver-memo
```

#### 6. Audit Commercial Pricing & Prevailing Wage Labor Rates
```bash
govbid price tests/fixtures/sample_rfp.txt tests/fixtures/sample_staffing_plan.json
# Generate formal Certified Payroll Compliance Declaration:
govbid price tests/fixtures/sample_rfp.txt tests/fixtures/sample_staffing_plan.json \
  --vendor-name "Jemo Platform LLC" \
  --certified-payroll
```

#### 7. Ingest Procurement Feeds & Triage Solicitations (SAM.gov & NYC City Record)
```bash
# Scan and triage SAM.gov opportunities:
govbid scan tests/fixtures/sample_sam_gov_feed.json tests/fixtures/sample_vendor.json

# Scan NYC City Record feed with fit score threshold:
govbid scan tests/fixtures/sample_city_record_feed.json tests/fixtures/sample_vendor.json --min-score 70.0
```

#### 8. Synthesize Complete Grounded Proposal Response Document
```bash
# Synthesize 5-section markdown proposal draft:
govbid draft tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json \
  --staffing-file tests/fixtures/sample_staffing_plan.json \
  --output proposal_draft.md

# Machine-readable JSON output with groundedness score:
govbid --json draft tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json \
  --staffing-file tests/fixtures/sample_staffing_plan.json
```

#### 9. Generate Grounded Proposal Outline with Verified Citations
```bash
govbid outline tests/fixtures/sample_rfp.txt tests/fixtures/sample_vendor.json
```

#### 10. Machine-Readable JSON Output (for CI/CD Gateways)
```bash
govbid --json price tests/fixtures/sample_rfp.txt tests/fixtures/sample_staffing_plan.json
govbid --json scan tests/fixtures/sample_sam_gov_feed.json tests/fixtures/sample_vendor.json
```

#### 11. Launch Enterprise REST API & Interactive Console
```bash
govbid serve --host 127.0.0.1 --port 8000
# Open browser at:
#   Console: http://127.0.0.1:8000/console
#   Swagger: http://127.0.0.1:8000/docs
```

---

## 🧪 Verification & Test Suite

GovBid AI includes a comprehensive test suite running across Python 3.10, 3.11, and 3.12:

```bash
python3 -m unittest discover -s tests -v
```

All 71 test cases validate:
- 5-section grounded proposal synthesis, RAG Triad groundedness auditing, and readiness gates.
- FastAPI REST endpoints, OpenAPI schemas, and RFC 7807 error responses.
- Interactive Bid Console HTML rendering, root redirect, and sample feed routes.
- SAM.gov v2 and NYC City Record feed ingestion, normalization, and automated opportunity triage.
- Loaded labor rate calculations, statutory wage floor audits, and certified payroll declarations.
- Schedule B M/WBE allocation plans, MBE/WBE demographic splits, deficit detection, and waiver memo generation.
- Native PDF text extraction, metadata parsing, and stream error handling.
- Addendum deadline extensions, threshold modification detection, and Q&A parsing.
- Regex clause detection across prevailing wage, insurance, and M/WBE goals.
- Disqualification triggers for insurance, experience, and registration deficits.
- Fit score boundaries and Go/Conditional-Go/No-Go decisions.
- Proposal groundedness verification and citation mapping.
- End-to-end CLI execution with human-readable and JSON outputs.

---

## 📄 License

Licensed under the [Apache License, Version 2.0](LICENSE). Engineered by James Ambenge.
