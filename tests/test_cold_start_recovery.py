from __future__ import annotations

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_reconstructor():
    path = ROOT / "scripts/reconstruct_cold_start.py"
    spec = importlib.util.spec_from_file_location("reconstruct_cold_start", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load cold-start reconstructor")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ColdStartRecoveryTests(unittest.TestCase):
    def test_repository_only_reconstruction_recovers_required_state(self):
        snapshot = load_reconstructor().reconstruct()
        self.assertEqual(snapshot["active_mission"], "CONTROL_BRIDGE_G2B")
        self.assertEqual(snapshot["branch"], "codex/control-bridge-g2b")
        self.assertEqual(snapshot["pull_request"], 11)
        self.assertEqual(snapshot["pull_request_state"], "DRAFT_DO_NOT_MERGE")
        self.assertEqual(snapshot["tasks_1_6"], "COMPLETE_MATERIALLY_REVIEWED")
        self.assertEqual(snapshot["task_7"], "COMPLETE_7_PASS_0_FAIL")
        self.assertEqual(snapshot["known_red"], "RESOLVED_EXISTING_GRANT_EXACT_KEY_SET_ENFORCED")
        self.assertEqual(snapshot["tasks_8_10"], "NOT_STARTED")
        self.assertEqual(snapshot["f1_2c"], "ISOLATED_DO_NOT_MODIFY")
        self.assertEqual(snapshot["node01_g2b_gate"], "CLOSED_NOT_AUTHORIZED")
        self.assertEqual(snapshot["real_grant_gate"], "CLOSED_NOT_AUTHORIZED")
        self.assertEqual(snapshot["real_write_gate"], "CLOSED_NOT_AUTHORIZED")
        self.assertEqual(snapshot["merge_gate"], "CLOSED_NOT_AUTHORIZED")
        self.assertFalse(snapshot["real_write_executed"])
        self.assertEqual(snapshot["next_exact_step"], snapshot["current_state_next_exact_step"])


if __name__ == "__main__":
    unittest.main()
