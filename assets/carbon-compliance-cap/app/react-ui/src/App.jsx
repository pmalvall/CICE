import { useEffect, useState } from 'react'
import {
  FlexBox,
  Title,
  Card,
  CardHeader,
  Text,
  Tag,
  Button,
  Table,
  TableHeaderRow,
  TableHeaderCell,
  TableRow,
  TableCell,
  BusyIndicator,
  Bar,
  Icon,
  MessageStrip,
  ObjectStatus,
} from '@ui5/webcomponents-react'
import '@ui5/webcomponents-icons/dist/AllIcons.js'

const BASE = '/compliance'

async function fetchJSON(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const body = await res.json()
  return body.value ?? body
}

function severityColor(sev) {
  const map = { LOW: 'Information', MEDIUM: 'Warning', HIGH: 'Caution', CRITICAL: 'Negative' }
  return map[sev] || 'None'
}

function statusBadge(status) {
  const map = {
    DRAFT: { state: 'None', text: 'Draft' },
    PENDING_APPROVAL: { state: 'Information', text: 'Pending Approval' },
    APPROVED: { state: 'Positive', text: 'Approved' },
    SUBMITTED: { state: 'Positive', text: 'Submitted' },
  }
  return map[status] || { state: 'None', text: status }
}

// ------------------------------------------------------------------
// KPI Card
// ------------------------------------------------------------------
function KpiCard({ title, value, unit, state = 'None', icon }) {
  return (
    <Card style={{ minWidth: '180px', flex: '1 1 180px' }}>
      <CardHeader titleText={title} avatar={icon ? <Icon name={icon} /> : undefined} />
      <div style={{ padding: '0.75rem 1rem' }}>
        <Title level="H3" style={{ color: state === 'Negative' ? 'var(--sapNegativeColor)' : undefined }}>
          {value != null ? Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 }) : '—'}
        </Title>
        <Text style={{ color: 'var(--sapContent_LabelColor)' }}>{unit}</Text>
      </div>
    </Card>
  )
}

