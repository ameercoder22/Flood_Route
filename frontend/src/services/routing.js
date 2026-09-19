// OSRM routing service for real route calculation
const OSRM_URL = 'https://router.project-osrm.org/route/v1/driving'

export async function calculateRoute(origin, destination) {
  if (!origin || !destination) {
    throw new Error('Origin and destination are required')
  }

  const coords = `${origin.longitude},${origin.latitude};${destination.longitude},${destination.latitude}`
  const url = `${OSRM_URL}/${coords}?overview=full&geometries=geojson`

  try {
    const response = await fetch(url)

    if (!response.ok) {
      throw new Error('Routing service unavailable')
    }

    const data = await response.json()

    if (data.code !== 'Ok' || !data.routes || data.routes.length === 0) {
      throw new Error('No route found')
    }

    const route = data.routes[0]

    // Convert GeoJSON coordinates [lon, lat] to {latitude, longitude}
    const coordinates = route.geometry.coordinates.map(coord => ({
      latitude: coord[1],
      longitude: coord[0]
    }))

    return {
      coordinates,
      distance: route.distance, // meters
      duration: route.duration, // seconds
    }
  } catch (error) {
    console.error('Routing error:', error)
    throw error
  }
}

export function formatDistance(meters) {
  if (meters < 1000) {
    return `${Math.round(meters)} m`
  }
  return `${(meters / 1000).toFixed(1)} km`
}

export function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) {
    return `${minutes} min`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}
