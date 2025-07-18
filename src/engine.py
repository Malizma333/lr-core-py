# The physics engine

from typing import Union
from lrtypes import (
    RiderStartState,
    PhysicsLine,
    Entity,
    GridVersion,
    NormalBone,
    MountBone,
    RepelBone,
)


NUM_ITERATIONS = 6
MAX_SUBIT = 22
MAX_SUBIT_MOMENTUM = 3

LINE_HITBOX_HEIGHT = 10
LINE_SPACE_GRID_CELL_SIZE = 14
LINE_EXTENSION_RATIO = 0.25

GRAVITY_X = 0
GRAVITY_Y = 0.175


def make_rider(startState: RiderStartState):
    entity: Entity = {"bones": [], "points": [], "joints": []}

    POINT_DATA = [
        (10.0, 5.0, 0.0),  # left foot
        (10.0, 5.0, 0.0),  # right foot
        (11.5, -5.0, 0.1),  # left hand
        (11.5, -5.0, 0.1),  # right hand
        (5.0, -5.5, 0.8),  # shoulder
        (5.0, 0.0, 0.8),  # butt
        (0.0, 0.0, 0.8),  # peg
        (15.0, 5.0, 0.0),  # nose
        (0.0, 5.0, 0.0),  # tail
        (17.5, 0.0, 0.0),  # string
    ]

    BONE_DATA = [
        ("NORMAL", 6, 8),  # peg-tail
        ("NORMAL", 8, 7),  # tail-nose
        ("NORMAL", 7, 9),  # nose-string
        ("NORMAL", 9, 6),  # string-peg
        ("MOUNT", 6, 5, 0.057),  # peg-butt
        ("MOUNT", 8, 5, 0.057),  # tail-butt
        ("MOUNT", 7, 5, 0.057),  # nose-butt
        ("NORMAL", 4, 5),  # shoulder-butt
        ("NORMAL", 4, 2),  # shoulder-lefthand
        ("NORMAL", 4, 3),  # shoulder-righthand
        ("NORMAL", 5, 0),  # butt-leftfoot
        ("NORMAL", 5, 1),  # butt-rightfoot
        ("MOUNT", 4, 6, 0.057),  # shoulder-peg
        ("MOUNT", 9, 2, 0.057),  # string-lefthand
        ("MOUNT", 9, 3, 0.057),  # string-righthand
        ("MOUNT", 0, 7, 0.057),  # leftfoot-nose
        ("MOUNT", 1, 7, 0.057),  # rightfoot-nose
        ("REPEL", 4, 0, 0.5),  # shoulder-leftfoot
        ("REPEL", 4, 1, 0.5),  # shoulder-rightfoot
    ]

    for x, y, friction in POINT_DATA:
        entity["points"].append(
            {
                "x": x + startState["X"],
                "y": y + startState["Y"],
                "FRICTION": friction,
                "dx": 0.0 + startState["DX"],
                "dy": 0.0 + startState["DY"],
            }
        )

    for bone_tuple in BONE_DATA:
        bone_type = bone_tuple[0]
        point1 = bone_tuple[1]
        point2 = bone_tuple[2]
        cp1 = entity["points"][point1]
        cp2 = entity["points"][point2]
        rest_length = ((cp1["x"] - cp2["x"]) ** 2 + (cp1["y"] - cp2["y"]) ** 2) ** 0.5
        if bone_type == "NORMAL":
            normal_bone: NormalBone = {
                "POINT1": point1,
                "POINT2": point2,
                "RESTING_LENGTH": rest_length,
            }
            entity["bones"].append(normal_bone)
        elif bone_type == "MOUNT":
            mount_bone: MountBone = {
                "POINT1": point1,
                "POINT2": point2,
                "RESTING_LENGTH": rest_length,
                "ENDURANCE": bone_tuple[3],
            }
            entity["bones"].append(mount_bone)
        else:
            repel_bone: RepelBone = {
                "POINT1": point1,
                "POINT2": point2,
                "RESTING_LENGTH": rest_length,
                "LENGTH_FACTOR": bone_tuple[3],
            }
            entity["bones"].append(repel_bone)

    return entity


def get_moment(
    grid_version: GridVersion,
    target_frame: int,
    target_iteration: int,
    target_sub_iteration: int,
    riders: list[RiderStartState],
    lines: list[PhysicsLine],
) -> Union[list[Entity], None]:
    if target_frame < -1:
        return None

    if target_iteration < 0 or target_iteration > NUM_ITERATIONS:
        return None

    if target_sub_iteration < 0:
        return None

    if target_iteration == 0 and target_sub_iteration > MAX_SUBIT_MOMENTUM:
        return None

    if target_iteration >= 1 and target_sub_iteration > MAX_SUBIT:
        return None

    entities: list[Entity] = []

    for initial_rider_state in riders:
        entities.append(make_rider(initial_rider_state))

    max_frame = target_frame
    for frame in range(max_frame + 1):
        for entity_index, entity in enumerate(entities):
            if frame == target_frame:
                max_iteration = target_iteration
            else:
                max_iteration = NUM_ITERATIONS

            for iteration in range(max_iteration + 1):
                if frame == target_frame and iteration == target_iteration:
                    max_subiteration = target_sub_iteration
                elif iteration == 0:
                    max_subiteration = MAX_SUBIT_MOMENTUM
                else:
                    max_subiteration = MAX_SUBIT

                is_momentum_tick = iteration == 0

                for subiteration in range(max_subiteration + 1):
                    if is_momentum_tick:
                        if subiteration == 0:
                            # gravity
                            for index in range(len(entity["points"])):
                                entities[entity_index]["points"][index]["dx"] += (
                                    GRAVITY_X
                                )
                                entities[entity_index]["points"][index]["dy"] += (
                                    GRAVITY_Y
                                )
                        elif subiteration == 1:
                            # friction
                            pass
                        elif subiteration == 2:
                            # acceleration
                            pass
                        else:
                            # momentum
                            for index in range(len(entity["points"])):
                                dx = entities[entity_index]["points"][index]["dx"]
                                dy = entities[entity_index]["points"][index]["dy"]
                                entities[entity_index]["points"][index]["x"] += dx
                                entities[entity_index]["points"][index]["y"] += dy
                            pass
                    else:
                        pass

    return entities
