import './ReportList.css'

export default function ReportList({ reports }) {
  if (!reports || reports.length === 0) {
    return <div className="empty-reports">No reports found</div>
  }

  const getSeverityColor = (severity) => {
    if (severity === 'HIGH') return '#cc0000'
    if (severity === 'MEDIUM') return '#ff9900'
    if (severity === 'LOW') return '#00aa00'
    return '#999999'
  }

  const getSourceLabel = (source) => {
    if (source === 'DEMO') return '🔶 DEMO REPORT'
    if (source === 'CITIZEN') return 'Citizen Report'
    if (source === 'AI_ASSISTED') return 'AI-Assisted'
    return source
  }

  const formatTime = (timestamp) => {
    const now = new Date()
    const created = new Date(timestamp)
    const minutes = Math.floor((now - created) / 60000)
    if (minutes < 1) return 'just now'
    if (minutes < 60) return `${minutes}m ago`
    const hours = Math.floor(minutes / 60)
    if (hours < 24) return `${hours}h ago`
    const days = Math.floor(hours / 24)
    return `${days}d ago`
  }

  return (
    <div className="report-list">
      <h3>Recent Reports ({reports.length})</h3>
      <div className="reports-container">
        {reports.slice(0, 10).map((report) => (
          <div key={report.report_id} className="report-item">
            <div className="report-header">
              <span
                className="severity-badge"
                style={{ backgroundColor: getSeverityColor(report.severity) }}
              >
                {report.severity}
              </span>
              <span className={`source-badge ${report.source === 'DEMO' ? 'demo-badge' : ''}`}>
                {getSourceLabel(report.source)}
              </span>
              <span className="time">{formatTime(report.created_at)}</span>
            </div>

            <div className="report-body">
              <p><strong>{report.condition}</strong></p>
              <p className="description">{report.description}</p>

              {report.vehicle_impact && (
                <p><small>Impact: {report.vehicle_impact.replace(/_/g, ' ')}</small></p>
              )}

              {report.ai_confidence && (
                <p><small>AI Confidence: {(report.ai_confidence * 100).toFixed(0)}%</small></p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
