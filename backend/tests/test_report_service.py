from app.repositories.report_repository import InMemoryReportRepository
from app.schemas.report import Condition, FloodReportCreate, Severity, AIAnalysisResult, EvidenceFlags, FinalAnalysis
from app.services.bedrock_service import MockProvider, AIAnalysisError
from app.services.report_service import ReportService
from unittest.mock import MagicMock
import pytest
from app.services.s3_service import S3Service

class FailingAIProvider(MockProvider):
    def analyze_text_report(self, description: str) -> AIAnalysisResult:
        raise AIAnalysisError("Bedrock unavailable")
    def analyze_flood_image(self, image_bytes: bytes, content_type: str) -> AIAnalysisResult:
        raise AIAnalysisError("Bedrock unavailable")

@pytest.fixture
def report_service_with_s3(mock_s3_service):
    repo = InMemoryReportRepository()
    return ReportService(repo, MockProvider(), mock_s3_service, 5 * 1024 * 1024, {"image/jpeg", "image/png", "image/webp"})

def test_report_creation_without_aws():
    repo = InMemoryReportRepository()
    service = ReportService(repo, MockProvider(), None, 5 * 1024 * 1024, {"image/jpeg", "image/png", "image/webp"})
    report = service.create(FloodReportCreate(
        latitude=15.8281, longitude=78.0373, condition=Condition.FLOODED,
        description="Water is covering the road and motorcycles cannot pass.",
    ))
    assert report.severity == Severity.HIGH
    assert repo.get_report(report.report_id) is not None

def test_report_creation_with_image(report_service_with_s3, mock_s3_service):
    # S3 is already mocked
    report = report_service_with_s3.create(
        FloodReportCreate(
            latitude=15.8281, longitude=78.0373, condition=Condition.FLOODED,
            description="Water is covering the road.",
        ),
        image_bytes=b"fake-image",
        image_filename="test.jpg",
        image_content_type="image/jpeg"
    )
    assert report.image_uploaded is True
    # Verify s3 was called
    mock_s3_service.validate_image.assert_called_once()
    mock_s3_service.upload_image.assert_called_once()

def test_report_creation_ai_failure_fallback():
    repo = InMemoryReportRepository()
    service = ReportService(repo, FailingAIProvider(), None, 5 * 1024 * 1024, {"image/jpeg", "image/png", "image/webp"})
    report = service.create(FloodReportCreate(
        latitude=15.8281, longitude=78.0373, condition=Condition.WATERLOGGED,
        description="Just a bit of water.",
    ))
    # Should fall back to citizen-provided condition
    assert report.condition == Condition.WATERLOGGED
    # Should be set to FAILED as per report_service logic (text_analysis is None and image_analysis is None)
    assert report.ai_status == "FAILED"
