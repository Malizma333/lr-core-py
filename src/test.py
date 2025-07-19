# Reads test case data from tests.json and run tests

from engine.engine import Engine
from engine.entity import Entity
from utils.convert import convert_lines, convert_riders, convert_version
import json
from typing import Union

tests = json.load(open("tests.json", "r"))
fail_count = 0
loaded: dict[str, Engine] = {}


def check_equal(
    state1: Union[list[Entity], None], state2: Union[list[list[list[float]]], None]
):
    if state1 == None and state2 == None:
        return True

    if not (state1 != None and state2 != None):
        return False

    if len(state1) != len(state2):
        return False

    for i, entity_data in enumerate(state2):
        for j, point in enumerate(entity_data):
            # Scarf points (TODO)
            if len(state1[i].points) == j:
                break

            if state1[i].points[j].position.x != point[0]:
                return False
            if state1[i].points[j].position.y != point[1]:
                return False
            if state1[i].points[j].velocity.x != point[2]:
                return False
            if state1[i].points[j].velocity.y != point[3]:
                return False

    return True


for [
    test_name,
    frame,
    track_file,
    rider_data,
] in tests:
    if track_file not in loaded:
        track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
        version = convert_version(track_data["version"])
        riders = convert_riders(track_data["riders"])
        lines = convert_lines(track_data["lines"])
        loaded[track_file] = Engine(version, riders, lines)

    engine = loaded[track_file]

    if not check_equal(engine.get_frame(frame), rider_data):
        print("FAIL\t", test_name)
        fail_count += 1
    else:
        print("PASS\t", test_name)

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)
