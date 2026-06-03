using { ccie } from '../db/schema';

/**
 * AgentIntegrationService — REST endpoints for CCIE agent write-back.
 *
 * Consumed exclusively by the carbon-compliance-agent to push computed results
 * into the CAP database. Not exposed to end-user dashboard consumers.
 */
@path: '/agent'
@requires: 'system-user'
service AgentIntegrationService {

  // Bulk push endpoints for agent-computed data
  entity EmissionsRecords         as projection on ccie.EmissionsRecords;
  entity HotspotAlerts            as projection on ccie.HotspotAlerts;
  entity RegulatoryReports        as projection on ccie.RegulatoryReports;
  entity DataLineageRecords       as projection on ccie.DataLineageRecords;
  entity DecarbonizationRecommendations as projection on ccie.DecarbonizationRecommendations;
}
