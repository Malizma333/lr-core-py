# Runs track tests, line grid tests, and other unit tests

import unittest
import json
import math
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from engine.grid import CellPosition
from engine.vector import Vector
from utils.create_fixture_test import sanitize, create_fixture_test

# Caps the engine test cases that get included based on frame * rider calculations
MAX_ENGINE_CALCS: Optional[int] = 500


class ColorTestResult(unittest.TextTestResult):
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    END = "\033[0m"

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(self.GREEN + "PASS" + self.END + "\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(self.RED + "FAIL" + self.END + "\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(self.YELLOW + "ERROR" + self.END + "\n")


class ColorTextTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, resultclass=ColorTestResult, **kwargs)  # type: ignore


class TestGrid(unittest.TestCase):
    def test_cellposition_hashes_unique(self):
        """Ensure CellPosition.get_key() produces unique keys for signed integer pairs"""
        seen = {}
        for i in range(-10, 11):
            for j in range(-10, 11):
                key = CellPosition(Vector(i, j), 1).get_key()
                self.assertNotIn(
                    key,
                    seen,
                    f"Duplicate key {key} for {(i, j)} and {seen.get(key)}",
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
        self.assertNotEqual(v, v)


def create_fixture_tests():
    fixtures: list[Dict[str, Any]] = json.loads(Path("fixture_tests.json").read_text())
    _classes_by_file: dict[str, type] = {}

    for i, fixture in enumerate(fixtures):
        group = fixture["file"]
        class_name = f"Test_{sanitize(group)}"
        if class_name not in globals():
            cls = type(
                class_name,
                (unittest.TestCase,),
                {"__doc__": f"Fixture tests for '{group}'"},
            )
            globals()[class_name] = cls
            _classes_by_file[group] = cls

        frame = fixture.get("frame", 0)
        num_riders = len(fixture.get("state", {}).get("entities", []))
        complexity = frame * num_riders

        if MAX_ENGINE_CALCS != None and complexity > MAX_ENGINE_CALCS:
            continue

        func_name = f"test_{i}_{sanitize(fixture['test'])}"
        setattr(_classes_by_file[group], func_name, create_fixture_test(fixture))


if __name__ == "__main__":
    create_fixture_tests()
    unittest.main(testRunner=ColorTextTestRunner(verbosity=2, stream=sys.stdout))
