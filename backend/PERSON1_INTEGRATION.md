# PERSON1_INTEGRATION.md — Frontend Integration Guide

## Overview

Person 1 (the frontend/mobile app) will integrate with Person 2's backend to:

1. Display flood risk along a user's planned route
2. Show which segments are affected
3. Recommend alternative routes with lower reported risk
4. Allow users to submit reports with optional photos

## API Endpoint: `POST /reports/near-route`

This is the PRIMARY integration point for Person 1.

### Request

```json
{
  "route": [
    {"latitude": 15.8281, "longitude": 78.0373},
    {"latitude": 15.8285, "longitude": 78.0381},
    {"latitude": 15.8290, "longitude": 78.0390}
  ],
  "radius_meters": 100
}
```

**Fields**:
- `route` (array of objects, required)
  - Must contain at least 2 points
  - Maximum 5000 points (practical limit for a single route)
  - Each point must have `latitude` (-90 to 90) and `longitude` (-180 to 180)
  - Coordinates are in decimal degrees (WGS84)

- `radius_meters` (number, optional, default 100)
  - Search radius around each route point for reports
  - Minimum 1 meter
  - Maximum 5000 meters

### Response (Success)

```json
{
  "success": true,
  "route_risk": "HIGH_REPORTED_RISK",
  "risk_score": 6.4,
  "affected_segments": [
    {
      "latitude": 15.8285,
      "longitude": 78.0381,
      "risk": "HIGH",
      "reports": 3,
      "latest_report_minutes_ago": 8,
      "nearest_distance_meters": 12.4
    },
    {
      "latitude": 15.8290,
      "longitude": 78.0390,
      "risk": "MEDIUM",
      "reports": 1,
      "latest_report_minutes_ago": 45,
      "nearest_distance_meters": 87.2
    }
  ],
  "summary": {
    "active_reports": 4,
    "high_reports": 3,
    "medium_reports": 1,
    "low_reports": 0,
    "unknown_reports": 0
  },
  "message": "Based on available reports. Conditions may change rapidly."
}
```

**Fields**:
- `route_risk`: One of `LOW_REPORTED_RISK`, `MEDIUM_REPORTED_RISK`, `HIGH_REPORTED_RISK`
  - Computed from all nearby reports and their freshness
  - NOT a guarantee of safety or danger
  - Based on reported conditions only

- `risk_score`: Numeric aggregate (sum of report weights)
  - Higher = more reported risk
  - Useful for sorting alternative routes

- `affected_segments`: Array of route points with nearby reports
  - `risk`: Severity level at that segment
  - `reports`: Count of nearby reports at that segment
  - `latest_report_minutes_ago`: Age of most recent report
  - `nearest_distance_meters`: Closest report distance in meters

- `summary`: Counts of reports by severity
  - Useful for display (e.g., "3 HIGH severity reports")

### Response (Error)

```json
{
  "success": false,
  "error": {
    "code": "RISK_CALCULATION_FAILED",
    "message": "Route risk could not be calculated."
  }
}
```

**Common error codes**:
- `VALIDATION_ERROR` (422): Invalid coordinates or route
- `DATABASE_UNAVAILABLE` (503): Backend cannot reach DynamoDB
- `RISK_CALCULATION_FAILED` (500): Unexpected error during calculation

## JavaScript Integration Example

### Basic Route Risk Check

```javascript
const API_URL = "https://your-backend.example.com"; // or http://localhost:8000 for dev

async function checkRouteRisk(routeCoordinates, radiusMeters = 100) {
  try {
    const response = await fetch(
      `${API_URL}/reports/near-route`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          route: routeCoordinates,
          radius_meters: radiusMeters
        })
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      return {
        routeRisk: data.route_risk,
        riskScore: data.risk_score,
        affectedSegments: data.affected_segments,
        summary: data.summary
      };
    } else {
      throw new Error(data.error.message);
    }
  } catch (error) {
    console.error("Failed to check route risk:", error);
    return null;
  }
}
```

### Display Route Risk

```javascript
function displayRouteRisk(risk) {
  const riskColors = {
    "HIGH_REPORTED_RISK": "#cc0000",     // Red
    "MEDIUM_REPORTED_RISK": "#ff9900",   // Orange
    "LOW_REPORTED_RISK": "#00aa00"       // Green
  };

  const riskLabels = {
    "HIGH_REPORTED_RISK": "High Reported Risk",
    "MEDIUM_REPORTED_RISK": "Medium Reported Risk",
    "LOW_REPORTED_RISK": "Low Reported Risk"
  };

  console.log(`Route Risk: ${riskLabels[risk.routeRisk]}`);
  console.log(`Reports: ${risk.summary.active_reports} total`);
  console.log(`  - HIGH: ${risk.summary.high_reports}`);
  console.log(`  - MEDIUM: ${risk.summary.medium_reports}`);
  console.log(`  - LOW: ${risk.summary.low_reports}`);

  // Highlight affected segments on map
  risk.affectedSegments.forEach((segment, index) => {
    console.log(`Segment ${index}: ${segment.latitude}, ${segment.longitude}`);
    console.log(`  Risk: ${segment.risk}`);
    console.log(`  Reports: ${segment.reports}`);
    console.log(`  Latest: ${segment.latest_report_minutes_ago} minutes ago`);
    console.log(`  Distance: ${segment.nearest_distance_meters}m`);
  });
}
```

