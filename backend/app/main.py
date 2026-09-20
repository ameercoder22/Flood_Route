from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.health import router as health_router
from app.api.reports import router as reports_router
from app.api.flood import router as flood_router
from app.config import get_settings
from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact
from app.repositories.report_repository import DynamoDBReportRepository, InMemoryReportRepository
from app.services.bedrock_service import BedrockService, MockProvider
from app.services.report_service import ReportService
from app.services.s3_service import S3Service

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()

logger.info(f"Application startup: DEMO_MODE={settings.demo_mode}, AWS_REGION={settings.aws_region}, DYNAMODB_TABLE={settings.dynamodb_table_name}")


def seed_in_memory_demo_reports(repo: InMemoryReportRepository) -> None:
    now = datetime.now(timezone.utc)
    demo_reports = [
        StoredReport(
            report_id="DEMO-H1", latitude=15.8285, longitude=78.0381, condition=Condition.FLOODED,
            severity=Severity.HIGH, description="DEMO DATA — 2.5 ft water covering road near Kurnool junction. Two-wheelers stalled.",
            vehicle_impact=VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED, flood_detected=True,
            ai_confidence=0.92, ai_reason="DEMO DATA — High water depth reported.",
            image_uploaded=False, created_at=now - timedelta(minutes=8), updated_at=now - timedelta(minutes=8),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
        StoredReport(
            report_id="DEMO-H2", latitude=15.8287, longitude=78.0383, condition=Condition.FLOODED,
            severity=Severity.HIGH, description="DEMO DATA — Heavy overflow across roadway near Kurnool bypass.",
            vehicle_impact=VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED, flood_detected=True,
            ai_confidence=0.89, ai_reason="DEMO DATA — Active flood overflow.",
            image_uploaded=False, created_at=now - timedelta(minutes=15), updated_at=now - timedelta(minutes=15),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
        StoredReport(
            report_id="DEMO-H3", latitude=15.8290, longitude=78.0388, condition=Condition.ROAD_BLOCKED,
            severity=Severity.HIGH, description="DEMO DATA — Road impassable for light vehicles due to flash runoff.",
            vehicle_impact=VehicleImpact.MOST_VEHICLES_LIKELY_AFFECTED, flood_detected=True,
            ai_confidence=0.95, ai_reason="DEMO DATA — Road blocked by standing water.",
            image_uploaded=False, created_at=now - timedelta(minutes=22), updated_at=now - timedelta(minutes=22),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
        StoredReport(
            report_id="DEMO-M1", latitude=15.8294, longitude=78.0392, condition=Condition.WATERLOGGED,
            severity=Severity.MEDIUM, description="DEMO DATA — Water accumulation ~1 foot in low-lying transit corridor.",
            vehicle_impact=VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED, flood_detected=True,
            ai_confidence=0.85, ai_reason="DEMO DATA — Waterlogged roadway.",
            image_uploaded=False, created_at=now - timedelta(minutes=45), updated_at=now - timedelta(minutes=45),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
        StoredReport(
            report_id="DEMO-M2", latitude=15.8297, longitude=78.0395, condition=Condition.WATERLOGGED,
            severity=Severity.MEDIUM, description="DEMO DATA — Moderate waterlogging on service road, slow traffic.",
            vehicle_impact=VehicleImpact.POSSIBLE, flood_detected=True,
            ai_confidence=0.78, ai_reason="DEMO DATA — Slow traffic waterlogging.",
            image_uploaded=False, created_at=now - timedelta(minutes=70), updated_at=now - timedelta(minutes=70),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
        StoredReport(
            report_id="DEMO-L1", latitude=15.8300, longitude=78.0398, condition=Condition.WATERLOGGED,
            severity=Severity.LOW, description="DEMO DATA — Minor roadside puddle accumulation, passable.",
            vehicle_impact=VehicleImpact.NONE_REPORTED, flood_detected=True,
            ai_confidence=0.72, ai_reason="DEMO DATA — Minor pooling.",
            image_uploaded=False, created_at=now - timedelta(minutes=90), updated_at=now - timedelta(minutes=90),
            status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
        ),
    ]
    for r in demo_reports:
        repo.create_report(r)
    logger.info("Seeded %d demo reports into InMemoryReportRepository", len(demo_reports))


if settings.demo_mode:
    repository = InMemoryReportRepository()
    seed_in_memory_demo_reports(repository)
    ai_provider = MockProvider()
    s3_service = None
else:
    repository = DynamoDBReportRepository(settings.aws_region, settings.dynamodb_table_name) if settings.aws_region and settings.dynamodb_table_name else InMemoryReportRepository()

    # Conditional Bedrock/AWS validation: only if Bedrock is actually enabled
    if settings.bedrock_model_id:
        settings.require_aws("aws_region", "bedrock_model_id")
        ai_provider = BedrockService(settings.aws_region, settings.bedrock_model_id)
    else:
        ai_provider = MockProvider()
        logger.warning("Bedrock not configured, using MockProvider for AI services.")

    s3_service = S3Service(settings.aws_region, settings.s3_bucket_name, settings.s3_presigned_url_expiry) if settings.aws_region and settings.s3_bucket_name else None

report_service = ReportService(
    repository=repository,
    ai=ai_provider,
    s3=s3_service,
    max_upload_bytes=settings.max_upload_bytes,
    allowed_types=settings.allowed_content_types,
)

app = FastAPI(
    title="FloodRoute Backend",
    description="Citizen flood evidence and deterministic route-risk API. Results are based on available reports and are not guarantees of road safety.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(reports_router)
app.include_router(flood_router)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": "HTTP_ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": "Invalid request parameters", "details": exc.errors()}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled request error: %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "An internal server error occurred."}})
