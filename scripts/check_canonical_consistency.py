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
        "LIVE_STATE_RECONCILED_OPEN_GOVERNANCE_DEBT",
        "COMPLETE_LIVE_VERIFIED",
        "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
        "INTERMITTENT_NOT_CLOSED",
        "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
    ):
        require_token(Path("README.md"), token)

    for path in (Path("CONTEXT.md"), Path("CHECKPOINT.md")):
        for token in (
            "scripts/test.sh",
            "LIVE_STATE_RECONCILED_OPEN_GOVERNANCE_DEBT",
            "COMPLETE_LIVE_VERIFIED",
            "TECHNICAL_PASS_DRAFT_UNINTEGRATED",
            "INTERMITTENT_NOT_CLOSED",
            "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED",
            "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED",
            "PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE",
        ):
            require_token(path, token)

    for path in (Path("README.md"), Path("ROADMAP-CHECKLIST.md")):
        for token in (
            "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED",
            "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED",
            "PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE",
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
    if checkpoint.get("status") != "HISTORICAL_VERIFIED_REFRESH_REQUIRED":
        raise AssertionError("pre-reboot checkpoint freshness classification drift")
    if checkpoint.get("accepted_for_current_reboot") is not False:
        raise AssertionError("historical checkpoint must not be accepted for current reboot")

    coordination = state.get("reboot_coordination", {})
    if coordination.get("status") != "HUMAN_GATE_AND_EXTERNAL_SERVICE_COORDINATION_REQUIRED":
        raise AssertionError("reboot coordination gate drift")
    if coordination.get("deepseek_harness") != "EXTERNALLY_MANAGED_OBSERVE_ONLY":
        raise AssertionError("DeepSeek Harness ownership boundary drift")
    if coordination.get("ninerouter") != "EXTERNALLY_MANAGED_OBSERVE_ONLY":
        raise AssertionError("9router ownership boundary drift")

    if state["project"].get("next_exact_step") != "PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE":
        raise AssertionError("project next exact step drift")
    if state["toolchain"]["canonical_entrypoint"] != "scripts/test.sh":
        raise AssertionError("toolchain entrypoint drift")

    print("CANONICAL_CONSISTENCY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
