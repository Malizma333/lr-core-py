# Converts .track.json file portions for usage in test cases
from lrtypes import PhysicsLine, RiderStartState


def convert_lines(lines: list) -> list[PhysicsLine]:
    converted_lines: list[PhysicsLine] = []
    for line in lines:
        if line["type"] != 2:
            converted_lines.append(
                {
                    "X1": line["x1"],
                    "Y1": line["y1"],
                    "X2": line["x2"],
                    "Y2": line["y2"],
                    "FLIPPED": line["flipped"],
                    "LEFT_EXTENSION": line["leftExtended"],
                    "RIGHT_EXTENSION": line["rightExtended"],
                    "MULTIPLIER": line.get("multiplier", 0),
                }
            )
    return converted_lines


def convert_riders(riders: list) -> list[RiderStartState]:
    converted_riders: list[RiderStartState] = []
    for rider in riders:
        converted_riders.append(
            {
                "X": rider["startPosition"]["x"],
                "Y": rider["startPosition"]["y"],
                "DX": rider["startVelocity"]["x"],
                "DY": rider["startVelocity"]["y"],
                "ANGLE": rider.get("startAngle", 0),
                "REMOUNT": bool(rider.get("remountable", False)),
            }
        )

    return converted_riders
