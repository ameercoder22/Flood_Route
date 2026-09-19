export const normalizeRoute = (route) => {
  if (!Array.isArray(route)) return []

  return route.map(point => {
    // Handle [lon, lat] format (from OSRM/GeoJSON)
    if (Array.isArray(point) && point.length === 2) {
      return {
        latitude: point[1],
        longitude: point[0]
      }
    }

    // Handle {lat, lon} format
    if (point.lat !== undefined && point.lon !== undefined) {
      return {
        latitude: point.lat,
        longitude: point.lon
      }
    }

    // Already in {latitude, longitude} format
    if (point.latitude !== undefined && point.longitude !== undefined) {
      return point
    }

    return null
  }).filter(Boolean)
}

export const getRiskColor = (risk) => {
  if (!risk) return '#999999'
  if (risk.includes('HIGH')) return '#cc0000'
  if (risk.includes('MEDIUM')) return '#ff9900'
  if (risk.includes('LOW')) return '#00aa00'
  return '#999999'
}

export const formatTime = (timestamp) => {
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

export const formatDistance = (meters) => {
  if (meters < 1000) return `${Math.round(meters)}m`
  return `${(meters / 1000).toFixed(1)}km`
}
