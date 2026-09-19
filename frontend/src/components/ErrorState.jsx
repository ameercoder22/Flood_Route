export default function ErrorState({ error, onDismiss }) {
  return (
    <div className="error-state">
      <div className="error-content">
        <span className="error-icon">⚠</span>
        <p>{error}</p>
        <button onClick={onDismiss}>Dismiss</button>
      </div>
    </div>
  )
}
