from main import get_moment
from convert import convert_lines
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
        lines = convert_lines(
            json.load(open(f"fixtures/{track_file}.track.json", "r"))["lines"]
        )
        loaded[track_file] = lines

    if (
        get_moment(grid_version, frame, iteration, sub_iteration, riders, lines)
        != result
    ):
        print(message)
        fail_count += 1

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)
