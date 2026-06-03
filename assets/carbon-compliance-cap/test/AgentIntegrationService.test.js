const cds = require('@sap/cds')
const test = cds.test(__dirname + '/..')

let srv

beforeAll(async () => {
  srv = await cds.connect.to('AgentIntegrationService')
})

describe('AgentIntegrationService', () => {
  it('should expose EmissionsRecords entity for agent write-back', async () => {
    const { EmissionsRecords } = srv.entities
    expect(EmissionsRecords).toBeDefined()
  })

  it('should allow inserting an emissions record via the service', async () => {
    const { EmissionsRecords } = srv.entities
    const id = cds.utils.uuid()
    await INSERT.into(EmissionsRecords).entries({
      ID: id,
      asset_id: 'AGENT-TEST-PLANT',
      asset_type_code: 'PLANT',
      period_start: '2024-02-01',
      period_end: '2024-02-29',
      scope1_tCO2e: 180.50,
      scope2_tCO2e: 15.20,
      scope3_tCO2e: 820.00,
      carbon_intensity_tCO2e_per_BOE: 0.0389,
      total_production_BOE: 25000,
      methodology: 'GHG Protocol',
      validation_status_code: 'PENDING',
    })

    const [rec] = await SELECT.from(EmissionsRecords).where({ ID: id })
    expect(rec.asset_id).toBe('AGENT-TEST-PLANT')
    expect(Number(rec.scope1_tCO2e)).toBeCloseTo(180.50, 1)
  })
})
