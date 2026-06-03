# Product Requirements Document

**Title:** Carbon Compliance Intelligence Engine (CCIE)
**Date:** 2026-06-03
**Owner:** ESG & Sustainability Office / SAP PRA Operations
**Solution Category:** AI Agent, BTP Extension

---

## Product Purpose & Value Proposition

**Elevator Pitch:**
Oil & gas operators produce volumes every hour but have no automated way to convert that data into defensible carbon disclosures. CCIE bridges SAP PRA and SAP Sustainability Footprint Management via an AI agent that autonomously computes Scope 1/2/3 emissions, detects flaring and methane hotspots in real time, and generates audit-grade XBRL/PDF/JSON regulatory filings for CSRD, IFRS S2, and California SB253.

**Business Need:**
Manual ESG reporting is slow (weeks), costly (FTE-intensive), and audit-exposed. Regulatory penalties under CSRD reach 10% of global turnover; SB253 fines reach USD 500K/year. Real-time carbon intelligence is now a license-to-operate requirement, not a reporting exercise.

**Expected Value:**
- 60–80% reduction in ESG reporting cost through workflow automation
- 20–40% methane emissions reduction via real-time hotspot visibility
- Zero manual compilation for CSRD, IFRS S2, SB253 filings
- Full data lineage from production barrel to regulatory disclosure

**Product Objectives:**
1. Automate Scope 1/2/3 emissions computation from SAP PRA production volumes with full traceability.
2. Generate compliant regulatory disclosures (XBRL, PDF, JSON) for CSRD, IFRS S2, and SB253.
3. Deliver real-time carbon intensity monitoring and hotspot alerts (flaring, methane, inefficient wells).
4. Provide ranked decarbonization recommendations by cost-vs-emissions impact.

---

## Requirements

### Must-Have Requirements

**R1: SAP PRA Data Ingestion**
- **User Story:** As a Carbon Data Manager, I need the agent to ingest well, reservoir, field, and plant volume data from SAP PRA OData APIs so that production volumes are the authoritative, real-time basis for all emissions calculations.
- **Acceptance Criteria:** Given a scheduled trigger or change event, when PRA APIs are polled, then well completions, reservoir volumes, and plant volumes are retrieved, normalized, and stored with timestamp and audit metadata.
- **Priority Rank:** 1

**R2: Scope 1/2/3 Emissions Calculation**
- **User Story:** As an ESG Reporting Officer, I need automated computation of Scope 1 (direct combustion, flaring), Scope 2 (purchased energy), and Scope 3 (downstream product use) emissions per asset so that calculations are scientifically defensible and traceable.
- **Acceptance Criteria:** Given normalized PRA production volumes, when emissions are calculated using region-specific emission factors (GHG Protocol), then Scope 1/2/3 results are produced per well, field, and aggregate asset level with factor provenance logged.
- **Priority Rank:** 2

**R3: Real-Time Carbon Hotspot Detection**
- **User Story:** As a Field Operations Manager, I need the agent to flag flaring events, methane leak anomalies, and inefficient wells in real time so that my team can take immediate corrective action.
- **Acceptance Criteria:** Given live well completion variable data, when anomaly thresholds are exceeded (configurable), then an alert is generated with asset ID, emission type, severity score, and recommended corrective action within 15 minutes of detection.
- **Priority Rank:** 3

**R4: Multi-Jurisdiction Regulatory Disclosure Generation**
- **User Story:** As a Sustainability Compliance Officer, I need audit-grade CSRD, IFRS S2, and SB253 reports generated automatically in XBRL, PDF, and JSON formats so that I can file without manual compilation.
- **Acceptance Criteria:** Given validated Scope 1/2/3 data, when a report is requested for a given period and jurisdiction, then a compliant output file is produced with full data lineage, calculation methodology, and reconciliation to financial records.
- **Priority Rank:** 4

**R5: Decarbonization Recommendation Engine**
- **User Story:** As an Asset Manager, I need prioritized recommendations for emissions reduction so that I can allocate operational budgets to the highest-impact interventions first.
- **Acceptance Criteria:** Given emissions data and operational cost inputs, when the agent evaluates intervention options, then a ranked list is produced showing projected emissions reduction (tCO₂e) and estimated cost savings per recommended action.
- **Priority Rank:** 5

