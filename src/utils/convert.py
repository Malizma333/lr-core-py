# Converts .track.json files to in-memory representations

from engine.vector import Vector
from engine.grid import GridVersion
from engine.line import NormalLine, AccelerationLine, BaseLine
from engine.entity import Entity, RemountVersion, EntityState
from engine.engine import Engine
import math
from typing import TypedDict, Union, Any


class InitialEntityParams(TypedDict):
    POSITION: Vector
    VELOCITY: Vector
    ROTATION: float  # In degrees
    REMOUNT: bool


def create_default_rider(
    init_state: InitialEntityParams, remount_version: RemountVersion
) -> Entity:
    entity = Entity(EntityState(init_state["REMOUNT"], remount_version))

    # Apply initial state once everything is initialized
    # This updates the contact points with initial position, velocity, and initial rotation
    # This must be applied after bone rest lengths are calculated because it does not affect them

    # Note that the use of cos and sin here may not give the same results for all numbers in different languages
    # This gets tested with 50 degrees so it happens to pass the test case
    cos_theta = math.cos(init_state["ROTATION"] * math.pi / 180)
    sin_theta = math.sin(init_state["ROTATION"] * math.pi / 180)
    origin = entity.contact_points[1].base.position  # Hardcoded to be tail

    for point in entity.points:
        offset = point.position - origin
        point.update_state(
            Vector(
                origin.x + offset.x * cos_theta - offset.y * sin_theta,
                origin.y + offset.x * sin_theta + offset.y * cos_theta,
            ),
            point.velocity,
            point.previous_position,
        )

    for point in entity.points:
        start_position = point.position + init_state["POSITION"]
        start_velocity = point.velocity + init_state["VELOCITY"]
        point.update_state(
            start_position, start_velocity, start_position - start_velocity
        )

    return entity


def convert_lines(lines: list):
    converted_lines: list[Union[NormalLine, AccelerationLine]] = []
    for line in lines:
        if line["type"] != 2 and not (
            line["x1"] == line["x2"] and line["y1"] == line["y2"]
        ):
            new_line = BaseLine(
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


def convert_riders(riders: list, LRA: bool) -> list[Entity]:
    converted_entities: list[Entity] = []
    for rider in riders:
        mount_joint_version = RemountVersion.NONE

        remountable = rider.get("remountable", None)
        if type(remountable) == bool:
            mount_joint_version = RemountVersion.COM_V1
        elif type(remountable) == int:
            mount_joint_version = RemountVersion.COM_V2

        # Override remount version
        if LRA:
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
        converted_entities.append(
            create_default_rider(initial_state, mount_joint_version)
        )

    return converted_entities


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)


def convert_track(track_data: dict[str, Any]):
    version = convert_version(track_data["version"])
    entities = convert_riders(
        track_data["riders"], track_data.get("USE_LRA_MOUNT_PHYSICS", False)
    )
    lines = convert_lines(track_data["lines"])
    return Engine(version, entities, lines)
