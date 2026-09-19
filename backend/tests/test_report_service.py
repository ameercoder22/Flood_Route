from app.repositories.report_repository import InMemoryReportRepository
from app.schemas.report import Condition, FloodReportCreate, Severity
from app.services.bedrock_service import MockProvider
from app.services.report_service import ReportService


def test_report_creation_without_aws():
    repo = InMemoryReportRepository()
    service = ReportService(repo, MockProvider(), None, 5 * 1024 * 1024, {"image/jpeg", "image/png", "image/webp"})
    report = service.create(FloodReportCreate(
        latitude=15.8281, longitude=78.0373, condition=Condition.FLOODED,
        description="Water is covering the road and motorcycles cannot pass.",
    ))
    assert report.severity == Severity.HIGH
    assert repo.get_report(report.report_id) is not None
