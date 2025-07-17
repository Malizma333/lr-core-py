# Reads test case data from tests.json and run tests

from engine import get_moment
from convert import convert_lines, convert_riders
import json

tests = json.load(open("tests.json", "r"))
fail_count = 0
loaded = {}

for [
    grid_version,
    frame,
    iteration,
    sub_iteration,
    track_file,
    result,
    message,
] in tests:
    if track_file in loaded:
        lines = loaded[track_file]["lines"]
        riders = loaded[track_file]["riders"]
    else:
        track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
        lines = convert_lines(track_data["lines"])
        riders = convert_riders(track_data["riders"])
        loaded[track_file] = {"lines": lines, "riders": riders}

    if (
        get_moment(grid_version, frame, iteration, sub_iteration, riders, lines)
        != result
    ):
        print(message)
        fail_count += 1

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)
