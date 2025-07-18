# Converts .track.json file portions for usage in test cases
from lrtypes import PhysicsLine, EntityStartState, GridVersion
from math_utils import Vector


def convert_lines(lines: list) -> list[PhysicsLine]:
    converted_lines: list[PhysicsLine] = []
    for line in lines:
        if line["type"] != 2:
            converted_lines.append(
                {
                    "ENDPOINTS": (
                        Vector(line["x1"], line["y1"]),
                        Vector(line["x2"], line["y2"]),
                    ),
                    "FLIPPED": line["flipped"],
                    "LEFT_EXTENSION": line["leftExtended"],
                    "RIGHT_EXTENSION": line["rightExtended"],
                    "MULTIPLIER": line.get("multiplier", 0),
                }
            )
    return converted_lines


def convert_riders(riders: list) -> list[EntityStartState]:
    converted_riders: list[EntityStartState] = []
    for rider in riders:
        converted_riders.append(
            {
                "POSITION": Vector(
                    rider["startPosition"]["x"], rider["startPosition"]["y"]
                ),
                "VELOCITY": Vector(
                    rider["startVelocity"]["x"],
                    rider["startVelocity"]["y"],
                ),
                "ANGLE": rider.get("startAngle", 0),
                "REMOUNT": bool(rider.get("remountable", False)),
            }
        )

    return converted_riders


def convert_version(grid_version: str) -> GridVersion:
    if grid_version == "6.2":
        return GridVersion.V6_2
    elif grid_version == "6.1":
        return GridVersion.V6_1
    elif grid_version == "6.0":
        return GridVersion.V6_0
    else:
        return GridVersion.V6_2
