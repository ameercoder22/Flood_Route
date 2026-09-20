import { useState, useEffect } from 'react'
import './ReportForm.css'

const CONDITIONS = ['NORMAL', 'WATERLOGGED', 'FLOODED', 'ROAD_BLOCKED', 'UNKNOWN']
const VEHICLES = ['NONE_REPORTED', 'POSSIBLE', 'TWO_WHEELERS_LIKELY_AFFECTED', 'MOST_VEHICLES_LIKELY_AFFECTED']

export default function ReportForm({ selectedLocation, onSubmit, loading }) {
  const [latitude, setLatitude] = useState(selectedLocation?.latitude || '')
  const [longitude, setLongitude] = useState(selectedLocation?.longitude || '')

  useEffect(() => {
    if (selectedLocation) {
        setLatitude(selectedLocation.latitude)
        setLongitude(selectedLocation.longitude)
    }
  }, [selectedLocation])

  const [description, setDescription] = useState('')
  const [condition, setCondition] = useState('FLOODED')
  const [image, setImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [error, setError] = useState(null)

  const handleImageChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image must be less than 5 MB')
        return
      }
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        setError('Only JPEG, PNG, and WebP images are supported')
        return
      }
      setImage(file)
      const reader = new FileReader()
      reader.onload = (evt) => setImagePreview(evt.target.result)
      reader.readAsDataURL(file)
      setError(null)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!latitude || !longitude) {
      setError('Location is required')
      return
    }

    if (!description || description.length < 3) {
      setError('Description must be at least 3 characters')
      return
    }

    const formData = new FormData()
    formData.append('latitude', parseFloat(latitude))
    formData.append('longitude', parseFloat(longitude))
    formData.append('description', description)
    formData.append('condition', condition)
    if (image) {
      formData.append('image', image)
    }

    try {
      await onSubmit(formData)
      setDescription('')
      setImage(null)
      setImagePreview(null)
    } catch (err) {
      setError(err.message || 'Failed to submit report')
    }
  }

  return (
    <form className="report-form" onSubmit={handleSubmit}>
      <h3>Report Flooded Road</h3>

      <div className="form-group">
        <label>Location</label>
        <div className="location-display">
          {latitude && longitude ? (
            <div>
              <span>{parseFloat(latitude).toFixed(4)}, {parseFloat(longitude).toFixed(4)}</span>
              <button
                type="button"
                className="change-location-btn"
                onClick={() => {
                  setLatitude('')
                  setLongitude('')
                }}
              >
                Change
              </button>
            </div>
          ) : (
            <span className="empty">👉 Click on the map to select location</span>
          )}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="description">What did you observe?</label>
        <textarea
          id="description"
          placeholder="Describe the water level, affected vehicles, road conditions..."
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          minLength={3}
          maxLength={2000}
          required
        />
        <small>{description.length}/2000</small>
      </div>

      <div className="form-group">
        <label htmlFor="condition">Road Condition</label>
        <select
          id="condition"
          value={condition}
          onChange={(e) => setCondition(e.target.value)}
        >
          {CONDITIONS.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="image">Add Photo (optional)</label>
        {imagePreview && (
          <div className="image-preview">
            <img src={imagePreview} alt="Preview" />
            <button
              type="button"
              className="remove-image"
              onClick={() => {
                setImage(null)
                setImagePreview(null)
              }}
            >
              Remove
            </button>
          </div>
        )}
        {!imagePreview && (
          <input
            id="image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={handleImageChange}
            disabled={loading}
          />
        )}
        <small>JPEG, PNG, or WebP (max 5 MB)</small>
      </div>

      {error && <div className="error-message">{error}</div>}

      <button
        type="submit"
        className="submit-btn"
        disabled={loading || !description || !latitude || !longitude}
      >
        {loading ? 'Submitting...' : 'Submit Report'}
      </button>
    </form>
  )
}
