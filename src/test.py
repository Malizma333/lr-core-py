# Reads test case data from tests.json and run tests

from engine.engine import Engine
from engine.entity import Entity
from utils.convert import convert_lines, convert_entities, convert_version
import json
from typing import Union
import sys

tests = json.load(open("tests.json", "r"))
fail_count = 0
loaded: dict[str, Engine] = {}
# TODO dismount test + sled break test
# TODO remount single rider + multi rider tests
# TODO replace first feature.track.json test with scarf position test


# Compare 17 point precision float strings from test cases to python formatting
def compare(f: float, s: str):
    x = format(f, ".17g")
    if x != s:
        print(x, "!=", s)
    return x == s


def equal(
    result_state: Union[list[Entity], None],
    expected_state: Union[list[list[list[str]]], None],
) -> bool:
    if result_state == None and expected_state == None:
        return True

    if not (result_state != None and expected_state != None):
        print("one state was null")
        return False

    if len(result_state) != len(expected_state):
        print("states did not match in length")
        return False

    for i, entity_data in enumerate(expected_state):
        # Switch hands for .com order
        entity_data[6], entity_data[7] = (
            entity_data[7],
            entity_data[6],
        )
        for j, point in enumerate(entity_data):
            if len(result_state[i].points) != len(entity_data):
                print("entity points did not match in length")
                return False

            result_data = (
                (result_state[i].points[j].position.x),
                (result_state[i].points[j].position.y),
                (result_state[i].points[j].velocity.x),
                (result_state[i].points[j].velocity.y),
            )

            if not all(compare(result_data[k], point[k]) for k in range(4)):
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

    if equal(engine.get_frame(frame), frame_data):
        print(format_string.format("PASS", track_file, test_name))
    else:
        print(format_string.format("FAIL", track_file, test_name))
        fail_count += 1

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)

if fail_count > 0:
    sys.exit(1)
