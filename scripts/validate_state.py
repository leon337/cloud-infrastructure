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
        ("state_classification",): "CURRENT_POST_REBOOT_INTEGRATION_COMPLETE_BRANCH_HYGIENE_CLASSIFIED_FINAL_AUDIT_NEXT",
        ("documentation_state",): "POST_REBOOT_INTEGRATION_COMPLETE_BRANCH_HYGIENE_CLASSIFIED_FINAL_AUDIT_NEXT",
        ("continuity", "validation_entrypoint"): "scripts/test.sh",
        ("continuity", "active_mission_model", "status"): "NOT_ADOPTED",
        ("continuity", "roadmap_checklist", "status"): "ADOPTED",
        ("continuity", "roadmap_checklist", "authority"): "SUBORDINATE_TO_README_EXECUTIVE_PANEL",
        ("continuity", "roadmap_checklist", "scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("freshness", "canonical_executive_panel"): "README.md",
        ("freshness", "mission_operational_checklist"): "ROADMAP-CHECKLIST.md",
        ("freshness", "checklist_scope"): "IMPLEMENTACAO_DA_VPS_ONLY",
        ("source_snapshot", "main", "executive_projection"): "README.md",
        ("source_snapshot", "main", "sha"): "ec9bc8cbac143197ab8d8102da23d3cb54fcd43a",
        ("source_snapshot", "main", "latest_integrated_pr"): 52,
        ("project", "integration_status"): "PR51_OPERATIONAL_AND_PR50_CANONICAL_INTEGRATED",
        ("project", "status"): "ACTIVE_BRANCH_HYGIENE_CLASSIFIED_FINAL_AUDIT_NEXT",
        ("project", "next_exact_step"): "FINAL_TRANSVERSAL_AUDIT",
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
        ("pre_reboot_checkpoint", "blocking_reason"): "HUMAN_UPDATE_REBOOT_AUTHORIZATION_PENDING",
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
        ("reboot_coordination", "status"): "MAINTENANCE_COMPLETED_POST_REBOOT_LIVE_VERIFIED",
        ("reboot_coordination", "checkpoint_refresh_required"): False,
        ("reboot_coordination", "offhost_recovery_freshness_required"): False,
        ("authorization", "pre_reboot_checkpoint"): "FRESH_READ_ONLY_COMPLETED_OFFHOST_RECOVERY_FRESH",
        ("reboot_coordination", "external_service_coordination_required"): False,
        ("reboot_coordination", "coordination_attempted"): True,
        ("reboot_coordination", "coordination_gate_result"): "PASS_ACTIVE_CHAT_CONSUMERS_CHECKPOINTED",
        ("reboot_coordination", "external_owner_status"): "NOT_RESOLVED_NOT_GATE_BLOCKING_AFTER_LEANDRO_CLARIFICATION",
        ("reboot_coordination", "external_contact_channel_status"): "GUI_CHAT_CHANNEL_VERIFIED",
        ("reboot_coordination", "maintenance_window_status"): "COMPLETED",
        ("reboot_coordination", "contact_attempt_sent"): True,
        ("reboot_coordination", "contact_attempt_reason"): "ACTIVE_CHAT_CONSUMERS_COORDINATED_VIA_GUI",
        ("authorization", "external_service_coordination_gate"): "AUTHORIZED_EXECUTED_PASS_ACTIVE_CONSUMERS_CHECKPOINTED",
        ("reboot_coordination", "host_reboot_would_interrupt_external_services"): True,
        ("reboot_coordination", "deepseek_harness"): "EXTERNALLY_MANAGED_OBSERVE_ONLY",
        ("reboot_coordination", "ninerouter"): "EXTERNALLY_MANAGED_OBSERVE_ONLY",
        ("reboot_coordination", "active_consumers_ready"): True,
        ("reboot_coordination", "post_reboot_validation_required"): False,
        ("reboot_coordination", "reboot_authorized"): False,
        ("reboot_coordination", "updates_authorized"): False,
        ("reboot_coordination", "maintenance_execution", "status"): "PASS_POST_REBOOT_LIVE_VERIFIED",
        ("reboot_coordination", "maintenance_execution", "authorization_choice"): "B_UPDATES_AND_REBOOT",
        ("reboot_coordination", "maintenance_execution", "current_kernel"): "6.8.0-139-generic",
        ("reboot_coordination", "maintenance_execution", "post_reboot_checker_candidate"): "9070c24e637e6d571bc53c66d0c54d3825340ffb",
        ("reboot_coordination", "maintenance_execution", "post_reboot_checker_result"): "NETWORK_CONVERGENCE_CHECK_PASS_RECOVERED",
        ("reboot_coordination", "maintenance_execution", "independent_postverify"): "PASS",
        ("reboot_coordination", "coordination_channel"): "CHATGPT_GUI",
        ("reboot_coordination", "active_consumers", "hy4_teste", "status"): "READY_FOR_NODE01_MAINTENANCE",
        ("reboot_coordination", "active_consumers", "dsh_gpt", "status"): "PAUSED_SAFE_CHECKPOINT_NO_NEW_DSH_9ROUTER_EXECUTIONS",
        ("post_reboot_integration", "status"): "PR51_OPERATIONAL_AND_PR50_CANONICAL_INTEGRATED",
        ("post_reboot_integration", "operational_fix", "pr"): 51,
        ("post_reboot_integration", "operational_fix", "branch"): "fix/f1-2c-systemd-runtime-lock",
        ("post_reboot_integration", "operational_fix", "candidate_head"): "9070c24e637e6d571bc53c66d0c54d3825340ffb",
        ("post_reboot_integration", "operational_fix", "merge_sha"): "d5508e1ed417b85bd4863ae5771605079d15aa99",
        ("post_reboot_integration", "operational_fix", "tree_sha"): "b0a51bef522bbb6c872baf5f4ef15116d6f584b0",
        ("post_reboot_integration", "operational_fix", "postmerge_validation"): "PASS_166_OF_166",
        ("post_reboot_integration", "canonical_reconciliation", "pr"): 50,
        ("post_reboot_integration", "canonical_reconciliation", "merge_status"): "MERGED",
        ("post_reboot_integration", "canonical_reconciliation", "merge_sha"): "c7315e43e86beedae5a921e39b1ab7103f4da276",
        ("post_reboot_integration", "canonical_reconciliation", "tree_sha"): "9dd8c3031c9d0ace580685ba08e6a00c88f14f2d",
        ("post_reboot_integration", "canonical_reconciliation", "postmerge_validation"): "PASS_35_OF_35",
        ("post_reboot_integration", "canonical_reconciliation", "postmerge_ci_run"): 34065344230,
        ("control_bridge", "g2b", "accepted"): False,
        ("control_bridge", "g2b", "tasks_1_7"): "COMPLETE",
        ("control_bridge", "g2b", "task_8", "last_terminal_attempt"): "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("control_bridge", "g2b", "task_8", "acceptance_markers_proven"): True,
        ("control_bridge", "g2b", "task_8", "diagnostic_head"): "f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8",
        ("control_bridge", "g2b", "task_8", "diagnostic_status"): "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("control_bridge", "g2b", "tasks_9_10"): "NOT_STARTED",
        ("control_bridge", "g2b", "merge_status"): "TASK_8_TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ("repository_hygiene", "status"): "PR_BRANCH_HYGIENE_CLASSIFIED",
        ("repository_hygiene", "remote_branch_count"): 68,
        ("repository_hygiene", "branch_deletions"): 0,
        ("repository_hygiene", "active_prs_retained"): [21],
        ("repository_hygiene", "legacy_prs_closed"): [1, 2, 3, 7, 8, 23, 41, 45],
        ("repository_hygiene", "deletion_gate"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("repository_hygiene", "legacy_pr_classification_pending"): False,
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
        ("boundaries", "branches_deleted_by_this_hygiene"): False,
        ("boundaries", "legacy_prs_closed_by_this_hygiene"): True,
        ("authorization", "production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "g2b_real_write"): "NOT_AUTHORIZED",
        ("authorization", "f1_2c_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "network_convergence_p2_node01_reapply"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "updates"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "reboot"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "post_reboot_integration"): "PR51_AND_PR50_INTEGRATION_COMPLETED",
        ("authorization", "pr50_canonical_merge"): "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED",
        ("authorization", "canonical_pr_branch_hygiene"): "AUTHORIZED_EXECUTED_CLASSIFICATION_ONLY_NO_BRANCH_DELETION",
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
