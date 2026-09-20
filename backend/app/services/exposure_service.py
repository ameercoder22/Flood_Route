from shapely.geometry import shape, LineString, Polygon
from shapely.ops import transform
import pyproj

def calculate_flood_exposure(route_geometry: list[dict], flood_data: dict) -> dict:
    """
    Calculates flood exposure percentage for a route using real NASA observation geometry.

    Args:
        route_geometry: List of {"latitude": float, "longitude": float}
        flood_data: GeoJSON FeatureCollection

    Returns:
        dict: {
            "route_distance_km": float,
            "flood_affected_distance_km": float,
            "flood_exposure_percentage": float
        }
    """
    # 1. Convert route to LineString
    route_coords = [(p["longitude"], p["latitude"]) for p in route_geometry]
    route_line = LineString(route_coords)

    # Convert to a projected coordinate system to calculate accurate distances in meters (e.g., EPSG:3857)
    project = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True).transform
    route_line_proj = transform(project, route_line)

    total_distance_m = route_line_proj.length

    # 2. Convert flood data features to Multipolygon
    flood_polygons = []
    for feature in flood_data.get("features", []):
        geom = shape(feature["geometry"])
        flood_polygons.append(transform(project, geom))

    if not flood_polygons:
        return {
            "route_distance_km": total_distance_m / 1000,
            "flood_affected_distance_km": 0.0,
            "flood_exposure_percentage": 0.0
        }

    # 3. Intersection
    # Use unary_union to merge flood polygons
    from shapely.ops import unary_union
    flood_union = unary_union(flood_polygons)

    intersection = route_line_proj.intersection(flood_union)
    affected_distance_m = intersection.length

    return {
        "route_distance_km": round(total_distance_m / 1000, 2),
        "flood_affected_distance_km": round(affected_distance_m / 1000, 2),
        "flood_exposure_percentage": round((affected_distance_m / total_distance_m) * 100, 2) if total_distance_m > 0 else 0.0
    }
