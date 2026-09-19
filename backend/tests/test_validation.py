import pytest
from pydantic import ValidationError

from app.schemas.report import Condition, FloodReportCreate


def test_coordinates_are_validated():
    with pytest.raises(ValidationError):
        FloodReportCreate(latitude=91, longitude=0, condition=Condition.FLOODED, description="abc")
    with pytest.raises(ValidationError):
        FloodReportCreate(latitude=0, longitude=181, condition=Condition.FLOODED, description="abc")


def test_description_limits():
    with pytest.raises(ValidationError):
        FloodReportCreate(latitude=0, longitude=0, condition=Condition.FLOODED, description="a")
    payload = FloodReportCreate(latitude=0, longitude=0, condition=Condition.FLOODED, description="  road flooded  ")
    assert payload.description == "road flooded"
