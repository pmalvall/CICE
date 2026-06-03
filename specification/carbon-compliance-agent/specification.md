# Specification: carbon-compliance-agent

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-agent.md](../guidelines-agent.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` for full context
- [x] Bootstrap agent code in `assets/carbon-compliance-agent/` using skill `sap-agent-bootstrap` (invoke from inside `assets/carbon-compliance-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

## SAP PRA Data Ingestion (R1)

- [ ] Implement `get_pra_field_data` tool: fetch field-level metadata from PRA using `specification/carbon-compliance-agent/api-specs/OP_PRAFIELD_0001.edmx` as the API contract. Returns field ID, name, region, operator, and active status.
- [ ] Implement `get_pra_plant_volumes` tool: fetch plant-level production volumes per measurement period using `specification/carbon-compliance-agent/api-specs/OP_SIMPLEPLANTVOLUME_0001.edmx`. Returns volumes by hydrocarbon type (oil, gas, condensate, water) per plant and period.
- [ ] Implement `get_pra_revenue_document` tool: read revenue accounting documents from `specification/carbon-compliance-agent/api-specs/OP_PRAREVENUEACCTDOCUMENT_0001.edmx`. Returns document header, transaction amounts, and volume references for financial reconciliation.
- [ ] Implement `get_pra_well_data` tool: fetch well and well-completion master data from SAP PRA (ORD ID: `sap.s4:apiResource:OP_PRAWELL_0001:v1`). Returns well ID, name, completion type, production status, field assignment, and coordinates.
- [ ] Implement `get_pra_well_completion_variable_data` tool: fetch time-series well completion variable data (ORD ID: `sap.s4:apiResource:OP_PRAWELLCOMPLETIONDATED_0001:v1`). Returns operational parameters such as flow rates, pressures, GOR (gas-oil ratio), and flare volumes per well completion per day.
- [ ] Implement `get_pra_reservoir_data` tool: fetch reservoir master data (ORD ID: `sap.s4:apiResource:OP_PRARESERVOIR_0001:v1`). Returns reservoir ID, name, type, depth, and field association.
- [ ] Normalize all PRA data responses into a unified internal schema: `{ asset_id, asset_type, period_start, period_end, volumes: { oil_bbl, gas_mcf, condensate_bbl, flare_mcf, methane_mcf }, metadata: { region, field_id, well_id, reservoir_id } }`
- [ ] Log data ingestion completeness: total assets retrieved, missing data flags, and period coverage

## Scope 1/2/3 Emissions Calculation Engine (R2)

- [ ] Implement `get_emission_factors` tool: retrieve region-specific and gas-type-specific emission factors from SAP Sustainability Footprint Management. Parameters: region code, gas type (CO2, CH4, N2O), activity type (combustion, flaring, venting, fugitive). Returns factor value (kg CO2e per unit), source standard (GHG Protocol, EPA, IPCC), and effective date.
- [ ] Implement `calculate_scope1_emissions` tool: compute direct Scope 1 emissions per asset for a given period. Inputs: normalized PRA volume data, emission factors. Logic:
  - Combustion: fuel gas consumed × combustion emission factor
  - Flaring: flare gas volume × flaring emission factor (CO2 + CH4 + N2O)
  - Venting: reported methane vent volume × GWP100 factor
  - Fugitive: equipment count × fugitive emission factor per equipment type
  Returns: tCO2e per asset broken down by emission source, with factor provenance.
- [ ] Implement `calculate_scope2_emissions` tool: compute indirect Scope 2 emissions from purchased electricity per asset. Inputs: energy consumption kWh, regional grid emission factor. Returns: tCO2e with grid factor source and regional applicability.
- [ ] Implement `calculate_scope3_emissions` tool: compute downstream Scope 3 (Category 11 - use of sold products) emissions. Inputs: oil volumes sold (bbl), gas volumes sold (MMBtu), product-specific combustion factors. Returns: tCO2e per product type with methodology note.
- [ ] Implement `validate_emissions_results` tool: submit calculated emissions to SAP Sustainability Footprint Management for validation. Parameters: asset_id, period, scope1_tCO2e, scope2_tCO2e, scope3_tCO2e, methodology. Returns: validation status (approved/flagged/rejected), flags with reason codes, and recommended adjustments.
- [ ] Compute carbon intensity metrics: tCO2e per barrel of oil equivalent (BOE) per asset, aggregate field-level intensity, and portfolio-level intensity.
- [ ] Persist validated emissions results with full audit trail: input volumes, applied factors, calculation steps, validation status, and factor source citations.

## Real-Time Carbon Hotspot Detection (R3)

- [ ] Implement `detect_flaring_anomalies` tool: compare reported flare volumes against historical baseline (rolling 30-day average per well) and regulatory flaring limits. Inputs: well_id, period, flare_volume_mcf, baseline_mcf, regulatory_limit_mcf. Returns: anomaly flag (True/False), severity (LOW/MEDIUM/HIGH/CRITICAL), excess_volume, regulatory_breach flag, and recommended action.
- [ ] Implement `detect_methane_leaks` tool: evaluate methane venting and fugitive emission rates against threshold limits per well completion. Inputs: well_completion_id, period, methane_rate_mcfd, equipment_type. Returns: leak flag, severity score, estimated leak rate in tCH4/day, and repair priority ranking.
- [ ] Implement `detect_inefficient_wells` tool: identify wells with carbon intensity significantly above field average. Inputs: well_id, field_avg_intensity_tCO2e_per_BOE, well_intensity_tCO2e_per_BOE. Returns: inefficiency flag, variance from field average (%), root cause hypothesis, and efficiency improvement potential (tCO2e/year).
- [ ] Implement `generate_hotspot_alert` tool: create structured alert objects from anomaly detection results. Alert schema: `{ alert_id, timestamp, asset_type, asset_id, alert_type (FLARING|METHANE_LEAK|INEFFICIENT_WELL), severity, metric_name, current_value, threshold_value, excess_amount, recommended_action, estimated_annual_impact_tCO2e }`.
- [ ] Evaluate hotspot conditions on each ingestion cycle. Route HIGH/CRITICAL alerts to the compliance dashboard; route CRITICAL alerts with a human approval step before closure.

## Multi-Jurisdiction Regulatory Disclosure Generation (R4)

- [ ] Implement `prepare_csrd_disclosure` tool: structure Scope 1/2/3 validated data and carbon intensity metrics into CSRD ESRS E1 disclosure requirements. Inputs: company_id, reporting_period, emissions data, intensity metrics, methodology docs. Output: CSRD-compliant data object with all required ESRS E1 data points and narrative sections.
- [ ] Implement `prepare_ifrs_s2_disclosure` tool: map emissions data to IFRS S2 disclosure requirements (physical and transition risk exposure, Scope 1/2/3 with Scope 3 category breakdowns). Output: IFRS S2-compliant data object with quantitative and qualitative requirements.
- [ ] Implement `prepare_sb253_disclosure` tool: structure California SB253 (Climate Corporate Data Accountability Act) compliant report for companies with >$1B revenue. Map Scope 1/2/3 figures to required SB253 format with attestation metadata.
- [ ] Implement `render_regulatory_report` tool: generate final disclosure files in requested format. Parameters: disclosure_data_object, format (XBRL|PDF|JSON), jurisdiction (CSRD|IFRS_S2|SB253), reporting_period. Output: rendered file bytes with audit metadata: `{ file_name, jurisdiction, format, reporting_period, generated_at, lineage_record_count, methodology_ref }`.
- [ ] Implement data lineage tracker: for every disclosure generated, record the full chain — PRA source document IDs → normalized volumes → emission factors applied → calculation steps → validation status → disclosure section reference. Store as a JSON lineage object attached to the report artefact.
- [ ] Flag all generated disclosures as DRAFT status until a human approval event is received. Never auto-submit.

## Decarbonization Recommendation Engine (R5)

- [ ] Implement `get_decarbonization_recommendations` tool: analyze emissions profile across all assets and generate ranked intervention recommendations. Logic:
  - Identify top 10 emission sources by tCO2e contribution
  - For each source, evaluate applicable interventions: flare capture, methane monitoring upgrades, electrification of compressors, well optimization, renewable energy procurement
  - Score interventions by: (projected_tCO2e_reduction / estimated_capex_USD) — highest ratio = highest priority
  - Return: ranked list of up to 10 recommendations with fields: `{ rank, intervention_type, target_asset, projected_reduction_tCO2e, estimated_capex_USD, payback_period_years, co_benefit (cost_saving_USD/year), implementation_complexity (LOW|MEDIUM|HIGH), regulatory_compliance_impact }`
- [ ] Push metrics to SAP Sustainability Control Tower: after each calculation cycle, call the SAP SCT Push Metric Data API to update KPIs including total_scope1_tCO2e, total_scope2_tCO2e, total_scope3_tCO2e, portfolio_carbon_intensity_tCO2e_per_BOE, active_hotspot_count.

## Agent Orchestration & System Prompt

- [ ] System prompt must instruct the agent to:
  - Always use SAP PRA as the authoritative source — never estimate or extrapolate volumes
  - Apply GHG Protocol methodology for all Scope 1/2/3 calculations
  - Never submit regulatory disclosures without explicit human approval
  - Set page-size limit to maximum 100 on all paginated tool calls
  - Flag any data gaps or missing emission factors as unresolved before proceeding
  - Provide calculation methodology and factor provenance in all responses
- [ ] Implement the main orchestration flow in `_run_agent()` (extracted from `stream()` to enable instrumentation):
  1. Ingest PRA data for target period
  2. Calculate Scope 1/2/3 emissions
  3. Detect hotspots
  4. Validate emissions with SAP SFM
  5. Generate regulatory disclosures (DRAFT)
  6. Generate decarbonization recommendations
  7. Push metrics to SAP SCT

## Business Step Instrumentation (Milestones)

- [ ] Implement business step instrumentation for each milestone from the PRD: structured logging with pattern `[MILESTONE_ID].[achieved|missed]: [description]` and OpenTelemetry custom spans. Extract business logic from `stream()` into `_run_agent()` and instrument that helper — never wrap a `yield` inside `with tracer.start_as_current_span(...)`.
- [ ] M1 — Production Data Ingested: log `M1.achieved: SAP PRA production data ingested successfully — wells={count}, reservoirs={count}, fields={count}, period={period}` on success; `M1.missed: SAP PRA data ingestion failed or incomplete — asset={asset_id}, error={error_detail}, period={period}` on failure.
- [ ] M2 — Scope 1/2/3 Emissions Computed: log `M2.achieved: Emissions calculated — scope1={tCO2e}, scope2={tCO2e}, scope3={tCO2e}, assets={count}, factors_source={source}` on success; `M2.missed: Emissions calculation incomplete — missing_factors={count}, failed_assets={list}, period={period}` on failure.
- [ ] M3 — Carbon Hotspots Identified: log `M3.achieved: Hotspot detection complete — alerts_generated={count}, high_severity={count}, assets_flagged={list}` on success; `M3.missed: Hotspot detection did not complete — reason={reason}, affected_assets={list}` on failure.
- [ ] M4 — Regulatory Disclosures Generated: log `M4.achieved: Regulatory disclosures generated — jurisdictions={list}, formats={XBRL,PDF,JSON}, period={period}, lineage_records={count}` on success; `M4.missed: Disclosure generation failed — jurisdiction={name}, format={format}, error={error_detail}` on failure.
- [ ] M5 — Optimization Recommendations Delivered: log `M5.achieved: Decarbonization recommendations delivered — recommendations={count}, top_intervention={description}, projected_reduction={tCO2e}` on success; `M5.missed: Recommendation generation did not complete — reason={reason}` on failure.
- [ ] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

## MCP Integration

- [ ] Verify `api-discovery-results.md` exists at workspace root with ORD IDs for all required PRA APIs
- [ ] Invoke `mcp-translation-file` skill for each EDMX spec in `specification/carbon-compliance-agent/api-specs/` — if the skill is unavailable, skip MCP server asset creation and log `[MCP-SKILL] mcp-translation-file unavailable — skipping`.
  - `OP_PRAFIELD_0001.edmx` → MCP server for PRA Field data (ORD ID: `sap.s4:apiResource:OP_PRAFIELD_0001:v1`)
  - `OP_SIMPLEPLANTVOLUME_0001.edmx` → MCP server for PRA Plant Volume data (ORD ID: `sap.s4:apiResource:OP_SIMPLEPLANTVOLUME_0001:v1`)
  - `OP_PRAREVENUEACCTDOCUMENT_0001.edmx` → MCP server for PRA Revenue Accounting Document (ORD ID: `sap.s4:apiResource:OP_PRAREVENUEACCTDOCUMENT_0001:v1`)
- [ ] Then invoke `setup-solution` to create/register MCP server assets for each translation file generated
- [ ] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from `mcp_tools.py` — NEVER create direct HTTP clients
- [ ] Add all MCP server dependencies to `assets/carbon-compliance-agent/asset.yaml` under `requires`
- [ ] Generate `mcp-mock.json` using `mcp-mock-config` skill after MCP translation and setup-solution complete

## Testing

- [ ] `conftest.py` only sets `IBD_TESTING=true` — agent runs with mock MCP tool results during tests
- [ ] Write unit tests in `assets/carbon-compliance-agent/tests/` — one per tool:
  - `test_get_pra_field_data.py` — mock empty/populated PRA field response
  - `test_get_pra_plant_volumes.py` — mock volume data, verify normalization
  - `test_get_pra_revenue_document.py` — mock revenue document, verify financial reconciliation fields
  - `test_calculate_scope1_emissions.py` — assert combustion + flaring + venting + fugitive sum to expected tCO2e
  - `test_calculate_scope2_emissions.py` — assert grid factor multiplication correct
  - `test_calculate_scope3_emissions.py` — assert downstream product combustion calculation
  - `test_detect_flaring_anomalies.py` — assert anomaly flag when flare > baseline + 20%, no flag when within limits
  - `test_detect_methane_leaks.py` — assert severity levels map to correct threshold bands
  - `test_detect_inefficient_wells.py` — assert wells >25% above field avg flagged as HIGH
  - `test_prepare_csrd_disclosure.py` — assert all required ESRS E1 data points present
  - `test_render_regulatory_report.py` — assert output schema contains file_name, jurisdiction, format, lineage_record_count
  - `test_get_decarbonization_recommendations.py` — assert recommendations ranked by tCO2e_reduction/capex ratio
- [ ] Write one integration test: `test_integration_full_cycle.py` — end-to-end flow with mocked PRA data, verify M1→M5 milestones fire in sequence
- [ ] Run `pytest` from `assets/carbon-compliance-agent/` (no args) — if coverage < 70%, add tests until threshold met
- [ ] Verify `assets/carbon-compliance-agent/app/agent.py` has exactly 3 decorated functions — run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/carbon-compliance-agent/app/agent.py` and confirm it returns 3
- [ ] Run `pytest` again from `assets/carbon-compliance-agent/` to generate final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/carbon-compliance-agent/`
