FloodRoute --- Risk-Aware Navigation During Urban Flooding

FloodRoute is an AI-assisted route risk assessment system for travel
during urban flooding.

It combines recent citizen flood reports, NASA VIIRS satellite
flood evidence, and a deterministic risk engine to assess reported
flood risk around a route.

Important: Reported risk is based on available recent reports and
satellite evidence near the tested route. It does not guarantee
current road conditions or that a road is safe or unsafe.

What FloodRoute Does

Users can:

Enter an origin and destination.

Geocode locations using OpenStreetMap Nominatim.

Generate a route using OSRM.

Check reported flood risk around the route.

View affected route segments and recent reports.

Submit a flood report with location, description, road condition,
and optional image.

Use AI-assisted analysis to interpret citizen report text/images.

Combine citizen evidence with NASA flood evidence.

View a unified route-risk assessment.

Risk levels:

LOW_REPORTED_RISK

MEDIUM_REPORTED_RISK

HIGH_REPORTED_RISK

The final risk is produced by a deterministic evidence aggregation layer
rather than allowing an LLM to directly decide whether a road is safe.

Architecture

React + Leaflet Frontend
          |
          v
      FastAPI API
          |
   +------+------+------+
   |      |      |      |
   v      v      v      v
Bedrock  S3  DynamoDB  NASA
   |      |      |      |
   +------+------+------+
          |
          v
Deterministic Risk Engine
          |
          v
Unified Route Risk

AWS Usage

Amazon Bedrock

Used for AI-assisted analysis of citizen flood reports and uploaded
images.

The backend validates model output against predefined schemas and enums.
AI failures are handled gracefully and do not directly determine the
final route risk.

Amazon S3

Used for private storage of uploaded report images.

Example key:

reports/{report_id}/{uuid}.{extension}

Uploads are validated for file type, extension, size, and content
signature.

Amazon DynamoDB

Used for persistent flood report storage.

The repository supports creating, retrieving, and listing active
reports. Route proximity is calculated in application code using
Haversine distance.

NASA Flood Evidence

FloodRoute integrates NASA's VIIRS Global Flood Product
(Near-Real-Time) using:

VCDWD_L3_NRT

NASA evidence is treated as area-level satellite evidence.

The application intentionally says:

NASA flood evidence overlaps X% of the tested route.

It does not claim that X% of a particular road is flooded.

Risk Engine

Citizen severity weights:

HIGH     = 3
MEDIUM   = 2
LOW      = 1
UNKNOWN  = 0

Freshness weights:

0–30 minutes    = 1.0
30–120 minutes  = 0.7
2–6 hours       = 0.4
6+ hours        = 0.1

Default route proximity:

100 meters

Haversine distance is used instead of raw latitude/longitude
subtraction.

NASA overlap thresholds:

0%              -> NONE
>0% to <20%     -> LOW
20% to <50%     -> MEDIUM
>=50%           -> HIGH

Citizen and NASA evidence are combined deterministically.

Core API

GET  /health
POST /reports
GET  /reports
GET  /reports/{report_id}
POST /reports/near-route
GET  /flood
POST /flood/analyze-route

Example /reports/near-route request:

{
  "route": [
    {"latitude": 15.8281, "longitude": 78.0373},
    {"latitude": 15.8285, "longitude": 78.0381}
  ],
  "radius_meters": 100
}

Testing

The backend includes tests for API behavior, risk calculation,
repositories, S3, Bedrock, NASA integration, and unified citizen + NASA
evidence aggregation.

Current validation:

58 tests passed

Run:

cd backend
python -m pytest tests -q

Frontend production build:

cd frontend
npm run build

Local Development

Backend

Requires Python 3.11.

cd backend
python -m venv .venv

Windows PowerShell:

.\.venv\Scripts\Activate.ps1

Install:

pip install -r requirements.txt

For a local demo:

DEMO_MODE=true
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=FloodReports

Run:

python -m uvicorn app.main:app --reload --port 8000

Swagger:

http://127.0.0.1:8000/docs

Frontend

cd frontend
npm install
npm run dev

Production build:

npm run build

Environment Variables

Example backend configuration:

DEMO_MODE=true
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=FloodReports
S3_BUCKET_NAME=
BEDROCK_MODEL_ID=
CORS_ORIGINS=
NASA_EARTHDATA_USERNAME=
NASA_EARTHDATA_PASSWORD=

Never commit secrets.

Do not commit:

.env
.venv/
node_modules/
__pycache__/

AWS credentials should use environment configuration, IAM roles, or
boto3's standard credential chain.

Project Structure

Flood_Route/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   ├── scripts/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── services/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── .gitignore
└── README.md

Responsible AI

FloodRoute uses generative AI as an assistive component rather than the
sole decision-maker.

Safeguards include:

Schema validation of AI output.

Enum and confidence validation.

Citizen input treated as untrusted.

Graceful AI failure handling.

Deterministic risk aggregation.

Clear separation between satellite evidence and road-level claims.

No guarantee that a road is safe or unsafe.

Limitations

FloodRoute is a decision-support prototype, not an emergency-response
system.

Citizen reports can be incomplete, inaccurate, or outdated.

Satellite observations have spatial and temporal limitations.

Routing data may not reflect temporary closures.

NASA evidence does not confirm the condition of a specific road.

The system does not guarantee safe travel.

Free deployments may experience cold starts.

Production-scale geospatial querying would require additional
optimization.

Future Improvements

More robust geospatial indexing.

Additional satellite and weather sources.

More route alternatives.

Automated report verification.

Municipal and authoritative flood feeds.

Push notifications.

Larger-scale cloud deployment.

Field validation with real flood events.

Hackathon Summary

Project: FloodRoute
Category: AI / Cloud / Disaster Management
Frontend: React, Vite, Leaflet
Backend: FastAPI, Python
AI: Amazon Bedrock
Storage: Amazon S3, DynamoDB
Satellite evidence: NASA VIIRS Global Flood Product
Geocoding: OpenStreetMap Nominatim
Routing: OSRM

Core Differentiator

FloodRoute does not ask an LLM to decide whether a road is safe. It
combines recent citizen evidence and satellite flood evidence through
a deterministic risk engine to provide transparent, evidence-based
route risk information.

Team

FloodRoute was developed as a two-person hackathon project combining
frontend/map development, FastAPI backend engineering, AI-assisted
report analysis, AWS architecture, satellite flood evidence,
deterministic risk modeling, and automated testing.