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
        self.assertEqual(mission["roadmap"]["R3"], "COMPLETE")
        self.assertEqual(mission["roadmap"]["R4"], "NEXT")
        self.assertEqual(
            state["continuity"]["startup_recovery_protocol"],
            "governance/AI-STARTUP-RECOVERY-PROTOCOL.md",
        )
        self.assertEqual(
            state["continuity"]["startup_recovery_protocol_state"],
            "state/startup-recovery-protocol.yaml",
        )
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

    def test_entrypoints_require_protocol_and_point_to_r4(self):
        for relative in ("README.md", "CONTEXT.md", "CHECKPOINT.md"):
            text = (ROOT / relative).read_text()
            self.assertNotIn("Codex está indisponível", text)
            self.assertIn("governance/AI-STARTUP-RECOVERY-PROTOCOL.md", text)
            self.assertIn("state/startup-recovery-protocol.yaml", text)
            self.assertIn("R4_DEFINE_LONG_RUNNING_MISSION_PERSISTENCE_POLICY", text)
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

    def test_active_mission_state_points_to_r4_and_closed_human_gates(self):
        state = yaml.safe_load((ROOT / "state/active-mission.yaml").read_text())
        self.assertEqual(state["continuity_roadmap"]["R1"], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R2"], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R3"], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R4"], "NEXT")
        self.assertEqual(
            state["startup_recovery_protocol"]["protocol_version"],
            "CLOUD_INFRA_AI_STARTUP_RECOVERY_V1",
        )
        self.assertEqual(
            state["control_bridge_g2b"]["recovery_checkpoint_doc"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )
        self.assertEqual(
            state["next_exact_step"],
            "R4_DEFINE_LONG_RUNNING_MISSION_PERSISTENCE_POLICY",
        )
        for value in state["human_gates"].values():
            self.assertIn("NOT_AUTHORIZED", value)

    def test_startup_recovery_contract_is_fail_closed(self):
        protocol = yaml.safe_load((ROOT / "state/startup-recovery-protocol.yaml").read_text())
        self.assertEqual(protocol["status"], "ACTIVE_REQUIRED")
        self.assertEqual(
            protocol["principle"],
            "NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS",
        )
        self.assertTrue(protocol["startup_gate"]["implementation_must_not_begin_before_report"])
        self.assertTrue(protocol["startup_gate"]["pass_required_for_mutation"])
        self.assertTrue(protocol["startup_gate"]["human_gate_still_applies_after_pass"])
        self.assertFalse(protocol["verdicts"]["PASS_READ_ONLY"]["implementation_allowed"])
        self.assertFalse(protocol["verdicts"]["BLOCKED_RECONCILIATION"]["implementation_allowed"])
        self.assertFalse(protocol["verdicts"]["WAITING_HUMAN_GATE"]["implementation_allowed"])
        self.assertIn("LOCAL_REMOTE_DIVERGENCE_UNEXPLAINED", protocol["fail_closed_conditions"])
        self.assertIn("UNCOMMITTED_OR_UNTRACKED_WORK_WITH_UNKNOWN_OWNERSHIP", protocol["fail_closed_conditions"])
