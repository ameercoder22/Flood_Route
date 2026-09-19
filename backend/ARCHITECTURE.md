# Architecture — FloodRoute Backend

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│ Citizen User / Mobile App                                       │
│ (Person 1 Frontend)                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTP/JSON
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ API Gateway / FastAPI                                           │
│ - POST /reports (submit text + image)                           │
│ - GET /reports (list active)                                    │
│ - GET /reports/{id} (retrieve one)                              │
│ - POST /reports/near-route (route risk)                         │
│ - GET /health (health check)                                    │
└──┬──────────────────┬──────────────────┬──────────────────┬─────┘
   │                  │                  │                  │
   │                  │                  │                  │
   ↓                  ↓                  ↓                  ↓
┌──────────┐    ┌────────────┐    ┌──────────────┐    ┌────────┐
│    S3    │    │  Bedrock   │    │  DynamoDB    │    │ Risk   │
│ (Images) │    │ (AI Parse) │    │ (Reports)    │    │ Engine │
└──────────┘    └────────────┘    └──────────────┘    └────────┘
     ↑                ↑                   ↑                  ↑
     └────────────────┴───────────────────┴──────────────────┘
                          FastAPI Service
                          (Data & Logic)
```

## AWS Services

### 1. Amazon S3 (Image Storage)

**Purpose**: Store uploaded images privately.

**Configuration**:
- Bucket name: `floodroute-reports`
- Private access (no public read)
- Object key format: `reports/{report_id}/{uuid}.{ext}`

**Operations**:
- `PutObject` — Store image
- `GetObject` — Retrieve for validation
- `GeneratePresignedUrl` — Time-limited image display URL (future)

**Validation**:
- File signature (magic bytes)
- MIME type vs. extension matching
- File size (≤5 MB default)
- Allowed types: JPEG, PNG, WEBP

### 2. Amazon Bedrock (AI Analysis)

**Purpose**: Analyze text and images to extract structured flood evidence.

**Model**: Configurable (default: `anthropic.claude-3-5-sonnet-20241022`)

**Capabilities**:
- Text analysis: Parse citizen description → evidence
- Image analysis: Detect flood/water in submitted photos
- Multimodal: Analyze text + image together

**Input**:
- System prompt (instructs model to treat input as data, not instructions)
- User prompt + optionally an image

**Output** (validated by Pydantic):
```json
{
  "flood_detected": true/false,
  "condition": "FLOODED|WATERLOGGED|NORMAL|ROAD_BLOCKED|UNKNOWN",
  "severity": "HIGH|MEDIUM|LOW|UNKNOWN",
  "vehicle_impact": "NONE_REPORTED|POSSIBLE|TWO_WHEELERS_LIKELY_AFFECTED|MOST_VEHICLES_LIKELY_AFFECTED|UNKNOWN",
  "confidence": 0.0-1.0,
  "reason": "explanation"
}
```

**Error Handling**:
- Network timeout → AIAnalysisError (graceful fallback)
- Malformed JSON → Parse error, retry parsing
- Missing fields → Validation error
- Invalid enums → Rejection + use citizen input as fallback

### 3. Amazon DynamoDB (Report Storage)

**Purpose**: Persist geotagged, timestamped reports for queries.

**Table**: `FloodReports`

**Schema**:
- Partition key: `report_id` (String)
- Sort key: None (scan + app-side filtering for MVP)

**Attributes**:
```
report_id              String (primary key)
latitude              Number
longitude             Number
condition             String (enum)
severity              String (enum)
description           String (citizen text)
vehicle_impact        String (enum)
flood_detected        Boolean
ai_confidence         Number (0-1) or null
ai_reason             String or null
image_key             String (S3 path) or null
image_uploaded        Boolean
created_at            String (ISO-8601 UTC)
updated_at            String (ISO-8601 UTC)
status                String (ACTIVE|EXPIRED|FLAGGED|INVALID)
source                String (CITIZEN|AI_ASSISTED|SYSTEM|DEMO)
ai_status             String (SUCCESS|FAILED|PARTIAL_FAILURE|NOT_REQUESTED)
```

**Operations**:
- `PutItem` — Store new report
- `GetItem` — Retrieve by report_id
- `Scan` — List all active reports (application-side filter by status=ACTIVE)

**Scaling**:
- Pay-per-request billing (MVP-friendly)
- No DynamoDB Streams (no real-time subscriptions in v1)
- Future: Global secondary index on `(status, created_at)` for geotemporal queries

### 4. FastAPI Application (Orchestration)

**Purpose**: Coordinate S3, Bedrock, DynamoDB, and risk calculations.

**Layers**:

```
API Layer (app/api/reports.py)
    ↓
Service Layer (app/services/report_service.py)
    ├─ report_service.create()
    │  ├─ Validate request (Pydantic)
    │  ├─ Upload image → S3
    │  ├─ Analyze text → Bedrock
    │  ├─ Analyze image → Bedrock
    │  ├─ Combine evidence
    │  └─ Persist → DynamoDB
    │
    └─ risk_service.calculate_route_risk()
       ├─ Retrieve active reports
       ├─ Calculate distance to route (Haversine)
       ├─ Calculate report weights (severity × freshness)
       ├─ Classify route risk
       └─ Identify affected segments
