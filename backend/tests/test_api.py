"""Integration tests for the FastAPI endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.repositories.report_repository import InMemoryReportRepository
from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact


def create_test_report(
    report_id: str,
    latitude: float,
    longitude: float,
    severity: Severity = Severity.HIGH,
    age_minutes: int = 10,
) -> StoredReport:
    """Create a test report."""
    now = datetime.now(timezone.utc)
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
        status=ReportStatus.ACTIVE,
        source=ReportSource.DEMO,
        ai_status="SUCCESS",
    )


@pytest.fixture
def test_repo():
    """Create a fresh in-memory repo for each test."""
    return InMemoryReportRepository()


@pytest.fixture
def test_client(test_repo):
    """Create a test client with mocked repository."""
    # Override the dependency
    def get_repo_override():
        return test_repo

    app.dependency_overrides = {}
    # Find and patch the get_repository function
    from app.api.reports import get_repository
    app.dependency_overrides[get_repository] = get_repo_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_health_endpoint(test_client):
    """Test GET /health."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "floodroute-backend"


def test_list_reports_empty(test_client):
    """Test GET /reports when no reports exist."""
    response = test_client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


def test_list_reports_with_data(test_client, test_repo):
    """Test GET /reports returns active reports sorted by creation date."""
    now = datetime.now(timezone.utc)

    report1 = create_test_report("R001", 15.8281, 78.0373, Severity.HIGH, age_minutes=5)
    report2 = create_test_report("R002", 15.8290, 78.0390, Severity.MEDIUM, age_minutes=30)

    test_repo.create_report(report1)
    test_repo.create_report(report2)

    response = test_client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    # Should be sorted most recent first
    assert data["data"][0]["report_id"] == "R001"


def test_get_report_found(test_client, test_repo):
    """Test GET /reports/{report_id} when report exists."""
    report = create_test_report("R001", 15.8281, 78.0373, Severity.HIGH)
    test_repo.create_report(report)

    response = test_client.get("/reports/R001")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["report_id"] == "R001"
    assert data["data"]["severity"] == "HIGH"


def test_get_report_not_found(test_client):
    """Test GET /reports/{report_id} when report doesn't exist."""
    response = test_client.get("/reports/NONEXISTENT")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "REPORT_NOT_FOUND"


def test_list_reports_limit(test_client, test_repo):
    """Test GET /reports with limit parameter."""
    for i in range(3):
        report = create_test_report(f"R{i:03d}", 15.8281 + i * 0.001, 78.0373, age_minutes=i)
        test_repo.create_report(report)

    response = test_client.get("/reports?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2


def test_list_reports_invalid_limit(test_client):
    """Test GET /reports with invalid limit."""
    response = test_client.get("/reports?limit=0")
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False


def test_near_route_no_nearby_reports(test_client):
    """Test POST /reports/near-route when no reports are nearby."""
    payload = {
        "route": [
            {"latitude": 20.0, "longitude": 80.0},
            {"latitude": 20.1, "longitude": 80.1},
        ],
        "radius_meters": 100,
    }
    response = test_client.post("/reports/near-route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "LOW_REPORTED_RISK" in data["route_risk"]
    assert len(data["affected_segments"]) == 0


def test_near_route_basic(test_client, test_repo):
    """Test POST /reports/near-route finds nearby reports."""
    report = create_test_report("R001", 15.8281, 78.0373, Severity.HIGH, age_minutes=5)
    test_repo.create_report(report)

    payload = {
        "route": [
            {"latitude": 15.8281, "longitude": 78.0373},
            {"latitude": 15.8290, "longitude": 78.0390},
        ],
        "radius_meters": 500,
    }
    response = test_client.post("/reports/near-route", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "HIGH_REPORTED_RISK" in data["route_risk"]
    assert len(data["affected_segments"]) > 0


def test_near_route_invalid_route(test_client):
    """Test POST /reports/near-route with invalid route."""
    payload = {
        "route": [{"latitude": 15.8281, "longitude": 78.0373}],  # Only 1 point, need 2+
        "radius_meters": 100,
    }
    response = test_client.post("/reports/near-route", json=payload)
    assert response.status_code == 422
