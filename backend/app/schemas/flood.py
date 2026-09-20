from pydantic import BaseModel
from typing import List

class Point(BaseModel):
    latitude: float
    longitude: float

class RouteRequest(BaseModel):
    route: List[Point]
