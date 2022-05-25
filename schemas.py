from typing import List, Union, Optional
from enum import Enum

from pydantic import BaseModel, validator


class Type(str, Enum):
    S = 'S'
    C = 'C'
    M = 'M'

class Asteroids(BaseModel):
    name: str
    type: Type
    size: float
    distance: float
    location: dict
    probability_of_collision: float
    observation_time: str

    @validator("location")
    def check_coordinates(cls,location):
        if not ('x' in location or 'y' and location and 'z' in location):
            raise ValueError(f"location coordinates missing. All three are required.")
        return location


class Asteroids_update(BaseModel):
    name: str
    type: Optional[Type]
    size: Optional[float]
    distance: Optional[float]
    location: Optional[dict]
    probability_of_collision: Optional[float]
    observation_time: Optional[str]

    @validator("location")
    def check_coordinates(cls,location):
        if not ('x' in location or 'y' and location and 'z' in location):
            raise ValueError(f"location coordinates missing. All three x,y,z are required.")
        return location

