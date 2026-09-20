# Implementation Plan: Backend Flood-Aware Routing Upgrade

## Context
Upgrade the FloodRoute backend to support real geospatial flood-aware routing using NASA data, replacing mock/demo processes with validated analysis.

## Critical Files to Modify/Create
- `backend/requirements.txt`: Add `shapely`, `geopandas`, `rasterio` (or necessary geospatial libs).
- `backend/app/services/nasa_flood_service.py` (NEW): Logic to fetch/process NASA flood data.
- `backend/app/api/flood.py` (NEW): New flood-specific endpoints (`/api/flood`, `/api/analyze-route`).
- `backend/app/main.py`: Register new flood router and setup configuration.

## Implementation Steps

### 1. Dependencies and Environment
- Update `backend/requirements.txt` with geospatial libraries.
- Added necessary environment variables to `app/config.py` (e.g., `NASA_API_KEY`).

### 2. NASA Flood Service Layer
- Implement `NASAFloodService` in `backend/app/services/nasa_flood_service.py` to:
    - Retrieve near-real-time flood data (e.g., VIIRS/JPSS).
    - Expose processed geometry (GeoJSON).
    - Implement caching (in-memory or file-based).

### 3. Spatial Analysis Engine
- Add logic in `NASAFloodService` or a separate `analysis` service to:
    - Perform spatial intersection between route `LineString` and flood `Polygon`s.
    - Calculate exposure percentages correctly using geographic projections (`GeoDataFrame`).

### 4. API Endpoints
- Implement `GET /api/flood` for retrieving flood extent geometry (GeoJSON).
- Implement `POST /api/analyze-route` for route risk analysis.
- Ensure all logic is behind `DEMO_MODE=false` flag for production.

### 5. Integration
- Register new router in `backend/app/main.py`.
- Ensure CORS configuration supports frontend communications.

## Verification Plan
1. **Tool Tests**: Unit test spatial intersection logic in `backend/tests/test_geo.py`.
2. **Endpoint Test**: Verify `/api/flood` returns valid GeoJSON.
3. **End-to-End Test**:
    - Submit a route POST request.
    - Verify backend calculates intersection, exposure, and classification.
    - Check response structure matches requirements.
4. **Data Integrity Test**: Ensure no demo/fake data is returned when `DEMO_MODE=false`.
5. **Secrets Test**: Verify API keys are retrieved from environment not hardcoded.
