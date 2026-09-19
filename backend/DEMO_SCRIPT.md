# DEMO_SCRIPT.md — 3-Minute Live Demo

## Setup (Before Demo)

1. Backend running locally:
   ```bash
   cd backend
   source .venv/bin/activate  # or .venv\Scripts\Activate.ps1
   DEMO_MODE=true uvicorn app.main:app --reload --port 8000
   ```

2. Frontend running on `http://localhost:5173` (or your dev port)

3. API docs available at `http://localhost:8000/docs`

## Demo Flow (3 Minutes)

### 0:00 – Problem Statement (20 seconds)

> "In India, monsoons cause severe flooding. Commuters don't know which routes are safe. Emergency alerts are slow. We're building FloodRoute — a real-time citizen-reported flood-risk API."

**Show**: Map view with major roads around Kurnool.

### 0:20 – Scenario: Submit a Report (40 seconds)

**Narrator**: "A citizen notices water on the road. They open FloodRoute and submit a report."

**Demo**:
1. Open the report form in the frontend
2. Enter coordinates: latitude `15.8281`, longitude `78.0373`
3. Select condition: `FLOODED`
4. Type description: `"Water is covering the road and motorcycles are struggling to pass."`
5. (Optional) Upload a test image from `scripts/test_images/` if you prepared one
6. Click Submit

**Show the response**:
```json
{
  "report_id": "R1a2b3c4d5e6f",
  "condition": "FLOODED",
  "severity": "HIGH",
  "ai_confidence": 0.95,
  "ai_status": "SUCCESS"
}
```

> "In DEMO mode, Bedrock is mocked — but in production, it would analyze the text and image to extract structured evidence. It returns severity, vehicle impact, and confidence."

### 1:00 – Bedrock AI Analysis (25 seconds)

**Narrator**: "Behind the scenes, our Bedrock integration analyzes both text and images."

**Show terminal/logs**:
```
Text Analysis: FLOODED condition, HIGH severity, TWO_WHEELERS_LIKELY_AFFECTED
Image Analysis: (mock in DEMO mode) UNKNOWN
Final Analysis: Combines evidence → HIGH severity confidence 0.95
```

> "The AI never uses eval() or trusts the model output directly. All responses are validated by Pydantic. If the model returns malformed JSON, we gracefully fall back to the citizen-selected condition."

### 1:25 – DynamoDB Persistence (15 seconds)

**Narrator**: "The report is now stored in DynamoDB with its location, time, and AI confidence."

**Show in backend logs**:
```
DynamoDB: PutItem FloodReports table, report_id=R1a2b3c4d5e6f
```

> "S3 would store the image privately if one was uploaded. Presigned URLs are time-limited."

### 1:40 – Route Risk Analysis (20 seconds)

**Narrator**: "Now a different user plans a route. They ask: is this route safe?"

**Demo**:
1. Open the route planner in the frontend
2. Enter origin: `15.8281, 78.0373`
3. Enter destination: `15.8300, 78.0400`
4. (Map API calculates route points)
5. Frontend calls `POST /reports/near-route`

**Show the request**:
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

### 1:50 – Route Risk Response (15 seconds)

**Show the response**:
```json
{
  "route_risk": "HIGH_REPORTED_RISK",
  "risk_score": 3.0,
  "affected_segments": [
    {
      "latitude": 15.8285,
      "longitude": 78.0381,
      "risk": "HIGH",
      "reports": 1,
      "latest_report_minutes_ago": 8,
      "nearest_distance_meters": 12.4
    }
  ],
  "summary": {
    "active_reports": 1,
    "high_reports": 1,
    "medium_reports": 0,
    "low_reports": 0,
    "unknown_reports": 0
  }
}
```

> "The backend uses Haversine distance to find reports within 100 meters of the route. Then it calculates freshness (8 minutes old), severity (HIGH = 3.0), and classifies the route risk."

### 2:05 – Map Visualization (20 seconds)

**Demo**:
1. Frontend highlights the affected segment on the map (orange/red color)
2. Show marker: "HIGH REPORTED RISK — 1 report — 8 min ago"
3. Display route risk badge: "⚠️ HIGH REPORTED RISK"

> "The frontend can now suggest an alternative route or recommend caution. FloodRoute doesn't guarantee safety — it surfaces reported conditions so users can make informed decisions."

