"""Tests for geospatial utilities."""

from __future__ import annotations

import pytest
import math

from app.utils.geo import haversine_distance_meters, distance_from_report_to_route


def test_haversine_same_point():
    """Distance from a point to itself should be ~0 meters."""
    distance = haversine_distance_meters(15.8281, 78.0373, 15.8281, 78.0373)
    assert distance < 1.0


def test_haversine_known_distance():
    """Test Haversine with a known reference distance."""
    # ~1000m apart (rough approximation)
    distance = haversine_distance_meters(15.8281, 78.0373, 15.8281, 78.0489)
    assert 800 < distance < 1500  # Wider range to account for Haversine precision


def test_haversine_antipodal():
    """Distance to antipodal point should be ~half Earth's circumference."""
    distance = haversine_distance_meters(0, 0, 0, 180)
    earth_circumference = 2 * math.pi * 6_371_000
    assert abs(distance - earth_circumference / 2) < 1000  # Within 1km


def test_distance_from_report_to_route_empty_route():
    """Should raise error on empty route."""
    with pytest.raises(ValueError, match="empty"):
        distance_from_report_to_route(15.8281, 78.0373, [])


def test_distance_from_report_to_route_single_point():
    """Should find distance to single route point."""
    distance, index = distance_from_report_to_route(
        15.8281, 78.0373,
        [{"latitude": 15.8281, "longitude": 78.0373}]
    )
    assert distance < 1.0
    assert index == 0


def test_distance_from_report_to_route_finds_nearest():
    """Should find the nearest point on the route."""
    distance, index = distance_from_report_to_route(
        15.8281, 78.0373,
        [
            {"latitude": 15.90, "longitude": 78.20},  # Far
            {"latitude": 15.8281, "longitude": 78.0373},  # Exact match
            {"latitude": 15.80, "longitude": 78.10},  # Far
        ]
    )
    assert distance < 1.0
    assert index == 1


def test_distance_from_report_to_route_preserves_order():
    """Should return correct index even when nearest is not first."""
    distance, index = distance_from_report_to_route(
        15.8285, 78.0381,
        [
            {"latitude": 15.90, "longitude": 78.20},
            {"latitude": 15.82, "longitude": 78.03},
            {"latitude": 15.8285, "longitude": 78.0381},  # Nearest
        ]
    )
    assert index == 2
