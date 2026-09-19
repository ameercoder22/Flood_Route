"""Fixtures and mocks for FloodRoute tests."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from app.repositories.report_repository import InMemoryReportRepository
from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact
from app.services.bedrock_service import MockProvider
from app.services.report_service import ReportService
from app.services.s3_service import S3Service
from datetime import datetime, timezone


@pytest.fixture
def in_memory_repo():
    """Provide an in-memory report repository for tests."""
    return InMemoryReportRepository()


@pytest.fixture
def mock_ai_provider():
    """Provide a mock AI provider."""
    return MockProvider()


@pytest.fixture
def mock_s3_service():
    """Provide a mocked S3 service that doesn't make actual AWS calls."""
    service = MagicMock(spec=S3Service)
    service.validate_image = MagicMock(return_value="image/jpeg")
    service.upload_image = MagicMock(return_value="reports/test-id/abc123.jpg")
    service.generate_presigned_url = MagicMock(return_value="https://s3.example.com/...")
    return service


@pytest.fixture
def report_service(in_memory_repo, mock_ai_provider, mock_s3_service):
    """Provide a ReportService with in-memory repo and mocked AWS."""
    return ReportService(
        repository=in_memory_repo,
        ai=mock_ai_provider,
        s3=mock_s3_service,
        max_upload_bytes=5 * 1024 * 1024,
        allowed_types={"image/jpeg", "image/png", "image/webp"},
    )


def make_demo_report(
    report_id: str,
    latitude: float,
    longitude: float,
    severity: Severity = Severity.HIGH,
    age_minutes: int = 10,
    status: ReportStatus = ReportStatus.ACTIVE,
) -> StoredReport:
    """Create a synthetic report for testing."""
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    created = now - timedelta(minutes=age_minutes)
    return StoredReport(
        report_id=report_id,
        latitude=latitude,
        longitude=longitude,
        condition=Condition.FLOODED,
        severity=severity,
        description="Test report",
        vehicle_impact=VehicleImpact.POSSIBLE,
        flood_detected=True,
        ai_confidence=0.9,
        ai_reason="test",
        image_uploaded=False,
        created_at=created,
        updated_at=created,
        status=status,
        source=ReportSource.DEMO,
        ai_status="SUCCESS",
    )