### Full Flow Example

```javascript
// 1. User enters origin and destination
const origin = { latitude: 15.8281, longitude: 78.0373 };
const destination = { latitude: 15.8300, longitude: 78.0400 };

// 2. Get route coordinates from map provider (Google Maps, Mapbox, etc.)
const routeCoordinates = await getRouteFromMapProvider(origin, destination);
// routeCoordinates = [
//   { latitude: 15.8281, longitude: 78.0373 },
//   { latitude: 15.8285, longitude: 78.0381 },
//   { latitude: 15.8290, longitude: 78.0390 },
//   ...
// ]

// 3. Check flood risk
const riskData = await checkRouteRisk(routeCoordinates, 100);

// 4. Display to user
if (riskData) {
  displayRouteRisk(riskData);

  // 5. Highlight affected segments on map
  riskData.affectedSegments.forEach(segment => {
    addMarkerToMap(segment.latitude, segment.longitude, segment.risk);
  });

  // 6. If high risk, suggest alternative route
  if (riskData.routeRisk === "HIGH_REPORTED_RISK") {
    suggestAlternativeRoute(origin, destination);
  }
} else {
  console.log("Could not check route risk. Continue with caution.");
}
```

## Additional Endpoints

### Submit a Report

Users can submit flood reports through the frontend.

**Endpoint**: `POST /reports`

**Request** (multipart form):
```
latitude: 15.8281
longitude: 78.0373
condition: FLOODED | WATERLOGGED | NORMAL | ROAD_BLOCKED | UNKNOWN
description: "Water is covering the road and motorcycles cannot pass."
image: (optional) JPEG, PNG, or WEBP file
```

**Response**:
```json
{
  "success": true,
  "data": {
    "report_id": "R1a2b3c4d5e6f",
    "latitude": 15.8281,
    "longitude": 78.0373,
    "condition": "FLOODED",
    "severity": "HIGH",
    "vehicle_impact": "TWO_WHEELERS_LIKELY_AFFECTED",
    "flood_detected": true,
    "ai_confidence": 0.95,
    "ai_status": "SUCCESS",
    "created_at": "2026-09-18T15:07:18Z"
  }
}
```

**JavaScript Example**:

```javascript
async function submitFloodReport(latitude, longitude, condition, description, imageFile = null) {
  const formData = new FormData();
  formData.append("latitude", latitude);
  formData.append("longitude", longitude);
  formData.append("condition", condition);
  formData.append("description", description);

  if (imageFile) {
    formData.append("image", imageFile);
  }

  try {
    const response = await fetch(
      `${API_URL}/reports`,
      {
        method: "POST",
        body: formData
        // Note: Do NOT set Content-Type header — browser will set it correctly with boundary
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      console.log("Report submitted:", data.data.report_id);
      return data.data;
    } else {
      throw new Error(data.error.message);
    }
  } catch (error) {
    console.error("Failed to submit report:", error);
    return null;
  }
}
```

### List Reports

Retrieve all active flood reports (useful for map display, debugging).

**Endpoint**: `GET /reports?limit=100`

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "report_id": "R1a2b3c4d5e6f",
      "latitude": 15.8281,
      "longitude": 78.0373,
      "condition": "FLOODED",
      "severity": "HIGH",
      ...
    },
    ...
  ]
}
```

**JavaScript Example**:

```javascript
async function listReports(limit = 100) {
  try {
    const response = await fetch(
      `${API_URL}/reports?limit=${limit}`,
      { method: "GET" }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.success ? data.data : [];
  } catch (error) {
    console.error("Failed to list reports:", error);
    return [];
  }
}
```

## Coordinate System

**Latitude/Longitude Format**:
- Decimal degrees (WGS84)
- Latitude: -90 (South Pole) to +90 (North Pole)
- Longitude: -180 (west) to +180 (east)

**Example (Kurnool, India)**:
```json
{
  "latitude": 15.8281,
  "longitude": 78.0373
}
```

## Error Handling

Always check `success` field before accessing `data`:

```javascript
async function safeApiCall(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_URL}${endpoint}`, options);
    const data = await response.json();

    if (!response.ok || !data.success) {
      console.error("API Error:", data.error || response.statusText);
      return null;
    }

    return data.data;
  } catch (error) {
    console.error("Network error:", error);
    return null;
  }
}
```

## CORS Configuration

The backend allows requests from configured origins (default: `http://localhost:5173`).

Update `CORS_ORIGINS` environment variable to allow your frontend domain:

```
CORS_ORIGINS=http://localhost:5173,https://your-frontend.example.com
```

## Performance Notes

- Route risk calculation scans all active reports (typical: <1s for <10k reports)
- Recommended radius: 100–500 meters
- Avoid routes with >5000 points (very long routes)
- Cache results locally if the route hasn't changed
- Rate limit: No explicit limit (configure at API Gateway if needed)

## Important Disclaimers

Display clearly to users:

> **FloodRoute does not claim a route is guaranteed safe.** It surfaces recent reported flood conditions to support better-informed route decisions. Conditions may change rapidly. Always check official emergency alerts and exercise caution.

Never represent:
- "Safe route" (reports don't exist doesn't mean no flood risk)
- "Unsafe route" (a single report doesn't guarantee danger)
- "Exact flood prediction" (AI confidence is classification confidence, not probability)
- "Official emergency alert" (this is citizen-reported evidence)
