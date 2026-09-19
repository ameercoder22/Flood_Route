from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import get_settings
from app.repositories.report_repository import DynamoDBReportRepository
from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact


def build(report_id: str, lat: float, lon: float, severity: Severity, minutes_ago: int) -> StoredReport:
    timestamp = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return StoredReport(
        report_id=report_id, latitude=lat, longitude=lon, condition=Condition.FLOODED if severity != Severity.LOW else Condition.WATERLOGGED,
        severity=severity, description="DEMO DATA — not a real citizen report.",
        vehicle_impact=VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED if severity == Severity.HIGH else VehicleImpact.POSSIBLE,
        flood_detected=severity != Severity.UNKNOWN, ai_confidence=0.9, ai_reason="DEMO DATA",
        image_uploaded=False, created_at=timestamp, updated_at=timestamp,
        status=ReportStatus.ACTIVE, source=ReportSource.DEMO, ai_status="DEMO",
    )


def main() -> None:
    settings = get_settings()
    settings.require_aws("aws_region", "dynamodb_table_name")
    repo = DynamoDBReportRepository(settings.aws_region, settings.dynamodb_table_name)
    reports = [
        build("DEMO-H1", 15.8285, 78.0381, Severity.HIGH, 8),
        build("DEMO-H2", 15.8287, 78.0383, Severity.HIGH, 15),
        build("DEMO-H3", 15.8290, 78.0388, Severity.HIGH, 22),
        build("DEMO-M1", 15.8294, 78.0392, Severity.MEDIUM, 45),
        build("DEMO-M2", 15.8297, 78.0395, Severity.MEDIUM, 70),
        build("DEMO-L1", 15.8300, 78.0398, Severity.LOW, 90),
    ]
    for report in reports:
        repo.create_report(report)
    print(f"Seeded {len(reports)} clearly labeled DEMO reports.")


if __name__ == "__main__":
    main()