### 2:25 – Architecture Overview (20 seconds)

**Show diagram** (on screen or whiteboard):

```
Citizen Report
     ↓
   S3 (image)
   Bedrock (analysis)
   DynamoDB (storage)
     ↓
Route Risk Engine
(Haversine, freshness, severity)
     ↓
Frontend Map
```

> "Three AWS services power this:"
> - **S3**: Stores images privately
> - **Bedrock**: Analyzes evidence (no hallucinations, strict validation)
> - **DynamoDB**: Persists reports for queries

### 2:40 – Important Disclaimer (15 seconds)

**Read this aloud carefully**:

> "**FloodRoute does NOT claim a route is safe.** It surfaces recent reported flood conditions. Conditions change rapidly. Always check official emergency alerts. This is citizen-reported evidence, not an authoritative flood prediction or emergency system."

**Show the disclaimer on screen** (should appear on every route result).

### 2:55 – End

> "Thank you. Questions?"

---

## Key Talking Points

### If asked about AI:
- "We use Bedrock's Converse API. The system prompt treats user input as DATA, not instructions — it can't be jailbroken."
- "All output is validated with Pydantic. If malformed, we reject it."
- "In DEMO mode, the provider is a deterministic mock — in production, it's real Bedrock."

### If asked about scale:
- "For MVP, we scan active reports + apply Haversine distance in the backend. No geospatial indexing yet — but DynamoDB can handle thousands of reports."
- "Bedrock is pay-per-inference. At scale, we could cache or batch."

### If asked about security:
- "S3 bucket is private. Images are stored with UUIDs, not user IDs."
- "AWS credentials use the standard SDK chain — no hardcoded secrets."
- "CORS is configured to only allow the frontend domain."

### If asked about errors:
- "Network timeout? We return HTTP 503 and log it. User sees 'Bedrock temporarily unavailable.'"
- "Invalid image? File signature validation catches it before S3."
- "Route too long? We validate max 5000 points."

---

## Demo Troubleshooting

### "DEMO_MODE is not set"
```bash
DEMO_MODE=true uvicorn app.main:app --reload --port 8000
```

### "Port 8000 is in use"
```bash
lsof -i :8000  # Find process
kill -9 <pid>  # Kill it
# Or use a different port:
uvicorn app.main:app --reload --port 8001
```

### "No reports showing up"
- Check that you submitted a report in the previous step
- Verify the coordinates are near your route (within radius_meters)
- Try `GET http://localhost:8000/reports` to list all reports

### "Bedrock returns 'unavailable'"
- Confirm DEMO_MODE=true (if not set, the app tries real Bedrock)
- Check that the mock provider is loaded: `app/services/bedrock_service.py::MockProvider`

### "CORS error in frontend"
- Ensure backend is running with `CORS_ORIGINS=http://localhost:5173` (or your port)
- Check browser console for exact CORS error

---

## Demo Variations

### Quick (1 minute) — Skip architecture
- Skip the diagram at 2:25
- Focus on the user journey (report → risk → map)

### Extended (5 minutes) — Add code walkthrough
- Show `app/services/bedrock_service.py` — JSON parsing safety
- Show `app/services/risk_service.py` — Haversine + freshness logic
- Explain error handling

### Production Pitch (3 minutes, no code) — Emphasize AWS
- Same flow, but emphasize:
  - "S3 can store unlimited images"
  - "DynamoDB scales to millions of reports"
  - "Bedrock is multi-modal (text + image)"
  - "No credit card charges; we bill per-inference"

---

## Pre-Demo Checklist

- [ ] Backend running on http://localhost:8000
- [ ] Frontend running on http://localhost:5173 (or configured)
- [ ] DEMO_MODE=true in environment
- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] One test report submitted (or demo script pre-seeded in DEMO_MODE)
- [ ] Map displays route points clearly
- [ ] Disclaimer is visible on route results
- [ ] Network connection is stable (no timeout errors mid-demo)

---

## Optional: Pre-Seed Demo Data

In production, run:
```bash
python scripts/seed_demo_reports.py
```

This creates 6 DEMO-labeled reports around Kurnool with various severities and ages. (Not used in DEMO_MODE, but useful for production dry-run.)
