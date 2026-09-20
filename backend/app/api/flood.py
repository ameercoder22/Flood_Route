from fastapi import APIRouter
from app.schemas.flood import RouteRequest
from app.services.nasa_flood_service import NASAFloodService
from app.services.exposure_service import calculate_flood_exposure

from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/flood", tags=["flood"])

# ... (rest of the file remains same) ...

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
async def analyze_route(payload: RouteRequest):
    service = NASAFloodService()

    # Get bounding box from route
    lats = [p.latitude for p in payload.route]
    lons = [p.longitude for p in payload.route]
    bbox = (min(lons), min(lats), max(lons), max(lats))

    flood_data = await service.get_flood_extent(bbox)

    # Convert payload to list of dicts for the service
    route_geometry = [p.model_dump() for p in payload.route]

    analysis = calculate_flood_exposure(route_geometry, flood_data)

    return {
        "success": True,
        "flood_analysis": analysis,
        "flood_data": flood_data["features"][0]["properties"] if flood_data["features"] else {}
    }
