# FloodRoute Frontend

React + Vite frontend for the FloodRoute flood-risk assessment system.

## Setup

```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173`.

## Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Set `VITE_API_BASE_URL` to your backend URL (default: `http://localhost:8000`).

## Build

```bash
npm run build
```

Output goes to `dist/`.

## Architecture

- **React 18** — Component-based UI
- **Vite** — Fast dev server and build
- **Leaflet + React-Leaflet** — Map display
- **CSS** — Styled components (not using CSS-in-JS library for simplicity)

## Components

- **SearchPanel** — Origin/destination input with autocomplete
- **MapView** — Leaflet map with route, markers, affected segments
- **RouteRiskCard** — Route risk assessment display
- **ReportForm** — Citizen report submission
- **ReportList** — Nearby reports display
- **Header** — Application header
- **LoadingState** — Loading indicator
- **ErrorState** — Error message display

## Services

- **api.js** — Backend API client
- **geo.js** — Geospatial utilities (route normalization, formatting)

## API Integration

All API calls go through `services/api.js`. The backend is expected to be running on `http://localhost:8000`.

## Demo Flow

1. Enter origin and destination
2. Click "Check Route Risk"
3. View route on map
4. See affected segments and nearby reports
5. Click "Report Flooded Road" to submit a report
6. Watch route risk update in real-time

## Limitations

- Routing is simplified (point-to-point line) — a real app would use OSRM/HERE/Google Maps
- Geocoding is mock (Kurnool, Hyderabad, etc.) — a real app would use Nominatim or similar
- No user authentication
- No report verification system
- No alternative route comparison (but API supports it)

## Future Enhancements

- Real routing provider integration
- Real geocoding (Nominatim)
- User authentication and history
- Report image display
- Report filtering and sorting
- Route waypoint support
- Offline mode (service workers)
- Progressive Web App (PWA)
