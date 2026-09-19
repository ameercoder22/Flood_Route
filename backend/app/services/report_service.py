from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.repositories.report_repository import ReportRepository
from app.schemas.report import AIAnalysisResult, EvidenceFlags, FinalAnalysis, FloodReportCreate, ReportSource, ReportStatus, StoredReport, VehicleImpact, Severity, Condition
from app.services.bedrock_service import AIAnalysisError, AIProvider
from app.services.s3_service import S3Service, StorageError

logger = logging.getLogger(__name__)


def combine_evidence(text: AIAnalysisResult | None, image: AIAnalysisResult | None) -> FinalAnalysis:
    evidence = EvidenceFlags(text=text is not None, image=image is not None)
    analyses = [item for item in (text, image) if item is not None]
    if not analyses:
        return FinalAnalysis(
            flood_detected=False, condition=Condition.UNKNOWN, severity=Severity.UNKNOWN,
            vehicle_impact=VehicleImpact.UNKNOWN, confidence=0.0,
            reason="No AI evidence was available.", evidence=evidence,
        )
    if len(analyses) == 1:
        result = analyses[0]
        return FinalAnalysis(**result.model_dump(), evidence=evidence)

    severity_rank = {Severity.UNKNOWN: 0, Severity.LOW: 1, Severity.MEDIUM: 2, Severity.HIGH: 3}
    selected_severity = max((item.severity for item in analyses), key=lambda item: severity_rank[item])
    conditions = [item.condition for item in analyses]
    if conditions[0] == conditions[1]:
        condition = conditions[0]
    else:
        condition = next((item for item in conditions if item == Condition.FLOODED), Condition.UNKNOWN)
        if condition == Condition.UNKNOWN:
            condition = next((item for item in conditions if item != Condition.UNKNOWN), Condition.UNKNOWN)
    impacts = [item.vehicle_impact for item in analyses]
    impact_rank = {
        VehicleImpact.UNKNOWN: 0, VehicleImpact.NONE_REPORTED: 1, VehicleImpact.POSSIBLE: 2,
        VehicleImpact.TWO_WHEELERS_LIKELY_AFFECTED: 3, VehicleImpact.MOST_VEHICLES_LIKELY_AFFECTED: 4,
    }
    vehicle_impact = max(impacts, key=lambda item: impact_rank[item])
    confidence = min(1.0, max(item.confidence for item in analyses) + 0.05 if conditions[0] == conditions[1] else max(item.confidence for item in analyses))
    reasons = " ".join(item.reason for item in analyses)
    return FinalAnalysis(
        flood_detected=any(item.flood_detected for item in analyses), condition=condition,
        severity=selected_severity, vehicle_impact=vehicle_impact, confidence=confidence,
        reason=reasons[:1000], evidence=evidence,
    )


class ReportService:
    def __init__(self, repository: ReportRepository, ai: AIProvider, s3: S3Service | None, max_upload_bytes: int, allowed_types: set[str]):
        self.repository = repository
        self.ai = ai
        self.s3 = s3
        self.max_upload_bytes = max_upload_bytes
        self.allowed_types = allowed_types

    def create(self, payload: FloodReportCreate, image_bytes: bytes | None = None, image_filename: str | None = None, image_content_type: str | None = None) -> StoredReport:
        report_id = "R" + uuid.uuid4().hex[:12].upper()
        now = datetime.now(timezone.utc)
        image_key = None
        image_uploaded = False
        ai_status = "NOT_REQUESTED"

        if image_bytes is not None:
            if self.s3 is None:
                raise StorageError("Image storage is not configured")
            self.s3.validate_image(image_content_type or "", image_filename or "", image_bytes, self.max_upload_bytes, self.allowed_types)
            image_key = self.s3.upload_image(report_id, image_filename or "upload", image_content_type or "", image_bytes)
            image_uploaded = True

        text_analysis = None
        image_analysis = None
        ai_failures = []
        try:
            text_analysis = self.ai.analyze_text_report(payload.description)
            ai_status = "SUCCESS"
        except AIAnalysisError as exc:
            ai_failures.append(str(exc))

        if image_bytes is not None:
            try:
                image_analysis = self.ai.analyze_flood_image(image_bytes, image_content_type or "")
                ai_status = "SUCCESS" if ai_status == "SUCCESS" else "IMAGE_ONLY_SUCCESS"
            except AIAnalysisError as exc:
                ai_failures.append(str(exc))

        final = combine_evidence(text_analysis, image_analysis)
        # The citizen-selected condition is retained as a safe fallback if AI is unavailable.
        if text_analysis is None and image_analysis is None:
            final = FinalAnalysis(
                flood_detected=payload.condition in {Condition.FLOODED, Condition.WATERLOGGED},
                condition=payload.condition, severity=Severity.UNKNOWN,
                vehicle_impact=VehicleImpact.UNKNOWN, confidence=0.0,
                reason="AI analysis unavailable; using the citizen-selected condition only.",
                evidence=EvidenceFlags(text=False, image=False),
            )
            ai_status = "FAILED"
        elif ai_failures:
            ai_status = "PARTIAL_FAILURE"

        source = ReportSource.AI_ASSISTED if text_analysis or image_analysis else ReportSource.CITIZEN
        report = StoredReport(
            report_id=report_id, latitude=payload.latitude, longitude=payload.longitude,
            condition=final.condition if final.condition != Condition.UNKNOWN else payload.condition,
            severity=final.severity, description=payload.description,
            vehicle_impact=final.vehicle_impact, flood_detected=final.flood_detected,
            ai_confidence=final.confidence if final.evidence.text or final.evidence.image else None,
            ai_reason=final.reason, text_analysis=text_analysis, image_analysis=image_analysis,
            final_analysis=final, image_key=image_key, image_uploaded=image_uploaded,
            created_at=now, updated_at=now, status=ReportStatus.ACTIVE, source=source,
            ai_status=ai_status,
        )
        self.repository.create_report(report)
        return report
