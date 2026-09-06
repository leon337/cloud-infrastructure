#!/usr/bin/env python3
"""Check consistency across canonical state and documentation surfaces."""

from __future__ import annotations

from pathlib import Path

import yaml


def require_token(path: Path, token: str) -> None:
    text = path.read_text(encoding="utf-8")
    if token not in text:
        raise AssertionError(f"{path} missing canonical token {token!r}")


def main() -> int:
    required = [
        Path("README.md"),
        Path("CONTEXT.md"),
        Path("CHECKPOINT.md"),
        Path("ROADMAP-CHECKLIST.md"),
        Path("state/current.yaml"),
        Path("scripts/test.sh"),
    ]
    for path in required:
        if not path.is_file():
            raise AssertionError(f"missing canonical surface: {path}")

    state = yaml.safe_load(Path("state/current.yaml").read_text(encoding="utf-8"))

    for token in (
        "CANONICAL_EXECUTIVE_PANEL_IMPLEMENTACAO_DA_VPS",
        "Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**",
        "POST_REBOOT_PR51_INTEGRATED_PR50_CANONICAL_MERGE_PENDING",
        "COMPLETE_LIVE_VERIFIED",
        "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        "INTERMITTENT_NOT_CLOSED",
        "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
    ):
        require_token(Path("README.md"), token)

    for path in (Path("CONTEXT.md"), Path("CHECKPOINT.md")):
        for token in (
            "scripts/test.sh",
            "POST_REBOOT_PR51_INTEGRATED_PR50_CANONICAL_MERGE_PENDING",
            "COMPLETE_LIVE_VERIFIED",
            "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
            "INTERMITTENT_NOT_CLOSED",
            "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED",
            "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED",
            "HUMAN_GATE_PR50_CANONICAL_MERGE",
        ):
            require_token(path, token)

    for path in (Path("README.md"), Path("ROADMAP-CHECKLIST.md")):
        for token in (
            "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED",
            "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED",
            "HUMAN_GATE_PR50_CANONICAL_MERGE",
            "COMPLETE_LIVE_VERIFIED",
            "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        ):
            require_token(path, token)

    active = state["continuity"]["active_mission_model"]
    if active["status"] == "NOT_ADOPTED" and Path(active["file"]).exists():
        raise AssertionError("state/active-mission.yaml exists despite NOT_ADOPTED decision")

    roadmap = state["continuity"]["roadmap_checklist"]
    roadmap_path = Path(roadmap["file"])
    if roadmap["status"] == "NOT_ADOPTED" and roadmap_path.exists():
        raise AssertionError("ROADMAP-CHECKLIST.md exists despite NOT_ADOPTED decision")
    if roadmap["status"] == "ADOPTED":
        if not roadmap_path.is_file():
            raise AssertionError("adopted ROADMAP-CHECKLIST.md is missing")
        require_token(roadmap_path, "IMPLEMENTACAO_DA_VPS_OPERATIONAL_CHECKLIST")
        require_token(roadmap_path, "subordinado ao `README.md`")
        if "<!-- CANONICAL_OPERATIONAL_CHECKLIST -->" in roadmap_path.read_text(encoding="utf-8"):
            raise AssertionError("roadmap must not self-declare as canonical executive authority")
        if roadmap.get("authority") != "SUBORDINATE_TO_README_EXECUTIVE_PANEL":
            raise AssertionError("roadmap authority must remain subordinate to README executive panel")
        if roadmap.get("scope") != "IMPLEMENTACAO_DA_VPS_ONLY":
            raise AssertionError("roadmap scope must remain IMPLEMENTACAO_DA_VPS_ONLY")
    elif roadmap["status"] != "NOT_ADOPTED":
        raise AssertionError(f"unexpected roadmap checklist status: {roadmap['status']!r}")

    freshness = state["freshness"]
    if freshness.get("canonical_executive_panel") != "README.md":
        raise AssertionError("README.md must remain the canonical executive panel")
    if freshness.get("mission_operational_checklist") != "ROADMAP-CHECKLIST.md":
        raise AssertionError("mission operational checklist drift")
    if freshness.get("checklist_scope") != "IMPLEMENTACAO_DA_VPS_ONLY":
        raise AssertionError("mission checklist scope drift")
    if state["source_snapshot"]["main"].get("executive_projection") != "README.md":
        raise AssertionError("source snapshot executive projection must remain README.md")

    runner = state.get("runner_isolation", {})
    if runner.get("status") != "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED":
        raise AssertionError("runner isolation state drift")
    if runner.get("global_hook") != "ACTIVE_VERIFIED":
        raise AssertionError("runner global hook boundary drift")
    if runner.get("global_hook_last_probe_run") != 33998487949:
        raise AssertionError("runner global hook probe run drift")
    if runner.get("global_hook_last_probe_result") != "PASS_ACTIVE_VERIFIED":
        raise AssertionError("runner global hook probe result drift")
    if runner.get("next_exact_step") != "NONE":
        raise AssertionError("runner global hook next gate drift")

    ssh = state.get("ssh_key_governance", {})
    if ssh.get("status") != "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED":
        raise AssertionError("ssh key governance state drift")
    if ssh.get("dsh_key", {}).get("current_dependency") != "CONFIRMED_BY_LEANDRO_USER_WORKFLOW":
        raise AssertionError("ssh key governance must preserve LEANDRO-confirmed dependency")
    if ssh.get("decision") != "KEEP_REQUIRED_FOR_CURRENT_USER_WORKFLOW":
        raise AssertionError("ssh key governance must keep current user workflow")
    if ssh.get("authorized_keys_changed") is not False:
        raise AssertionError("ssh key governance must preserve authorized_keys")

    f1 = state.get("platform", {}).get("f1_2c", {})
    if f1.get("status") != "COMPLETE_LIVE_VERIFIED" or f1.get("accepted") is not True:
        raise AssertionError("F1.2c current state must reflect verified live completion")

    network = state.get("network_convergence_p2", {})
    if network.get("status") != "COMPLETE_LIVE_VERIFIED" or network.get("accepted") is not True:
        raise AssertionError("Network P2 current state must reflect verified live completion")
    if network.get("route_removal_agent") != "NOT_VERIFIED":
        raise AssertionError("Network P2 exact route-removal agent must remain NOT_VERIFIED")

    g2b = state.get("control_bridge", {}).get("g2b", {})
    if g2b.get("task_8", {}).get("diagnostic_status") != "TECHNICAL_PASS_DRAFT_UNINTEGRATED":
        raise AssertionError("G2-B Task 8 current technical status drift")
    if g2b.get("accepted") is not False:
        raise AssertionError("G2-B must not be promoted to accepted")

    sentinel = state.get("sentinelx_direct_connectivity", {})
    if sentinel.get("status") != "INTERMITTENT_NOT_CLOSED":
        raise AssertionError("SentinelX direct-connectivity state drift")
    if sentinel.get("root_cause") != "NOT_VERIFIED":
        raise AssertionError("SentinelX current root cause must remain NOT_VERIFIED")

    checkpoint = state.get("pre_reboot_checkpoint", {})
    if checkpoint.get("status") != "FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH":
        raise AssertionError("pre-reboot checkpoint freshness classification drift")
    if checkpoint.get("accepted_for_current_reboot") is not False:
        raise AssertionError("historical checkpoint must not be accepted for current reboot")
    if checkpoint.get("refresh_required_before_reboot") is not False:
        raise AssertionError("fresh read-only checkpoint must not still require checkpoint refresh")
    if checkpoint.get("live_snapshot_fresh") is not True:
        raise AssertionError("fresh checkpoint live snapshot drift")
    if checkpoint.get("blocking_reason") != "HUMAN_UPDATE_REBOOT_AUTHORIZATION_PENDING":
        raise AssertionError("pre-reboot blocking reason drift")
    if checkpoint.get("latest_onhost_config_backup_integrity") != "PASS":
        raise AssertionError("on-host backup integrity drift")
    offhost = checkpoint.get("offhost_recovery", {})
    if offhost.get("sha256_status") != "PASS_6_OF_6":
        raise AssertionError("off-host recovery checksum status drift")
    if offhost.get("current_day_recovery_present") is not True:
        raise AssertionError("off-host current-day freshness drift")
    if offhost.get("freshness") != "FRESH_FOR_2026_09_06_REBOOT_GATE":
        raise AssertionError("off-host recovery freshness classification drift")
    if offhost.get("recovery_format") != "RECOVERY-P2-v1":
        raise AssertionError("off-host recovery format drift")
    if offhost.get("root_backup_sha256") != "ec5d83ddcf8ef72d92d2d52590e6d8a4329fdce6893088ee16520ebb0c5816f4":
        raise AssertionError("off-host root backup hash drift")
    if offhost.get("restore_smoke") != "PASS" or offhost.get("secret_scan") != "PASS":
        raise AssertionError("off-host recovery verification drift")
    if offhost.get("root_cause_missing_current_day") != "NOT_VERIFIED":
        raise AssertionError("historical off-host missing-run cause must remain NOT_VERIFIED")

    coordination = state.get("reboot_coordination", {})
    if coordination.get("status") != "MAINTENANCE_COMPLETED_POST_REBOOT_LIVE_VERIFIED":
        raise AssertionError("reboot coordination gate drift")
    if coordination.get("checkpoint_refresh_required") is not False:
        raise AssertionError("checkpoint refresh must be closed after fresh read-only collection")
    if coordination.get("offhost_recovery_freshness_required") is not False:
        raise AssertionError("off-host recovery freshness gate must be closed")
    if coordination.get("coordination_attempted") is not True:
        raise AssertionError("external coordination attempt receipt missing")
    if coordination.get("coordination_gate_result") != "PASS_ACTIVE_CHAT_CONSUMERS_CHECKPOINTED":
        raise AssertionError("external coordination gate result drift")
    if coordination.get("external_owner_status") != "NOT_RESOLVED_NOT_GATE_BLOCKING_AFTER_LEANDRO_CLARIFICATION":
        raise AssertionError("external owner status drift after LEANDRO coordination clarification")
    if coordination.get("external_contact_channel_status") != "GUI_CHAT_CHANNEL_VERIFIED":
        raise AssertionError("GUI chat coordination channel drift")
    if coordination.get("maintenance_window_status") != "COMPLETED":
        raise AssertionError("maintenance human gate status drift")
    if coordination.get("contact_attempt_sent") is not True:
        raise AssertionError("active-consumer coordination message receipt missing")
    if coordination.get("contact_attempt_reason") != "ACTIVE_CHAT_CONSUMERS_COORDINATED_VIA_GUI":
        raise AssertionError("active-consumer coordination reason drift")
    if coordination.get("deepseek_harness") != "EXTERNALLY_MANAGED_OBSERVE_ONLY":
        raise AssertionError("DeepSeek Harness ownership boundary drift")
    if coordination.get("ninerouter") != "EXTERNALLY_MANAGED_OBSERVE_ONLY":
        raise AssertionError("9router ownership boundary drift")
    if coordination.get("external_service_coordination_required") is not False:
        raise AssertionError("active consumer coordination gate must be closed")
    if coordination.get("active_consumers_ready") is not True:
        raise AssertionError("maintenance coordination checkpoint receipt drift")
    if coordination.get("post_reboot_validation_required") is not False:
        raise AssertionError("post-reboot validation must be closed after live PASS")
    if coordination.get("reboot_authorized") is not False or coordination.get("updates_authorized") is not False:
        raise AssertionError("one-shot maintenance authorization must be consumed")
    execution = coordination.get("maintenance_execution", {})
    if execution.get("status") != "PASS_POST_REBOOT_LIVE_VERIFIED":
        raise AssertionError("maintenance execution receipt drift")
    if execution.get("post_reboot_checker_candidate") != "9070c24e637e6d571bc53c66d0c54d3825340ffb":
        raise AssertionError("post-reboot checker candidate drift")
    if execution.get("independent_postverify") != "PASS":
        raise AssertionError("independent post-reboot verification drift")
    if coordination.get("coordination_channel") != "CHATGPT_GUI":
        raise AssertionError("coordination channel drift")
    active = coordination.get("active_consumers", {})
    if active.get("hy4_teste", {}).get("status") != "READY_FOR_NODE01_MAINTENANCE":
        raise AssertionError("hy4 maintenance checkpoint drift")
    if active.get("dsh_gpt", {}).get("status") != "PAUSED_SAFE_CHECKPOINT_NO_NEW_DSH_9ROUTER_EXECUTIONS":
        raise AssertionError("Dsh Gpt maintenance checkpoint drift")

    integration = state.get("post_reboot_integration", {})
    if integration.get("status") != "PR51_OPERATIONAL_FIX_INTEGRATED_PR50_CANONICAL_MERGE_PENDING":
        raise AssertionError("post-reboot integration status drift")
    operational = integration.get("operational_fix", {})
    if operational.get("merge_sha") != "d5508e1ed417b85bd4863ae5771605079d15aa99":
        raise AssertionError("PR #51 merge SHA drift")
    if operational.get("postmerge_validation") != "PASS_166_OF_166":
        raise AssertionError("PR #51 post-merge validation drift")
    if integration.get("canonical_reconciliation", {}).get("merge_status") != "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED":
        raise AssertionError("PR #50 merge gate must remain closed")

    if state.get("authorization", {}).get("pre_reboot_checkpoint") != "FRESH_READ_ONLY_COMPLETED_OFFHOST_RECOVERY_FRESH":
        raise AssertionError("pre-reboot authorization receipt drift")
    if state.get("authorization", {}).get("external_service_coordination_gate") != "AUTHORIZED_EXECUTED_PASS_ACTIVE_CONSUMERS_CHECKPOINTED":
        raise AssertionError("external coordination authorization receipt drift")
    if state.get("authorization", {}).get("updates") != "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED":
        raise AssertionError("update authorization receipt drift")
    if state.get("authorization", {}).get("reboot") != "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED":
        raise AssertionError("reboot authorization receipt drift")
    if state.get("authorization", {}).get("post_reboot_integration") != "PR51_OPERATIONAL_INTEGRATION_COMPLETED":
        raise AssertionError("PR #51 integration authorization receipt drift")
    if state.get("authorization", {}).get("pr50_canonical_merge") != "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED":
        raise AssertionError("PR #50 canonical merge must remain human-gated")

    if state["project"].get("next_exact_step") != "HUMAN_GATE_PR50_CANONICAL_MERGE":
        raise AssertionError("project next exact step drift")
    if state["toolchain"]["canonical_entrypoint"] != "scripts/test.sh":
        raise AssertionError("toolchain entrypoint drift")

    print("CANONICAL_CONSISTENCY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
