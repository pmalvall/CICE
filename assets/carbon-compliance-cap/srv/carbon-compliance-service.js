const cds = require('@sap/cds')

module.exports = class CarbonComplianceService extends cds.ApplicationService {

  async init() {
    const {
      EmissionsRecords,
      HotspotAlerts,
      RegulatoryReports,
      DecarbonizationRecommendations,
    } = this.entities

    // ---------------------------------------------------------------------------
    // CarbonKPIs — aggregate portfolio-level KPIs from live data
    // ---------------------------------------------------------------------------
    this.on('READ', 'CarbonKPIs', async () => {
      const emissionsRows = await SELECT
        .from(EmissionsRecords)
        .columns('scope1_tCO2e', 'scope2_tCO2e', 'scope3_tCO2e', 'carbon_intensity_tCO2e_per_BOE')

      const emissions = {
        total_scope1: emissionsRows.reduce((s, r) => s + (Number(r.scope1_tCO2e) || 0), 0),
        total_scope2: emissionsRows.reduce((s, r) => s + (Number(r.scope2_tCO2e) || 0), 0),
        total_scope3: emissionsRows.reduce((s, r) => s + (Number(r.scope3_tCO2e) || 0), 0),
        avg_intensity: emissionsRows.length > 0
          ? emissionsRows.reduce((s, r) => s + (Number(r.carbon_intensity_tCO2e_per_BOE) || 0), 0) / emissionsRows.length
          : 0,
      }
      const openAlerts = await SELECT
        .from(HotspotAlerts)
        .where({ status: 'OPEN' })
        .columns('ID', 'severity_code')

      const open_count = openAlerts.length
      const critical_count = openAlerts.filter(a => a.severity_code === 'CRITICAL').length

      const draftReports = await SELECT
        .from(RegulatoryReports)
        .where({ status_code: 'DRAFT' })
        .columns('ID')

      const [topRec] = await SELECT
        .from(DecarbonizationRecommendations)
        .where({ rank: 1 })
        .columns('intervention_type')

      return [{
        dummy: 'kpis',
        total_scope1_tCO2e: emissions.total_scope1,
        total_scope2_tCO2e: emissions.total_scope2,
        total_scope3_tCO2e: emissions.total_scope3,
        portfolio_intensity: emissions.avg_intensity,
        open_alert_count: open_count,
        critical_alert_count: critical_count,
        draft_report_count: draftReports.length || 0,
        top_recommendation: topRec?.intervention_type || 'No recommendations yet',
      }]
    })

    // ---------------------------------------------------------------------------
    // acknowledgeAlert — set status to ACKNOWLEDGED with timestamp
    // ---------------------------------------------------------------------------
    this.on('acknowledgeAlert', async (req) => {
      const { alertId } = req.data
      if (!alertId) return req.reject(400, 'alertId is required')

      const n = await UPDATE(HotspotAlerts, alertId)
        .with({
          status: 'ACKNOWLEDGED',
          acknowledged_by: req.user?.id || 'system',
          acknowledged_at: new Date().toISOString(),
        })

      if (!n) return req.reject(404, `Alert ${alertId} not found or already acknowledged`)
      return `Alert ${alertId} acknowledged successfully`
    })

    // ---------------------------------------------------------------------------
    // approveReport — transition DRAFT → APPROVED, record approver
    // ---------------------------------------------------------------------------
    this.on('approveReport', async (req) => {
      const { reportId } = req.data
      if (!reportId) return req.reject(400, 'reportId is required')

      const report = await SELECT.one.from(RegulatoryReports, reportId)
      if (!report) return req.reject(404, `Report ${reportId} not found`)
      if (report.status_code === 'APPROVED') return req.reject(409, `Report ${reportId} is already approved`)
      if (report.status_code === 'SUBMITTED') return req.reject(409, `Report ${reportId} has already been submitted`)

      await UPDATE(RegulatoryReports, reportId).with({
        status_code: 'APPROVED',
        approved_by: req.user?.id || 'compliance-officer',
        approved_at: new Date().toISOString(),
      })

      return `Report ${reportId} approved successfully. Jurisdiction: ${report.jurisdiction_code}. Ready for submission.`
    })

    // ---------------------------------------------------------------------------
    // downloadReport — return report metadata / download reference
    // ---------------------------------------------------------------------------
    this.on('downloadReport', async (req) => {
      const { reportId } = req.data
      if (!reportId) return req.reject(400, 'reportId is required')

      const report = await SELECT.one.from(RegulatoryReports, reportId)
      if (!report) return req.reject(404, `Report ${reportId} not found`)
      if (report.status_code === 'DRAFT') {
        return req.reject(403, `Report ${reportId} is a DRAFT and cannot be downloaded until approved`)
      }

      // In production, this returns a signed URL. Here we return metadata.
      return JSON.stringify({
        reportId,
        fileName: report.file_name,
        jurisdiction: report.jurisdiction_code,
        format: report.format_code,
        status: report.status_code,
        downloadRef: `/api/reports/${reportId}/download`,
        note: 'Download endpoint returns the rendered artefact (XBRL/PDF/JSON)',
      })
    })

    // ---------------------------------------------------------------------------
    // updateRecommendationStatus — progress tracking for decarbonization actions
    // ---------------------------------------------------------------------------
    this.on('updateRecommendationStatus', async (req) => {
      const { recommendationId, status } = req.data
      const valid = ['OPEN', 'IN_PROGRESS', 'COMPLETED', 'DISMISSED']
      if (!valid.includes(status)) {
        return req.reject(400, `Invalid status '${status}'. Must be one of: ${valid.join(', ')}`)
      }

      const n = await UPDATE(DecarbonizationRecommendations, recommendationId).with({
        status_code: status,
      })

      if (!n) return req.reject(404, `Recommendation ${recommendationId} not found`)
      return `Recommendation ${recommendationId} status updated to ${status}`
    })

    return super.init()
  }
}
