import { useState, useEffect } from 'react'
import MapView from './components/MapView'
import SearchPanel from './components/SearchPanel'
import RouteRiskCard from './components/RouteRiskCard'
import ReportForm from './components/ReportForm'
import ReportList from './components/ReportList'
import LoadingState from './components/LoadingState'
import ErrorState from './components/ErrorState'
import Header from './components/Header'
import { checkRouteRisk, getReports, createReport } from './services/api'
import { calculateRoute, formatDistance, formatDuration } from './services/routing'
import './App.css'

export default function App() {
  const [origin, setOrigin] = useState(null)
  const [destination, setDestination] = useState(null)
  const [route, setRoute] = useState(null)
  const [routeInfo, setRouteInfo] = useState(null)
  const [routeRisk, setRouteRisk] = useState(null)
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [showReportForm, setShowReportForm] = useState(false)
  const [mapCenter, setMapCenter] = useState([15.8281, 78.0373])
  const [selectedReportLocation, setSelectedReportLocation] = useState(null)

  const handleCheckRoute = async () => {
    if (!origin || !destination) {
      setError('Please enter both origin and destination')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Calculate actual route using OSRM
      const routeData = await calculateRoute(origin, destination)

      setRoute(routeData.coordinates)
      setRouteInfo({
        distance: formatDistance(routeData.distance),
        duration: formatDuration(routeData.duration),
      })

      // Fetch route risk from backend
      const risk = await checkRouteRisk(routeData.coordinates, 100)
      setRouteRisk(risk)

      // Fetch nearby reports
      const reportsData = await getReports({ limit: 50 })
      setReports(reportsData || [])

      // Center map on midpoint
      setMapCenter([
        (origin.latitude + destination.latitude) / 2,
        (origin.longitude + destination.longitude) / 2
      ])
    } catch (err) {
      setError(err.message || 'Failed to check route risk')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleMapClick = (latitude, longitude) => {
    setSelectedReportLocation({ latitude, longitude })
    if (!showReportForm) {
      setShowReportForm(true)
    }
  }

  const handleReportSubmit = async (reportData) => {
    try {
      setLoading(true)
      await createReport(reportData)
      setShowReportForm(false)
      setSelectedReportLocation(null)

      // Refresh reports and route risk
      if (route) {
        const risk = await checkRouteRisk(route, 100)
        setRouteRisk(risk)
      }

      const reportsData = await getReports({ limit: 50 })
      setReports(reportsData || [])
    } catch (err) {
      setError(err.message || 'Failed to submit report')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <Header />

      <div className="container">
        <SearchPanel
          origin={origin}
          destination={destination}
          onOriginChange={setOrigin}
          onDestinationChange={setDestination}
          onCheckRoute={handleCheckRoute}
          loading={loading}
        />

        <div className="main-content">
          <MapView
            origin={origin}
            destination={destination}
            route={route}
            routeRisk={routeRisk}
            reports={reports}
            mapCenter={mapCenter}
            onMapClick={handleMapClick}
            showReportMode={showReportForm}
            selectedReportLocation={selectedReportLocation}
          />

          <div className="sidebar">
            {loading && <LoadingState />}
            {error && <ErrorState error={error} onDismiss={() => setError(null)} />}

            {routeRisk && (
              <>
                {routeInfo && (
                  <div className="route-info-card">
                    <div className="route-stat">
                      <span className="label">Distance:</span>
                      <span className="value">{routeInfo.distance}</span>
                    </div>
                    <div className="route-stat">
                      <span className="label">Duration:</span>
                      <span className="value">{routeInfo.duration}</span>
                    </div>
                  </div>
                )}
                <RouteRiskCard routeRisk={routeRisk} />
                <button
                  className="report-button"
                  onClick={() => setShowReportForm(!showReportForm)}
                >
                  {showReportForm ? 'Cancel' : 'Report Flooded Road'}
                </button>
              </>
            )}

            {showReportForm && (
              <ReportForm
                selectedLocation={selectedReportLocation}
                onSubmit={handleReportSubmit}
                loading={loading}
              />
            )}

            {reports.length > 0 && !showReportForm && (
              <ReportList reports={reports} />
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
