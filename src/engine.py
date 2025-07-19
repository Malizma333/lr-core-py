# The physics engine

from typing import Union
from lrtypes import (
    InitialEntityParams,
    PhysicsLine,
    EntityState,
    Entity,
    GridVersion,
    NormalBone,
    MountBone,
    RepelBone,
    ContactPoint,
)
from math_utils import Vector, hash_pair

ACCELERATION_MULT = 0.1
FRAMES_PER_SECOND = 40
NUM_ITERATIONS = 6
LINE_HITBOX_HEIGHT = 10
GRID_CELL_SIZE = 14
MAX_LINE_EXTENSION_RATIO = 0.25
GRAVITY = Vector(0, 1)
GRAVITY_SCALE = 0.175
BONE_ENDURANCE = 0.0285

# TODO remove side effects from functions
# TODO remount physics? + remount versions?
# TODO scarf physics? + scarf versions?


def make_rider(startState: InitialEntityParams) -> Entity:
    entity: Entity = {"bones": [], "points": [], "state": EntityState.MOUNTED}

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


def interact_with_line(point: ContactPoint, line: PhysicsLine):
    line_vector = line["ENDPOINTS"][1] - line["ENDPOINTS"][0]
    line_magnitude = line_vector.magnitude()
    unit_line_vector = line_vector / line_magnitude

    line_normal_vector = unit_line_vector.rot_ccw()
    if line["FLIPPED"]:
        line_normal_vector = unit_line_vector.rot_cw()

    ext_ratio = min(MAX_LINE_EXTENSION_RATIO, LINE_HITBOX_HEIGHT / line_magnitude)

    limit_left = 0.0
    if line["LEFT_EXTENSION"]:
        limit_left -= ext_ratio

    limit_right = 1.0
    if line["RIGHT_EXTENSION"]:
        limit_right += ext_ratio

    accel = line_normal_vector * ACCELERATION_MULT * line["MULTIPLIER"]

    # TODO suspicious of this
    accel = accel.rot_ccw()
    if line["FLIPPED"]:
        accel = accel.rot_cw()

    if not ((point["velocity"] @ line_normal_vector) > 0):
        return False

    line_endpoint_to_contact_point = point["position"] - line["ENDPOINTS"][0]
    dist_from_line_top = line_normal_vector @ line_endpoint_to_contact_point

    if not (0 < dist_from_line_top and dist_from_line_top < LINE_HITBOX_HEIGHT):
        return False

    pos_between_ends = (
        line_endpoint_to_contact_point @ line_vector
    ) / line_magnitude**2

    if not (limit_left <= pos_between_ends and pos_between_ends <= limit_right):
        return False

    new_position = point["position"] - dist_from_line_top * line_normal_vector
    previous_position = point["position"] - point["velocity"]
    friction = line_normal_vector.copy() * point["FRICTION"] * dist_from_line_top

    if previous_position.x >= new_position.x:
        friction.x = -friction.x
    if previous_position.y >= new_position.y:
        friction.y = -friction.y

    # Side effects
    # TODO this might be wrong (StandardLine.Interact + RedLine.Interact)
    point["position"] = new_position
    point["velocity"] = point["position"] - (previous_position + friction + accel)

    return True


def simulate_bone(
    bone: Union[NormalBone, MountBone, RepelBone],
    entity: Entity,
    entities: list[Entity],
    entity_index: int,
):
    joint1 = bone["POINT1"]
    joint2 = bone["POINT2"]
    position1 = entity["points"][joint1]["position"]
    position2 = entity["points"][joint2]["position"]
    delta = position1 - position2
    magnitude = delta.magnitude()
    rest_length = bone["RESTING_LENGTH"]

    if type(bone) == RepelBone:
        rest_length *= bone["LENGTH_FACTOR"]

    if type(bone) != RepelBone or magnitude < rest_length:
        if magnitude * 0.5 != 0:
            scalar = (magnitude - rest_length) / magnitude * 0.5
        else:
            scalar = 0

        # Side effects
        if type(bone) == MountBone and (
            entity["state"] == EntityState.DISMOUNTED
            or scalar > rest_length * BONE_ENDURANCE
        ):
            entities[entity_index]["state"] = EntityState.DISMOUNTED
        else:
            entities[entity_index]["points"][joint1]["position"] -= delta * scalar
            entities[entity_index]["points"][joint2]["position"] += delta * scalar


# TODO 6.1 and 6.2 grid cell checks (SimulationGridStatic)
# TODO class for this?
def get_grid_cell(hash: int) -> list[PhysicsLine]:
    return []


def add_line_to_grid():
    pass


def get_frame(
    grid_version: GridVersion,
    target_frame: int,
    riders: list[InitialEntityParams],
    lines: list[PhysicsLine],
) -> Union[list[Entity], None]:
    if target_frame < 0:
        return None

    entities: list[Entity] = []

    for initial_rider_state in riders:
        entities.append(make_rider(initial_rider_state))

    for frame in range(target_frame):
        for entity_index, entity in enumerate(entities):
            # gravity
            for point_index in range(len(entity["points"])):
                entities[entity_index]["points"][point_index]["velocity"] += (
                    GRAVITY * GRAVITY_SCALE
                )

            # momentum
            for point_index, point in enumerate(entity["points"]):
                entities[entity_index]["points"][point_index]["position"] += point[
                    "velocity"
                ]

            # bones
            for _ in range(NUM_ITERATIONS):
                for bone in entity["bones"]:
                    simulate_bone(bone, entity, entities, entity_index)

            # line collisions
            for point_index, point in enumerate(entity["points"]):
                position = point["position"]
                cell_position = (
                    int(position.x / GRID_CELL_SIZE),
                    int(position.y / GRID_CELL_SIZE),
                )

                # get cells in a 3 x 3, but more if line_hitbox_height >= grid_cell_size
                box_boundary_size = int(1 + LINE_HITBOX_HEIGHT / GRID_CELL_SIZE)

                for x_offset in range(-box_boundary_size, box_boundary_size + 1):
                    for y_offset in range(-box_boundary_size, box_boundary_size + 1):
                        cell = get_grid_cell(
                            hash_pair(
                                cell_position[0] + x_offset, cell_position[1] + y_offset
                            )
                        )

                        if cell == None:
                            continue

                        for line in cell:
                            _collision_occurred = interact_with_line(point, line)

    return entities
