import re
import json
import unittest
import struct
from typing import Optional
from engine.engine import Engine
from engine.entity import MountPhase
from utils.convert import convert_track

_LOADED_ENGINES: dict[str, Engine] = {}


def compare_float(f: float, s: str) -> bool:
    """Compare float to test-case hex string."""
    return s == struct.pack(">d", f).hex()


def get_engine(track_file: str) -> Engine:
    eng = _LOADED_ENGINES.get(track_file)
    if eng is None:
        with open(f"fixtures/{track_file}.track.json", "r") as f:
            track_data = json.load(f)
        eng = convert_track(track_data)
        _LOADED_ENGINES[track_file] = eng
    return eng


def sanitize(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]", "_", name)


def create_fixture_test(fixture: dict):
    def test(self: unittest.TestCase):
        track_file: str = fixture["file"]
        frame: int = fixture["frame"]
        expected_state: Optional[dict] = fixture.get("state")

        engine = get_engine(track_file)
        result_state = engine.get_frame(frame)

        if result_state == None:
            self.assertIsNone(
                expected_state, msg=f"{track_file}: engine returned state"
            )
            return

        self.assertIsNotNone(expected_state, msg=f"{track_file}: engine returned None")

        if expected_state == None:
            return

        # Check number of entities
        expected_entities = expected_state.get("entities", [])
        result_entities = result_state.entities
        self.assertEqual(
            len(result_entities),
            len(expected_entities),
            msg=f"{track_file}: '{fixture['test']}' - entity count mismatch",
        )

        # Iterate entities
        for i, expected_entity_state in enumerate(expected_entities):
            result_entity = result_entities[i]

            # Mount state
            if "mount_state" in expected_entity_state:
                rider_state_map = {
                    "MOUNTED": MountPhase.MOUNTED,
                    "DISMOUNTING": MountPhase.DISMOUNTING,
                    "DISMOUNTED": MountPhase.DISMOUNTED,
                    "REMOUNTING": MountPhase.REMOUNTING,
                }
                expected_mount = rider_state_map.get(
                    expected_entity_state.get("mount_state") or "", MountPhase.MOUNTED
                )
                self.assertEqual(
                    result_entity.state.mount_phase,
                    expected_mount,
                    msg=f"{track_file}: '{fixture['test']}' - rider {i} mount state mismatch",
                )

            # Sled state
            if "sled_state" in expected_entity_state:
                expected_sled = (
                    expected_entity_state.get("sled_state") or "INTACT"
                ) == "INTACT"
                self.assertEqual(
                    result_entity.state.sled_intact,
                    expected_sled,
                    msg=f"{track_file}: '{fixture['test']}' - rider {i} sled state mismatch",
                )

            # Points
            exp_points = expected_entity_state.get("points", [])
            res_points = result_entity.points
            self.assertGreaterEqual(
                len(res_points),
                len(exp_points),
                msg=f"{track_file}: '{fixture['test']}' - rider {i} point count mismatch",
            )

            for j, expected_point_data in enumerate(exp_points):
                res_point = res_points[j]
                actual = (
                    res_point.position.x,
                    res_point.position.y,
                    res_point.velocity.x,
                    res_point.velocity.y,
                )
                labels = ["pos.x", "pos.y", "vel.x", "vel.y"]
                split_point_data = [
                    expected_point_data[i * 16 : i * 16 + 16] for i in range(4)
                ]
                for k, (a, b) in enumerate(zip(actual, split_point_data)):
                    float_b = struct.unpack(">d", bytes.fromhex(b))[0]
                    self.assertTrue(
                        compare_float(a, b),
                        msg=(
                            f"{track_file}: '{fixture['test']}' - rider {i} point {j} "
                            f"value mismatch ({labels[k]}): got {a}, expected {float_b}"
                        ),
                    )

    test.__name__ = f"test_{sanitize(fixture['test'])}"
    test.__doc__ = f"{fixture['file']}: {fixture['test']} (frame {fixture['frame']})"
    return test
