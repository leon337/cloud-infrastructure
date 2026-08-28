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
        "TASK_8_FAILED_ATTEMPT_3",
        "DOCUMENTATION_AND_INTEGRATION_DRIFT",
        "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
    ):
        require_token(Path("README.md"), token)

    for path in (Path("CONTEXT.md"), Path("CHECKPOINT.md")):
        for token in (
            "scripts/test.sh",
            "DOCUMENTATION_AND_INTEGRATION_DRIFT",
            "REQUIRES_REVIEW",
            "IN_PROGRESS_DIAGNOSTIC_REPRODUCTION",
            "REPOSITORY_HYGIENE_REVALIDATED",
            "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING",
            "SSH_KEY_GOVERNANCE_P1",
        ):
            require_token(path, token)

    for path in (Path("README.md"), Path("ROADMAP-CHECKLIST.md")):
        require_token(path, "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING")
        require_token(path, "SSH_KEY_GOVERNANCE_P1")

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
    if runner.get("status") != "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING":
        raise AssertionError("runner isolation state drift")
    if runner.get("global_hook") != "CONFIGURED_NOT_ACTIVE_BLOCKED_PRIVILEGE":
        raise AssertionError("runner global hook boundary drift")
    if state["project"].get("next_exact_step") != "SSH_KEY_GOVERNANCE_P1":
        raise AssertionError("next exact step drift after runner isolation")

    if state["toolchain"]["canonical_entrypoint"] != "scripts/test.sh":
        raise AssertionError("toolchain entrypoint drift")

    print("CANONICAL_CONSISTENCY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
