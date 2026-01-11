# Converts .track.json files to in-memory representations

from engine.vector import Vector
from engine.grid import GridVersion
from engine.line import NormalLine, AccelerationLine, BaseLine
from engine.entity import Entity, RemountVersion, EntityState, InitialEntityParams
from engine.engine import Engine
from typing import Union, Any


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
        if type(remountable) is bool:
            mount_joint_version = RemountVersion.COM_V1
        elif type(remountable) is int:
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
            "ROTATION": rider.get("startAngle", 0),
            "CAN_REMOUNT": bool(rider.get("remountable", False)),
        }
        converted_entities.append(
            Entity(EntityState(initial_state, mount_joint_version))
        )

    return converted_entities


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)


def convert_track(track_data: dict[str, Any], lra: bool):
    version = convert_version(track_data["version"])
    entities = convert_riders(track_data["riders"], lra)
    lines = convert_lines(track_data["lines"])
    return Engine(version, entities, lines)
