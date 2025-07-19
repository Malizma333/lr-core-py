# Converts .track.json file portions for usage in test cases

from lrtypes import PhysicsLine, InitialEntityParams, GridVersion
from vector import Vector


# TODO add scenery lines to grid as well?
def convert_lines(lines: list) -> list[PhysicsLine]:
    converted_lines: list[PhysicsLine] = []
    for line in lines:
        if line["type"] != 2:
            converted_lines.append(
                {
                    "ID": line["id"],
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


def convert_riders(riders: list) -> list[InitialEntityParams]:
    converted_riders: list[InitialEntityParams] = []
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


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
        "6.7": GridVersion.V6_7,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)
