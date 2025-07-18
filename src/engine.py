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
NUM_SUBITERATIONS = 22
NUM_MOMENTUM_TICKS = 3

LINE_HITBOX_HEIGHT = 10
LINE_SPACE_GRID_CELL_SIZE = 14
LINE_EXTENSION_RATIO = 0.25

GRAVITY_X = 0
GRAVITY_Y = 0.175


def make_rider(startState: RiderStartState):
    # Could be array, but want indices to serve as pointers
    entity: Entity = {"bones": [], "points": {}, "joints": []}

    LEFT_FOOT_DATA = (0, 10.0, 5.0, 0.0)
    RIGHT_FOOT_DATA = (1, 10.0, 5.0, 0.0)
    LEFT_HAND_DATA = (2, 11.5, -5.0, 0.1)
    RIGHT_HAND_DATA = (3, 11.5, -5.0, 0.1)
    SHOULDER_DATA = (4, 5.0, -5.5, 0.8)
    BUTT_DATA = (5, 5.0, 0.0, 0.8)
    PEG_DATA = (6, 0.0, 0.0, 0.8)
    NOSE_DATA = (7, 15.0, 5.0, 0.0)
    TAIL_DATA = (8, 0.0, 5.0, 0.0)
    STRING_DATA = (9, 17.5, 0.0, 0.0)

    POINT_DATA = [
        LEFT_FOOT_DATA,
        RIGHT_FOOT_DATA,
        LEFT_HAND_DATA,
        RIGHT_HAND_DATA,
        SHOULDER_DATA,
        BUTT_DATA,
        PEG_DATA,
        NOSE_DATA,
        TAIL_DATA,
        STRING_DATA,
    ]

    for index, x, y, friction in POINT_DATA:
        entity["points"][index] = {
            "x": x + startState["X"],
            "y": y + startState["Y"],
            "FRICTION": friction,
            "dx": 0.0 + startState["DX"],
            "dy": 0.0 + startState["DY"],
        }

    BONE_DATA = [
        ("NORMAL", PEG_DATA[0], TAIL_DATA[0]),
        ("NORMAL", TAIL_DATA[0], NOSE_DATA[0]),
        ("NORMAL", NOSE_DATA[0], STRING_DATA[0]),
        ("NORMAL", STRING_DATA[0], PEG_DATA[0]),
        ("MOUNT", PEG_DATA[0], BUTT_DATA[0], 0.057),
        ("MOUNT", TAIL_DATA[0], BUTT_DATA[0], 0.057),
        ("MOUNT", NOSE_DATA[0], BUTT_DATA[0], 0.057),
        ("NORMAL", SHOULDER_DATA[0], BUTT_DATA[0]),
        ("NORMAL", SHOULDER_DATA[0], LEFT_HAND_DATA[0]),
        ("NORMAL", SHOULDER_DATA[0], RIGHT_HAND_DATA[0]),
        ("NORMAL", BUTT_DATA[0], LEFT_FOOT_DATA[0]),
        ("NORMAL", BUTT_DATA[0], RIGHT_FOOT_DATA[0]),
        ("MOUNT", SHOULDER_DATA[0], PEG_DATA[0], 0.057),
        ("MOUNT", STRING_DATA[0], LEFT_HAND_DATA[0], 0.057),
        ("MOUNT", STRING_DATA[0], RIGHT_HAND_DATA[0], 0.057),
        ("MOUNT", LEFT_FOOT_DATA[0], NOSE_DATA[0], 0.057),
        ("MOUNT", RIGHT_FOOT_DATA[0], NOSE_DATA[0], 0.057),
        ("REPEL", SHOULDER_DATA[0], LEFT_FOOT_DATA[0], 0.5),
        ("REPEL", SHOULDER_DATA[0], RIGHT_FOOT_DATA[0], 0.5),
    ]

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
    if target_frame < 0:
        return None

    if target_iteration < 0 or target_iteration > NUM_ITERATIONS:
        return None

    if target_sub_iteration < 0:
        return None

    if target_iteration == 0 and target_sub_iteration > NUM_MOMENTUM_TICKS:
        return None

    if target_iteration >= 1 and target_sub_iteration > NUM_SUBITERATIONS:
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
                    max_subiteration = NUM_MOMENTUM_TICKS
                else:
                    max_subiteration = NUM_SUBITERATIONS

                is_momentum_tick = iteration == 0

                for subiteration in range(max_subiteration + 1):
                    if is_momentum_tick:
                        if subiteration == 0:
                            # momentum
                            for index in entity["points"].keys():
                                dx = entities[entity_index]["points"][index]["dx"]
                                dy = entities[entity_index]["points"][index]["dy"]
                                entities[entity_index]["points"][index]["x"] += dx
                                entities[entity_index]["points"][index]["y"] += dy
                        elif subiteration == 1:
                            # friction
                            pass
                        elif subiteration == 2:
                            # acceleration
                            pass
                        else:
                            # gravity
                            for index in entity["points"].keys():
                                entities[entity_index]["points"][index]["dx"] += (
                                    GRAVITY_X
                                )
                                entities[entity_index]["points"][index]["dy"] += (
                                    GRAVITY_Y
                                )
                            pass
                    else:
                        # bones
                        pass

    return entities
