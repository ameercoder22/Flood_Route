import pytest
from unittest.mock import MagicMock
from app.repositories.report_repository import DynamoDBReportRepository, DatabaseError
from app.schemas.report import StoredReport, Condition, ReportStatus, Severity, VehicleImpact, ReportSource
from datetime import datetime, timezone

@pytest.fixture
def mock_dynamodb():
    mock_dynamodb = MagicMock()
    # Mocking the boto3.resource pattern
    # The repository class does boto3.resource
    # Let's mock the resource and table

    mock_resource = MagicMock()
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    return mock_resource, mock_table

def test_dynamodb_repository_init_missing_params():
    with pytest.raises(ValueError):
        DynamoDBReportRepository("", "")
    with pytest.raises(ValueError):
        DynamoDBReportRepository("us-east-1", "")

def test_create_report_success(mock_dynamodb):
    mock_resource, mock_table = mock_dynamodb

    # Need to mock boto3.resource to return mock_resource
    from unittest.mock import patch
    with patch("boto3.resource", return_value=mock_resource):
        repo = DynamoDBReportRepository("us-east-1", "FloodReports")

        report = StoredReport(
            report_id="R001", latitude=15.0, longitude=78.0, condition=Condition.NORMAL,
            severity=Severity.LOW, description="Test", vehicle_impact=VehicleImpact.NONE_REPORTED,
            flood_detected=False, ai_confidence=0.9, ai_reason="Test", image_uploaded=False,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            status=ReportStatus.ACTIVE, source=ReportSource.CITIZEN
        )

        repo.create_report(report)
        mock_table.put_item.assert_called_once()

def test_create_report_failure(mock_dynamodb):
    mock_resource, mock_table = mock_dynamodb
    mock_table.put_item.side_effect = Exception("DynamoDB error")

    from unittest.mock import patch
    with patch("boto3.resource", return_value=mock_resource):
        repo = DynamoDBReportRepository("us-east-1", "FloodReports")

        report = StoredReport(
            report_id="R001", latitude=15.0, longitude=78.0, condition=Condition.NORMAL,
            severity=Severity.LOW, description="Test", vehicle_impact=VehicleImpact.NONE_REPORTED,
            flood_detected=False, ai_confidence=0.9, ai_reason="Test", image_uploaded=False,
            created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
            status=ReportStatus.ACTIVE, source=ReportSource.CITIZEN
        )

        with pytest.raises(DatabaseError):
            repo.create_report(report)
