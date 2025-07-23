# Reads test case data from tests.json and run tests

# Layout of tests.json
"""
[
  string,  (name of the test)
  uint,  (physics frame being tested)
  string,  (file name substituted into fixtures/*.track.json)
  [
    [ (first entity data)
      [ (entity's first point data)
        string,  (x position, float formatted as 17 point precision string representation)
        string,  (y position, ...)
        string,  (x velocity, ...)
        string  (y velocity, ...)
      ],
      ..., (some tests have extra points to check scarf positions)
    ],
    ...,
  ]
]
"""

from engine.engine import Engine
from engine.entity import Entity
from utils.convert import convert_lines, convert_entities, convert_version
import json
from typing import Union
import sys

LOAD_FRAME_THRESHOLD = None
tests = json.load(open("tests.json", "r"))
pass_count = 0
fail_count = 0
loaded: dict[str, Engine] = {}
# TODO dismount test + sled break test
# TODO remount single rider + multi rider tests
# Add new states for these?


# Compare 17 point precision float strings from test cases to python formatting
def compare(f: float, s: str):
    x = format(f, ".17g")
    if "e" in x:
        ind = x.index("e")
        ind2 = x.index(".")
        offset = int(x[ind + 2 :])
        if offset < 7:
            start = ""
            num = x[:ind2] + x[ind2 + 1 : ind]
            if x[0] == "-":
                start = "-"
                num = x[1:ind2] + x[ind2 + 1 : ind]
            x = start + "0." + "0" * (offset - 1) + num
    if x != s:
        print(x, "!=", s)
    return x == s


def equal(
    result_entities: Union[list[Entity], None],
    expected_entities: Union[list[list[list[str]]], None],
) -> bool:
    if result_entities == None and expected_entities == None:
        return True

    if not (result_entities != None and expected_entities != None):
        print("one state was null")
        return False

    if len(result_entities) != len(expected_entities):
        print("states did not match in length")
        return False

    for i, expected_points in enumerate(expected_entities):
        for j, expected_point_data in enumerate(expected_points):
            result_points = result_entities[i].get_all_points()
            if len(result_points) < len(expected_points):
                print("entity points did not match in length")
                return False

            result_point_data = (
                result_points[j].position.x,
                result_points[j].position.y,
                result_points[j].velocity.x,
                result_points[j].velocity.y,
            )

            if not all(
                compare(result_point_data[k], expected_point_data[k]) for k in range(4)
            ):
                return False

    return True


for [
    test_name,
    frame,
    track_file,
    frame_data,
] in tests:
    if track_file not in loaded:
        track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
        version = convert_version(track_data["version"])
        entities = convert_entities(track_data["riders"])
        lines = convert_lines(track_data["lines"])
        loaded[track_file] = Engine(version, entities, lines)

    engine = loaded[track_file]
    format_string = "{:<5} {:<15} {}"

    if LOAD_FRAME_THRESHOLD != None and frame > LOAD_FRAME_THRESHOLD:
        continue

    if equal(engine.get_frame(frame), frame_data):
        print(format_string.format("PASS", track_file, test_name))
        pass_count += 1
    else:
        print(format_string.format("FAIL", track_file, test_name))
        fail_count += 1

print("Passed", pass_count)
print("Failed", fail_count)

if fail_count > 0:
    sys.exit(1)
