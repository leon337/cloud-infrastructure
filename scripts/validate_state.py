#!/usr/bin/env python3
"""Validate the mainline-neutral canonical state contract."""

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
        ("documentation_state",): "DOCUMENTATION_AND_INTEGRATION_DRIFT",
        ("continuity", "validation_entrypoint"): "scripts/test.sh",
        ("continuity", "active_mission_model", "status"): "NOT_ADOPTED",
        ("continuity", "roadmap_checklist", "status"): "ADOPTED",
        ("continuity", "roadmap_checklist", "authority"): "SUBORDINATE_TO_README_EXECUTIVE_PANEL",
        ("continuity", "roadmap_checklist", "scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("freshness", "canonical_executive_panel"): "README.md",
        ("freshness", "mission_operational_checklist"): "ROADMAP-CHECKLIST.md",
        ("freshness", "checklist_scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("source_snapshot", "main", "executive_projection"): "README.md",
        ("project", "integration_status"): "DOCUMENTATION_AND_INTEGRATION_DRIFT",
        ("project", "next_exact_step"): "UPDATE_AND_CONTROLLED_REBOOT",
        ("runner_isolation", "status"): "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING",
        ("runner_isolation", "legacy_poc"): "RETIRED",
        ("runner_isolation", "live_cleanup"): "PASS",
        ("runner_isolation", "cross_job_proof"): "PASS",
        ("runner_isolation", "workflow_policy"): "PASS",
        ("runner_isolation", "recovery_regression"): "PASS",
        ("runner_isolation", "global_hook"): "CONFIGURED_NOT_ACTIVE_BLOCKED_PRIVILEGE",
        ("runner_isolation", "global_hook_restart_required"): True,
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
        ("platform", "f1_2c", "node01_reapply_authorized"): False,
        ("network_convergence_p2", "status"): "COMPLETE_LIVE_VERIFIED",
        ("network_convergence_p2", "accepted"): True,
        ("network_convergence_p2", "functional_cause"): "CONNECTED_IPV4_ROUTE_ABSENT_REPRODUCED_IN_KVM",
        ("network_convergence_p2", "route_removal_agent"): "NOT_VERIFIED",
        ("network_convergence_p2", "node01_reapply_authorized"): False,
        ("pre_reboot_checkpoint", "status"): "VERIFIED_PRE_REBOOT_CHECKPOINT_V2",
        ("pre_reboot_checkpoint", "accepted"): True,
        ("pre_reboot_checkpoint", "v1_status"): "REJECTED_INTERNAL_SHA256SUMS_SELF_HASH",
        ("pre_reboot_checkpoint", "reboot_authorized"): False,
        ("pre_reboot_checkpoint", "updates_authorized"): False,
        ("control_bridge", "g2b", "accepted"): False,
        ("control_bridge", "g2b", "tasks_1_7"): "COMPLETE",
        ("control_bridge", "g2b", "task_8", "last_terminal_attempt"): "FAILED_ATTEMPT_3_NOT_ACCEPTED",
        ("control_bridge", "g2b", "task_8", "acceptance_markers_proven"): False,
        ("control_bridge", "g2b", "tasks_9_10"): "NOT_STARTED",
        ("control_bridge", "g2b", "merge_status"): "NOT_ELIGIBLE",
        ("repository_hygiene", "status"): "REPOSITORY_HYGIENE_REVALIDATED",
        ("toolchain", "canonical_entrypoint"): "scripts/test.sh",
        ("toolchain", "package"): "CANONICAL_MAINLINE_NEUTRAL_V2",
        ("toolchain", "functional_lineage_code_imported"): False,
        ("toolchain", "g2b_functional_code_imported"): False,
        ("toolchain", "f1_2c_functional_code_imported"): False,
        ("boundaries", "node01_privileged_operations"): True,
        ("boundaries", "node01_privileged_operations_currently_authorized"): False,
        ("boundaries", "production_promoted"): False,
        ("authorization", "production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "g2b_real_write"): "NOT_AUTHORIZED",
        ("authorization", "f1_2c_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "network_convergence_p2_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "pre_reboot_checkpoint"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "updates"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "reboot"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "ssh_dsh_key_change"): "NOT_AUTHORIZED_WITHOUT_PRESERVING_CURRENT_USER_WORKFLOW",
    }
    for path, expected in exact.items():
        expect(data, path, expected)

    if value(data, "platform", "f1_2c", "disposable_kvm", "upstream_cause") != "NOT_VERIFIED":
        raise AssertionError("F1.2c runner cause must remain NOT_VERIFIED")
    if value(data, "control_bridge", "g2b", "task_8", "root_cause") != "NOT_VERIFIED":
        raise AssertionError("G2-B Task 8 root cause must remain NOT_VERIFIED")

    validation = value(data, "toolchain", "validation_status")
    if validation not in {"PENDING", "PASS", "BLOCKED_BY_REPOSITORY_HYGIENE"}:
        raise AssertionError(f"unexpected toolchain validation_status: {validation!r}")

    print("CANONICAL_STATE_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
