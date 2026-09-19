# FloodRoute Person 1 API Contract

Coordinates are always named `{latitude, longitude}` in decimal degrees. Timestamps are UTC ISO-8601.

## `GET /health`

```json
{"status":"ok","service":"floodroute-backend"}
```

## `POST /reports`

Multipart form fields:
- `latitude`: number, -90..90
- `longitude`: number, -180..180
- `condition`: `NORMAL | WATERLOGGED | FLOODED | ROAD_BLOCKED | UNKNOWN`
- `description`: 3..2000 characters
- `image`: optional JPEG/PNG/WEBP, configurable maximum (default 5 MB)

The backend stores the image privately in S3, analyzes supplied evidence through Bedrock when configured, combines evidence deterministically, and stores the structured report in DynamoDB.

Response shape:

```json
{
  "success": true,
  "data": {
    "report_id": "R...",
    "condition": "FLOODED",
    "severity": "HIGH",
    "vehicle_impact": "TWO_WHEELERS_LIKELY_AFFECTED",
    "flood_detected": true,
    "ai_confidence": 0.9,
    "ai_status": "SUCCESS"
  }
}
```

## `GET /reports/{report_id}`

Returns the stored structured report. AWS-specific DynamoDB types are never exposed.

## `POST /reports/near-route`

Request:

```json
{
  "route": [
    {"latitude": 15.8281, "longitude": 78.0373},
    {"latitude": 15.8285, "longitude": 78.0381}
  ],
  "radius_meters": 100
}
```

Response:

```json
{
  "success": true,
  "route_risk": "HIGH",
  "risk_score": 6.4,
  "affected_segments": [
    {
      "latitude": 15.8285,
      "longitude": 78.0381,
      "risk": "HIGH",
      "reports": 3,
      "latest_report_minutes_ago": 8,
      "nearest_distance_meters": 12.4
    }
  ],
  "summary": {"active_reports": 3, "high_reports": 3, "medium_reports": 0, "low_reports": 0, "unknown_reports": 0},
  "message": "Based on available reports. Conditions may change rapidly."
}
```

### Person 1 integration

```js
const response = await fetch(`${BACKEND_URL}/reports/near-route`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ route: routeCoordinates, radius_meters: 100 })
});
const data = await response.json();
// data.route_risk and data.affected_segments
```

Do not call S3, DynamoDB, or Bedrock from the frontend. The backend owns all AWS credentials and service details.

Risk wording should remain evidence-based: **LOW REPORTED RISK**, **MEDIUM REPORTED RISK**, **HIGH REPORTED RISK**, and **Based on available reports.** Never present a route as guaranteed safe.
