# Reads test case data from tests.json and run tests

from engine import Engine
from convert import convert_lines, convert_riders, convert_version
import json
from typing import Union
from lrtypes import Entity

tests = json.load(open("tests.json", "r"))
fail_count = 0
loaded: dict[str, Engine] = {}


def check_equal(state1: Union[list[Entity], None], state2: Union[list[Entity], None]):
    if state1 == None and state2 == None:
        return True

    if not (state1 != None and state2 != None):
        return False

    if len(state1) != len(state2):
        return False

    for i in range(len(state1)):
        for index in state1[i]["points"]:
            return False
            pass
            # if state1[i]["points"][index]["x"] != state2[i]["points"][index]["x"]:
            #     return False
            # if state1[i]["points"][index]["y"] != state2[i]["points"][index]["y"]:
            #     return False

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
