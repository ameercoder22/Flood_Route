from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Condition(str, Enum):
    NORMAL = "NORMAL"
    WATERLOGGED = "WATERLOGGED"
    FLOODED = "FLOODED"
    ROAD_BLOCKED = "ROAD_BLOCKED"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class VehicleImpact(str, Enum):
    NONE_REPORTED = "NONE_REPORTED"
    POSSIBLE = "POSSIBLE"
    TWO_WHEELERS_LIKELY_AFFECTED = "TWO_WHEELERS_LIKELY_AFFECTED"
    MOST_VEHICLES_LIKELY_AFFECTED = "MOST_VEHICLES_LIKELY_AFFECTED"
    UNKNOWN = "UNKNOWN"


class ReportStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    FLAGGED = "FLAGGED"
    INVALID = "INVALID"


class ReportSource(str, Enum):
    CITIZEN = "CITIZEN"
    AI_ASSISTED = "AI_ASSISTED"
    SYSTEM = "SYSTEM"
    DEMO = "DEMO"


class AIAnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flood_detected: bool
    condition: Condition
    severity: Severity
    vehicle_impact: VehicleImpact
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    reason: Annotated[str, Field(min_length=1, max_length=1000)]


class EvidenceFlags(BaseModel):
    text: bool = False
    image: bool = False


class FinalAnalysis(AIAnalysisResult):
    evidence: EvidenceFlags


class FloodReportCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]
    condition: Condition
    description: Annotated[str, Field(min_length=3, max_length=2000)]

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("description must contain at least 3 non-whitespace characters")
        return value


class RoutePoint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: Annotated[float, Field(ge=-90, le=90)]
    longitude: Annotated[float, Field(ge=-180, le=180)]


class RouteRiskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route: Annotated[list[RoutePoint], Field(min_length=2, max_length=5000)]
    radius_meters: Annotated[float, Field(gt=0, le=5000)] = 100.0


class AffectedSegment(BaseModel):
    latitude: float
    longitude: float
    risk: Severity
    reports: int
    latest_report_minutes_ago: Optional[int] = None
    nearest_distance_meters: float


class RiskSummary(BaseModel):
    active_reports: int
    high_reports: int
    medium_reports: int
    low_reports: int
    unknown_reports: int


class RouteRiskResponse(BaseModel):
    success: bool = True
    route_risk: str
    risk_score: float
    affected_segments: list[AffectedSegment]
    summary: RiskSummary
    message: str = "Based on available reports. Conditions may change rapidly."


class FloodReportResponse(BaseModel):
    success: bool = True
    data: dict


class ErrorBody(BaseModel):
    success: bool = False
    error: dict


class StoredReport(BaseModel):
    report_id: str
    latitude: float
    longitude: float
    condition: Condition
    severity: Severity
    description: str
    vehicle_impact: VehicleImpact
    flood_detected: bool
    ai_confidence: Optional[float] = None
    ai_reason: Optional[str] = None
    text_analysis: Optional[AIAnalysisResult] = None
    image_analysis: Optional[AIAnalysisResult] = None
    final_analysis: Optional[FinalAnalysis] = None
    image_key: Optional[str] = None
    image_uploaded: bool = False
    created_at: datetime
    updated_at: datetime
    status: ReportStatus
    source: ReportSource
    ai_status: str = "NOT_REQUESTED"
