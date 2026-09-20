import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from app.main import app
from app.repositories.report_repository import InMemoryReportRepository
from app.api.reports import get_repository
from app.schemas.report import Condition, ReportSource, ReportStatus, Severity, StoredReport, VehicleImpact
from datetime import datetime, timezone

# TEST SCENARIO PARAMETERIZATION
test_cases = [
    # Citizen + NASA combinations
    ("HIGH", 0.0, "HIGH_REPORTED_RISK", False),
    ("LOW", 60.0, "HIGH_REPORTED_RISK", False), # Elevate: MEDIUM+HIGH NASA -> HIGH
    ("NONE", 60.0, "HIGH_REPORTED_RISK", False), # NASA Risk
    ("HIGH", 0.0, "HIGH_REPORTED_RISK", False),
    ("HIGH", "FAIL", "HIGH_REPORTED_RISK", False),
    ("LOW", "FAIL", "MEDIUM_REPORTED_RISK", False), # NASA Fail, Citizen LOW -> MEDIUM
    ("NONE", 2.0, "LOW_REPORTED_RISK", False),  # LOW NASA -> LOW
    ("NONE", 30.0, "MEDIUM_REPORTED_RISK", False), # MEDIUM NASA -> MEDIUM
    ("NONE", 55.0, "HIGH_REPORTED_RISK", False),  # HIGH NASA -> HIGH
    ("NONE", 55.0, "HIGH_REPORTED_RISK", True),   # DEMO
]

@pytest.fixture
def test_repo():
    return InMemoryReportRepository()

@pytest.fixture
def test_client(test_repo):
    def get_repo_override():
        return test_repo
    app.dependency_overrides = {}
    app.dependency_overrides[get_repository] = get_repo_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def create_test_report(severity: Severity) -> StoredReport:
    now = datetime.now(timezone.utc)
    return StoredReport(
        report_id="R001", latitude=15.8, longitude=78.0,
        condition=Condition.FLOODED, severity=severity,
        description="Test", vehicle_impact=VehicleImpact.POSSIBLE,
        flood_detected=True, created_at=now, updated_at=now,
        status=ReportStatus.ACTIVE, source=ReportSource.CITIZEN,
    )

@pytest.mark.parametrize("citizen_severity, nasa_exposure, expected_risk, demo_mode", test_cases)
@patch("app.api.flood.get_settings")
@patch("app.api.flood.NASAFloodService")
@patch("app.api.flood.calculate_flood_exposure")
def test_unified_pipeline(
    mock_nasa_exposure,
    mock_nasa_service,
    mock_settings,
    test_client,
    test_repo,
    citizen_severity,
    nasa_exposure,
    expected_risk,
    demo_mode
):
    # Mock Setup
    mock_settings.return_value.demo_mode = demo_mode

    # Setup Citizen Risk
    if citizen_severity != "NONE":
        test_repo.create_report(create_test_report(Severity(citizen_severity)))

    # NASA Exposure
    if nasa_exposure == "FAIL":
        mock_nasa_service.return_value.get_flood_extent = AsyncMock(side_effect=Exception("NASA fail"))
        mock_nasa_exposure.return_value = None
    else:
        mock_nasa_service.return_value.get_flood_extent = AsyncMock(return_value={"features": [{"properties": {"source": "NASA VIIRS", "observation_time": "2026-09-13T00:00:00Z"}}]})
        mock_nasa_exposure.return_value = {
            "flood_exposed_percentage": nasa_exposure,
            "flood_affected_distance_km": 1.0,
            "route_distance_km": 10.0,
            "source": "NASA VIIRS",
            "observation_time": "2026-09-13T00:00:00Z"
        }

    # Execute
    payload = {"route": [{"latitude": 15.8, "longitude": 78.0}, {"latitude": 15.9, "longitude": 78.1}]}
    response = test_client.post("/flood/analyze-route", json=payload)

    # Assert
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["route_risk"] == expected_risk
    if nasa_exposure != "FAIL":
        assert data["evidence"]["nasa"]["available"] is True
    else:
        assert data["evidence"]["nasa"]["available"] is False
