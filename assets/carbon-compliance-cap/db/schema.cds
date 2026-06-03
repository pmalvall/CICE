namespace ccie;

using { cuid, managed } from '@sap/cds/common';

// --- Code Lists ---

entity AlertTypes {
  key code : String(32);
  name     : String(128);
  descr    : String(512);
}

entity SeverityLevels {
  key code : String(32);
  name     : String(128);
  descr    : String(512);
}

entity AssetTypes {
  key code : String(32);
  name     : String(128);
}

entity ValidationStatuses {
  key code : String(32);
  name     : String(128);
}

entity ReportStatuses {
  key code : String(32);
  name     : String(128);
}

entity Jurisdictions {
  key code : String(32);
  name     : String(128);
}

entity ReportFormats {
  key code : String(32);
  name     : String(32);
}

entity ComplexityLevels {
  key code : String(32);
  name     : String(32);
}

entity RecommendationStatuses {
  key code : String(32);
  name     : String(64);
}

// --- Core Entities ---

/**
 * EmissionsRecord — computed Scope 1/2/3 emissions per asset per period.
 */
entity EmissionsRecords : cuid, managed {
  asset_id                      : String(64) not null;
  asset_type                    : Association to AssetTypes;
  period_start                  : Date not null;
  period_end                    : Date not null;
  scope1_tCO2e                  : Decimal(18, 4);
  scope2_tCO2e                  : Decimal(18, 4);
  scope3_tCO2e                  : Decimal(18, 4);
  carbon_intensity_tCO2e_per_BOE: Decimal(18, 6);
  total_production_BOE          : Decimal(18, 2);
  methodology                   : String(256);
  factor_source                 : String(256);
  validation_status             : Association to ValidationStatuses;
  validated_by                  : String(128);
  validated_at                  : Timestamp;
}

/**
 * HotspotAlerts — flaring anomalies, methane leaks, and inefficient wells.
 */
entity HotspotAlerts : cuid, managed {
  alert_type                    : Association to AlertTypes;
  asset_id                      : String(64) not null;
  asset_type                    : Association to AssetTypes;
  severity                      : Association to SeverityLevels;
  metric_name                   : String(128);
  current_value                 : Decimal(18, 4);
  threshold_value               : Decimal(18, 4);
  excess_amount                 : Decimal(18, 4);
  recommended_action            : String(1024);
  estimated_annual_impact_tCO2e : Decimal(18, 2);
  status                        : String(32) default 'OPEN';
  acknowledged_by               : String(128);
  acknowledged_at               : Timestamp;
  resolved_at                   : Timestamp;
}

/**
 * RegulatoryReports — CSRD / IFRS S2 / SB253 disclosure artefacts.
 */
entity RegulatoryReports : cuid, managed {
  jurisdiction                  : Association to Jurisdictions;
  format                        : Association to ReportFormats;
  reporting_period_start        : Date not null;
  reporting_period_end          : Date not null;
  status                        : Association to ReportStatuses;
  file_name                     : String(256);
  lineage_record_count          : Integer default 0;
  taxonomy_applied              : String(256);
  methodology_ref               : String(256);
  approved_by                   : String(128);
  approved_at                   : Timestamp;
}

/**
 * DataLineageRecords — full provenance chain for each regulatory report.
 */
entity DataLineageRecords : cuid, managed {
  report                        : Association to RegulatoryReports;
  source_type                   : String(64);
  source_doc_id                 : String(128);
  volume_value                  : Decimal(18, 4);
  volume_unit                   : String(32);
  emission_factor_value         : Decimal(18, 8);
  emission_factor_source        : String(256);
  calculation_step              : String(512);
  disclosure_section_ref        : String(256);
}

/**
 * DecarbonizationRecommendations — prioritized interventions ranked by tCO2e/USD.
 */
entity DecarbonizationRecommendations : cuid, managed {
  rank                          : Integer;
  intervention_type             : String(256);
  target_asset_id               : String(64);
  description                   : String(2048);
  projected_reduction_tCO2e     : Decimal(18, 2);
  estimated_capex_USD           : Decimal(18, 2);
  payback_period_years          : Decimal(5, 2);
  cost_saving_USD_per_year      : Decimal(18, 2);
  implementation_complexity     : Association to ComplexityLevels;
  regulatory_compliance_impact  : String(512);
  status                        : Association to RecommendationStatuses;
}