**R6: Compliance Operations Dashboard (BTP Extension)**
- **User Story:** As an ESG Reporting Officer, I need a BTP-hosted React dashboard showing carbon KPIs, asset-level intensity, compliance status, and report download so that I have a single pane of glass for compliance operations.
- **Acceptance Criteria:** Dashboard displays: Scope 1/2/3 totals by asset, carbon intensity per barrel, hotspot alerts, report status per jurisdiction, and data lineage drill-through. All data sourced from agent outputs.
- **Priority Rank:** 6

---

## Solution Architecture

**Architecture Overview:**
A pro-code Python AI agent deployed on SAP BTP AI Core orchestrates data ingestion from SAP PRA (OData), emissions calculations via SAP Sustainability Footprint Management APIs, anomaly detection, and regulatory report generation. A CAP + React BTP Extension provides the compliance dashboard and serves as the integration hub. SAP Sustainability Control Tower handles objective tracking and ESG target management.

**Key Components:**
- **CCIE AI Agent (Python / A2A):** Core orchestrator — ingests PRA data, computes emissions, detects hotspots, generates disclosures, delivers recommendations.
- **SAP PRA OData Adapters:** Connectors for Well, Reservoir, Field, Plant Volume, Well Completion, and Revenue Accounting Document APIs.
- **SAP Sustainability Footprint Management:** Emissions factor management, carbon footprint calculation, and result validation.
- **SAP Sustainability Control Tower:** ESG objective tracking and sustainability performance management.
- **Regulatory Report Renderer:** Generates XBRL, PDF, and JSON outputs with data lineage metadata.
- **BTP Extension (CAP + React):** Compliance operations dashboard, report download, alert management UI.

**Integration Points:**
- SAP PRA → Agent: OData pull (scheduled + event-triggered), bidirectional audit log
- Agent → SAP SFM: Emissions calculation API calls, factor retrieval
- Agent → SAP SCT: Sustainability metric push via Push Metric/Measure Data APIs
- Agent → BTP Extension: REST API for dashboard data, report artefacts

---

## Agent Extensibility & Instrumentation

**Agent Extensibility:**
The CCIE agent is designed with the following extension points:
- **Emission factor plugins:** New regulatory datasets (EPA, IEA, regional) can be registered as pluggable factor providers without modifying core calculation logic.
- **Jurisdiction modules:** New regulatory frameworks (e.g., SEC climate rule, UK TCFD) can be added as standalone compliance modules.
- **Data source connectors:** Additional OT/SCADA data streams (e.g., real-time flare sensors, IoT methane monitors) can be registered as new ingestion adapters.
- **Report templates:** XBRL taxonomy updates and new disclosure templates are managed via configuration, not code changes.

**Business Step Instrumentation:**
All business logic steps emit structured logs following the pattern `[MILESTONE_ID].[achieved|missed]: [description]`.

---

## Automation & Agent Behaviour

**Automation Level:** Autonomous agent with human-in-the-loop for regulatory filing approval.

**Actions performed without human approval:**
- Ingest and normalize SAP PRA production data
- Calculate Scope 1/2/3 emissions per asset
- Detect and score carbon hotspots
- Generate draft regulatory disclosures
- Push metrics to SAP Sustainability Control Tower
- Issue real-time alerts to operations teams

**Actions requiring human review or approval:**
- Final submission of regulatory disclosures (CSRD, IFRS S2, SB253)
- Override of emission factor values
- Acknowledgment and closure of high-severity hotspot alerts

**Model / engine:** SAP Generative AI Hub (GPT-4o class model) for recommendation reasoning and natural language disclosure drafting; rule-based engine for deterministic emissions calculation.

**Knowledge & data sources accessed:**
- SAP PRA: Well, Reservoir, Field, Plant Volume, Revenue Accounting data
- SAP Sustainability Footprint Management: Emission factors, calculation results
- SAP Sustainability Control Tower: Sustainability objectives and KPIs
- Regulatory datasets: GHG Protocol, EU CSRD taxonomy, IFRS S2 standards, California SB253 rules

