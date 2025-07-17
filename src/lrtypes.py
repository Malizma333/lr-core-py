# Types for linting

from typing import TypedDict, Union
from enum import Enum


class GridVersion(Enum):
    V6_0 = 0
    V6_1 = 1
    V6_2 = 2


class RiderStartState(TypedDict):
    X: float
    Y: float
    DX: float
    DY: float
    ANGLE: float
    REMOUNT: bool


class PhysicsLine(TypedDict):
    X1: float
    Y1: float
    X2: float
    Y2: float
    FLIPPED: bool
    LEFT_EXTENSION: bool
    RIGHT_EXTENSION: bool
    MULTIPLIER: float  # zero for blue lines, otherwise red line


class ContactPoint(TypedDict):
    x: float
    y: float
    dx: float
    dy: float
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


class Joint(TypedDict):
    POINT_PAIR1: tuple[int, int]
    POINT_PAIR2: tuple[int, int]


class Entity(TypedDict):
    points: dict[int, ContactPoint]
    bones: list[Union[NormalBone, MountBone, RepelBone]]
    joints: list[Joint]
