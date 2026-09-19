from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.repositories.report_repository import DatabaseError, ReportRepository
from app.schemas.report import Condition, FloodReportCreate, RouteRiskRequest
from app.services.report_service import ReportService
from app.services.risk_service import calculate_route_risk
from app.services.s3_service import StorageError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service() -> ReportService:
    from app.main import report_service
    return report_service


def get_repository() -> ReportRepository:
    from app.main import repository
    return repository


@router.post("", status_code=status.HTTP_201_CREATED, summary="Submit a flood/road-condition report")
async def create_report(
    latitude: Annotated[float, Form(...)],
    longitude: Annotated[float, Form(...)],
    condition: Annotated[Condition, Form(...)],
    description: Annotated[str, Form(...)],
    image: Annotated[UploadFile | None, File()] = None,
    service: ReportService = Depends(get_report_service),
):
    try:
        payload = FloodReportCreate(latitude=latitude, longitude=longitude, condition=condition, description=description)
        image_bytes = await image.read(service.max_upload_bytes + 1) if image else None
        if image is not None and len(image_bytes or b"") == 0:
            raise HTTPException(status_code=400, detail={"success": False, "error": {"code": "INVALID_IMAGE", "message": "Uploaded image is empty."}})
        if image is not None and len(image_bytes or b"") > service.max_upload_bytes:
            raise HTTPException(status_code=413, detail={"success": False, "error": {"code": "UPLOAD_TOO_LARGE", "message": "Image exceeds the maximum upload size."}})
        report = service.create(
            payload, image_bytes=image_bytes,
            image_filename=image.filename if image else None,
            image_content_type=image.content_type if image else None,
        )
        return {"success": True, "data": report.model_dump(mode="json")}
    except HTTPException:
        raise
    except StorageError as exc:
        raise HTTPException(status_code=500, detail={"success": False, "error": {"code": "STORAGE_ERROR", "message": str(exc)}})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"success": False, "error": {"code": "VALIDATION_ERROR", "message": str(exc)}})
    except Exception as exc:
        logger.exception("Report creation failed")
        raise HTTPException(status_code=500, detail={"success": False, "error": {"code": "REPORT_CREATE_FAILED", "message": "The report could not be processed."}}) from exc


@router.get("/{report_id}", summary="Retrieve a flood report")
def get_report(report_id: str, repository: ReportRepository = Depends(get_repository)):
    try:
        report = repository.get_report(report_id)
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail={"success": False, "error": {"code": "DATABASE_UNAVAILABLE", "message": str(exc)}})
    if report is None:
        raise HTTPException(status_code=404, detail={"success": False, "error": {"code": "REPORT_NOT_FOUND", "message": "Report not found."}})
    return {"success": True, "data": report.model_dump(mode="json")}


@router.get("", summary="List active flood reports")
def list_reports(
    limit: int = 100,
    repository: ReportRepository = Depends(get_repository),
):
    """
    Retrieve active reports.

    Query parameters:
    - limit: maximum number of reports to return (1-1000, default 100)
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=422, detail={"success": False, "error": {"code": "INVALID_LIMIT", "message": "Limit must be between 1 and 1000."}})
        reports = repository.list_active_reports()
        # Return most recent first
        reports.sort(key=lambda r: r.created_at, reverse=True)
        return {"success": True, "data": [r.model_dump(mode="json") for r in reports[:limit]]}
    except HTTPException:
        raise
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail={"success": False, "error": {"code": "DATABASE_UNAVAILABLE", "message": str(exc)}})
    except Exception as exc:
        logger.exception("Report list retrieval failed")
        raise HTTPException(status_code=500, detail={"success": False, "error": {"code": "LIST_FAILED", "message": "Reports could not be retrieved."}}) from exc


@router.post("/near-route", summary="Find recent reports affecting a route")
def near_route(payload: RouteRiskRequest, repository: ReportRepository = Depends(get_repository)):
    try:
        reports = repository.list_active_reports()
        route = [(point.latitude, point.longitude) for point in payload.route]
        return calculate_route_risk(reports, route, payload.radius_meters).model_dump(mode="json")
    except DatabaseError as exc:
        raise HTTPException(status_code=503, detail={"success": False, "error": {"code": "DATABASE_UNAVAILABLE", "message": str(exc)}})
    except Exception as exc:
        logger.exception("Near-route risk calculation failed")
        raise HTTPException(status_code=500, detail={"success": False, "error": {"code": "RISK_CALCULATION_FAILED", "message": "Route risk could not be calculated."}}) from exc