// ------------------------------------------------------------------
// Main App
// ------------------------------------------------------------------
export default function App() {
  const [kpis, setKpis] = useState(null)
  const [emissions, setEmissions] = useState([])
  const [alerts, setAlerts] = useState([])
  const [reports, setReports] = useState([])
  const [lineage, setLineage] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedReport, setSelectedReport] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [k, em, al, rp, rec] = await Promise.all([
        fetchJSON('/CarbonKPIs'),
        fetchJSON('/EmissionsRecords?$orderby=period_start desc&$top=20'),
        fetchJSON('/HotspotAlerts?$orderby=createdAt desc&$top=20'),
        fetchJSON('/RegulatoryReports?$orderby=createdAt desc'),
        fetchJSON('/DecarbonizationRecommendations?$orderby=rank asc&$top=10'),
      ])
      setKpis(Array.isArray(k) ? k[0] : k)
      setEmissions(em)
      setAlerts(al)
      setReports(rp)
      setRecommendations(rec)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const loadLineage = async (reportId) => {
    try {
      const data = await fetchJSON(`/DataLineageRecords?$filter=report_ID eq ${reportId}&$top=50`)
      setLineage(data)
      setSelectedReport(reportId)
    } catch (e) {
      setLineage([])
    }
  }

  const acknowledgeAlert = async (alertId) => {
    try {
      const res = await fetch(`${BASE}/acknowledgeAlert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alertId }),
      })
      const body = await res.json()
      setActionMsg({ type: res.ok ? 'Positive' : 'Negative', text: body.value || body.error?.message })
      load()
    } catch (e) {
      setActionMsg({ type: 'Negative', text: e.message })
    }
  }

  const approveReport = async (reportId) => {
    try {
      const res = await fetch(`${BASE}/approveReport`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reportId }),
      })
      const body = await res.json()
      setActionMsg({ type: res.ok ? 'Positive' : 'Negative', text: body.value || body.error?.message })
      load()
    } catch (e) {
      setActionMsg({ type: 'Negative', text: e.message })
    }
  }

  const updateRecStatus = async (recId, status) => {
    try {
      const res = await fetch(`${BASE}/updateRecommendationStatus`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recommendationId: recId, status }),
      })
      const body = await res.json()
      setActionMsg({ type: res.ok ? 'Positive' : 'Negative', text: body.value || body.error?.message })
      load()
    } catch (e) {
      setActionMsg({ type: 'Negative', text: e.message })
    }
  }

  if (loading) return <BusyIndicator active size="Large" style={{ margin: '4rem auto', display: 'block' }} />
  if (error) return <MessageStrip design="Negative" style={{ margin: '2rem' }}>{error} — <Button onClick={load}>Retry</Button></MessageStrip>

  return (
    <div style={{ padding: '1.5rem', background: 'var(--sapBackgroundColor)', minHeight: '100vh' }}>
      {/* Header */}
      <Bar
        startContent={
          <FlexBox alignItems="Center" gap="0.5rem">
            <Icon name="environmental-policy" style={{ fontSize: '1.5rem', color: 'var(--sapBrandColor)' }} />
            <Title level="H4" style={{ margin: 0 }}>Carbon Compliance Intelligence Engine</Title>
          </FlexBox>
        }
        endContent={
          <FlexBox gap="0.5rem" alignItems="Center">
            <Button icon="refresh" onClick={load} design="Transparent">Refresh</Button>
          </FlexBox>
        }
        style={{ marginBottom: '1.5rem', borderRadius: '0.5rem' }}
      />

      {actionMsg && (
        <MessageStrip design={actionMsg.type} onClose={() => setActionMsg(null)} style={{ marginBottom: '1rem' }}>
          {actionMsg.text}
        </MessageStrip>
      )}

      {/* KPI Summary */}
      <FlexBox wrap="Wrap" gap="1rem" style={{ marginBottom: '1.5rem' }}>
        <KpiCard title="Scope 1 Emissions" value={kpis?.total_scope1_tCO2e} unit="tCO₂e" icon="flame" />
        <KpiCard title="Scope 2 Emissions" value={kpis?.total_scope2_tCO2e} unit="tCO₂e" icon="electricity" />
        <KpiCard title="Scope 3 Emissions" value={kpis?.total_scope3_tCO2e} unit="tCO₂e" icon="chain-link" />
        <KpiCard title="Carbon Intensity" value={kpis?.portfolio_intensity?.toFixed(5)} unit="tCO₂e / BOE" icon="measure" />
        <KpiCard title="Open Alerts" value={kpis?.open_alert_count} unit={`(${kpis?.critical_alert_count || 0} critical)`} state={kpis?.critical_alert_count > 0 ? 'Negative' : 'None'} icon="warning" />
        <KpiCard title="Draft Reports" value={kpis?.draft_report_count} unit="pending approval" icon="document" />
      </FlexBox>

      {/* Navigation Tabs */}
      <FlexBox gap="0.5rem" style={{ marginBottom: '1.5rem' }}>
        {['overview', 'alerts', 'reports', 'recommendations'].map(tab => (
          <Button
            key={tab}
            design={activeTab === tab ? 'Emphasized' : 'Default'}
            onClick={() => setActiveTab(tab)}
            style={{ textTransform: 'capitalize' }}
          >
            {tab === 'overview' ? 'Emissions' : tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Button>
        ))}
      </FlexBox>

      {/* EMISSIONS TAB */}
      {activeTab === 'overview' && (
        <Card>
          <CardHeader titleText="Asset Carbon Intensity" subtitleText="Scope 1/2/3 emissions by asset and period" />
          <Table
            headerRow={
              <TableHeaderRow>
                <TableHeaderCell>Asset</TableHeaderCell>
                <TableHeaderCell>Type</TableHeaderCell>
                <TableHeaderCell>Period</TableHeaderCell>
                <TableHeaderCell>Scope 1 (tCO₂e)</TableHeaderCell>
                <TableHeaderCell>Scope 2 (tCO₂e)</TableHeaderCell>
                <TableHeaderCell>Scope 3 (tCO₂e)</TableHeaderCell>
                <TableHeaderCell>Intensity (tCO₂e/BOE)</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
              </TableHeaderRow>
            }
          >
            {emissions.map(row => {
              const intensity = Number(row.carbon_intensity_tCO2e_per_BOE)
              const intensityHigh = intensity > 0.055
              return (
                <TableRow key={row.ID}>
                  <TableCell><Text>{row.asset_id}</Text></TableCell>
                  <TableCell><Text>{row.asset_type_code}</Text></TableCell>
                  <TableCell><Text>{row.period_start} – {row.period_end}</Text></TableCell>
                  <TableCell><Text>{Number(row.scope1_tCO2e).toFixed(2)}</Text></TableCell>
                  <TableCell><Text>{Number(row.scope2_tCO2e).toFixed(2)}</Text></TableCell>
                  <TableCell><Text>{Number(row.scope3_tCO2e).toFixed(2)}</Text></TableCell>
                  <TableCell>
                    <ObjectStatus state={intensityHigh ? 'Negative' : 'Positive'} inverted>
                      {intensity.toFixed(5)}
                    </ObjectStatus>
                  </TableCell>
                  <TableCell>
                    <Tag design={row.validation_status_code === 'VALIDATED' ? 'Positive' : row.validation_status_code === 'FLAGGED' ? 'Critical' : 'Neutral'}>
                      {row.validation_status_code}
                    </Tag>
                  </TableCell>
                </TableRow>
              )
            })}
          </Table>
        </Card>
      )}

      {/* ALERTS TAB */}
      {activeTab === 'alerts' && (
        <Card>
          <CardHeader titleText="Carbon Hotspot Alerts" subtitleText="Flaring anomalies, methane leaks, and inefficient wells" />
          <Table
            headerRow={
              <TableHeaderRow>
                <TableHeaderCell>Alert Type</TableHeaderCell>
                <TableHeaderCell>Asset</TableHeaderCell>
                <TableHeaderCell>Severity</TableHeaderCell>
                <TableHeaderCell>Metric</TableHeaderCell>
                <TableHeaderCell>Current / Threshold</TableHeaderCell>
                <TableHeaderCell>Est. Impact (tCO₂e/yr)</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Action</TableHeaderCell>
              </TableHeaderRow>
            }
          >
            {alerts.map(alert => (
              <TableRow key={alert.ID}>
                <TableCell><Text>{alert.alert_type_code}</Text></TableCell>
                <TableCell><Text>{alert.asset_id} ({alert.asset_type_code})</Text></TableCell>
                <TableCell>
                  <ObjectStatus state={severityColor(alert.severity_code)} inverted>
                    {alert.severity_code}
                  </ObjectStatus>
                </TableCell>
                <TableCell><Text>{alert.metric_name}</Text></TableCell>
                <TableCell>
                  <Text>{Number(alert.current_value).toFixed(2)} / {Number(alert.threshold_value).toFixed(2)}</Text>
                </TableCell>
                <TableCell><Text>{Number(alert.estimated_annual_impact_tCO2e).toFixed(1)}</Text></TableCell>
                <TableCell>
                  <Tag design={alert.status === 'OPEN' ? 'Critical' : alert.status === 'ACKNOWLEDGED' ? 'Information' : 'Positive'}>
                    {alert.status}
                  </Tag>
                </TableCell>
                <TableCell>
                  {alert.status === 'OPEN' && (
                    <Button design="Transparent" onClick={() => acknowledgeAlert(alert.ID)}>Acknowledge</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </Table>
        </Card>
      )}

      {/* REPORTS TAB */}
      {activeTab === 'reports' && (
        <>
          <Card style={{ marginBottom: '1rem' }}>
            <CardHeader titleText="Regulatory Compliance Reports" subtitleText="CSRD, IFRS S2, and SB253 disclosure artefacts" />
            <Table
              headerRow={
                <TableHeaderRow>
                  <TableHeaderCell>Jurisdiction</TableHeaderCell>
                  <TableHeaderCell>Format</TableHeaderCell>
                  <TableHeaderCell>Period</TableHeaderCell>
                  <TableHeaderCell>Status</TableHeaderCell>
                  <TableHeaderCell>Lineage Records</TableHeaderCell>
                  <TableHeaderCell>Actions</TableHeaderCell>
                </TableHeaderRow>
              }
            >
              {reports.map(report => {
                const s = statusBadge(report.status_code)
                return (
                  <TableRow key={report.ID}>
                    <TableCell><Text style={{ fontWeight: 'bold' }}>{report.jurisdiction_code}</Text></TableCell>
                    <TableCell><Text>{report.format_code}</Text></TableCell>
                    <TableCell><Text>{report.reporting_period_start} – {report.reporting_period_end}</Text></TableCell>
                    <TableCell>
                      <ObjectStatus state={s.state}>{s.text}</ObjectStatus>
                    </TableCell>
                    <TableCell><Text>{report.lineage_record_count}</Text></TableCell>
                    <TableCell>
                      <FlexBox gap="0.25rem">
                        {(report.status_code === 'DRAFT' || report.status_code === 'PENDING_APPROVAL') && (
                          <Button design="Positive" onClick={() => approveReport(report.ID)}>Approve</Button>
                        )}
                        <Button design="Transparent" onClick={() => loadLineage(report.ID)}>Lineage</Button>
                      </FlexBox>
                    </TableCell>
                  </TableRow>
                )
              })}
            </Table>
          </Card>

          {selectedReport && (
            <Card>
              <CardHeader
                titleText={`Data Lineage — Report ${selectedReport}`}
                subtitleText="Full provenance chain from SAP PRA source to regulatory disclosure section"
                action={<Button design="Transparent" onClick={() => { setLineage([]); setSelectedReport(null) }}>Close</Button>}
              />
              {lineage.length === 0 ? (
                <Text style={{ padding: '1rem' }}>No lineage records found for this report.</Text>
              ) : (
                <Table
                  headerRow={
                    <TableHeaderRow>
                      <TableHeaderCell>Source Type</TableHeaderCell>
                      <TableHeaderCell>Source Doc ID</TableHeaderCell>
                      <TableHeaderCell>Volume</TableHeaderCell>
                      <TableHeaderCell>Emission Factor</TableHeaderCell>
                      <TableHeaderCell>Calculation Step</TableHeaderCell>
                      <TableHeaderCell>Disclosure Section</TableHeaderCell>
                    </TableHeaderRow>
                  }
                >
                  {lineage.map(rec => (
                    <TableRow key={rec.ID}>
                      <TableCell><Text>{rec.source_type}</Text></TableCell>
                      <TableCell><Text>{rec.source_doc_id}</Text></TableCell>
                      <TableCell><Text>{rec.volume_value} {rec.volume_unit}</Text></TableCell>
                      <TableCell><Text>{rec.emission_factor_value} ({rec.emission_factor_source})</Text></TableCell>
                      <TableCell><Text>{rec.calculation_step}</Text></TableCell>
                      <TableCell><Text>{rec.disclosure_section_ref}</Text></TableCell>
                    </TableRow>
                  ))}
                </Table>
              )}
            </Card>
          )}
        </>
      )}

      {/* RECOMMENDATIONS TAB */}
      {activeTab === 'recommendations' && (
        <Card>
          <CardHeader
            titleText="Decarbonization Recommendations"
            subtitleText="Prioritized interventions ranked by tCO₂e reduction per USD capex invested"
          />
          <Table
            headerRow={
              <TableHeaderRow>
                <TableHeaderCell>#</TableHeaderCell>
                <TableHeaderCell>Intervention</TableHeaderCell>
                <TableHeaderCell>Target Asset</TableHeaderCell>
                <TableHeaderCell>Projected Reduction (tCO₂e)</TableHeaderCell>
                <TableHeaderCell>Capex (USD)</TableHeaderCell>
                <TableHeaderCell>Payback (yrs)</TableHeaderCell>
                <TableHeaderCell>Complexity</TableHeaderCell>
                <TableHeaderCell>Status</TableHeaderCell>
                <TableHeaderCell>Action</TableHeaderCell>
              </TableHeaderRow>
            }
          >
            {recommendations.map(rec => (
              <TableRow key={rec.ID}>
                <TableCell>
                  <Tag design="Information">{rec.rank}</Tag>
                </TableCell>
                <TableCell>
                  <Text style={{ fontWeight: 'bold' }}>{rec.intervention_type}</Text>
                  <br />
                  <Text style={{ fontSize: '0.75rem', color: 'var(--sapContent_LabelColor)' }}>
                    {rec.regulatory_compliance_impact}
                  </Text>
                </TableCell>
                <TableCell><Text>{rec.target_asset_id}</Text></TableCell>
                <TableCell>
                  <ObjectStatus state="Positive" inverted>
                    {Number(rec.projected_reduction_tCO2e).toLocaleString()} tCO₂e
                  </ObjectStatus>
                </TableCell>
                <TableCell><Text>${Number(rec.estimated_capex_USD).toLocaleString()}</Text></TableCell>
                <TableCell><Text>{rec.payback_period_years} yrs</Text></TableCell>
                <TableCell>
                  <Tag design={rec.implementation_complexity_code === 'LOW' ? 'Positive' : rec.implementation_complexity_code === 'MEDIUM' ? 'Warning' : 'Critical'}>
                    {rec.implementation_complexity_code}
                  </Tag>
                </TableCell>
                <TableCell>
                  <ObjectStatus state={rec.status_code === 'COMPLETED' ? 'Positive' : rec.status_code === 'IN_PROGRESS' ? 'Information' : rec.status_code === 'DISMISSED' ? 'Negative' : 'None'}>
                    {rec.status_code}
                  </ObjectStatus>
                </TableCell>
                <TableCell>
                  <FlexBox gap="0.25rem" wrap="Wrap">
                    {rec.status_code === 'OPEN' && (
                      <Button design="Transparent" onClick={() => updateRecStatus(rec.ID, 'IN_PROGRESS')}>Start</Button>
                    )}
                    {rec.status_code === 'IN_PROGRESS' && (
                      <Button design="Positive" onClick={() => updateRecStatus(rec.ID, 'COMPLETED')}>Complete</Button>
                    )}
                    {rec.status_code === 'OPEN' && (
                      <Button design="Negative" onClick={() => updateRecStatus(rec.ID, 'DISMISSED')}>Dismiss</Button>
                    )}
                  </FlexBox>
                </TableCell>
              </TableRow>
            ))}
          </Table>
        </Card>
      )}
    </div>
  )
}
