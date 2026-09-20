import logging
from fastapi import APIRouter, Depends
from app.schemas.flood import RouteRequest
from app.services.nasa_flood_service import NASAFloodService
from app.services.exposure_service import calculate_flood_exposure
from app.services.evidence_aggregator import aggregate_evidence
from app.services.risk_service import calculate_route_risk
from app.repositories.report_repository import ReportRepository
from app.api.reports import get_repository
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/flood", tags=["flood"])

@router.get("", summary="Retrieve flood extent for a region")
async def get_flood_data(min_lon: float, min_lat: float, max_lon: float, max_lat: float):
    service = NASAFloodService()
    # In reality, pass the bounding box to retrieve localized NASA data
    data = await service.get_flood_extent((min_lon, min_lat, max_lon, max_lat))

    # Add metadata about data source
    return {
        "success": True,
        "is_real_data": not settings.demo_mode,
        "data_status": "available",
        "data": data
    }

@router.post("/analyze-route", summary="Analyze route risk based on NASA flood observations")
async def analyze_route(payload: RouteRequest, repository: ReportRepository = Depends(get_repository)):
    # 1. Citizen Risk
    reports = repository.list_active_reports()
    route = [(point.latitude, point.longitude) for point in payload.route]
    # Default radius for risk calculation
    radius = 100.0
    citizen_risk = calculate_route_risk(reports, route, radius)

    # 2. NASA Exposure
    service = NASAFloodService()
    lats = [p.latitude for p in payload.route]
    lons = [p.longitude for p in payload.route]
    bbox = (min(lons), min(lats), max(lons), max(lats))

    nasa_exposure_data = None
    try:
        flood_data = await service.get_flood_extent(bbox)
        route_geometry = [p.model_dump() for p in payload.route]
        nasa_exposure_data = calculate_flood_exposure(route_geometry, flood_data)
        # Augment with metadata
        if flood_data.get("features"):
            meta = flood_data["features"][0]["properties"]
            nasa_exposure_data.update({
                "observation_time": meta.get("observation_time"),
                "source": meta.get("source"),
                "is_real_data": not settings.demo_mode,
            })
    except Exception as e:
        # Gracefully handle NASA failure
        logger.error(f"NASA analysis failed: {e}")

    # 3. Aggregate
    unified_results = aggregate_evidence(citizen_risk, nasa_exposure_data)

    return {
        "success": True,
        "flood_analysis": nasa_exposure_data if nasa_exposure_data else {},
        "flood_data": nasa_exposure_data.get("source", "NASA data unavailable") if nasa_exposure_data else "NASA data unavailable",
        "data": unified_results
    }
