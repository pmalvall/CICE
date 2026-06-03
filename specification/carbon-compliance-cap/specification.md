# Specification: carbon-compliance-cap

> **Guidelines**: Read [guidelines.md](../guidelines.md) and [guidelines-cap.md](../guidelines-cap.md) before executing ANY tasks below. Follow all constraints described there throughout execution.

## Basic Setup

- [x] Read `product-requirements-document.md` and `intent.md` for full context
- [x] Invoke the `cap-development` skill from `assets/carbon-compliance-cap/` to set up the CAP project structure
- [x] Install dependencies (`npm install`), validate the project starts (`cds watch`) and responds

## CDS Data Model

- [x] Define `db/schema.cds` with the following entities:
  - `EmissionsRecords`: asset_id, asset_type (assoc), period_start, period_end, scope1/2/3_tCO2e (Decimal), carbon_intensity_tCO2e_per_BOE, total_production_BOE, validation_status (assoc), managed
  - `HotspotAlerts`: alert_type (assoc), asset_id, asset_type (assoc), severity (assoc), metric_name, current/threshold/excess values, recommended_action, impact, status, acknowledged_by/at, resolved_at, managed
  - `RegulatoryReports`: jurisdiction (assoc), format (assoc), period_start/end, status (assoc), file_name, lineage_record_count, taxonomy/methodology refs, approved_by/at, managed
  - `DataLineageRecords`: report (assoc), source_type/doc_id, volume value/unit, emission factor value/source, calculation_step, disclosure_section_ref, managed
  - `DecarbonizationRecommendations`: rank, intervention_type, target_asset_id, description, projected_reduction, estimated_capex, payback_period, cost_saving, implementation_complexity (assoc), regulatory_compliance_impact, status (assoc), managed
  - 9 CodeList entities: AlertTypes, SeverityLevels, AssetTypes, ValidationStatuses, ReportStatuses, Jurisdictions, ReportFormats, ComplexityLevels, RecommendationStatuses
- [x] Run `cds compile db/schema.cds` to validate data model — PASSES (no errors)

## CAP Service Layer

- [x] Define `srv/carbon-compliance-service.cds`:
  - Expose `EmissionsRecords` (read + create + update)
  - Expose `HotspotAlerts` (read + update status + acknowledgeAlert action)
  - Expose `RegulatoryReports` (read + approveReport action + downloadReport function)
  - Expose `DataLineageRecords` (read-only)
  - Expose `DecarbonizationRecommendations` (read + updateRecommendationStatus action)
  - Expose `CarbonKPIs` (custom virtual entity: total scope 1/2/3, portfolio intensity, open/critical alert counts, draft report count, top recommendation)
- [x] Implement custom handler `srv/carbon-compliance-service.js`:
  - `CarbonKPIs` read handler: live aggregation of EmissionsRecords, HotspotAlerts, RegulatoryReports, DecarbonizationRecommendations
  - `approveReport` action: validates status, sets APPROVED + approved_by/approved_at
  - `downloadReport` function: returns report metadata + download reference
  - `acknowledgeAlert` action: sets ACKNOWLEDGED + acknowledged_by/acknowledged_at
  - `updateRecommendationStatus` action: validates status enum, updates status_code
- [x] Seed `db/data/` with realistic initial data:
  - 5 EmissionsRecords (2 plants, 1 field, 1 prior month, 1 plant 2)
  - 3 HotspotAlerts (FLARING/HIGH, METHANE_LEAK/MEDIUM, INEFFICIENT_WELL/MEDIUM)
  - 3 RegulatoryReports (CSRD/DRAFT, IFRS_S2/DRAFT, SB253/PENDING_APPROVAL)
  - 5 DataLineageRecords (full provenance chain for CSRD, IFRS S2, SB253 reports)
  - 5 DecarbonizationRecommendations (ranked by tCO₂e/USD impact)
  - 9 CodeList seed CSV files (AlertTypes, SeverityLevels, AssetTypes, etc.)

## React Frontend (Compliance Operations Dashboard)

- [x] Scaffold React UI in `assets/carbon-compliance-cap/app/react-ui/`
- [x] **Carbon KPI Summary Panel**: Scope 1/2/3 totals + carbon intensity + open alert count + draft report count as metric cards. Source: `CarbonKPIs`.
- [x] **Asset Carbon Intensity Table**: Tabular view with asset_id, type, period, scope 1/2/3, intensity (color-coded), validation status. Source: `EmissionsRecords`.
- [x] **Hotspot Alerts Panel**: Alerts with severity badge (ObjectStatus), alert type, asset, metric values, estimated impact, status tag, Acknowledge button. Source: `HotspotAlerts`.
- [x] **Regulatory Compliance Status Grid**: CSRD/IFRS S2/SB253 reports with status (ObjectStatus), Approve and Lineage drill-through buttons. Source: `RegulatoryReports`.
- [x] **Data Lineage Drill-Through**: Clickable lineage panel per report showing source → volume → emission factor → calculation step → disclosure section. Source: `DataLineageRecords`.
- [x] **Decarbonization Recommendations List**: Ranked list with intervention type, target asset, projected CO₂e reduction, capex, payback, complexity, Start/Complete/Dismiss actions. Source: `DecarbonizationRecommendations`.
- [x] React build passes (`npm run build --workspace=app/react-ui`) — 0 errors

## Agent Integration Endpoints

- [x] Add `srv/agent-integration-service.cds`: CAP service at `/agent` with full write access to:
  - EmissionsRecords, HotspotAlerts, RegulatoryReports, DataLineageRecords, DecarbonizationRecommendations
  - Annotated `@requires: 'system-user'` for agent auth in production

## Testing

- [x] Run `cds compile srv/` — PASSES (no errors)
- [x] CAP tests implemented (`test/CarbonComplianceService.test.js`, `test/AgentIntegrationService.test.js`):
  - `acknowledgeAlert` — assert OPEN→ACKNOWLEDGED transition, timestamp recorded
  - `approveReport` — assert DRAFT→APPROVED transition; assert double-approve rejected with 409
  - `CarbonKPIs` — assert returns 1 row with all required KPI fields
  - `updateRecommendationStatus` — assert status update and invalid status rejection (400)
  - Agent integration — assert INSERT via AgentIntegrationService + read-back
- [x] **11/11 tests pass**, 77.96% line coverage (`npm test`)
- [x] `cds watch` — server launches successfully on port 4004
- [x] All OData endpoints verified:
  - `GET /compliance/CarbonKPIs` → 1 row ✓
  - `GET /compliance/EmissionsRecords` → 5 rows ✓
  - `GET /compliance/HotspotAlerts` → 3 rows ✓
  - `GET /compliance/RegulatoryReports` → 3 rows ✓
  - `GET /compliance/DataLineageRecords` → 5 rows ✓
  - `GET /compliance/DecarbonizationRecommendations` → 5 rows ✓
