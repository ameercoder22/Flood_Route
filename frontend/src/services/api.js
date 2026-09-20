console.log("DEBUG: API_BASE_URL=", import.meta.env.VITE_API_BASE_URL); const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function checkRouteRisk(routeCoordinates, radiusMeters = 100) {
  // Normalize route coordinates to only include latitude and longitude
  const normalizedRoute = routeCoordinates.map(point => ({
    latitude: point.latitude,
    longitude: point.longitude
  }))

  console.log('DEBUG: Fetching URL:', `${API_BASE_URL}/flood/analyze-route`)
  const response = await fetch(`${API_BASE_URL}/flood/analyze-route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      route: normalizedRoute
    })
  })

  if (!response.ok) {
    const errorBody = await response.text()
    console.error('API Error Response:', {
      status: response.status,
      statusText: response.statusText,
      body: errorBody
    })
    throw new Error(`Failed to check route risk: ${response.statusText}`)
  }

  const data = await response.json()

  if (!data.success) {
    console.error('API Error Data:', data)
    throw new Error(data.error?.message || 'Failed to check route risk')
  }

  return {
    routeRisk: data.flood_analysis.flood_exposure_percentage > 50 ? 'HIGH_REPORTED_RISK' : (data.flood_analysis.flood_exposure_percentage > 10 ? 'MEDIUM_REPORTED_RISK' : 'LOW_REPORTED_RISK'),
    riskScore: data.flood_analysis.flood_exposure_percentage,
    affectedSegments: [],
    summary: { active_reports: 0 }
  }
}

export async function getReports(filters = {}) {
  const params = new URLSearchParams()
  if (filters.limit) params.append('limit', filters.limit)

  const response = await fetch(`${API_BASE_URL}/reports?${params}`, {
    method: 'GET'
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch reports: ${response.statusText}`)
  }

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error?.message || 'Failed to fetch reports')
  }

  return data.data || []
}

export async function getReport(reportId) {
  const response = await fetch(`${API_BASE_URL}/reports/${reportId}`, {
    method: 'GET'
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch report: ${response.statusText}`)
  }

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error?.message || 'Failed to fetch report')
  }

  return data.data
}

export async function createReport(formData) {
  const response = await fetch(`${API_BASE_URL}/reports`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    throw new Error(`Failed to create report: ${response.statusText}`)
  }

  const data = await response.json()

  if (!data.success) {
    throw new Error(data.error?.message || 'Failed to create report')
  }

  return data.data
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET'
  })

  if (!response.ok) {
    throw new Error(`Backend is not available: ${response.statusText}`)
  }

  return await response.json()
}
