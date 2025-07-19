# Types for linting

from typing import TypedDict, Union
from vector import Vector
from enum import Enum


class GridVersion(Enum):
    V6_2 = 0
    V6_1 = 1
    V6_0 = 2
    V6_7 = 3


class CellPosition(TypedDict):
    X: int
    Y: int
    REMAINDER_X: float
    REMAINDER_Y: float


class PhysicsLine(TypedDict):
    ID: int
    ENDPOINTS: tuple[Vector, Vector]
    FLIPPED: bool
    LEFT_EXTENSION: bool
    RIGHT_EXTENSION: bool
    MULTIPLIER: float  # zero for blue lines, otherwise red line


class ContactPoint(TypedDict):
    position: Vector
    velocity: Vector
    FRICTION: float


class NormalBone(TypedDict):
    POINT1: int
    POINT2: int
    RESTING_LENGTH: float


class MountBone(TypedDict):
    POINT1: int
    POINT2: int
    RESTING_LENGTH: float
    ENDURANCE: float


class RepelBone(TypedDict):
    POINT1: int
    POINT2: int
    RESTING_LENGTH: float
    LENGTH_FACTOR: float


class EntityState(Enum):
    MOUNTED = 0
    DISMOUNTED = 1


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ANGLE: float
    REMOUNT: bool


class Entity(TypedDict):
    points: list[ContactPoint]
    bones: list[Union[NormalBone, MountBone, RepelBone]]
    state: EntityState
