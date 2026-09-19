from datetime import datetime, timedelta, timezone

from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact
from app.services.risk_service import calculate_route_risk, distance_point_to_route, calculate_freshness


def make_report(report_id, lat, lon, severity, age_minutes, status=ReportStatus.ACTIVE):
    now = datetime.now(timezone.utc)
    return StoredReport(
        report_id=report_id, latitude=lat, longitude=lon, condition=Condition.FLOODED,
        severity=severity, description="Water on road", vehicle_impact=VehicleImpact.POSSIBLE,
        flood_detected=True, ai_confidence=0.9, ai_reason="test", image_uploaded=False,
        created_at=now - timedelta(minutes=age_minutes), updated_at=now - timedelta(minutes=age_minutes),
        status=status, source=ReportSource.DEMO, ai_status="SUCCESS",
    )


def test_distance_is_in_meters():
    distance, index = distance_point_to_route((15.8281, 78.0373), [(15.8281, 78.0373), (15.8290, 78.0380)])
    assert distance < 1
    assert index == 0


def test_freshness_buckets():
    now = datetime.now(timezone.utc)
    assert calculate_freshness(now - timedelta(minutes=10), now) == "VERY_RECENT"
    assert calculate_freshness(now - timedelta(minutes=60), now) == "RECENT"
    assert calculate_freshness(now - timedelta(hours=3), now) == "AGING"
    assert calculate_freshness(now - timedelta(hours=8), now) == "OLD"


def test_far_reports_are_excluded():
    route = [(15.8281, 78.0373), (15.8290, 78.0380)]
    report = make_report("R1", 15.90, 78.20, Severity.HIGH, 5)
    result = calculate_route_risk([report], route, 100)
    assert result.summary.active_reports == 0
    assert result.route_risk == "LOW_REPORTED_RISK"


def test_recent_high_reports_raise_route_risk():
    route = [(15.8281, 78.0373), (15.8290, 78.0380)]
    reports = [make_report(f"R{i}", 15.8281, 78.0373, Severity.HIGH, 8) for i in range(3)]
    result = calculate_route_risk(reports, route, 100)
    assert result.route_risk == "HIGH_REPORTED_RISK"
    assert result.summary.high_reports == 3


def test_non_active_reports_are_excluded():
    route = [(15.8281, 78.0373), (15.8290, 78.0380)]
    report = make_report("R1", 15.8281, 78.0373, Severity.HIGH, 5, ReportStatus.EXPIRED)
    result = calculate_route_risk([report], route, 100)
    assert result.summary.active_reports == 0
