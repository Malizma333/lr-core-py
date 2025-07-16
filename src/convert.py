def convert_lines(lines):
    converted_lines = []
    for line in lines:
        if line["type"] != 2:
            converted_lines.append(
                {
                    "x1": line["x1"],
                    "y1": line["y1"],
                    "x2": line["x2"],
                    "y2": line["y2"],
                    "flipped": line["flipped"],
                    "left_extension": line["leftExtended"],
                    "right_extension": line["rightExtended"],
                    "multiplier": line.get("multiplier", 0),
                }
            )
    return converted_lines


def convert_riders(riders):
    converted_riders = []
    for rider in riders:
        converted_riders.append(
            {
                "position_x": rider["startPosition"]["x"],
                "position_y": rider["startPosition"]["y"],
                "velocity_x": rider["startVelocity"]["x"],
                "velocity_y": rider["startVelocity"]["y"],
                "angle": rider.get("startAngle", 0),
                "remount": bool(rider.get("remountable", False)),
            }
        )

    return converted_riders
