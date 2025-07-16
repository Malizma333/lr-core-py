from typing import Union
from lrtypes import Rider, PhysicsLine, Entity

NUM_ITERATIONS = 6
NUM_SUBITERATIONS = 22


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
