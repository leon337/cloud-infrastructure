#!/usr/bin/env python3
"""Validate the canonical IMPLEMENTACAO_DA_VPS state contract."""

from __future__ import annotations

from pathlib import Path

from yaml_strict import load_strict

STATE_PATH = Path("state/current.yaml")


def read_state() -> dict:
    data = load_strict(STATE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("state/current.yaml must contain a mapping")
    return data


def value(data: dict, *path: str):
    current = data
    for key in path:
        if not isinstance(current, dict) or key not in current:
            raise AssertionError(f"missing state path: {'.'.join(path)}")
        current = current[key]
    return current


def expect(data: dict, path: tuple[str, ...], expected) -> None:
    actual = value(data, *path)
    if actual != expected:
        raise AssertionError(f"{'.'.join(path)} expected {expected!r}, got {actual!r}")


def main() -> int:
    data = read_state()

    exact = {
        ("canonical_repository",): "leon337/cloud-infrastructure",
        ("canonical_branch",): "main",
        ("documentation_state",): "PRE_REBOOT_EXTERNAL_COORDINATION_BLOCKED_OWNER_CHANNEL_WINDOW",
        ("continuity", "validation_entrypoint"): "scripts/test.sh",
        ("continuity", "active_mission_model", "status"): "NOT_ADOPTED",
        ("continuity", "roadmap_checklist", "status"): "ADOPTED",
        ("continuity", "roadmap_checklist", "authority"): "SUBORDINATE_TO_README_EXECUTIVE_PANEL",
        ("continuity", "roadmap_checklist", "scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("freshness", "canonical_executive_panel"): "README.md",
        ("freshness", "mission_operational_checklist"): "ROADMAP-CHECKLIST.md",
        ("freshness", "checklist_scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("source_snapshot", "main", "executive_projection"): "README.md",
        ("project", "integration_status"): "LIVE_STATE_RECONCILED_OPEN_INTEGRATION_DEBT",
        ("project", "next_exact_step"): "HUMAN_GATE_EXTERNAL_OWNER_CHANNEL_WINDOW",
        ("runner_isolation", "status"): "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED",
        ("runner_isolation", "legacy_poc"): "RETIRED",
        ("runner_isolation", "live_cleanup"): "PASS",
        ("runner_isolation", "cross_job_proof"): "PASS",
        ("runner_isolation", "workflow_policy"): "PASS",
        ("runner_isolation", "recovery_regression"): "PASS",
        ("runner_isolation", "global_hook"): "ACTIVE_VERIFIED",
        ("runner_isolation", "global_hook_restart_required"): False,
        ("runner_isolation", "global_hook_activation_authorized"): True,
        ("runner_isolation", "global_hook_last_probe_run"): 33998487949,
        ("runner_isolation", "global_hook_last_probe_result"): "PASS_ACTIVE_VERIFIED",
        ("runner_isolation", "next_exact_step"): "NONE",
        ("runner_isolation", "service_boundary_bypassed"): False,
        ("ssh_key_governance", "status"): "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED",
        ("ssh_key_governance", "dsh_key", "provenance"): "CONFIRMED_UBUNTU_HISTORY_AND_AUTH_LOG",
        ("ssh_key_governance", "dsh_key", "current_dependency"): "CONFIRMED_BY_LEANDRO_USER_WORKFLOW",
        ("ssh_key_governance", "fallback_auth"): "PASS_INDEPENDENT_KEY",
        ("ssh_key_governance", "authorized_keys_changed"): False,
        ("ssh_key_governance", "decision"): "KEEP_REQUIRED_FOR_CURRENT_USER_WORKFLOW",
        ("ssh_key_governance", "future_hardening_gate"): "PRESERVE_INTERACTIVE_NOTEBOOK_ACCESS",
        ("platform", "f1_2c", "status"): "COMPLETE_LIVE_VERIFIED",
        ("platform", "f1_2c", "accepted"): True,
        ("platform", "f1_2c", "applied_candidate_sha"): "baaf83908e8e83264baafc032434a4df1952450b",
        ("platform", "f1_2c", "live_postverify", "status"): "PASS",
        ("platform", "f1_2c", "live_postverify", "service_active"): True,
        ("platform", "f1_2c", "node01_reapply_authorized"): False,
        ("network_convergence_p2", "status"): "COMPLETE_LIVE_VERIFIED",
        ("network_convergence_p2", "accepted"): True,
        ("network_convergence_p2", "applied_candidate_sha"): "682c3e55d835ebea4bcc2edd297a8b819b2df434",
        ("network_convergence_p2", "live_postverify", "administrative_state"): "configured",
        ("network_convergence_p2", "live_postverify", "gateway_host_route"): "169.58.128.1/32_SCOPE_LINK",
        ("network_convergence_p2", "node01_reapply_authorized"): False,
        ("pre_reboot_checkpoint", "status"): "FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH",
        ("pre_reboot_checkpoint", "accepted_for_current_reboot"): False,
        ("pre_reboot_checkpoint", "refresh_required_before_reboot"): False,
        ("pre_reboot_checkpoint", "current_kernel"): "6.8.0-138-generic",
        ("pre_reboot_checkpoint", "target_kernel"): "6.8.0-139-generic",
        ("pre_reboot_checkpoint", "reboot_required"): True,
        ("pre_reboot_checkpoint", "live_snapshot_fresh"): True,
        ("pre_reboot_checkpoint", "blocking_reason"): "EXTERNAL_OWNER_CHANNEL_WINDOW_NOT_VERIFIED",
        ("pre_reboot_checkpoint", "latest_onhost_config_backup_integrity"): "PASS",
        ("pre_reboot_checkpoint", "offhost_recovery", "sha256_status"): "PASS_6_OF_6",
        ("pre_reboot_checkpoint", "offhost_recovery", "current_day_recovery_present"): True,
        ("pre_reboot_checkpoint", "offhost_recovery", "freshness"): "FRESH_FOR_2026_09_06_REBOOT_GATE",
        ("pre_reboot_checkpoint", "offhost_recovery", "recovery_format"): "RECOVERY-P2-v1",
        ("pre_reboot_checkpoint", "offhost_recovery", "root_backup"): "cloud-infrastructure-config-20260906T030657Z.tar.gz",
        ("pre_reboot_checkpoint", "offhost_recovery", "root_backup_sha256"): "ec5d83ddcf8ef72d92d2d52590e6d8a4329fdce6893088ee16520ebb0c5816f4",
        ("pre_reboot_checkpoint", "offhost_recovery", "restore_smoke"): "PASS",
        ("pre_reboot_checkpoint", "offhost_recovery", "secret_scan"): "PASS",
        ("pre_reboot_checkpoint", "offhost_recovery", "archive_path_safety"): "PASS",
        ("pre_reboot_checkpoint", "offhost_recovery", "archive_link_safety"): "PASS",
        ("pre_reboot_checkpoint", "offhost_recovery", "root_cause_missing_current_day"): "NOT_VERIFIED",
        ("sentinelx_direct_connectivity", "status"): "INTERMITTENT_NOT_CLOSED",
        ("sentinelx_direct_connectivity", "root_cause"): "NOT_VERIFIED",
        ("reboot_coordination", "status"): "BLOCKED_EXTERNAL_OWNER_CHANNEL_WINDOW_AND_HUMAN_GATE",
        ("reboot_coordination", "checkpoint_refresh_required"): False,
        ("reboot_coordination", "offhost_recovery_freshness_required"): False,
        ("authorization", "pre_reboot_checkpoint"): "FRESH_READ_ONLY_COMPLETED_OFFHOST_RECOVERY_FRESH",
        ("reboot_coordination", "external_service_coordination_required"): True,
        ("reboot_coordination", "coordination_attempted"): True,
        ("reboot_coordination", "coordination_gate_result"): "BLOCKED_NO_VERIFIED_OWNER_CHANNEL_WINDOW",
        ("reboot_coordination", "external_owner_status"): "NOT_VERIFIED",
        ("reboot_coordination", "external_contact_channel_status"): "NOT_VERIFIED",
        ("reboot_coordination", "maintenance_window_status"): "NOT_SCHEDULED",
        ("reboot_coordination", "contact_attempt_sent"): False,
        ("reboot_coordination", "contact_attempt_reason"): "NO_VERIFIED_RECIPIENT",
        ("authorization", "external_service_coordination_gate"): "AUTHORIZED_EXECUTED_BLOCKED_OWNER_CHANNEL_WINDOW",
        ("reboot_coordination", "host_reboot_would_interrupt_external_services"): True,
        ("reboot_coordination", "deepseek_harness"): "EXTERNALLY_MANAGED_OBSERVE_ONLY",
        ("reboot_coordination", "ninerouter"): "EXTERNALLY_MANAGED_OBSERVE_ONLY",
        ("control_bridge", "g2b", "accepted"): False,
        ("control_bridge", "g2b", "tasks_1_7"): "COMPLETE",
        ("control_bridge", "g2b", "task_8", "last_terminal_attempt"): "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("control_bridge", "g2b", "task_8", "acceptance_markers_proven"): True,
        ("control_bridge", "g2b", "task_8", "diagnostic_head"): "f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8",
        ("control_bridge", "g2b", "task_8", "diagnostic_status"): "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("control_bridge", "g2b", "tasks_9_10"): "NOT_STARTED",
        ("control_bridge", "g2b", "merge_status"): "TASK_8_TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("repository_hygiene", "status"): "REPOSITORY_HYGIENE_REVALIDATED",
        ("toolchain", "canonical_entrypoint"): "scripts/test.sh",
        ("toolchain", "package"): "CANONICAL_MAINLINE_NEUTRAL_V2",
        ("toolchain", "functional_lineage_code_imported"): False,
        ("toolchain", "g2b_functional_code_imported"): False,
        ("toolchain", "f1_2c_functional_code_imported"): False,
        ("boundaries", "production_promoted"): False,
        ("boundaries", "vps_mutation_by_this_reconciliation"): False,
        ("boundaries", "vps_restart_by_this_reconciliation"): False,
        ("boundaries", "deepseek_harness_mutated"): False,
        ("boundaries", "ninerouter_mutated"): False,
        ("authorization", "production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "g2b_real_write"): "NOT_AUTHORIZED",
        ("authorization", "f1_2c_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "network_convergence_p2_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "updates"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "reboot"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "ssh_dsh_key_change"): "NOT_AUTHORIZED_WITHOUT_PRESERVING_CURRENT_USER_WORKFLOW",
    }
    for path, expected in exact.items():
        expect(data, path, expected)

    if value(data, "network_convergence_p2", "route_removal_agent") != "NOT_VERIFIED":
        raise AssertionError("Network P2 route removal agent must remain NOT_VERIFIED")

    validation = value(data, "toolchain", "validation_status")
    if validation not in {"PENDING", "PASS", "BLOCKED_BY_REPOSITORY_HYGIENE"}:
        raise AssertionError(f"unexpected toolchain validation_status: {validation!r}")

    print("CANONICAL_STATE_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
