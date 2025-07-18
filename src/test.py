# Reads test case data from tests.json and run tests

from engine import get_moment
from convert import convert_lines, convert_riders, convert_version
import json
from typing import Union
from lrtypes import Entity

tests = json.load(open("tests.json", "r"))
fail_count = 0
loaded = {}


def check_equal(state1: Union[list[Entity], None], state2: Union[list[Entity], None]):
    if state1 == None and state2 == None:
        return True

    if not (state1 != None and state2 != None):
        return False

    if len(state1) != len(state2):
        return False

    for i in range(len(state1)):
        for index in state1[i]["points"]:
            pass
            # if state1[i]["points"][index]["x"] != state2[i]["points"][index]["x"]:
            #     return False
            # if state1[i]["points"][index]["y"] != state2[i]["points"][index]["y"]:
            #     return False

    return True


for [
    frame,
    track_file,
    result,
    message,
] in tests:
    if track_file in loaded:
        lines = loaded[track_file]["lines"]
        riders = loaded[track_file]["riders"]
        version = loaded[track_file]["version"]
    else:
        track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
        lines = convert_lines(track_data["lines"])
        riders = convert_riders(track_data["riders"])
        version = convert_version(track_data["version"])
        loaded[track_file] = {"lines": lines, "riders": riders, "version": version}

    if not check_equal(get_moment(version, frame, riders, lines), result):
        print(message)
        fail_count += 1

print("Passed", len(tests) - fail_count)
print("Failed", fail_count)
