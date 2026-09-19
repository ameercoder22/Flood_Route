import { useState, useCallback, useEffect, useRef } from 'react'
import { geocode } from '../services/geocoding'
import './SearchPanel.css'

export default function SearchPanel({
  origin,
  destination,
  onOriginChange,
  onDestinationChange,
  onCheckRoute,
  loading
}) {
  const [originText, setOriginText] = useState('')
  const [destText, setDestText] = useState('')
  const [originSuggestions, setOriginSuggestions] = useState([])
  const [destSuggestions, setDestSuggestions] = useState([])
  const [originLoading, setOriginLoading] = useState(false)
  const [destLoading, setDestLoading] = useState(false)
  const [geoError, setGeoError] = useState(null)

  const originAbortController = useRef(null)
  const destAbortController = useRef(null)
  const originDebounceTimer = useRef(null)
  const destDebounceTimer = useRef(null)

  const handleOriginChange = (e) => {
    const text = e.target.value
    setOriginText(text)
    setGeoError(null)

    if (originDebounceTimer.current) {
      clearTimeout(originDebounceTimer.current)
    }

    if (originAbortController.current) {
      originAbortController.current.abort()
    }

    if (text.length < 2) {
      setOriginSuggestions([])
      setOriginLoading(false)
      return
    }

    setOriginLoading(true)
    originAbortController.current = new AbortController()

    originDebounceTimer.current = setTimeout(async () => {
      try {
        const results = await geocode(text, originAbortController.current.signal)
        setOriginSuggestions(results)
        setOriginLoading(false)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setGeoError('Failed to search locations')
          setOriginLoading(false)
        }
      }
    }, 500)
  }

  const handleDestChange = (e) => {
    const text = e.target.value
    setDestText(text)
    setGeoError(null)

    if (destDebounceTimer.current) {
      clearTimeout(destDebounceTimer.current)
    }

    if (destAbortController.current) {
      destAbortController.current.abort()
    }

    if (text.length < 2) {
      setDestSuggestions([])
      setDestLoading(false)
      return
    }

    setDestLoading(true)
    destAbortController.current = new AbortController()

    destDebounceTimer.current = setTimeout(async () => {
      try {
        const results = await geocode(text, destAbortController.current.signal)
        setDestSuggestions(results)
        setDestLoading(false)
      } catch (err) {
        if (err.name !== 'AbortError') {
          setGeoError('Failed to search locations')
          setDestLoading(false)
        }
      }
    }, 500)
  }

  useEffect(() => {
    return () => {
      if (originAbortController.current) originAbortController.current.abort()
      if (destAbortController.current) destAbortController.current.abort()
      if (originDebounceTimer.current) clearTimeout(originDebounceTimer.current)
      if (destDebounceTimer.current) clearTimeout(destDebounceTimer.current)
    }
  }, [])

  const selectOrigin = (location) => {
    onOriginChange(location)
    setOriginText(location.displayName || location.name)
    setOriginSuggestions([])
  }

  const selectDest = (location) => {
    onDestinationChange(location)
    setDestText(location.displayName || location.name)
    setDestSuggestions([])
  }

  const handleUseMyLocation = () => {
    if ('geolocation' in navigator) {
      setOriginLoading(true)
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const location = {
            name: 'Current Location',
            displayName: 'Current Location',
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            type: 'current',
          }
          selectOrigin(location)
          setOriginLoading(false)
        },
        (error) => {
          setGeoError('Unable to get your location')
          setOriginLoading(false)
        }
      )
    } else {
      setGeoError('Geolocation is not supported')
    }
  }

  return (
    <div className="search-panel">
      {geoError && (
        <div className="geo-error">
          {geoError}
        </div>
      )}

      <div className="search-group">
        <label>From</label>
        <div className="input-with-button">
          <input
            type="text"
            placeholder="Search city, town, village, or locality"
            value={originText}
            onChange={handleOriginChange}
            disabled={loading}
          />
          <button
            type="button"
            className="location-btn"
            onClick={handleUseMyLocation}
            disabled={loading || originLoading}
            title="Use my location"
          >
            📍
          </button>
        </div>
        {originLoading && <div className="search-loading">Searching...</div>}
        {originSuggestions.length > 0 && (
          <ul className="suggestions">
            {originSuggestions.map((s, idx) => (
              <li key={`${s.latitude}-${s.longitude}-${idx}`} onClick={() => selectOrigin(s)}>
                <div className="suggestion-name">{s.name}</div>
                <div className="suggestion-type">{s.placeType}</div>
              </li>
            ))}
          </ul>
        )}
        {origin && <div className="selected">✓ {origin.displayName || origin.name}</div>}
      </div>

      <div className="search-group">
        <label>To</label>
        <input
          type="text"
          placeholder="Search city, town, village, or locality"
          value={destText}
          onChange={handleDestChange}
          disabled={loading}
        />
        {destLoading && <div className="search-loading">Searching...</div>}
        {destSuggestions.length > 0 && (
          <ul className="suggestions">
            {destSuggestions.map((s, idx) => (
              <li key={`${s.latitude}-${s.longitude}-${idx}`} onClick={() => selectDest(s)}>
                <div className="suggestion-name">{s.name}</div>
                <div className="suggestion-type">{s.placeType}</div>
              </li>
            ))}
          </ul>
        )}
        {destination && <div className="selected">✓ {destination.displayName || destination.name}</div>}
      </div>

      <button
        className="check-route-btn"
        onClick={onCheckRoute}
        disabled={!origin || !destination || loading}
      >
        {loading ? 'Checking Route...' : 'Check Route Risk'}
      </button>
    </div>
  )
}
