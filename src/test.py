# Reads test case data from tests.json and run tests

from engine.engine import Engine, CachedFrame
from engine.entity import MountPhase
from utils.convert import convert_lines, convert_riders, convert_version

from typing import TypedDict, List, Optional
from enum import Enum
import json
import sys

# Test flags to filter results
MAX_FRAME: Optional[int] = 80
TARGET_TESTS: Optional[tuple[int, int]] = None


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


class PRINT_STYLE(Enum):
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


def print_styled(message: str, style: PRINT_STYLE):
    print(f"{style.value}{message}\033[0m")


class Tests:
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
            self.fail_message += f"{x} != {s}"
        return x == s

    def states_equal(
        self,
        result_state: Optional[CachedFrame],
        expected_state: Optional[JsonTestState],
    ) -> bool:
        if result_state is None:
            if expected_state is None:
                return True
            else:
                self.fail_message += "expected state to not be None"
                return False

        if expected_state is None:
            self.fail_message += "expected state to be None"
            return False

        expected_entities = expected_state["entities"]
        result_entities = result_state.entities

        if len(result_entities) != len(expected_entities):
            self.fail_message += "states did not match in length"
            return False

        for i, expected_entity_state in enumerate(expected_entities):
            self.fail_message = f"rider {i}: "

            if "mount_state" in expected_entity_state:
                rider_state_map = {
                    "MOUNTED": MountPhase.MOUNTED,
                    "DISMOUNTING": MountPhase.DISMOUNTING,
                    "DISMOUNTED": MountPhase.DISMOUNTED,
                    "REMOUNTING": MountPhase.REMOUNTING,
                }
                if result_entities[i].state.mount_phase != rider_state_map.get(
                    expected_entity_state["mount_state"] or "", MountPhase.MOUNTED
                ):
                    self.fail_message += (
                        "mounted state did not match: "
                        + f"expected {expected_entity_state['mount_state']} got {result_entities[i].state.mount_phase}"
                    )
                    return False

            if "sled_state" in expected_entity_state:
                if result_entities[i].state.sled_intact != (
                    (expected_entity_state["sled_state"] or "INTACT") == "INTACT"
                ):
                    self.fail_message += (
                        "sled state did not match: "
                        + f"expected {expected_entity_state['sled_state']} got {result_entities[i].state.sled_intact}"
                    )
                    return False

            for j, expected_point_data in enumerate(expected_entity_state["points"]):
                result_points = result_entities[i].base_points
                if len(result_points) < len(expected_entity_state):
                    self.fail_message += "entity points did not match in length"
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
        for i, test in enumerate(self.tests):
            if (
                TARGET_TESTS != None
                and (TARGET_TESTS[0] > i + 1 or i + 1 > TARGET_TESTS[1])
            ) or (MAX_FRAME != None and test["frame"] > MAX_FRAME):
                continue

            track_file = test["file"]
            test_name = test["test"]
            frame = test["frame"]
            frame_state = test.get("state", None)

            if track_file not in self.loaded:
                track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
                version = convert_version(track_data["version"])
                entities = convert_riders(track_data["riders"])
                lines = convert_lines(track_data["lines"])
                self.loaded[track_file] = Engine(version, entities, lines)

            engine = self.loaded[track_file]
            format_string = "{:<2} {:<5} {:<25} {}"

            if self.states_equal(engine.get_frame(frame), frame_state):
                print_styled(
                    format_string.format(str(i + 1), "PASS", track_file, test_name),
                    PRINT_STYLE.GREEN,
                )
                self.pass_count += 1
            else:
                print_styled(
                    format_string.format(str(i + 1), "FAIL", track_file, test_name),
                    PRINT_STYLE.RED,
                )
                print_styled(self.fail_message, PRINT_STYLE.YELLOW)
                self.fail_count += 1
            self.fail_message = ""

        print_styled(f"Passed: {self.pass_count}", PRINT_STYLE.BOLD)
        print_styled(f"Failed: {self.fail_count}", PRINT_STYLE.BOLD)

        if self.fail_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    Tests().run_tests()
