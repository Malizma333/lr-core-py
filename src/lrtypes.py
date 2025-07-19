# Types for linting

from typing import TypedDict
from engine.vector import Vector


class PhysicsLine(TypedDict):
    ID: int
    ENDPOINTS: tuple[Vector, Vector]
    FLIPPED: bool
    LEFT_EXTENSION: bool
    RIGHT_EXTENSION: bool
    MULTIPLIER: float  # zero for blue lines, otherwise red line
