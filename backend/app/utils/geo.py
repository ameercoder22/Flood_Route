"""Geospatial utilities for FloodRoute using Haversine distance."""

from __future__ import annotations

import math


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using the Haversine formula.

    Args:
        lat1, lon1: First point latitude/longitude in decimal degrees
        lat2, lon2: Second point latitude/longitude in decimal degrees

    Returns:
        Distance in meters
    """
    earth_radius_m = 6_371_000.0

    p1_rad = math.radians(lat1)
    p2_rad = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = math.sin(dp / 2) ** 2 + math.cos(p1_rad) * math.cos(p2_rad) * math.sin(dl / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    return earth_radius_m * c


def distance_from_report_to_route(
    report_latitude: float,
    report_longitude: float,
    route_points: list[dict[str, float]]
) -> tuple[float, int]:
    """
    Find the minimum distance from a report point to any point on a route.

    Args:
        report_latitude: Report latitude in decimal degrees
        report_longitude: Report longitude in decimal degrees
        route_points: List of route points, each with 'latitude' and 'longitude' keys

    Returns:
        Tuple of (minimum_distance_meters, nearest_route_point_index)
    """
    if not route_points:
        raise ValueError("Route points list cannot be empty")

    distances = [
        haversine_distance_meters(
            report_latitude,
            report_longitude,
            point["latitude"],
            point["longitude"]
        )
        for point in route_points
    ]

    min_distance = min(distances)
    nearest_index = distances.index(min_distance)

    return min_distance, nearest_index
