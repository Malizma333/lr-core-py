from typing import TypedDict


class Rider(TypedDict):
    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float
    angle: float
    remount: bool


class PhysicsLine(TypedDict):
    x1: float
    y1: float
    x2: float
    y2: float
    flipped: bool
    left_extension: bool
    right_extension: bool
    multiplier: float


class ContactPoint(TypedDict):
    position_x: float
    position_y: float
    velocity_x: float
    velocity_y: float


class Entity(TypedDict):
    points: list[ContactPoint]