**Tools/Connectors:**
- `get_pra_well_data` — Read SAP PRA well and completion data (read-only)
- `get_pra_volumes` — Read plant volumes and reservoir production (read-only)
- `get_pra_revenue_document` — Read revenue accounting documents for financial reconciliation (read-only)
- `calculate_emissions` — Submit activity data to SAP SFM for Scope 1/2/3 calculation (write)
- `get_emission_factors` — Retrieve region-specific factors from SAP SFM (read-only)
- `push_sustainability_metrics` — Push computed metrics to SAP SCT (write)
- `generate_regulatory_report` — Render XBRL/PDF/JSON compliance report (write)
- `detect_hotspots` — Evaluate real-time anomaly signals and issue alerts (read + notify)
- `get_decarbonization_recommendations` — Generate prioritized intervention list (read-only)

**Guardrails & Fail-safes:**
- Regulatory disclosures are never submitted without an explicit human approval step.
- If SAP PRA data is unavailable or incomplete, the agent halts calculation for the affected asset, logs a data quality alert, and does not estimate missing volumes.
- Confidence scoring: if an emission factor cannot be matched to a validated source, the calculation is flagged as "estimated — requires review" in the disclosure.
- All agent actions are logged with full input/output payloads for audit trail.

---

## Milestones

### M1: Production Data Ingested
- **Description:** SAP PRA volumes (wells, reservoirs, plant volumes, fields) successfully retrieved and normalized.
- **Achieved when:** All configured PRA OData endpoints return data for the target period with no critical validation errors.
- **Log on achievement:** `M1.achieved: SAP PRA production data ingested successfully — wells={count}, reservoirs={count}, fields={count}, period={period}`
- **Log on miss:** `M1.missed: SAP PRA data ingestion failed or incomplete — asset={asset_id}, error={error_detail}, period={period}`

### M2: Scope 1/2/3 Emissions Computed
- **Description:** Per-asset emissions calculated using validated emission factors and GHG Protocol methodology, validated via SAP SFM.
- **Achieved when:** Scope 1, 2, and 3 values are produced for all active assets in the target period with emission factor provenance recorded.
- **Log on achievement:** `M2.achieved: Emissions calculated — scope1={tCO2e}, scope2={tCO2e}, scope3={tCO2e}, assets={count}, factors_source={source}`
- **Log on miss:** `M2.missed: Emissions calculation incomplete — missing_factors={count}, failed_assets={list}, period={period}`

### M3: Carbon Hotspots Identified
- **Description:** Real-time anomaly detection identifies flaring events, methane leaks, and inefficient wells with severity scoring.
- **Achieved when:** At least one anomaly evaluation cycle completes for the target period with alert routing confirmed.
- **Log on achievement:** `M3.achieved: Hotspot detection complete — alerts_generated={count}, high_severity={count}, assets_flagged={list}`
- **Log on miss:** `M3.missed: Hotspot detection did not complete — reason={reason}, affected_assets={list}`

### M4: Regulatory Disclosures Generated
- **Description:** Compliant CSRD, IFRS S2, and SB253 outputs produced in XBRL, PDF, and JSON with full audit trail.
- **Achieved when:** All three format artefacts are rendered for each configured jurisdiction with data lineage metadata attached.
- **Log on achievement:** `M4.achieved: Regulatory disclosures generated — jurisdictions={list}, formats={XBRL,PDF,JSON}, period={period}, lineage_records={count}`
- **Log on miss:** `M4.missed: Disclosure generation failed — jurisdiction={name}, format={format}, error={error_detail}`

### M5: Optimization Recommendations Delivered
- **Description:** Prioritized decarbonization interventions surfaced to operational and ESG teams ranked by cost-vs-emissions impact.
- **Achieved when:** A ranked recommendation list is produced and pushed to the compliance dashboard and operations team notification channel.
- **Log on achievement:** `M5.achieved: Decarbonization recommendations delivered — recommendations={count}, top_intervention={description}, projected_reduction={tCO2e}`
- **Log on miss:** `M5.missed: Recommendation generation did not complete — reason={reason}`
