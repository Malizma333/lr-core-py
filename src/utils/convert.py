# Converts .track.json file portions for usage in test cases

import math
from engine.vector import Vector
from engine.entity import create_default_rider, Entity, InitialEntityParams
from engine.grid import GridVersion
from engine.line import PhysicsLine


def convert_lines(lines: list) -> list[PhysicsLine]:
    converted_lines: list[PhysicsLine] = []
    for line in lines:
        if line["type"] != 2 and not (
            line["x1"] == line["x2"] and line["y1"] == line["y2"]
        ):
            converted_lines.append(
                PhysicsLine(
                    line["id"],
                    Vector(line["x1"], line["y1"]),
                    Vector(line["x2"], line["y2"]),
                    line["flipped"],
                    line["leftExtended"],
                    line["rightExtended"],
                    line.get("multiplier", 1 if line["type"] == 1 else 0),
                )
            )
    return converted_lines


def convert_entities(riders: list) -> list[Entity]:
    converted_entities: list[Entity] = []
    for rider in riders:
        initial_state: InitialEntityParams = {
            "POSITION": Vector(
                rider["startPosition"]["x"], rider["startPosition"]["y"]
            ),
            "VELOCITY": Vector(
                rider["startVelocity"]["x"],
                rider["startVelocity"]["y"],
            ),
            "ROTATION": rider.get("startAngle", 0) * math.pi / 180,
            "REMOUNT": bool(rider.get("remountable", False)),
        }
        converted_entities.append(create_default_rider(initial_state))

    return converted_entities


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
        "6.7": GridVersion.V6_7,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)
