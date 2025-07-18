# The physics engine

from typing import Union
from lrtypes import (
    EntityStartState,
    PhysicsLine,
    Entity,
    GridVersion,
    NormalBone,
    MountBone,
    RepelBone,
)
from math_utils import Vector


NUM_ITERATIONS = 6
MAX_SUBIT = 22
MAX_SUBIT_MOMENTUM = 3

LINE_HITBOX_HEIGHT = 10
LINE_SPACE_GRID_CELL_SIZE = 14
LINE_EXTENSION_RATIO = 0.25
MAX_EXTENSION_SIZE = 10

GRAVITY = Vector(0, 1)
GRAVITY_SCALE = 0.175


def make_rider(startState: EntityStartState):
    entity: Entity = {"bones": [], "points": [], "joints": []}

    POINT_DATA = [
        (Vector(10.0, 5.0), 0.0),  # left foot
        (Vector(10.0, 5.0), 0.0),  # right foot
        (Vector(11.5, -5.0), 0.1),  # left hand
        (Vector(11.5, -5.0), 0.1),  # right hand
        (Vector(5.0, -5.5), 0.8),  # shoulder
        (Vector(5.0, 0.0), 0.8),  # butt
        (Vector(0.0, 0.0), 0.8),  # peg
        (Vector(15.0, 5.0), 0.0),  # nose
        (Vector(0.0, 5.0), 0.0),  # tail
        (Vector(17.5, 0.0), 0.0),  # string
    ]

    BONE_DATA = [
        ("NORMAL", 6, 8, 0.0),  # peg-tail
        ("NORMAL", 8, 7, 0.0),  # tail-nose
        ("NORMAL", 7, 9, 0.0),  # nose-string
        ("NORMAL", 9, 6, 0.0),  # string-peg
        ("MOUNT", 6, 5, 0.057),  # peg-butt
        ("MOUNT", 8, 5, 0.057),  # tail-butt
        ("MOUNT", 7, 5, 0.057),  # nose-butt
        ("NORMAL", 4, 5, 0.0),  # shoulder-butt
        ("NORMAL", 4, 2, 0.0),  # shoulder-lefthand
        ("NORMAL", 4, 3, 0.0),  # shoulder-righthand
        ("NORMAL", 5, 0, 0.0),  # butt-leftfoot
        ("NORMAL", 5, 1, 0.0),  # butt-rightfoot
        ("MOUNT", 4, 6, 0.057),  # shoulder-peg
        ("MOUNT", 9, 2, 0.057),  # string-lefthand
        ("MOUNT", 9, 3, 0.057),  # string-righthand
        ("MOUNT", 0, 7, 0.057),  # leftfoot-nose
        ("MOUNT", 1, 7, 0.057),  # rightfoot-nose
        ("REPEL", 4, 0, 0.5),  # shoulder-leftfoot
        ("REPEL", 4, 1, 0.5),  # shoulder-rightfoot
    ]

    for init_pos, friction in POINT_DATA:
        entity["points"].append(
            {
                "position": init_pos + startState["POSITION"],
                "velocity": Vector(0, 0) + startState["VELOCITY"],
                "FRICTION": friction,
            }
        )

    for bone_tuple in BONE_DATA:
        bone_type = bone_tuple[0]
        point1_index = bone_tuple[1]
        point2_index = bone_tuple[2]
        cp1 = entity["points"][point1_index]
        cp2 = entity["points"][point2_index]
        rest_length = cp1["position"].distance_from(cp2["position"])

        if bone_type == "NORMAL":
            normal_bone: NormalBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
            }
            entity["bones"].append(normal_bone)
        elif bone_type == "MOUNT":
            mount_bone: MountBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
                "ENDURANCE": bone_tuple[3],
            }
            entity["bones"].append(mount_bone)
        else:
            repel_bone: RepelBone = {
                "POINT1": point1_index,
                "POINT2": point2_index,
                "RESTING_LENGTH": rest_length,
                "LENGTH_FACTOR": bone_tuple[3],
            }
            entity["bones"].append(repel_bone)

    return entity


# Step layout?
# Iteration 0: Momentum tick
# - gravity
# - acceleration
# - friction
# - momentum
# Iteration 1 - 6: Bone ticks
# - bone interactions
# - bone breaks
# Iteration 7: Separation ticks
# - fakie check
# - remount constraint checks


def get_moment(
    grid_version: GridVersion,
    target_frame: int,
    target_iteration: int,
    target_sub_iteration: int,
    riders: list[EntityStartState],
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
            # Max iteration clamp
            if frame == target_frame:
                max_iteration = target_iteration
            else:
                max_iteration = NUM_ITERATIONS

            for iteration in range(max_iteration + 1):
                # Max subiteration clamp
                if frame == target_frame and iteration == target_iteration:
                    max_subiteration = target_sub_iteration
                elif iteration == 0:
                    max_subiteration = MAX_SUBIT_MOMENTUM
                else:
                    max_subiteration = MAX_SUBIT

                for subiteration in range(max_subiteration + 1):
                    if iteration == 0:
                        if subiteration == 0:
                            # gravity
                            for point_index in range(len(entity["points"])):
                                entities[entity_index]["points"][point_index][
                                    "velocity"
                                ] += GRAVITY * GRAVITY_SCALE
                        elif subiteration == 1:
                            # friction
                            pass
                        elif subiteration == 2:
                            # acceleration
                            pass
                        else:
                            # momentum
                            for point_index, point in enumerate(entity["points"]):
                                entities[entity_index]["points"][point_index][
                                    "position"
                                ] += point["velocity"]
                            pass
                    else:
                        for bone_index, bone in enumerate(entity["bones"]):
                            joint1 = bone["POINT1"]
                            joint2 = bone["POINT2"]
                            position1 = entity["points"][joint1]["position"]
                            position2 = entity["points"][joint2]["position"]
                            delta = position1 - position2
                            magnitude = delta.magnitude()

    return entities
