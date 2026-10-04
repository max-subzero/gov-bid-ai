"""Embedded Single-Page Interactive Bid Console HTML & JavaScript."""

CONSOLE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GovBid AI — Interactive Compliance & Procurement Console</title>
  <style>
    :root {
      --bg-primary: #090d16;
      --bg-secondary: #111827;
      --bg-card: #1f2937;
      --border: #374151;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --emerald: #10b981;
      --emerald-dark: #065f46;
      --amber: #f59e0b;
      --rose: #ef4444;
      --cyan: #06b6d4;
      --blue: #3b82f6;
      --purple: #8b5cf6;
      --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-primary);
      color: var(--text-main);
      font-family: var(--font-sans);
      line-height: 1.5;
      padding: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #0f172a;
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }
    .brand-logo {
      background: linear-gradient(135deg, var(--emerald), var(--cyan));
      width: 32px;
      height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      color: #000;
      font-size: 1.1rem;
    }
    .brand-title {
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand-tag {
      font-size: 0.75rem;
      background: rgba(16, 185, 129, 0.15);
      color: var(--emerald);
      padding: 0.15rem 0.5rem;
      border-radius: 9999px;
      font-weight: 600;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .nav-tabs {
      display: flex;
      background: var(--bg-secondary);
      border-bottom: 1px solid var(--border);
      padding: 0 2rem;
      gap: 0.5rem;
      overflow-x: auto;
    }
    .tab-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.85rem 1.25rem;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      transition: all 0.2s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text-main);
    }
    .tab-btn.active {
      color: var(--emerald);
      border-bottom-color: var(--emerald);
      background: rgba(16, 185, 129, 0.05);
    }
    main {
      flex: 1;
      padding: 2rem;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
    }
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
      animation: fadeIn 0.2s ease-in-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(4px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
    @media (max-width: 960px) {
      .grid-2 { grid-template-columns: 1fr; }
    }
    .card {
      background: var(--bg-secondary);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 0.75rem;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
    }
    .btn-group {
      display: flex;
      gap: 0.5rem;
    }
    button.btn {
      background: var(--bg-card);
      color: var(--text-main);
      border: 1px solid var(--border);
      padding: 0.5rem 1rem;
      border-radius: 6px;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
    }
    button.btn:hover {
      background: #374151;
      border-color: #4b5563;
    }
    button.btn-primary {
      background: var(--emerald);
      color: #000;
      border: none;
    }
    button.btn-primary:hover {
      background: #059669;
    }
    textarea, input, select {
      background: #0b1120;
      color: var(--text-main);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 0.75rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      width: 100%;
    }
    textarea:focus, input:focus, select:focus {
      outline: none;
      border-color: var(--emerald);
      box-shadow: 0 0 0 1px var(--emerald);
    }
    textarea {
      min-height: 280px;
      resize: vertical;
    }
    .output-box {
      background: #060911;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      overflow-x: auto;
      max-height: 480px;
      white-space: pre-wrap;
      color: #e5e7eb;
    }
    .badge {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.2rem 0.6rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-go { background: rgba(16, 185, 129, 0.2); color: var(--emerald); border: 1px solid var(--emerald); }
    .badge-conditional { background: rgba(245, 158, 11, 0.2); color: var(--amber); border: 1px solid var(--amber); }
    .badge-nogo { background: rgba(239, 68, 68, 0.2); color: var(--rose); border: 1px solid var(--rose); }
    footer {
      border-top: 1px solid var(--border);
      padding: 1.25rem 2rem;
      text-align: center;
      font-size: 0.8rem;
      color: var(--text-muted);
      background: #0b0f19;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-logo">G</div>
      <div class="brand-title">GovBid AI</div>
      <div class="brand-tag">v1.0.0 Enterprise</div>
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      Engineered by <strong>James Ambenge</strong> | Soko Ads Public Sector Group
    </div>
  </header>

  <nav class="nav-tabs">
    <button class="tab-btn active" onclick="switchTab('parse')">1. RFP Parser</button>
    <button class="tab-btn" onclick="switchTab('audit')">2. Bid Audit & Fit</button>
    <button class="tab-btn" onclick="switchTab('schedule-b')">3. Schedule B M/WBE</button>
    <button class="tab-btn" onclick="switchTab('pricing')">4. Pricing & Prevailing Wage</button>
    <button class="tab-btn" onclick="switchTab('triage')">5. Portal Live Triage</button>
    <button class="tab-btn" onclick="switchTab('draft')">6. Proposal Synthesizer</button>
  </nav>

  <main>
    <!-- TAB 1: RFP PARSER -->
    <section id="tab-parse" class="tab-content active">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Solicitation Document Input</span>
            <button class="btn" onclick="loadSampleRfp()">Load Sample DCAS RFP</button>
          </div>
          <textarea id="rfp-input" placeholder="Paste solicitation text or RFP excerpt here..."></textarea>
          <div style="display:flex; justify-content:flex-end;">
            <button class="btn btn-primary" onclick="runParse()">Run Clause Detector &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Extracted Compliance Clauses & Metadata</span>
            <span id="parse-status" class="badge">Ready</span>
          </div>
          <pre id="parse-output" class="output-box">// Parsed RFP structure and detected regulatory clauses will render here.</pre>
        </div>
      </div>
    </section>

    <!-- TAB 2: AUDIT & FIT -->
    <section id="tab-audit" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Vendor Capability Profile (JSON)</span>
            <button class="btn" onclick="loadSampleVendor()">Load Sample Vendor</button>
          </div>
          <textarea id="vendor-input" placeholder="Paste vendor profile JSON here..."></textarea>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <button class="btn" onclick="runCheck()">Run Pre-Flight Check</button>
            <button class="btn btn-primary" onclick="runEvaluate()">Evaluate Fit (Go / No-Go) &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Disqualification Defense & Gap Analysis</span>
            <span id="audit-badge" class="badge">Ready</span>
          </div>
          <pre id="audit-output" class="output-box">// Disqualification triggers, fit score, and remediation steps will render here.</pre>
        </div>
      </div>
    </section>

    <!-- TAB 3: SCHEDULE B M/WBE -->
    <section id="tab-schedule-b" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Schedule B Subcontracting Parameters</span>
            <button class="btn" onclick="loadSampleScheduleB()">Load Defaults</button>
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem;">
            <label style="font-size:0.85rem; color:var(--text-muted);">Solicitation Number:</label>
            <input type="text" id="sched-solicitation" value="85626P0001" />
            <label style="font-size:0.85rem; color:var(--text-muted);">Total Proposed Bid Amount (USD):</label>
            <input type="number" id="sched-bid-amount" value="4500000" />
            <label style="font-size:0.85rem; color:var(--text-muted);">Mandatory M/WBE Goal Percentage (%):</label>
            <input type="number" id="sched-goal-pct" value="30.0" />
            <label style="font-size:0.85rem; color:var(--text-muted); display:flex; align-items:center; gap:0.5rem; margin-top:0.5rem;">
              <input type="checkbox" id="sched-recommend" checked style="width:auto;" />
              Auto-size allocations evenly across candidate subcontractors (--recommend)
            </label>
          </div>
          <div style="display:flex; justify-content:flex-end; margin-top:1rem;">
            <button class="btn btn-primary" onclick="runScheduleB()">Calculate Schedule B Plan &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Schedule B Compliance Audit & Sizing</span>
            <span id="sched-badge" class="badge">Ready</span>
          </div>
          <pre id="sched-output" class="output-box">// Subcontractor spend quotas, MBE/WBE splits, and shortfall analysis will render here.</pre>
        </div>
      </div>
    </section>

    <!-- TAB 4: PRICING & PREVAILING WAGE -->
    <section id="tab-pricing" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Staffing & Commercial Cost Plan</span>
            <button class="btn" onclick="loadSampleStaffing()">Load Staffing Plan</button>
          </div>
          <div style="display:flex; flex-direction:column; gap:0.75rem;">
            <label style="font-size:0.85rem; color:var(--text-muted); display:flex; align-items:center; gap:0.5rem;">
              <input type="checkbox" id="pricing-wage-mandated" checked style="width:auto;" />
              Prevailing Wage Floor Mandated (NY Labor Law § 220 / Davis-Bacon)
            </label>
            <label style="font-size:0.85rem; color:var(--text-muted); display:flex; align-items:center; gap:0.5rem;">
              <input type="checkbox" id="pricing-cert-payroll" checked style="width:auto;" />
              Generate Certified Payroll Compliance Declaration
            </label>
            <label style="font-size:0.85rem; color:var(--text-muted);">Staffing Plan JSON:</label>
            <textarea id="staffing-json" style="min-height: 180px;"></textarea>
          </div>
          <div style="display:flex; justify-content:flex-end;">
            <button class="btn btn-primary" onclick="runPricing()">Audit Wage Floors & Fee Schedule &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Fee Schedule Audit & Certified Payroll</span>
            <span id="pricing-badge" class="badge">Ready</span>
          </div>
          <pre id="pricing-output" class="output-box">// Loaded labor rates, statutory wage deficits, and certified payroll declaration will render here.</pre>
        </div>
      </div>
    </section>

    <!-- TAB 5: PORTAL LIVE TRIAGE -->
    <section id="tab-triage" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Procurement Portal Feed (JSON)</span>
            <div class="btn-group">
              <button class="btn" onclick="loadSampleSamFeed()">SAM.gov</button>
              <button class="btn" onclick="loadSampleCityFeed()">NYC City Record</button>
            </div>
          </div>
          <textarea id="portal-feed-json" placeholder="Paste SAM.gov or City Record JSON feed data here..."></textarea>
          <div style="display:flex; justify-content:flex-end;">
            <button class="btn btn-primary" onclick="runTriage()">Execute Automated Triage &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Ranked Opportunity Pipeline</span>
            <span id="triage-badge" class="badge">Ready</span>
          </div>
          <pre id="triage-output" class="output-box">// Ranked opportunities, qualified vs disqualified counts, and fatal barriers will render here.</pre>
        </div>
      </div>
    </section>

    <!-- TAB 6: PROPOSAL SYNTHESIZER -->
    <section id="tab-draft" class="tab-content">
      <div class="grid-2">
        <div class="card">
          <div class="card-header">
            <span class="card-title">Proposal Drafting Inputs</span>
            <span class="badge badge-go">RAG Triad Active</span>
          </div>
          <p style="font-size:0.85rem; color:var(--text-muted);">
            Synthesizes all 5 formal compliance sections grounded in verified past performance records, Schedule B M/WBE quotas, and prevailing wage fee schedules.
          </p>
          <div style="display:flex; flex-direction:column; gap:0.75rem;">
            <label style="font-size:0.85rem; color:var(--text-muted);">Total Proposal Bid Amount (USD):</label>
            <input type="number" id="draft-bid-amount" value="4500000" />
            <label style="font-size:0.85rem; color:var(--text-muted);">Materials & Direct ODC (USD):</label>
            <input type="number" id="draft-materials-odc" value="350000" />
            <label style="font-size:0.85rem; color:var(--text-muted);">Pre-Bid Waiver Justification (if applicable):</label>
            <input type="text" id="draft-waiver" placeholder="Leave blank if meeting full goal" />
          </div>
          <div style="display:flex; justify-content:flex-end; margin-top:1rem;">
            <button class="btn btn-primary" onclick="runDraft()">Synthesize Grounded Proposal Response &rarr;</button>
          </div>
        </div>
        <div class="card">
          <div class="card-header">
            <span class="card-title">Proposal Document Preview</span>
            <div style="display:flex; gap:0.5rem; align-items:center;">
              <span id="draft-badge" class="badge">Ready</span>
              <button class="btn" onclick="copyDraftMarkdown()">Copy Markdown</button>
            </div>
          </div>
          <div id="draft-meta" style="font-size:0.85rem; color:var(--text-muted); display:flex; gap:1rem; flex-wrap:wrap;">
            <span>Words: <strong id="draft-words" style="color:var(--text-main);">0</strong></span>
            <span>Groundedness: <strong id="draft-groundedness" style="color:var(--text-main);">0%</strong></span>
            <span>Citations: <strong id="draft-citations" style="color:var(--text-main);">0</strong></span>
          </div>
          <pre id="draft-output" class="output-box" style="max-height: 520px;">// Complete synthesized 5-section proposal narrative in Markdown will render here.</pre>
        </div>
      </div>
    </section>
  </main>

  <footer>
    GovBid AI Enterprise Platform &bull; Apache License 2.0 &bull; Authored by <strong>James Ambenge</strong>
  </footer>

  <script>
    // Tab switching
    function switchTab(name) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      const activeBtn = Array.from(document.querySelectorAll('.tab-btn')).find(b => b.getAttribute('onclick').includes(name));
      if (activeBtn) activeBtn.classList.add('active');
      const target = document.getElementById('tab-' + name);
      if (target) target.classList.add('active');
    }

    // Sample data loaders
    const SAMPLE_RFP = `CITY OF NEW YORK
DEPARTMENT OF CITYWIDE ADMINISTRATIVE SERVICES (DCAS)
REQUEST FOR PROPOSALS
PIN: 85626P0001
TITLE: Automated Vehicle Location (AVL) & Fleet Telematics Platform

1. MINIMUM PROPOSER QUALIFICATIONS:
Proposer must possess a minimum of five (5) consecutive years of continuous operating experience providing enterprise cloud telematics software to public sector or municipal government fleets.
Proposers must possess an active, approved vendor account in NYC PASSPort at the time of proposal submission. Failure to maintain an active PASSPort registration shall result in immediate non-responsiveness and rejection.

2. INSURANCE AND BONDING MANDATES:
- Commercial General Liability: $5,000,000 per occurrence.
- Cyber Liability & Data Breach: $5,000,000 per claim.

3. M/WBE SUBCONTRACTING GOAL:
Pursuant to NYC Local Law 1 of 2013 and Section 6-129 of the NYC Administrative Code, this solicitation is subject to a mandatory 30.0% M/WBE Subcontractor Participation Goal. Bidders must submit a completed Schedule B M/WBE Utilization Plan.

4. PREVAILING WAGE AND LABOR LAW COMPLIANCE:
Field installation technicians, wiremen, and electrical hardware specialists performing vehicle retrofits are subject to New York State Labor Law Section 220 prevailing wage and certified payroll mandates.`;

    const SAMPLE_VENDOR = {
      vendor_id: "VEND-SOKO-001",
      legal_name: "Soko Platform LLC",
      operating_years: 6,
      passport_active: true,
      sam_active: true,
      insurance: {
        general_liability: 5000000.0,
        cyber_liability: 5000000.0,
        surety_bonding: 10000000.0
      },
      candidate_subcontractors: [
        {
          subcontractor_name: "Apex Telematics Wiring Corp",
          certification_type: "MBE",
          certifying_agency: "NYC SBS",
          trade_specialty: "Low-voltage electrical and harness retrofitting",
          committed_amount: 800000.0
        },
        {
          subcontractor_name: "CipherShield Security Inc",
          certification_type: "WBE",
          certifying_agency: "NYC SBS",
          trade_specialty: "SOC 2 Type II audit and vulnerability penetration testing",
          committed_amount: 550000.0
        }
      ]
    };

    const SAMPLE_STAFFING = {
      staffing: [
        {
          labor_category: {
            category_id: "TECH-ELEC-01",
            title: "Field Telematics Installation Electrician",
            classification: "PREVAILING_WAGE_TRADE",
            trade_classification: "ELECTRICIAN",
            base_hourly_rate: 65.0,
            fringe_hourly_rate: 38.5,
            statutory_minimum_floor: 103.5
          },
          headcount: 2,
          hours_per_worker: 2000.0
        },
        {
          labor_category: {
            category_id: "ENG-CLOUD-01",
            title: "Principal Cloud Solutions Architect",
            classification: "EXEMPT_PROFESSIONAL",
            base_hourly_rate: 110.0,
            fringe_hourly_rate: 25.0
          },
          headcount: 1,
          hours_per_worker: 2000.0
        }
      ]
    };

    function loadSampleRfp() {
      document.getElementById('rfp-input').value = SAMPLE_RFP;
    }

    function loadSampleVendor() {
      document.getElementById('vendor-input').value = JSON.stringify(SAMPLE_VENDOR, null, 2);
    }

    function loadSampleScheduleB() {
      loadSampleVendor();
      document.getElementById('sched-solicitation').value = "85626P0001";
      document.getElementById('sched-bid-amount').value = "4500000";
      document.getElementById('sched-goal-pct').value = "30.0";
    }

    function loadSampleStaffing() {
      document.getElementById('staffing-json').value = JSON.stringify(SAMPLE_STAFFING, null, 2);
    }

    async function loadSampleSamFeed() {
      const res = await fetch('/api/v1/sample/sam-gov');
      if (res.ok) {
        const data = await res.json();
        document.getElementById('portal-feed-json').value = JSON.stringify(data, null, 2);
      }
    }

    async function loadSampleCityFeed() {
      const res = await fetch('/api/v1/sample/city-record');
      if (res.ok) {
        const data = await res.json();
        document.getElementById('portal-feed-json').value = JSON.stringify(data, null, 2);
      }
    }

    // API calls
    async function runParse() {
      const text = document.getElementById('rfp-input').value;
      if (!text.trim()) { alert("Please provide RFP text."); return; }
      const out = document.getElementById('parse-output');
      out.textContent = "Parsing solicitation clauses...";
      try {
        const res = await fetch('/api/v1/parse', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        document.getElementById('parse-status').textContent = `Parsed (${data.clauses ? data.clauses.length : 0} Clauses)`;
        document.getElementById('parse-status').className = 'badge badge-go';
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runCheck() {
      const text = document.getElementById('rfp-input').value;
      let vendor;
      try {
        vendor = JSON.parse(document.getElementById('vendor-input').value);
      } catch (e) {
        alert("Invalid vendor JSON: " + e.message); return;
      }
      const out = document.getElementById('audit-output');
      out.textContent = "Running pre-flight disqualification check...";
      try {
        const res = await fetch('/api/v1/check', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rfp_text: text || SAMPLE_RFP, vendor: vendor })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        const b = document.getElementById('audit-badge');
        if (data.is_compliant) {
          b.textContent = "COMPLIANT (0 DISQUALIFIERS)";
          b.className = "badge badge-go";
        } else {
          b.textContent = `DEFICIT DETECTED (${data.findings_count})`;
          b.className = "badge badge-nogo";
        }
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runEvaluate() {
      const text = document.getElementById('rfp-input').value;
      let vendor;
      try {
        vendor = JSON.parse(document.getElementById('vendor-input').value);
      } catch (e) {
        alert("Invalid vendor JSON: " + e.message); return;
      }
      const out = document.getElementById('audit-output');
      out.textContent = "Evaluating qualification fit...";
      try {
        const res = await fetch('/api/v1/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ rfp_text: text || SAMPLE_RFP, vendor: vendor })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        const b = document.getElementById('audit-badge');
        b.textContent = `${data.recommendation} (${data.fit_score}/100)`;
        b.className = data.recommendation === "GO" ? "badge badge-go" : (data.recommendation === "CONDITIONAL_GO" ? "badge badge-conditional" : "badge badge-nogo");
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runScheduleB() {
      let vendor;
      try {
        vendor = JSON.parse(document.getElementById('vendor-input').value || JSON.stringify(SAMPLE_VENDOR));
      } catch (e) {
        vendor = SAMPLE_VENDOR;
      }
      const sol = document.getElementById('sched-solicitation').value;
      const bid = parseFloat(document.getElementById('sched-bid-amount').value);
      const goal = parseFloat(document.getElementById('sched-goal-pct').value);
      const rec = document.getElementById('sched-recommend').checked;

      const out = document.getElementById('sched-output');
      out.textContent = "Calculating Schedule B allocations...";
      try {
        const res = await fetch('/api/v1/schedule-b', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            solicitation_number: sol,
            total_bid_amount: bid,
            mandatory_goal_percentage: goal,
            candidates: vendor.candidate_subcontractors,
            allocations: vendor.candidate_subcontractors,
            recommend: rec
          })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        const b = document.getElementById('sched-badge');
        b.textContent = `${data.status} (${data.actual_mwbe_percentage}%)`;
        b.className = data.status === "COMPLIANT" ? "badge badge-go" : "badge badge-nogo";
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runPricing() {
      let plan;
      try {
        plan = JSON.parse(document.getElementById('staffing-json').value);
      } catch (e) {
        alert("Invalid staffing plan JSON: " + e.message); return;
      }
      const wageMandated = document.getElementById('pricing-wage-mandated').checked;
      const certPayroll = document.getElementById('pricing-cert-payroll').checked;
      const out = document.getElementById('pricing-output');
      out.textContent = "Auditing labor rate compliance...";
      try {
        const res = await fetch('/api/v1/pricing', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            solicitation_number: "85626P0001",
            staffing: plan.staffing,
            prevailing_wage_mandated: wageMandated,
            generate_certified_payroll: certPayroll,
            vendor_name: "Soko Platform LLC"
          })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        const b = document.getElementById('pricing-badge');
        if (data.model_result && data.model_result.is_fully_compliant) {
          b.textContent = "COMPLIANT (ZERO DEFICITS)";
          b.className = "badge badge-go";
        } else {
          b.textContent = "WAGE DEFICITS DETECTED";
          b.className = "badge badge-nogo";
        }
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runTriage() {
      let feedData;
      try {
        feedData = JSON.parse(document.getElementById('portal-feed-json').value);
      } catch (e) {
        alert("Invalid portal feed JSON: " + e.message); return;
      }
      let vendor;
      try {
        vendor = JSON.parse(document.getElementById('vendor-input').value || JSON.stringify(SAMPLE_VENDOR));
      } catch (e) {
        vendor = SAMPLE_VENDOR;
      }
      const out = document.getElementById('triage-output');
      out.textContent = "Scanning portal feed and triaging opportunities...";
      try {
        const res = await fetch('/api/v1/triage', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            feed_data: feedData,
            vendor: vendor,
            min_score: 0.0
          })
        });
        const data = await res.json();
        out.textContent = JSON.stringify(data, null, 2);
        const b = document.getElementById('triage-badge');
        b.textContent = `TRIAGED (${data.qualified_count} QUALIFIED / ${data.disqualified_count} NO-GO)`;
        b.className = "badge badge-go";
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    async function runDraft() {
      const text = document.getElementById('rfp-input').value;
      let vendor;
      try {
        vendor = JSON.parse(document.getElementById('vendor-input').value);
      } catch (e) {
        vendor = SAMPLE_VENDOR;
      }
      let staffing = null;
      try {
        const staffRaw = document.getElementById('staffing-json').value;
        if (staffRaw && staffRaw.trim()) {
          const parsed = JSON.parse(staffRaw);
          staffing = parsed.staffing || null;
        }
      } catch (e) {
        staffing = null;
      }
      const bid = parseFloat(document.getElementById('draft-bid-amount').value) || 4500000;
      const odc = parseFloat(document.getElementById('draft-materials-odc').value) || 0;
      const waiver = document.getElementById('draft-waiver').value || null;

      const out = document.getElementById('draft-output');
      out.textContent = "Synthesizing grounded proposal response across 5 compliance sections...";
      try {
        const res = await fetch('/api/v1/draft', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            rfp_text: text || SAMPLE_RFP,
            vendor: vendor,
            staffing: staffing,
            total_bid_amount: bid,
            materials_and_odc: odc,
            waiver_reason: waiver
          })
        });
        const data = await res.json();
        out.textContent = data.full_markdown;
        document.getElementById('draft-words').textContent = data.total_words.toLocaleString();
        document.getElementById('draft-groundedness').textContent = (data.groundedness_score * 100).toFixed(1) + "%";
        document.getElementById('draft-citations').textContent = data.total_citations;
        const b = document.getElementById('draft-badge');
        if (data.is_submission_ready) {
          b.textContent = "SUBMISSION READY";
          b.className = "badge badge-go";
        } else {
          b.textContent = "ACTION REQUIRED";
          b.className = "badge badge-conditional";
        }
      } catch (err) {
        out.textContent = "Error: " + err.message;
      }
    }

    function copyDraftMarkdown() {
      const text = document.getElementById('draft-output').textContent;
      navigator.clipboard.writeText(text);
      alert("Proposal Markdown copied to clipboard!");
    }

    // Initialize defaults on load
    window.onload = function() {
      loadSampleRfp();
      loadSampleVendor();
      loadSampleStaffing();
    };
  </script>
</body>
</html>
"""
