from main import get_moment
import json

fail_count = 0
tests = json.load(open("tests.json", "r"))

loaded = {}

for [
    grid_version,
    frame,
    iteration,
    sub_iteration,
    riders,
    track_file,
    result,
    message,
] in tests:
    if track_file in loaded:
        lines = loaded[track_file]
    else:
        lines = json.load(open(f"fixtures/{track_file}.track.json", "r"))["lines"]
        loaded[track_file] = list(
            map(
                lambda line: {
                    "x1": line["x1"],
                    "y1": line["y1"],
                    "x2": line["x2"],
                    "y2": line["y2"],
                    "flipped": line["flipped"],
                    "left_extension": line["leftExtended"],
                    "right_extension": line["rightExtended"],
                    "multiplier": line.get("multiplier", 0),
                },
                filter(lambda line: line["type"] != 2, lines),
            )
        )

    if (
        get_moment(grid_version, frame, iteration, sub_iteration, riders, lines)
        != result
    ):
        print(message)
        fail_count += 1

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)
