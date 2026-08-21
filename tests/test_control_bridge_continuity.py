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
        for key in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
            self.assertEqual(mission["roadmap"][key], "COMPLETE")
        self.assertEqual(mission["roadmap"]["R8"], "NEXT")
        self.assertEqual(
            state["continuity"]["startup_recovery_protocol"],
            "governance/AI-STARTUP-RECOVERY-PROTOCOL.md",
        )
        self.assertEqual(
            state["continuity"]["startup_recovery_protocol_state"],
            "state/startup-recovery-protocol.yaml",
        )
        self.assertEqual(
            state["continuity"]["mission_persistence_policy"],
            "governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md",
        )
        self.assertEqual(
            state["continuity"]["mission_persistence_policy_state"],
            "state/mission-persistence-policy.yaml",
        )
        self.assertEqual(
            state["continuity"]["institutional_memory_state"],
            "state/institutional-memory.yaml",
        )
        self.assertEqual(
            state["continuity"]["continuity_drift_controls_state"],
            "state/continuity-drift-controls.yaml",
        )
        self.assertEqual(
            state["continuity"]["cold_start_validation_state"],
            "state/cold-start-validation.yaml",
        )
        self.assertEqual(
            state["continuity"]["max_material_work_without_remote_checkpoint_minutes"],
            30,
        )
        self.assertEqual(
            state["continuity"]["g2b_recovery_checkpoint_doc"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )
        self.assertEqual(
            state["continuity"]["next_exact_step"],
            "R8_RESUME_G2B_TASK7_FROM_RECOVERED_POINT",
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

    def test_entrypoints_require_continuity_controls_and_point_to_r8(self):
        for relative in ("README.md", "CONTEXT.md", "CHECKPOINT.md"):
            text = (ROOT / relative).read_text()
            self.assertNotIn("Codex está indisponível", text)
            self.assertIn("governance/AI-STARTUP-RECOVERY-PROTOCOL.md", text)
            self.assertIn("state/startup-recovery-protocol.yaml", text)
            self.assertIn("governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md", text)
            self.assertIn("state/mission-persistence-policy.yaml", text)
            self.assertIn("state/institutional-memory.yaml", text)
            self.assertIn("state/continuity-drift-controls.yaml", text)
            self.assertIn("state/cold-start-validation.yaml", text)
            self.assertIn("R8_RESUME_G2B_TASK7_FROM_RECOVERED_POINT", text)
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
        self.assertEqual(state["continuity"]["roadmap_stage"], "R7_COMPLETE_R8_NEXT")
        self.assertEqual(
            state["continuity"]["mission_persistence_policy_state"],
            "state/mission-persistence-policy.yaml",
        )
        self.assertEqual(
            state["continuity"]["cold_start_validation_state"],
            "state/cold-start-validation.yaml",
        )
        self.assertFalse(state["evidence"]["real_write"])
        self.assertFalse(state["evidence"]["real_rollback"])
        self.assertFalse(state["evidence"]["real_revocation"])

    def test_active_mission_state_points_to_r8_and_closed_human_gates(self):
        state = yaml.safe_load((ROOT / "state/active-mission.yaml").read_text())
        for key in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
            self.assertEqual(state["continuity_roadmap"][key], "COMPLETE")
        self.assertEqual(state["continuity_roadmap"]["R8"], "NEXT")
        self.assertEqual(
            state["startup_recovery_protocol"]["protocol_version"],
            "CLOUD_INFRA_AI_STARTUP_RECOVERY_V1",
        )
        self.assertEqual(
            state["mission_persistence_policy"]["protocol_version"],
            "CLOUD_INFRA_LONG_RUNNING_MISSION_PERSISTENCE_V1",
        )
        self.assertEqual(
            state["institutional_memory"]["protocol_version"],
            "CLOUD_INFRA_INSTITUTIONAL_MEMORY_V1",
        )
        self.assertEqual(
            state["continuity_drift_controls"]["protocol_version"],
            "CLOUD_INFRA_CONTINUITY_DRIFT_CONTROLS_V1",
        )
        self.assertEqual(
            state["cold_start_validation"]["protocol_version"],
            "CLOUD_INFRA_COLD_START_VALIDATION_V1",
        )
        self.assertEqual(state["cold_start_validation"]["status"], "PASS")
        self.assertEqual(
            state["control_bridge_g2b"]["recovery_checkpoint_doc"],
            "docs/54-control-bridge-g2b-recovery-checkpoint.md",
        )
        self.assertEqual(
            state["next_exact_step"],
            "R8_RESUME_G2B_TASK7_FROM_RECOVERED_POINT",
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

    def test_long_running_persistence_contract_is_fail_closed(self):
        policy = yaml.safe_load((ROOT / "state/mission-persistence-policy.yaml").read_text())
        self.assertEqual(policy["status"], "ACTIVE_REQUIRED")
        self.assertEqual(
            policy["limits"]["max_material_work_without_remote_checkpoint_minutes"],
            30,
        )
        self.assertIn(
            "NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS",
            policy["principles"],
        )
        self.assertIn("WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE", policy["principles"])
        self.assertFalse(policy["acceptance"]["persistence_implies_acceptance"])
        self.assertTrue(policy["acceptance"]["pass_requires_applicable_evidence"])
        self.assertTrue(policy["subagents"]["controlling_agent_owns_durability"])
        self.assertFalse(policy["subagents"]["subagent_transcript_is_durable_state"])
        self.assertTrue(policy["restart_recovery"]["startup_recovery_protocol_required"])
        self.assertIn(
            "REMOTE_PERSISTENCE_BROKEN_AND_NEW_UNRELATED_MATERIAL_WORK_WOULD_ACCUMULATE",
            policy["fail_closed_conditions"],
        )
        self.assertIn(
            "MATERIAL_GIT_PROGRESS_WITH_STALE_LEDGER_STATE",
            policy["fail_closed_conditions"],
        )
