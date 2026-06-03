using { ccie } from '../db/schema';

/**
 * CarbonComplianceService — OData v4 service exposing the CCIE compliance dashboard.
 *
 * Consumed by:
 *  - The React compliance operations dashboard (frontend)
 *  - The CCIE AI agent write-back endpoints (via agent-integration-service)
 */
@path: '/compliance'
service CarbonComplianceService {

  // --- Emissions Records ---
  entity EmissionsRecords as projection on ccie.EmissionsRecords;

  // --- Hotspot Alerts ---
  entity HotspotAlerts as projection on ccie.HotspotAlerts;

  action acknowledgeAlert(alertId: UUID) returns String;

  // --- Regulatory Reports ---
  entity RegulatoryReports as projection on ccie.RegulatoryReports;

  action   approveReport(reportId: UUID) returns String;
  function downloadReport(reportId: UUID) returns String;

  // --- Data Lineage ---
  @readonly
  entity DataLineageRecords as projection on ccie.DataLineageRecords;

  // --- Decarbonization Recommendations ---
  entity DecarbonizationRecommendations as projection on ccie.DecarbonizationRecommendations;

  action updateRecommendationStatus(recommendationId: UUID, status: String) returns String;

  // --- Portfolio KPIs (virtual, computed via handler) ---
  @readonly
  entity CarbonKPIs {
    key dummy            : String default 'kpis';
    total_scope1_tCO2e   : Decimal(18, 2);
    total_scope2_tCO2e   : Decimal(18, 2);
    total_scope3_tCO2e   : Decimal(18, 2);
    portfolio_intensity  : Decimal(18, 6);
    open_alert_count     : Integer;
    critical_alert_count : Integer;
    draft_report_count   : Integer;
    top_recommendation   : String(256);
  }
}
