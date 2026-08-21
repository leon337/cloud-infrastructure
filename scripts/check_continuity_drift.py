#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import sys
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
ROADMAP_KEYS = [f"R{i}" for i in range(1, 9)]
ALLOWED_STATES = {
    "NOT_STARTED",
    "NEXT",
    "IN_PROGRESS",
    "PARTIAL",
    "BLOCKED",
    "BLOCKED_EXTERNAL",
    "WAITING_HUMAN_GATE",
    "REVIEW_REQUIRED",
    "PASS",
    "FAILED",
    "COMPLETE",
}


def load_yaml(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative}: expected mapping")
    return data


def read_text(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    return path.read_text(encoding="utf-8")


def collect_errors() -> list[str]:
    errors: list[str] = []

    def check(condition: bool, code: str, detail: str) -> None:
        if not condition:
            errors.append(f"{code}: {detail}")

    try:
        active = load_yaml("state/active-mission.yaml")
        current = load_yaml("state/current.yaml")
        bridge = load_yaml("state/control-bridge-g2b.yaml")
        memory = load_yaml("state/institutional-memory.yaml")
        drift = load_yaml("state/continuity-drift-controls.yaml")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        return [f"CURRENT_STATE_DRIFT: cannot load canonical state: {exc}"]

    mission = active.get("mission", {})
    repository = active.get("repository", {})
    roadmap = active.get("continuity_roadmap", {})
    current_mission = current.get("active_mission", {})
    current_continuity = current.get("continuity", {})
    current_bridge = current.get("control_bridge", {})

    check(
        mission.get("id") == "REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING",
        "STALE_ACTIVE_MISSION_REFERENCE",
        "unexpected active mission id",
    )
    check(mission.get("github_issue") == 10, "STALE_ACTIVE_MISSION_REFERENCE", "issue must be #10")
    check(repository.get("name") == "leon337/cloud-infrastructure", "STALE_ACTIVE_MISSION_REFERENCE", "repository mismatch")
    check(repository.get("active_branch") == bridge.get("branch"), "MISSION_BRANCH_OR_PR_MISMATCH", "active branch differs from G2-B state")
    check(repository.get("pull_request") == bridge.get("recovery_checkpoint", {}).get("pull_request"), "MISSION_BRANCH_OR_PR_MISMATCH", "PR differs from G2-B state")
    check(mission.get("github_issue") == bridge.get("continuity", {}).get("mission_issue"), "MISSION_BRANCH_OR_PR_MISMATCH", "issue differs from G2-B continuity state")

    check(set(ROADMAP_KEYS).issubset(roadmap), "ROADMAP_STATE_REGRESSION_OR_INVALID_TRANSITION", "R1-R8 must all be present")
    for key in ROADMAP_KEYS:
        state = roadmap.get(key)
        check(state in ALLOWED_STATES, "ROADMAP_STATE_REGRESSION_OR_INVALID_TRANSITION", f"{key} has invalid state {state!r}")

    first_incomplete_index = None
    for idx, key in enumerate(ROADMAP_KEYS):
        if roadmap.get(key) != "COMPLETE":
            first_incomplete_index = idx
            break
    if first_incomplete_index is not None:
        for key in ROADMAP_KEYS[:first_incomplete_index]:
            check(roadmap.get(key) == "COMPLETE", "ROADMAP_STATE_REGRESSION_OR_INVALID_TRANSITION", f"{key} regressed before active stage")
        for key in ROADMAP_KEYS[first_incomplete_index + 1 :]:
            check(roadmap.get(key) == "NOT_STARTED", "ROADMAP_STATE_REGRESSION_OR_INVALID_TRANSITION", f"{key} advanced ahead of first incomplete stage")

    next_step = active.get("next_exact_step")
    check(isinstance(next_step, str) and bool(next_step.strip()), "MISSING_NEXT_EXACT_STEP", "active mission next_exact_step is empty")

    check(current_mission.get("id") == mission.get("id"), "CURRENT_STATE_DRIFT", "state/current.yaml mission id mismatch")
    check(current_mission.get("branch") == repository.get("active_branch"), "CURRENT_STATE_DRIFT", "state/current.yaml active branch mismatch")
    check(current_mission.get("pull_request") == repository.get("pull_request"), "CURRENT_STATE_DRIFT", "state/current.yaml PR mismatch")
    current_roadmap = current_mission.get("roadmap", {})
    for key in ROADMAP_KEYS:
        check(current_roadmap.get(key) == roadmap.get(key), "CURRENT_STATE_DRIFT", f"state/current.yaml {key} differs from active mission")
    check(current_continuity.get("next_exact_step") == next_step, "CURRENT_STATE_DRIFT", "state/current.yaml next_exact_step mismatch")

    check(bridge.get("implementation", {}).get("tasks_1_6") == "COMPLETE_MATERIALLY_REVIEWED", "G2B_TASK_STATE_DRIFT", "Tasks 1-6 changed")
    check(bridge.get("implementation", {}).get("task_7") == "PARTIAL", "G2B_TASK_STATE_DRIFT", "Task 7 must remain PARTIAL before R8 technical work")
    check(bridge.get("implementation", {}).get("task_7_focused_tests", {}).get("pass") == 6, "G2B_TASK_STATE_DRIFT", "Task 7 pass count changed without R8")
    check(bridge.get("implementation", {}).get("task_7_focused_tests", {}).get("fail") == 1, "G2B_TASK_STATE_DRIFT", "Task 7 fail count changed without R8")
    check(bridge.get("implementation", {}).get("tasks_8_10") == "NOT_STARTED", "G2B_TASK_STATE_DRIFT", "Tasks 8-10 advanced before R8")
    check(current_bridge.get("g2b_task_7") == "PARTIAL_6_PASS_1_FAIL", "CURRENT_STATE_DRIFT", "state/current.yaml G2-B Task 7 mismatch")
    check(current_bridge.get("g2b_tasks_8_10") == "NOT_STARTED", "CURRENT_STATE_DRIFT", "state/current.yaml Tasks 8-10 mismatch")

    for gate, value in active.get("human_gates", {}).items():
        check(isinstance(value, str) and "NOT_AUTHORIZED" in value, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", f"{gate} is not fail-closed")
    check(bridge.get("evidence", {}).get("real_write") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real write evidence unexpectedly true")
    check(bridge.get("evidence", {}).get("real_rollback") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real rollback evidence unexpectedly true")
    check(bridge.get("evidence", {}).get("real_revocation") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real revocation evidence unexpectedly true")

    parallel = active.get("parallel_work", {}).get("f1_2c_systemd_runtime_lock", {})
    current_parallel = current.get("work_ownership", {}).get("f1_2c_systemd_runtime_lock", {})
    check(parallel.get("status_for_this_mission") == "ISOLATED_DO_NOT_MODIFY", "PARALLEL_OWNERSHIP_DRIFT", "active mission no longer isolates F1.2c")
    check(current_parallel.get("rule_for_active_continuity_mission") == "ISOLATED_DO_NOT_MODIFY", "PARALLEL_OWNERSHIP_DRIFT", "current state no longer isolates F1.2c")
    check(current_parallel.get("frozen_for_codex") is True, "PARALLEL_OWNERSHIP_DRIFT", "F1.2c is no longer frozen for Codex in this mission")

    memory_path = memory.get("first_memo", {}).get("path")
    check(memory.get("status") == "ACTIVE_REQUIRED", "INSTITUTIONAL_MEMORY_MISSING", "memory contract inactive")
    check(isinstance(memory_path, str) and (ROOT / memory_path).is_file(), "INSTITUTIONAL_MEMORY_MISSING", "first institutional memo missing")
    check((ROOT / "history/memos/README.md").is_file(), "INSTITUTIONAL_MEMORY_MISSING", "memo model missing")

    check(drift.get("status") == "ACTIVE_REQUIRED", "CURRENT_STATE_DRIFT", "drift control contract inactive")
    check(drift.get("principle") == "NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT", "CURRENT_STATE_DRIFT", "unexpected drift principle")

    entrypoints = [
        "README.md",
        "CONTEXT.md",
        "CHECKPOINT.md",
        "docs/53-repository-continuity-context-recovery-mission.md",
    ]
    if isinstance(next_step, str) and next_step:
        for relative in entrypoints:
            try:
                text = read_text(relative)
            except FileNotFoundError:
                errors.append(f"ENTRYPOINT_NEXT_STEP_DRIFT: missing {relative}")
                continue
            check(next_step in text, "ENTRYPOINT_NEXT_STEP_DRIFT", f"{relative} does not expose active next step")
            check(repository.get("active_branch", "") in text, "ENTRYPOINT_NEXT_STEP_DRIFT", f"{relative} does not expose active branch")

    if roadmap.get("R7") == "COMPLETE":
        try:
            cold = load_yaml("state/cold-start-validation.yaml")
        except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"COLD_START_EVIDENCE_MISSING: {exc}")
        else:
            report = cold.get("report")
            check(cold.get("status") == "PASS", "PASS_WITHOUT_EVIDENCE", "R7 complete but cold-start status is not PASS")
            check(isinstance(report, str) and (ROOT / report).is_file(), "COLD_START_EVIDENCE_MISSING", "cold-start report missing")
            evidence = cold.get("evidence", [])
            check(isinstance(evidence, list) and len(evidence) >= 5, "PASS_WITHOUT_EVIDENCE", "cold-start PASS lacks evidence inventory")
            reconstruction = cold.get("reconstruction", {})
            check(reconstruction.get("active_mission") == "REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING", "PASS_WITHOUT_EVIDENCE", "cold-start mission reconstruction mismatch")
            check(reconstruction.get("branch") == "codex/control-bridge-g2b", "PASS_WITHOUT_EVIDENCE", "cold-start branch reconstruction mismatch")
            check(reconstruction.get("tasks_1_6") == "COMPLETE_MATERIALLY_REVIEWED", "PASS_WITHOUT_EVIDENCE", "cold-start Tasks 1-6 mismatch")
            check(reconstruction.get("task_7") == "PARTIAL_6_PASS_1_FAIL", "PASS_WITHOUT_EVIDENCE", "cold-start Task 7 mismatch")
            check(reconstruction.get("tasks_8_10") == "NOT_STARTED", "PASS_WITHOUT_EVIDENCE", "cold-start Tasks 8-10 mismatch")
            check(reconstruction.get("f1_2c") == "ISOLATED_DO_NOT_MODIFY", "PASS_WITHOUT_EVIDENCE", "cold-start F1.2c mismatch")
            check(reconstruction.get("node01_g2b_gate") == "CLOSED_NOT_AUTHORIZED", "PASS_WITHOUT_EVIDENCE", "cold-start NODE-01 gate mismatch")
            check(reconstruction.get("next_exact_step") == next_step, "PASS_WITHOUT_EVIDENCE", "cold-start next step mismatch")

    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(f"CONTINUITY_DRIFT_FAIL {error}", file=sys.stderr)
        return 1
    print("CONTINUITY_DRIFT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
