console.log("DEBUG: API_BASE_URL=", import.meta.env.VITE_API_BASE_URL); const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function checkRouteRisk(routeCoordinates, radiusMeters = 100) {
  // Normalize route coordinates to only include latitude and longitude
  // (strip any extra fields like 'name' that the backend schema rejects)
  const normalizedRoute = routeCoordinates.map(point => ({
    latitude: point.latitude,
    longitude: point.longitude
  }))

  const response = await fetch(`${API_BASE_URL}/reports/near-route`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      route: normalizedRoute,
      radius_meters: radiusMeters
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
    routeRisk: data.route_risk,
    riskScore: data.risk_score,
    affectedSegments: data.affected_segments,
    summary: data.summary
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
