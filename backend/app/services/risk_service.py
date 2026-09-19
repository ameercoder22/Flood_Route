from __future__ import annotations

import math
from collections import defaultdict
from datetime import datetime, timezone

from app.schemas.report import AffectedSegment, ReportStatus, RiskSummary, RouteRiskResponse, Severity, StoredReport

SEVERITY_WEIGHT = {Severity.HIGH: 3.0, Severity.MEDIUM: 2.0, Severity.LOW: 1.0, Severity.UNKNOWN: 0.0}


def calculate_freshness(created_at: datetime, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    timestamp = created_at if created_at.tzinfo else created_at.replace(tzinfo=timezone.utc)
    minutes = max(0.0, (now - timestamp).total_seconds() / 60.0)
    if minutes <= 30: return "VERY_RECENT"
    if minutes <= 120: return "RECENT"
    if minutes <= 360: return "AGING"
    return "OLD"


def freshness_multiplier(bucket: str) -> float:
    return {"VERY_RECENT": 1.0, "RECENT": 0.7, "AGING": 0.4, "OLD": 0.1}[bucket]


def report_weight(report: StoredReport, now: datetime | None = None) -> float:
    return SEVERITY_WEIGHT[report.severity] * freshness_multiplier(calculate_freshness(report.created_at, now))


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def distance_point_to_route(report_point: tuple[float, float], route_points: list[tuple[float, float]]) -> tuple[float, int]:
    """Returns minimum Haversine distance and index of the nearest route point.

    For hackathon-scale routes this point-to-sampled-route approximation is sufficiently
    practical and avoids pretending latitude/longitude subtraction is a distance measure.
    """
    distances = [
        _haversine_m(report_point[0], report_point[1], point[0], point[1])
        for point in route_points
    ]
    index = min(range(len(distances)), key=distances.__getitem__)
    return distances[index], index


def is_report_active(report: StoredReport, now: datetime | None = None) -> bool:
    if report.status != ReportStatus.ACTIVE:
        return False
    # ACTIVE is eligible; freshness reduces its weight instead of silently deleting it.
    return True


def _risk_category(score: float, nearby_count: int) -> str:
    if nearby_count == 0:
        return "LOW_REPORTED_RISK"
    if score <= 2.0:
        return "MEDIUM_REPORTED_RISK"
    return "HIGH_REPORTED_RISK"


def calculate_route_risk(reports: list[StoredReport], route_points: list[tuple[float, float]], radius_meters: float, now: datetime | None = None) -> RouteRiskResponse:
    now = now or datetime.now(timezone.utc)
    nearby: list[tuple[StoredReport, float, int]] = []
    for report in reports:
        if not is_report_active(report, now):
            continue
        distance, index = distance_point_to_route((report.latitude, report.longitude), route_points)
        if distance <= radius_meters:
            nearby.append((report, distance, index))

    score = sum(report_weight(report, now) for report, _, _ in nearby)
    category = _risk_category(score, len(nearby))

    grouped: dict[int, list[tuple[StoredReport, float]]] = defaultdict(list)
    for report, distance, index in nearby:
        grouped[index].append((report, distance))

    affected: list[AffectedSegment] = []
    for index, group in sorted(grouped.items()):
        reports_at_segment = [item[0] for item in group]
        latest = max(reports_at_segment, key=lambda item: item.created_at)
        minutes_ago = max(0, int((now - latest.created_at).total_seconds() // 60))
        segment_score = sum(report_weight(item, now) for item in reports_at_segment)
        segment_risk_str = _risk_category(segment_score, len(reports_at_segment))
        # Convert "HIGH_REPORTED_RISK" back to Severity enum value "HIGH"
        segment_risk_severity = Severity(segment_risk_str.replace("_REPORTED_RISK", ""))
        point = route_points[index]
        affected.append(AffectedSegment(
            latitude=point[0], longitude=point[1], risk=segment_risk_severity,
            reports=len(reports_at_segment), latest_report_minutes_ago=minutes_ago,
            nearest_distance_meters=round(min(distance for _, distance in group), 1),
        ))

    summary = RiskSummary(
        active_reports=len(nearby),
        high_reports=sum(1 for report, _, _ in nearby if report.severity == Severity.HIGH),
        medium_reports=sum(1 for report, _, _ in nearby if report.severity == Severity.MEDIUM),
        low_reports=sum(1 for report, _, _ in nearby if report.severity == Severity.LOW),
        unknown_reports=sum(1 for report, _, _ in nearby if report.severity == Severity.UNKNOWN),
    )
    return RouteRiskResponse(
        route_risk=category, risk_score=round(score, 2), affected_segments=affected,
        summary=summary,
    )
