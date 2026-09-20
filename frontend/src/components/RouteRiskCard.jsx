import './RouteRiskCard.css'

const getRiskColor = (risk) => {
  if (risk.includes('HIGH')) return '#cc0000'
  if (risk.includes('MEDIUM')) return '#ff9900'
  if (risk.includes('LOW')) return '#00aa00'
  return '#999999'
}

export default function RouteRiskCard({ routeRisk }) {
  if (!routeRisk) return null

  const riskLabel = routeRisk.routeRisk || 'UNKNOWN'

  return (
    <div className="route-risk-card">
      <div className="risk-header">
        <h2>Route Risk Assessment</h2>
      </div>

      <div
        className="risk-badge"
        style={{ borderLeftColor: getRiskColor(riskLabel) }}
      >
        <div className="risk-label">{riskLabel}</div>
        {routeRisk.riskScore !== undefined && (
          <div className="risk-score">Score: {routeRisk.riskScore}</div>
        )}
      </div>

      {routeRisk.summary && (
        <div className="risk-summary">
          <p>
            <strong>Active Reports:</strong> {routeRisk.summary.active_reports || 0}
          </p>
          {routeRisk.summary.high_reports > 0 && (
            <p>
              <span className="badge high">
                ⚠ {routeRisk.summary.high_reports} HIGH
              </span>
            </p>
          )}
          {routeRisk.summary.medium_reports > 0 && (
            <p>
              <span className="badge medium">
                ⚠ {routeRisk.summary.medium_reports} MEDIUM
              </span>
            </p>
          )}
          {routeRisk.summary.low_reports > 0 && (
            <p>
              <span className="badge low">
                • {routeRisk.summary.low_reports} LOW
              </span>
            </p>
          )}
        </div>
      )}

      <div className="risk-disclaimer">
        <p>
          Reported risk is based on available recent reports near the route and does not guarantee current road conditions.
        </p>
      </div>
    </div>
  )
}
