# Specification

> **Guidelines**: Read [guidelines.md](./guidelines.md) before executing ANY tasks below.

Check off items as completed.

## Solution Setup

- [x] Create asset directories: `mkdir -p assets/carbon-compliance-agent/ assets/carbon-compliance-cap/`
- [x] Invoke `setup-solution` skill to create `solution.yaml` and `asset.yaml` files for every asset
- [x] Validate all `asset.yaml` and `solution.yaml` files exist and are well-formed

## Asset Implementation

- [x] Execute specification/carbon-compliance-agent/specification.md (all items) — 43/43 agent tests pass, 91% coverage
- [x] Execute specification/carbon-compliance-cap/specification.md (all items) — 11/11 CAP tests pass, 77.96% coverage
- [x] Cross-implementation compatibility check — all interfaces, data shapes, and entity names aligned:
  - Agent tools write to CAP via `/agent/*` endpoints using the same entity field names as `db/schema.cds`
  - EmissionsRecords: agent `emissions_tools.py` produces `scope1_tCO2e`, `scope2_tCO2e`, `scope3_tCO2e`, `carbon_intensity_tCO2e_per_BOE` — matches CAP schema ✓
  - HotspotAlerts: agent `hotspot_tools.py` produces `alert_type_code`, `severity_code`, `metric_name`, `current_value`, `threshold_value` — matches CAP schema ✓
  - RegulatoryReports: agent `disclosure_tools.py` produces `jurisdiction_code`, `format_code`, `status_code`, `lineage_record_count` — matches CAP schema ✓
  - DecarbonizationRecommendations: agent `recommendations_tools.py` produces `rank`, `intervention_type`, `projected_reduction_tCO2e`, `estimated_capex_USD` — matches CAP schema ✓
  - DataLineageRecords: agent `disclosure_tools.py` includes `source_type`, `source_doc_id`, `emission_factor_source`, `calculation_step`, `disclosure_section_ref` — matches CAP schema ✓
  - React UI sources data from `/compliance/CarbonKPIs`, `/compliance/EmissionsRecords`, `/compliance/HotspotAlerts`, `/compliance/RegulatoryReports`, `/compliance/DataLineageRecords`, `/compliance/DecarbonizationRecommendations` — all verified ✓
