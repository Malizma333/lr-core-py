# Reads test case data from tests.json and run tests

from engine.entity import EntityState
from engine.engine import Engine, CachedFrame
from utils.convert import convert_lines, convert_entities, convert_version

from typing import Union, TypedDict, List, Optional
import json
import sys

# TODO remount single rider + multi rider tests


# This is not enforced at runtime, but useful for documentation
class JsonPointData(tuple[str, str, str, str]):
    """A list of 4 stringified floats: x, y, vx, vy"""


class JsonEntityState(TypedDict):
    points: List[List[str]]
    rider_state: Optional[str]
    sled_state: Optional[str]


class JsonTestState(TypedDict):
    entities: List[JsonEntityState]


class JsonTestFile(TypedDict):
    file: str  # substituted into fixtures/*.track.json
    test: str  # name/description
    frame: int  # frame number
    state: Optional[JsonTestState]  # optional state block


class Tests:
    LOAD_FRAME_THRESHOLD: Union[int, None] = None

    def __init__(self):
        self.tests = json.load(open("tests.json", "r"))
        self.pass_count = 0
        self.fail_count = 0
        self.loaded: dict[str, Engine] = {}
        self.fail_message = ""

    # Compare 17 point precision float strings from test cases to python formatting
    def compare(self, f: float, s: str):
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
            self.fail_message = f"{x} != {s}"
        return x == s

    def states_equal(
        self,
        result_state: Union[CachedFrame, None],
        expected_state: Union[JsonTestState, None],
    ) -> bool:
        if result_state is None:
            if expected_state is None:
                return True
            else:
                self.fail_message = "expected state to not be None"
                return False

        if expected_state is None:
            self.fail_message = "expected state to be None"
            return False

        result_entities = result_state.entities
        expected_entities = expected_state["entities"]

        if len(result_entities) != len(expected_entities):
            self.fail_message = "states did not match in length"
            return False

        for i, expected_entity_state in enumerate(expected_entities):
            if "rider_state" in expected_entity_state:
                if result_entities[i].binded_states[EntityState.MOUNTED.name] != (
                    expected_entity_state["rider_state"] == "MOUNTED"
                ):
                    self.fail_message = "mounted state did not match"
                    return False

            if "sled_state" in expected_entity_state:
                if result_entities[i].binded_states[EntityState.SLED_INTACT.name] != (
                    expected_entity_state["sled_state"] == "INTACT"
                ):
                    self.fail_message = "sled state did not match"
                    return False

            for j, expected_point_data in enumerate(expected_entity_state["points"]):
                result_points = result_entities[i].get_all_points()
                if len(result_points) < len(expected_entity_state):
                    self.fail_message = "entity points did not match in length"
                    return False

                result_point_data = (
                    result_points[j].position.x,
                    result_points[j].position.y,
                    result_points[j].velocity.x,
                    result_points[j].velocity.y,
                )

                if not all(
                    self.compare(result_point_data[k], expected_point_data[k])
                    for k in range(4)
                ):
                    return False

        return True

    def run_tests(self):
        for test in self.tests:
            track_file = test["file"]
            test_name = test["test"]
            frame = test["frame"]
            frame_state = test.get("state", None)

            if track_file not in self.loaded:
                track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
                version = convert_version(track_data["version"])
                entities = convert_entities(track_data["riders"])
                lines = convert_lines(track_data["lines"])
                self.loaded[track_file] = Engine(version, entities, lines)

            engine = self.loaded[track_file]
            format_string = "{:<5} {:<15} {}"

            if self.LOAD_FRAME_THRESHOLD != None and frame > self.LOAD_FRAME_THRESHOLD:
                continue

            if self.states_equal(engine.get_frame(frame), frame_state):
                print(format_string.format("PASS", track_file, test_name))
                self.pass_count += 1
            else:
                print(format_string.format("FAIL", track_file, test_name))
                print(self.fail_message)
                self.fail_message = ""
                self.fail_count += 1

        print("Passed", self.pass_count)
        print("Failed", self.fail_count)

        if self.fail_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    Tests().run_tests()
