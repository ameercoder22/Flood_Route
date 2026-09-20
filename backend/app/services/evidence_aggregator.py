from typing import Any, Dict, Optional
from app.schemas.report import RouteRiskResponse, Severity

def get_nasa_evidence_level(exposure_percentage: float) -> str:
    if exposure_percentage <= 0:
        return "NONE"
    if exposure_percentage < 20:
        return "LOW"
    if exposure_percentage < 50:
        return "MEDIUM"
    return "HIGH"

def get_risk_mapping(level: str) -> str:
    """Helper to map evidence levels to risk categories."""
    return f"{level}_REPORTED_RISK"

def aggregate_evidence(citizen_risk_response: Any, nasa_exposure: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    citizen_evidence = {
        "active_reports": citizen_risk_response.summary.active_reports,
        "high_reports": citizen_risk_response.summary.high_reports,
        "medium_reports": citizen_risk_response.summary.medium_reports,
        "low_reports": citizen_risk_response.summary.low_reports,
    }

    nasa_evidence = {
        "available": nasa_exposure is not None,
        "is_real_data": nasa_exposure.get("is_real_data", False) if nasa_exposure else False,
        "evidence_level": "NONE",
        "flood_exposed_percentage": 0.0,
        "flood_affected_distance_km": 0.0,
        "route_distance_km": 0.0,
        "observation_time": None,
        "source": None,
    }

    if nasa_exposure:
        nasa_evidence.update({
            "observation_time": nasa_exposure.get("observation_time"),
            "source": nasa_exposure.get("source"),
            "flood_exposed_percentage": nasa_exposure.get("flood_exposed_percentage", 0.0),
            "flood_affected_distance_km": nasa_exposure.get("flood_affected_distance_km", 0.0),
            "route_distance_km": nasa_exposure.get("route_distance_km", 0.0),
            "evidence_level": get_nasa_evidence_level(nasa_exposure.get("flood_exposed_percentage", 0.0))
        })

    # Aggregation Rules
    citizen_risk = citizen_risk_response.route_risk # e.g., "HIGH_REPORTED_RISK"
    nasa_level = nasa_evidence["evidence_level"]

    # Determine risk score (mapping string to numerical level)
    risk_map = {"LOW_REPORTED_RISK": 1, "MEDIUM_REPORTED_RISK": 2, "HIGH_REPORTED_RISK": 3}
    nasa_map = {"NONE": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3}

    c_score = risk_map.get(citizen_risk, 0)
    n_score = nasa_map.get(nasa_level, 0)

    # Simplified Aggregation: Max of the two, but Citizen HIGH overrides
    final_score = max(c_score, n_score)
    # Ensure Citizen HIGH overrides NASA
    if citizen_risk == "HIGH_REPORTED_RISK":
        final_score = 3

    final_risk = {1: "LOW_REPORTED_RISK", 2: "MEDIUM_REPORTED_RISK", 3: "HIGH_REPORTED_RISK"}.get(final_score, "LOW_REPORTED_RISK")

    # Explanation
    explanation = []
    if citizen_evidence["high_reports"] > 0:
        explanation.append(f"{citizen_evidence['high_reports']} high-severity citizen reports found near the route.")
    if nasa_level != "NONE":
        explanation.append(f"NASA flood evidence overlaps {nasa_evidence['flood_exposed_percentage']}% of the route.")

    return {
        "route_risk": final_risk,
        "evidence": {
            "citizen": citizen_evidence,
            "nasa": nasa_evidence
        },
        "explanation": explanation
    }
