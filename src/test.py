# Runs track tests, line grid tests, and other unit tests

import unittest
import json
import math
import sys
from enum import Enum
from typing import Optional
from engine.engine import Engine, CachedFrame
from engine.entity import MountPhase
from engine.grid import CellPosition
from engine.vector import Vector
from utils.convert import convert_track


# ANSI styles
class STYLE:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    END = "\033[0m"


class ColorTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(STYLE.GREEN + "PASS" + STYLE.END + "\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(STYLE.RED + "FAIL" + STYLE.END + "\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(STYLE.YELLOW + "ERROR" + STYLE.END + "\n")


class ColorTextTestRunner(unittest.TextTestRunner):
    resultclass = ColorTestResult  # type: ignore


class PRINT_STYLE(Enum):
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"


def compare_float(f: float, s: str) -> bool:
    """Compare float to test-case string representation at ~17-digit precision."""
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
    return x == s


def engine_states_equal(
    result_state: Optional[CachedFrame], expected_state: dict
) -> bool:
    if result_state is None or expected_state is None:
        return result_state is None and expected_state is None

    expected_entities = expected_state["entities"]
    result_entities = result_state.entities

    if len(result_entities) != len(expected_entities):
        return False

    for i, expected_entity_state in enumerate(expected_entities):
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
                return False

        if "sled_state" in expected_entity_state:
            if result_entities[i].state.sled_intact != (
                (expected_entity_state["sled_state"] or "INTACT") == "INTACT"
            ):
                return False

        for j, expected_point_data in enumerate(expected_entity_state["points"]):
            result_points = result_entities[i].points
            if len(result_points) < len(expected_entity_state):
                return False

            result_point_data = (
                result_points[j].position.x,
                result_points[j].position.y,
                result_points[j].velocity.x,
                result_points[j].velocity.y,
            )

            if not all(
                compare_float(result_point_data[k], expected_point_data[k])
                for k in range(4)
            ):
                return False

    return True


class TestEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Load all test fixtures once
        with open("fixture_tests.json", "r") as f:
            cls.engine_tests = json.load(f)
        cls.loaded_tracks: dict[str, Engine] = {}

    def test_engine_states(self):
        """Run all engine state tests in fixtures"""
        for engine_test in self.engine_tests:
            with self.subTest(engine_test=engine_test):
                track_file = engine_test["file"]
                description = engine_test["test"]
                frame = engine_test["frame"]
                frame_state = engine_test.get("state", None)

                if track_file not in self.loaded_tracks:
                    with open(f"fixtures/{track_file}.track.json", "r") as f:
                        track_data = json.load(f)
                    self.loaded_tracks[track_file] = convert_track(track_data)

                engine = self.loaded_tracks[track_file]
                result_state = engine.get_frame(frame)

                self.assertTrue(
                    engine_states_equal(result_state, frame_state),
                    msg=f"Track {track_file}, Test {description} failed",
                )


class TestGrid(unittest.TestCase):
    def test_cellposition_hashes_unique(self):
        """Ensure CellPosition.get_key() produces unique keys in -10..10 range"""
        seen = {}
        for i in range(-10, 11):
            for j in range(-10, 11):
                key = CellPosition(Vector(i, j), 1).get_key()
                self.assertNotIn(
                    key,
                    seen,
                    f"Duplicate key {key} for {(i, j)} and {seen.get(key, None)}",
                )
                seen[key] = (i, j)


class TestVector(unittest.TestCase):
    def setUp(self):
        self.v1 = Vector(1, 2)
        self.v2 = Vector(-2, 1)

    def test_add(self):
        v = self.v1 + self.v2
        self.assertTrue(math.isclose(v.x, -1))
        self.assertTrue(math.isclose(v.y, 3))

    def test_sub(self):
        v = self.v1 - self.v2
        self.assertTrue(math.isclose(v.x, 3))
        self.assertTrue(math.isclose(v.y, 1))

    def test_mul_scalar(self):
        v = self.v1 * 2
        self.assertTrue(math.isclose(v.x, 2))
        self.assertTrue(math.isclose(v.y, 4))

    def test_rmul_scalar(self):
        v = 2 * self.v1
        self.assertTrue(math.isclose(v.x, 2))
        self.assertTrue(math.isclose(v.y, 4))

    def test_div_scalar(self):
        v = self.v1 / 2
        self.assertTrue(math.isclose(v.x, 0.5))
        self.assertTrue(math.isclose(v.y, 1.0))

    def test_dot(self):
        self.assertTrue(math.isclose(self.v1 @ self.v2, 0))

    def test_cross(self):
        self.assertTrue(math.isclose(self.v1.cross(self.v2), 5))

    def test_length_and_length_sq(self):
        self.assertTrue(math.isclose(self.v1.length_sq(), 5))
        self.assertTrue(math.isclose(self.v1.length(), math.sqrt(5)))

    def test_distance(self):
        self.assertTrue(math.isclose(self.v1.distance_from(self.v2), math.sqrt(10)))

    def test_eq_and_ne(self):
        self.assertEqual(self.v1, Vector(1, 2))
        self.assertNotEqual(self.v1, self.v2)

    def test_copy(self):
        v = self.v1.copy()
        self.assertEqual(v, self.v1)
        self.assertIsNot(v, self.v1)

    def test_rot_cw(self):
        v = self.v1.rot_cw()
        self.assertTrue(math.isclose(v.x, 2))
        self.assertTrue(math.isclose(v.y, -1))

    def test_rot_ccw(self):
        v = self.v1.rot_ccw()
        self.assertTrue(math.isclose(v.x, -2))
        self.assertTrue(math.isclose(v.y, 1))

    def test_rot_preserves_length(self):
        self.assertTrue(math.isclose(self.v1.length(), self.v1.rot_cw().length()))
        self.assertTrue(math.isclose(self.v1.length(), self.v1.rot_ccw().length()))

    def test_repr(self):
        s = repr(self.v1)
        self.assertIn("1", s)
        self.assertIn("2", s)

    # ---- Extra edge cases ----

    def test_zero_vector_length(self):
        v = Vector(0, 0)
        self.assertEqual(v.length(), 0)
        self.assertEqual(v.length_sq(), 0)
        self.assertEqual(v.cross(self.v1), 0)
        self.assertEqual(v @ self.v1, 0)

    def test_negative_scalar(self):
        v = self.v1 * -1
        self.assertEqual(v, Vector(-1, -2))

    def test_division_by_negative_scalar(self):
        v = self.v1 / -2
        self.assertEqual(v, Vector(-0.5, -1))

    def test_chainable(self):
        v = (self.v1 * 2) / 2
        self.assertEqual(v, self.v1)

    def test_nan_behavior(self):
        v = Vector(float("nan"), 1)
        # NaN is never equal to anything, even itself
        self.assertNotEqual(v, v)


if __name__ == "__main__":
    unittest.main(testRunner=ColorTextTestRunner(verbosity=2, stream=sys.stdout))
