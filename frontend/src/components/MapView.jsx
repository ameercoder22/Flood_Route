import { useRef, useEffect } from 'react'
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMapEvent } from 'react-leaflet'
import L from 'leaflet'
import './MapView.css'

const createIcon = (type) => {
  const colors = {
    origin: '#4CAF50',
    destination: '#F44336',
    report: '#FF9800',
    reportLocation: '#0066FF'
  }
  const iconText = {
    origin: 'A',
    destination: 'B',
    report: '!',
    reportLocation: '●'
  }
  return L.divIcon({
    className: `marker-${type}`,
    html: `<div style="background-color: ${colors[type]}; width: 30px; height: 30px; border-radius: 50%; border: 2px solid white; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">
      ${iconText[type]}
    </div>`,
    iconSize: [30, 30]
  })
}

function MapClickHandler({ onMapClick, showReportMode }) {
  useMapEvent('click', (e) => {
    if (showReportMode) {
      onMapClick(e.latlng.lat, e.latlng.lng)
    }
  })
  return null
}

export default function MapView({
  origin,
  destination,
  route,
  routeRisk,
  reports,
  mapCenter,
  onMapClick,
  showReportMode
}) {
  const polylineColor = routeRisk?.routeRisk?.includes('HIGH')
    ? '#cc0000'
    : routeRisk?.routeRisk?.includes('MEDIUM')
    ? '#ff9900'
    : '#00aa00'

  return (
    <div className="map-view">
      <MapContainer center={mapCenter} zoom={12} className="map-container">
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />

        {showReportMode && <MapClickHandler onMapClick={onMapClick} showReportMode={showReportMode} />}

        {route && (
          <Polyline
            positions={route.map(p => [p.latitude, p.longitude])}
            color={polylineColor}
            weight={4}
          />
        )}

        {origin && (
          <Marker position={[origin.latitude, origin.longitude]} icon={createIcon('origin')}>
            <Popup>{origin.name || 'Origin'}</Popup>
          </Marker>
        )}

        {destination && (
          <Marker position={[destination.latitude, destination.longitude]} icon={createIcon('destination')}>
            <Popup>{destination.name || 'Destination'}</Popup>
          </Marker>
        )}

        {reports.map(report => (
          <Marker
            key={report.report_id}
            position={[report.latitude, report.longitude]}
            icon={createIcon('report')}
          >
            <Popup>
              <div className="report-popup">
                <strong>{report.condition}</strong>
                {report.source === 'DEMO' && (
                  <div style={{ color: '#e65100', fontWeight: 'bold', fontSize: '11px', marginTop: '4px' }}>
                    🔶 DEMO REPORT
                  </div>
                )}
                <p>Severity: {report.severity}</p>
                <p>Reported: {Math.round((Date.now() - new Date(report.created_at).getTime()) / 60000)} min ago</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {routeRisk?.affectedSegments?.map((segment, idx) => (
          <Marker
            key={`segment-${idx}`}
            position={[segment.latitude, segment.longitude]}
            icon={L.divIcon({
              className: 'affected-segment',
              html: `<div style="background-color: #ff6600; width: 20px; height: 20px; border-radius: 50%; opacity: 0.7;"></div>`,
              iconSize: [20, 20]
            })}
          >
            <Popup>
              <div>
                <strong>Affected Segment</strong>
                <p>Risk: {segment.risk}</p>
                <p>Reports: {segment.reports}</p>
                <p>Latest: {segment.latest_report_minutes_ago} min ago</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      <div className="map-legend">
        <h4>Legend</h4>
        <div><span style={{color: '#4CAF50'}}>●</span> Origin</div>
        <div><span style={{color: '#F44336'}}>●</span> Destination</div>
        <div><span style={{color: '#FF9800'}}>●</span> Report</div>
        {showReportMode && (
          <div><span style={{color: '#0066FF'}}>●</span> Report Location (click to select)</div>
        )}
        <div style={{marginTop: '10px'}}>
          <div><span style={{color: '#cc0000'}}>─</span> High Risk Route</div>
          <div><span style={{color: '#ff9900'}}>─</span> Medium Risk Route</div>
          <div><span style={{color: '#00aa00'}}>─</span> Low Risk Route</div>
        </div>
      </div>
    </div>
  )
}
