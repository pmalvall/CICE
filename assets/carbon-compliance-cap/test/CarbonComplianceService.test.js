const cds = require('@sap/cds')
const test = cds.test(__dirname + '/..')

let srv, HotspotAlerts, RegulatoryReports, DecarbonizationRecommendations

beforeAll(async () => {
  srv = await cds.connect.to('CarbonComplianceService')
  ;({ HotspotAlerts, RegulatoryReports, DecarbonizationRecommendations } = srv.entities)
})

// ---------------------------------------------------------------------------
// CarbonKPIs — aggregated portfolio metrics
// ---------------------------------------------------------------------------
describe('CarbonKPIs', () => {
  it('should return exactly one KPI row', async () => {
    const result = await srv.run(SELECT.from('CarbonComplianceService.CarbonKPIs'))
    expect(result).toHaveLength(1)
  })

  it('should include all required KPI fields', async () => {
    const [kpis] = await srv.run(SELECT.from('CarbonComplianceService.CarbonKPIs'))
    expect(kpis).toHaveProperty('total_scope1_tCO2e')
    expect(kpis).toHaveProperty('total_scope2_tCO2e')
    expect(kpis).toHaveProperty('total_scope3_tCO2e')
    expect(kpis).toHaveProperty('open_alert_count')
    expect(kpis).toHaveProperty('draft_report_count')
  })
})

// ---------------------------------------------------------------------------
// acknowledgeAlert — status transition
// ---------------------------------------------------------------------------
describe('acknowledgeAlert', () => {
  let alertId

  beforeEach(async () => {
    // Seed a fresh OPEN alert for each test
    alertId = cds.utils.uuid()
    await INSERT.into(HotspotAlerts).entries({
      ID: alertId,
      alert_type_code: 'FLARING',
      asset_id: 'WELL-TEST',
      asset_type_code: 'WELL',
      severity_code: 'HIGH',
      metric_name: 'flare_volume_mcf',
      current_value: 300,
      threshold_value: 150,
      excess_amount: 150,
      recommended_action: 'Test action',
      estimated_annual_impact_tCO2e: 50,
      status: 'OPEN',
    })
  })

  it('should acknowledge an OPEN alert and return success message', async () => {
    const result = await srv.send('acknowledgeAlert', { alertId })
    expect(result).toContain('acknowledged successfully')

    const [updated] = await SELECT.from(HotspotAlerts).where({ ID: alertId })
    expect(updated.status).toBe('ACKNOWLEDGED')
    expect(updated.acknowledged_at).toBeTruthy()
  })

  it('should reject acknowledgeAlert without alertId', async () => {
    await expect(srv.send('acknowledgeAlert', {})).rejects.toMatchObject({
      code: 400,
    })
  })
})

// ---------------------------------------------------------------------------
// approveReport — status transition
// ---------------------------------------------------------------------------
describe('approveReport', () => {
  let reportId

  beforeEach(async () => {
    reportId = cds.utils.uuid()
    await INSERT.into(RegulatoryReports).entries({
      ID: reportId,
      jurisdiction_code: 'CSRD',
      format_code: 'JSON',
      reporting_period_start: '2024-01-01',
      reporting_period_end: '2024-12-31',
      status_code: 'DRAFT',
      file_name: 'test-report.json',
      lineage_record_count: 5,
    })
  })

  it('should approve a DRAFT report and return success message', async () => {
    const result = await srv.send('approveReport', { reportId })
    expect(result).toContain('approved successfully')

    const [updated] = await SELECT.from(RegulatoryReports).where({ ID: reportId })
    expect(updated.status_code).toBe('APPROVED')
    expect(updated.approved_at).toBeTruthy()
  })

  it('should reject approveReport for already-approved report', async () => {
    // Approve once
    await srv.send('approveReport', { reportId })
    // Try again
    await expect(srv.send('approveReport', { reportId })).rejects.toMatchObject({
      code: 409,
    })
  })

  it('should reject approveReport without reportId', async () => {
    await expect(srv.send('approveReport', {})).rejects.toMatchObject({
      code: 400,
    })
  })
})

// ---------------------------------------------------------------------------
// updateRecommendationStatus — status tracking
// ---------------------------------------------------------------------------
describe('updateRecommendationStatus', () => {
  let recId

  beforeEach(async () => {
    recId = cds.utils.uuid()
    await INSERT.into(DecarbonizationRecommendations).entries({
      ID: recId,
      rank: 99,
      intervention_type: 'Test Intervention',
      target_asset_id: 'WELL-TEST',
      projected_reduction_tCO2e: 100,
      estimated_capex_USD: 500000,
      payback_period_years: 5,
      cost_saving_USD_per_year: 10000,
      implementation_complexity_code: 'LOW',
      status_code: 'OPEN',
    })
  })

  it('should update status from OPEN to IN_PROGRESS', async () => {
    const result = await srv.send('updateRecommendationStatus', { recommendationId: recId, status: 'IN_PROGRESS' })
    expect(result).toContain('IN_PROGRESS')

    const [updated] = await SELECT.from(DecarbonizationRecommendations).where({ ID: recId })
    expect(updated.status_code).toBe('IN_PROGRESS')
  })

  it('should reject invalid status values', async () => {
    await expect(
      srv.send('updateRecommendationStatus', { recommendationId: recId, status: 'INVALID_STATUS' })
    ).rejects.toMatchObject({ code: 400 })
  })
})
