from __future__ import annotations

import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ControlBridgeContinuityTests(unittest.TestCase):
    def test_current_state_records_active_mission_and_parallel_ownership(self):
        state = yaml.safe_load((ROOT / "state/current.yaml").read_text())
        bridge = state["control_bridge"]
        mission = state["active_mission"]

        self.assertEqual(mission["id"], "REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING")
        self.assertEqual(mission["status"], "ACTIVE")
        self.assertEqual(mission["issue"], 10)
        self.assertEqual(mission["pull_request"], 11)
        self.assertEqual(mission["roadmap"]["R1"], "COMPLETE")
        self.assertEqual(mission["roadmap"]["R2"], "COMPLETE")
        self.assertEqual(mission["roadmap"]["R3"], "NEXT")
        self.assertEqual(
            state["continuity"]["g2b_recovery_checkpoint_doc"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )

        self.assertEqual(bridge["priority"], "P0")
        self.assertEqual(bridge["g1"], "PASS_REAL_NODE_01_ROUNDTRIP")
        self.assertEqual(bridge["g2a"], "PASS_REAL_NODE_01_READ_ONLY")
        self.assertEqual(bridge["g2b"], "TASK_7_PARTIAL_RECOVERED_REMOTE")
        self.assertEqual(bridge["g2b_task_7"], "PARTIAL_6_PASS_1_FAIL")
        self.assertEqual(bridge["g2b_tasks_8_10"], "NOT_STARTED")
        self.assertEqual(
            state["work_ownership"]["f1_2c_systemd_runtime_lock"]["owner"],
            "MESTRE_MCF_AND_LEANDRO",
        )
        self.assertTrue(
            state["work_ownership"]["f1_2c_systemd_runtime_lock"]["frozen_for_codex"]
        )
        self.assertEqual(
            state["work_ownership"]["f1_2c_systemd_runtime_lock"]["rule_for_active_continuity_mission"],
            "ISOLATED_DO_NOT_MODIFY",
        )

    def test_entrypoints_identify_active_mission_and_do_not_treat_mainline_as_active(self):
        for relative in ("README.md", "CONTEXT.md", "CHECKPOINT.md"):
            text = (ROOT / relative).read_text()
            self.assertNotIn("Codex está indisponível", text)
            self.assertIn("CONTROL_BRIDGE_G2B", text)
            self.assertIn("R3_DEFINE_MANDATORY_AI_PROJECT_STARTUP_AND_RECOVERY_PROTOCOL", text)
            self.assertIn("codex/control-bridge-g2b", text)
            self.assertIn("docs/54-control-bridge-g2b-recovery-checkpoint.md", text)

    def test_g2b_state_preserves_partial_status_and_fail_closed_boundaries(self):
        state = yaml.safe_load((ROOT / "state/control-bridge-g2b.yaml").read_text())
        self.assertEqual(state["status"], "TASK_7_PARTIAL_RECOVERED_REMOTE")
        self.assertEqual(
            state["recovery_checkpoint"]["document"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )
        self.assertEqual(state["implementation"]["tasks_1_6"], "COMPLETE_MATERIALLY_REVIEWED")
        self.assertEqual(state["implementation"]["task_7"], "PARTIAL")
        self.assertEqual(state["implementation"]["task_7_focused_tests"]["pass"], 6)
        self.assertEqual(state["implementation"]["task_7_focused_tests"]["fail"], 1)
        self.assertEqual(state["implementation"]["tasks_8_10"], "NOT_STARTED")
        self.assertEqual(state["pilot"]["project"], "leon337/g2a-smoke/dev")
        self.assertEqual(state["pilot"]["path"], "G2B-PILOT.txt")
        self.assertEqual(state["pilot"]["grant_duration_hours"], 24)
        self.assertFalse(state["evidence"]["real_write"])
        self.assertFalse(state["evidence"]["real_rollback"])
        self.assertFalse(state["evidence"]["real_revocation"])

    def test_active_mission_state_points_to_r3_and_closed_human_gates(self):
        state = yaml.safe_load((ROOT / "state/active-mission.yaml").read_text())
        self.assertEqual(state["continuity_roadmap"]["R1"], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R2"], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R3"], "NEXT")
        self.assertEqual(
            state["control_bridge_g2b"]["recovery_checkpoint_doc"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )
        self.assertEqual(
            state["next_exact_step"],
            "R3_DEFINE_MANDATORY_AI_PROJECT_STARTUP_AND_RECOVERY_PROTOCOL",
        )
        for value in state["human_gates"].values():
            self.assertIn("NOT_AUTHORIZED", value)
