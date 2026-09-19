// Nominatim geocoding service for real location search
const NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'

let debounceTimer = null

// OSM place types that are useful for routing (cities, towns, villages, etc.)
const USEFUL_PLACE_TYPES = [
  'city',
  'town',
  'village',
  'municipality',
  'suburb',
  'neighbourhood',
  'locality',
  'hamlet',
  'county',
  'state',
  'administrative'
]

// Rank places by relevance for routing
function rankPlace(result) {
  const type = result.type
  const osm_type = result.osm_type
  const address = result.address || {}

  // Prefer administrative boundaries and populated places
  if (address.city) return 1
  if (address.town) return 2
  if (address.municipality) return 3
  if (address.village) return 4
  if (address.suburb) return 5
  if (address.neighbourhood) return 6
  if (address.locality) return 7
  if (address.hamlet) return 8

  // Counties and states are useful for broad searches
  if (address.county) return 9
  if (address.state) return 10

  // Administrative boundaries
  if (type === 'administrative') return 11

  // Less specific results
  if (type === 'residential') return 20
  if (type === 'road') return 25

  // Very specific addresses are less useful for routing
  if (type === 'house') return 50
  if (type === 'building') return 51
  if (type === 'amenity') return 52

  // Default
  return 30
}

function isUsefulPlace(result) {
  const type = result.type
  const address = result.address || {}

  // Include if it has a useful place type in address
  if (address.city || address.town || address.village ||
      address.municipality || address.suburb || address.neighbourhood ||
      address.locality || address.hamlet) {
    return true
  }

  // Include if it's an administrative boundary
  if (type === 'administrative' || type === 'boundary') {
    return true
  }

  // Include if type is in our useful list
  if (USEFUL_PLACE_TYPES.includes(type)) {
    return true
  }

  // Exclude very specific addresses unless nothing else matches
  if (type === 'house' || type === 'building' || type === 'amenity') {
    return false
  }

  return true
}

function extractPlaceName(result) {
  const address = result.address || {}

  // Prefer the most relevant place name from address
  if (address.city) return address.city
  if (address.town) return address.town
  if (address.municipality) return address.municipality
  if (address.village) return address.village
  if (address.suburb) return address.suburb
  if (address.neighbourhood) return address.neighbourhood
  if (address.locality) return address.locality
  if (address.hamlet) return address.hamlet
  if (address.county) return address.county

  // Fall back to first part of display_name
  return result.display_name.split(',')[0]
}

function getPlaceType(result) {
  const address = result.address || {}

  if (address.city) return 'city'
  if (address.town) return 'town'
  if (address.municipality) return 'municipality'
  if (address.village) return 'village'
  if (address.suburb) return 'suburb'
  if (address.neighbourhood) return 'neighbourhood'
  if (address.locality) return 'locality'
  if (address.hamlet) return 'hamlet'
  if (address.county) return 'county'
  if (address.state) return 'state'

  return result.type || 'place'
}

export async function geocode(query, signal) {
  if (!query || query.length < 2) {
    return []
  }

  const params = new URLSearchParams({
    q: query,
    format: 'json',
    addressdetails: '1',
    limit: '20', // Get more results to filter
    countrycodes: 'in', // Focus on India for FloodRoute
  })

  try {
    const response = await fetch(`${NOMINATIM_URL}?${params}`, {
      signal,
      headers: {
        'User-Agent': 'FloodRoute/1.0',
      },
    })

    if (!response.ok) {
      throw new Error('Geocoding failed')
    }

    const results = await response.json()

    // Filter to useful places
    const usefulResults = results.filter(isUsefulPlace)

    // If we have useful places, use them; otherwise fall back to all results
    const filteredResults = usefulResults.length > 0 ? usefulResults : results.slice(0, 10)

    // Transform and rank
    const transformed = filteredResults.map((result) => ({
      name: extractPlaceName(result),
      displayName: result.display_name,
      latitude: parseFloat(result.lat),
      longitude: parseFloat(result.lon),
      type: result.type,
      placeType: getPlaceType(result),
      rank: rankPlace(result),
      raw: result // Keep for debugging if needed
    }))

    // Sort by rank (lower is better)
    transformed.sort((a, b) => a.rank - b.rank)

    // Return top 10
    return transformed.slice(0, 10)
  } catch (error) {
    if (error.name === 'AbortError') {
      return []
    }
    console.error('Geocoding error:', error)
    throw error
  }
}

export function debounce(fn, delay = 500) {
  return (...args) => {
    clearTimeout(debounceTimer)
    return new Promise((resolve) => {
      debounceTimer = setTimeout(() => resolve(fn(...args)), delay)
    })
  }
}

