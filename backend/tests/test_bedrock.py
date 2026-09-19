import pytest

from app.schemas.report import Condition, Severity, VehicleImpact
from app.services.bedrock_service import AIAnalysisError, BedrockService, MockProvider


VALID_HIGH = {
    "flood_detected": True,
    "condition": "FLOODED",
    "severity": "HIGH",
    "vehicle_impact": "TWO_WHEELERS_LIKELY_AFFECTED",
    "confidence": 0.87,
    "reason": "Standing water covers a substantial portion of the roadway.",
}


class FakeBedrockClient:
    def __init__(self, raw: str):
        self.raw = raw

    def converse(self, **kwargs):
        return {"output": {"message": {"content": [{"text": self.raw}]}}}


def service_with(raw: str) -> BedrockService:
    service = object.__new__(BedrockService)
    service.model_id = "test-model"
    service.client = FakeBedrockClient(raw)
    return service


def test_flooded_report():
    result = service_with('{"flood_detected":true,"condition":"FLOODED","severity":"HIGH","vehicle_impact":"TWO_WHEELERS_LIKELY_AFFECTED","confidence":0.87,"reason":"Water covers the road."}').analyze_text_report("Water is covering the road and motorcycles cannot pass.")
    assert result.condition == Condition.FLOODED
    assert result.severity == Severity.HIGH
    assert result.vehicle_impact == VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED


def test_waterlogged_report():
    raw = '{"flood_detected":true,"condition":"WATERLOGGED","severity":"LOW","vehicle_impact":"NONE_REPORTED","confidence":0.84,"reason":"Small water accumulation is visible beside the road."}'
    result = service_with(raw).analyze_text_report("Small amount of water is collected beside the road.")
    assert result.condition == Condition.WATERLOGGED
    assert result.severity == Severity.LOW


def test_road_blocked_report():
    raw = '{"flood_detected":false,"condition":"ROAD_BLOCKED","severity":"HIGH","vehicle_impact":"MOST_VEHICLES_LIKELY_AFFECTED","confidence":0.92,"reason":"Fallen debris blocks the roadway."}'
    result = service_with(raw).analyze_text_report("Road is blocked by fallen debris.")
    assert result.condition == Condition.ROAD_BLOCKED
    assert result.severity == Severity.HIGH


def test_normal_report():
    raw = '{"flood_detected":false,"condition":"NORMAL","severity":"LOW","vehicle_impact":"NONE_REPORTED","confidence":0.91,"reason":"Traffic is moving normally and no flood condition is reported."}'
    result = service_with(raw).analyze_text_report("Traffic is moving normally; the road is dry.")
    assert result.condition == Condition.NORMAL
    assert result.severity == Severity.LOW
    assert result.flood_detected is False


def test_ambiguous_report():
    raw = '{"flood_detected":false,"condition":"UNKNOWN","severity":"UNKNOWN","vehicle_impact":"UNKNOWN","confidence":0.31,"reason":"The report does not provide enough evidence."}'
    result = service_with(raw).analyze_text_report("Something seems wrong near the road.")
    assert result.condition == Condition.UNKNOWN
    assert result.severity == Severity.UNKNOWN


def test_markdown_code_fence_is_accepted():
    result = service_with("```json\n" + __import__('json').dumps(VALID_HIGH) + "\n```").analyze_text_report("Water is covering the road.")
    assert result.condition == Condition.FLOODED


def test_malformed_ai_json():
    with pytest.raises(AIAnalysisError, match="malformed JSON"):
        service_with('{"condition":"FLOODED"').analyze_text_report("Water on road")


def test_missing_field():
    raw = '{"flood_detected":true,"condition":"FLOODED","severity":"HIGH","confidence":0.8,"reason":"Water covers the road."}'
    with pytest.raises(AIAnalysisError, match="invalid analysis fields"):
        service_with(raw).analyze_text_report("Water on road")


def test_invalid_severity():
    raw = '{"flood_detected":true,"condition":"FLOODED","severity":"EXTREME","vehicle_impact":"POSSIBLE","confidence":0.8,"reason":"Water covers the road."}'
    with pytest.raises(AIAnalysisError, match="invalid analysis fields"):
        service_with(raw).analyze_text_report("Water on road")


def test_invalid_confidence():
    raw = '{"flood_detected":true,"condition":"FLOODED","severity":"HIGH","vehicle_impact":"POSSIBLE","confidence":1.5,"reason":"Water covers the road."}'
    with pytest.raises(AIAnalysisError, match="invalid analysis fields"):
        service_with(raw).analyze_text_report("Water on road")


def test_bedrock_failure():
    class FailingClient:
        def converse(self, **kwargs):
            raise TimeoutError("timed out")

    service = object.__new__(BedrockService)
    service.model_id = "test-model"
    service.client = FailingClient()
    with pytest.raises(AIAnalysisError, match="temporarily unavailable"):
        service.analyze_text_report("Water on road")


def test_mock_provider_remains_available_for_unit_tests():
    result = MockProvider().analyze_text_report("Water is covering the road and motorcycles cannot pass.")
    assert result.condition == Condition.FLOODED
    assert result.severity == Severity.HIGH
