# Converts .track.json files to in-memory representations

from engine.vector import Vector
from engine.entity import Entity, InitialEntityParams, RemountVersion
from engine.grid import GridVersion
from engine.line import Line, NormalLine, AccelerationLine, PhysicsLine
from engine.flags import LRA_REMOUNT, LR_COM_SCARF, LRA_LEGACY_FAKIE_CHECK
import math


def create_default_rider(
    init_state: InitialEntityParams,
    mount_joint_version: RemountVersion,
) -> tuple[Entity, Entity]:
    rider = Entity(init_state["REMOUNT"], mount_joint_version)
    sled = Entity(init_state["REMOUNT"], mount_joint_version)
    sled.mount(rider)

    DEFAULT_MOUNT_ENDURANCE = 0.057
    DEFAULT_REPEL_LENGTH_FACTOR = 0.5

    if LR_COM_SCARF:
        SCARF_FRICTION = 0.2
    else:
        SCARF_FRICTION = 0.1

    # Create the contact points first, at their initial positions
    # Order doesn't really matter, added in this order to match linerider.com
    # based test cases

    # Sled points
    PEG = sled.add_contact_point(Vector(0.0, 0.0), 0.8)
    TAIL = sled.add_contact_point(Vector(0.0, 5.0), 0.0)
    NOSE = sled.add_contact_point(Vector(15.0, 5.0), 0.0)
    STRING = sled.add_contact_point(Vector(17.5, 0.0), 0.0)

    # Rider points
    BUTT = rider.add_contact_point(Vector(5.0, 0.0), 0.8)
    SHOULDER = rider.add_contact_point(Vector(5.0, -5.5), 0.8)
    RIGHT_HAND = rider.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_HAND = rider.add_contact_point(Vector(11.5, -5.0), 0.1)
    LEFT_FOOT = rider.add_contact_point(Vector(10.0, 5.0), 0.0)
    RIGHT_FOOT = rider.add_contact_point(Vector(10.0, 5.0), 0.0)
    SCARF_0 = rider.add_flutter_point(Vector(3, -5.5), SCARF_FRICTION)
    SCARF_1 = rider.add_flutter_point(Vector(1, -5.5), SCARF_FRICTION)
    SCARF_2 = rider.add_flutter_point(Vector(-1, -5.5), SCARF_FRICTION)
    SCARF_3 = rider.add_flutter_point(Vector(-3, -5.5), SCARF_FRICTION)
    SCARF_4 = rider.add_flutter_point(Vector(-5, -5.5), SCARF_FRICTION)
    SCARF_5 = rider.add_flutter_point(Vector(-7, -5.5), SCARF_FRICTION)
    SCARF_6 = rider.add_flutter_point(Vector(-9, -5.5), SCARF_FRICTION)

    # Sled bones
    SLED_BACK = sled.add_normal_bone(PEG, TAIL)
    sled.add_normal_bone(TAIL, NOSE)
    sled.add_normal_bone(NOSE, STRING)
    SLED_FRONT = sled.add_normal_bone(STRING, PEG)
    sled.add_normal_bone(PEG, NOSE)
    sled.add_normal_bone(STRING, TAIL)
    sled.add_mount_bone(PEG, BUTT, DEFAULT_MOUNT_ENDURANCE)
    sled.add_mount_bone(TAIL, BUTT, DEFAULT_MOUNT_ENDURANCE)
    sled.add_mount_bone(NOSE, BUTT, DEFAULT_MOUNT_ENDURANCE)

    # Rider bones
    TORSO = rider.add_normal_bone(SHOULDER, BUTT)
    rider.add_normal_bone(SHOULDER, LEFT_HAND)
    rider.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider.add_normal_bone(BUTT, LEFT_FOOT)
    rider.add_normal_bone(BUTT, RIGHT_FOOT)
    rider.add_normal_bone(SHOULDER, RIGHT_HAND)
    rider.add_mount_bone(SHOULDER, PEG, DEFAULT_MOUNT_ENDURANCE)
    rider.add_mount_bone(LEFT_HAND, STRING, DEFAULT_MOUNT_ENDURANCE)
    rider.add_mount_bone(RIGHT_HAND, STRING, DEFAULT_MOUNT_ENDURANCE)
    rider.add_mount_bone(LEFT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider.add_mount_bone(RIGHT_FOOT, NOSE, DEFAULT_MOUNT_ENDURANCE)
    rider.add_repel_bone(SHOULDER, LEFT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.add_repel_bone(SHOULDER, RIGHT_FOOT, DEFAULT_REPEL_LENGTH_FACTOR)
    rider.add_flutter_connector_bone(SHOULDER, SCARF_0)
    rider.add_flutter_bone(SCARF_0, SCARF_1)
    rider.add_flutter_bone(SCARF_1, SCARF_2)
    rider.add_flutter_bone(SCARF_2, SCARF_3)
    rider.add_flutter_bone(SCARF_3, SCARF_4)
    rider.add_flutter_bone(SCARF_4, SCARF_5)
    rider.add_flutter_bone(SCARF_5, SCARF_6)

    # Add the bindings with their joints
    sled.add_self_mount_joint(SLED_BACK, SLED_FRONT)
    rider.add_other_mount_joint(TORSO, SLED_FRONT)
    sled.add_self_joint(SLED_BACK, SLED_FRONT)

    if LRA_LEGACY_FAKIE_CHECK:
        rider.add_other_joint(TORSO, SLED_FRONT)

    # Apply initial state once everything is initialized
    # This updates the contact points with initial position, velocity, and initial rotation
    # This must be applied after bone rest lengths are calculated because it does not affect them

    # Note that the use of cos and sin here may not give the same results for all numbers in different languages
    # This gets tested with 50 degrees so it happens to pass the test case
    cos_theta = math.cos(init_state["ROTATION"] * math.pi / 180)
    sin_theta = math.sin(init_state["ROTATION"] * math.pi / 180)
    origin = sled.contact_points[TAIL].base.position

    for point in sled.get_overall_points():
        offset = point.position - origin
        point.update_state(
            Vector(
                origin.x + offset.x * cos_theta - offset.y * sin_theta,
                origin.y + offset.x * sin_theta + offset.y * cos_theta,
            ),
            point.velocity,
            point.previous_position,
        )

    for point in sled.get_overall_points():
        start_position = point.position + init_state["POSITION"]
        start_velocity = point.velocity + init_state["VELOCITY"]
        point.update_state(
            start_position, start_velocity, start_position - start_velocity
        )

    return (sled, rider)


def convert_lines(lines: list) -> list[Line]:
    converted_lines: list[Line] = []
    for line in lines:
        if line["type"] != 2 and not (
            line["x1"] == line["x2"] and line["y1"] == line["y2"]
        ):
            new_line = PhysicsLine(
                line["id"],
                Vector(line["x1"], line["y1"]),
                Vector(line["x2"], line["y2"]),
                line["flipped"],
                line["leftExtended"],
                line["rightExtended"],
            )
            if line["type"] == 0:
                converted_lines.append(NormalLine(new_line))
            elif line["type"] == 1:
                converted_lines.append(
                    AccelerationLine(new_line, line.get("multiplier", 1))
                )
    return converted_lines


def merge_entity_pairs(riders: list) -> list[Entity]:
    converted_entities: list[Entity] = []
    for rider in riders:
        mount_joint_version = RemountVersion.NONE

        remountable = rider.get("remountable", None)
        if type(remountable) == bool:
            mount_joint_version = RemountVersion.COM_V1
        elif type(remountable) == int:
            mount_joint_version = RemountVersion.COM_V2

        # Override remount version
        if LRA_REMOUNT:
            mount_joint_version = RemountVersion.LRA

        initial_state: InitialEntityParams = {
            "POSITION": Vector(
                rider["startPosition"]["x"], rider["startPosition"]["y"]
            ),
            "VELOCITY": Vector(
                rider["startVelocity"]["x"],
                rider["startVelocity"]["y"],
            ),
            # Convert to radians
            "ROTATION": rider.get("startAngle", 0),
            "REMOUNT": bool(rider.get("remountable", False)),
        }
        sled, rider = create_default_rider(initial_state, mount_joint_version)
        converted_entities.append(sled)
        converted_entities.append(rider)

    return converted_entities


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)
