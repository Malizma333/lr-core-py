# Converts .track.json file portions for usage in test cases

from engine.vector import Vector
from engine.entity import (
    create_default_rider,
    RiderVehiclePair,
    InitialEntityParams,
    RemountVersion,
)
from engine.grid import GridVersion
from engine.line import Line, NormalLine, AccelerationLine, PhysicsLine


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


def convert_entities(riders: list) -> list[RiderVehiclePair]:
    converted_entities: list[RiderVehiclePair] = []
    for rider in riders:
        remount_version = RemountVersion.NONE

        remountable = rider.get("remountable", None)
        if remountable == True:
            remount_version = RemountVersion.COM_V1
        elif remountable == 1:
            remount_version = RemountVersion.COM_V2

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
        converted_entities.append(create_default_rider(initial_state, remount_version))

    return converted_entities


def convert_version(grid_version_string: str) -> GridVersion:
    grid_version_mapping = {
        "6.0": GridVersion.V6_0,
        "6.1": GridVersion.V6_1,
        "6.2": GridVersion.V6_2,
    }

    return grid_version_mapping.get(grid_version_string, GridVersion.V6_2)
