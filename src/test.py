# Reads test case data from tests.json and run tests

from engine.engine import Engine, CachedFrame
from engine.entity import MountPhase
from engine.grid import CellPosition
from engine.vector import Vector
from utils.convert import convert_track
from typing import Optional, Any
from enum import Enum
import json
import sys


class PRINT_STYLE(Enum):
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


class Tests:
    def __init__(self):
        self.engine_tests = json.load(open("tests.json", "r"))
        self.test_number = 0
        self.pass_count = 0
        self.fail_count = 0
        self.loaded_tracks: dict[str, Engine] = {}
        self.fail_message = ""

    def print_styled(self, message: str, style: PRINT_STYLE):
        print(f"{style.value}{message}\033[0m")

    def output_result(self, test_name: str, passed: bool):
        format_string = "{:<3} {:<5} {:<25}"
        if passed:
            self.print_styled(
                format_string.format(self.test_number + 1, "PASS", test_name),
                PRINT_STYLE.GREEN,
            )
            self.pass_count += 1
        else:
            self.print_styled(
                format_string.format(self.test_number + 1, "FAIL", test_name),
                PRINT_STYLE.RED,
            )
            self.print_styled(self.fail_message, PRINT_STYLE.YELLOW)
            self.fail_count += 1
            self.fail_message = ""
        self.test_number += 1

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

    def engine_states_equal(
        self,
        result_state: Optional[CachedFrame],
        expected_state: Optional[Any],
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
                result_points = result_entities[i].points
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

    def run_engine_tests(self):
        for engine_tests in self.engine_tests:
            track_file = engine_tests["file"]
            description = engine_tests["test"]
            frame = engine_tests["frame"]
            frame_state = engine_tests.get("state", None)

            if track_file not in self.loaded_tracks:
                track_data = json.load(open(f"fixtures/{track_file}.track.json", "r"))
                self.loaded_tracks[track_file] = convert_track(track_data)

            engine = self.loaded_tracks[track_file]
            test_name = f"{track_file}: {description}"
            passed = self.engine_states_equal(engine.get_frame(frame), frame_state)
            self.output_result(test_name, passed)

    def run_hash_tests(self):
        seen = dict()
        failed = False
        for i in range(-10, 11):
            for j in range(-10, 11):
                key = CellPosition(Vector(i, j), 1).get_key()
                if key in seen:
                    self.fail_message += (
                        f"duplicate key {key} for hash({(i, j)}) and hash({seen[key]})"
                    )
                    failed = True
                    break
                seen[key] = (i, j)
            if failed:
                break
        self.output_result("hash test", not failed)

    def run_tests(self):
        self.run_engine_tests()
        self.run_hash_tests()

        self.print_styled(f"Passed: {self.pass_count}", PRINT_STYLE.BOLD)
        self.print_styled(f"Failed: {self.fail_count}", PRINT_STYLE.BOLD)

        if self.fail_count > 0:
            sys.exit(1)


if __name__ == "__main__":
    Tests().run_tests()
