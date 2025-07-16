from typing import TypedDict, Union

NUM_ITERATIONS = 6
NUM_SUBITERATIONS = 22


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


def get_moment(
    grid_version: int,
    frame: int,
    iteration: int,
    sub_iteration: int,
    riders: list[Rider],
    lines: list[PhysicsLine],
) -> Union[list[Entity], None]:
    if grid_version < 0 or grid_version > 2:
        return None

    if frame < 0:
        return None

    if iteration < 0 or iteration > NUM_ITERATIONS:
        return None

    if sub_iteration < 0:
        return None

    if iteration == 0 and sub_iteration > 3:
        return None

    if iteration >= 1 and sub_iteration > NUM_SUBITERATIONS:
        return None

    return []