```

**Error Handling**:
- ValidationError → 422 Unprocessable Entity
- StorageError (S3) → 500 + meaningful message
- AIAnalysisError (Bedrock) → 500 + fallback to citizen input
- DatabaseError (DynamoDB) → 503 Service Unavailable
- Unhandled → 500 Internal Server Error (logged)

## Risk Calculation

### Severity Weights

```
HIGH    → 3.0
MEDIUM  → 2.0
LOW     → 1.0
UNKNOWN → 0.0
```

### Freshness Multipliers

```
0–30 min:    VERY_RECENT  → 1.0
30–120 min:  RECENT       → 0.7
2–6 hours:   AGING        → 0.4
6+ hours:    OLD          → 0.1
```

### Report Weight

```
weight = severity_weight × freshness_multiplier
```

### Route Risk Score

```
route_risk_score = sum(weight for all nearby reports within radius)

Classification:
- 0 nearby reports          → LOW_REPORTED_RISK
- 0 < score ≤ 2.0          → MEDIUM_REPORTED_RISK
- score > 2.0              → HIGH_REPORTED_RISK
```

### Affected Segments

For each route point with nearby reports:
- Calculate group weight (sum of all report weights at that point)
- Classify segment risk (same thresholds as route risk)
- Record latest report age
- Record nearest distance in meters

## Configuration

All configuration is environment-driven (no hardcoded values):

```python
AWS_REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "..."          # or use IAM role
AWS_SECRET_ACCESS_KEY = "..."      # or use IAM role
S3_BUCKET_NAME = "floodroute-reports"
DYNAMODB_TABLE_NAME = "FloodReports"
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022"

MAX_UPLOAD_SIZE_MB = 5             # bytes limit
ALLOWED_IMAGE_TYPES = "image/jpeg,image/png,image/webp"
CORS_ORIGINS = "http://localhost:5173"

DEMO_MODE = false                  # Use in-memory repo + mock AI
S3_PRESIGNED_URL_EXPIRY = 900      # 15 minutes
```

## Credential Resolution

**AWS SDK Credential Chain** (no explicit credentials in code):

1. Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
2. AWS CLI profile (~/.aws/credentials, ~/.aws/config)
3. IAM role (if running on EC2, Lambda, ECS, etc.)
4. Container credentials (if running in ECS with a task role)

Production deployments use IAM roles; development uses CLI profiles or environment variables.

## Testing Strategy

**Unit Tests** (mocked):
- Bedrock parsing (valid/invalid/malformed JSON)
- Risk calculation (freshness, severity, distance)
- Validation (coordinates, description)
- Report service (with in-memory repo)

**Integration Tests** (FastAPI test client):
- API endpoints (create, get, list, near-route)
- Error responses (404, 422, 500)
- Route risk with nearby reports

**Environment**:
- No real AWS credentials required
- In-memory repository + mock AI provider
- SQLite for future schema testing (not used yet)

## Deployment

### Local Development

```bash
DEMO_MODE=true uvicorn app.main:app --reload
```

Uses in-memory storage + mock Bedrock.

### Production (AWS)

**Option 1: EC2 + FastAPI**
```bash
# On EC2 instance with IAM role
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Option 2: Lambda + API Gateway** (not implemented yet)
```
API Gateway → Lambda (FastAPI via Mangum) → S3/Bedrock/DynamoDB
```

**Option 3: ECS + Fargate** (not implemented yet)
```
API Gateway → ALB → ECS Task (Docker container) → S3/Bedrock/DynamoDB
```

## Security

**Data in Transit**:
- HTTPS enforced (API Gateway / Lambda)
- S3 presigned URLs are time-limited (15 min default)

**Data at Rest**:
- S3 bucket is private (no public read)
- DynamoDB is in private VPC (no direct internet access)
- Bedrock model calls are within AWS (no external model API calls)

**AI Safety**:
- System prompt treats user input as DATA, not instructions
- No `eval()` or code execution on AI output
- JSON parsing is strict (Pydantic validation)
- Markdown fence stripping is dumb (doesn't execute)

**Access Control**:
- IAM policy limits to specific S3, DynamoDB, Bedrock operations
- No `AdministratorAccess`
- CORS restricted to frontend origin(s)

## Monitoring & Logging

**CloudWatch Logs** (automatic):
```
/aws/lambda/floodroute-backend
/aws/ecs/floodroute-backend
```

**Application Logs** (structured JSON):
```
{
  "timestamp": "2026-09-18T15:07:18Z",
  "level": "ERROR",
  "logger": "app.services.bedrock_service",
  "message": "Bedrock analysis failed",
  "exception": "ConnectTimeoutError"
}
```

**Metrics** (CloudWatch):
- Bedrock invocation count / latency
- DynamoDB write/read capacity
- S3 upload volume / errors
- API latency by endpoint

## Limitations & Future Work

**Current MVP**:
- ✓ Text + image analysis
- ✓ Deterministic heuristic risk
- ✓ Single-region deployment
- ✓ No authentication (for hackathon)
- ✓ No real-time subscriptions

**Future Enhancements**:
- [ ] User authentication / authorization
- [ ] Geospatial index (DynamoDB GSI or PostGIS)
- [ ] Real-time updates (WebSocket or SSE)
- [ ] Report verification workflow (upvotes/downvotes)
- [ ] Multi-region replication
- [ ] Historical trend analysis
- [ ] Integration with official weather / flood alerts
- [ ] Mobile app offline-first sync
