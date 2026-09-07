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
        task9_basis_receipt = load_yaml("evidence/CONTROL-BRIDGE-G2B/TASK-9-VALIDATION-BASIS-20260907.yaml")
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        return [f"CURRENT_STATE_DRIFT: cannot load canonical state: {exc}"]

    mission = active.get("mission", {})
    repository = active.get("repository", {})
    roadmap = active.get("continuity_roadmap", {})
    current_mission = current.get("active_mission", {})
    current_continuity = current.get("continuity", {})
    current_bridge = current.get("control_bridge", {})

    check(
        mission.get("id") == "CONTROL_BRIDGE_G2B",
        "STALE_ACTIVE_MISSION_REFERENCE",
        "unexpected active mission id",
    )
    check(mission.get("continuity_origin_issue") == 10, "STALE_ACTIVE_MISSION_REFERENCE", "continuity origin issue must be #10")
    check(repository.get("name") == "leon337/cloud-infrastructure", "STALE_ACTIVE_MISSION_REFERENCE", "repository mismatch")
    check(repository.get("active_branch") == bridge.get("branch"), "MISSION_BRANCH_OR_PR_MISMATCH", "active branch differs from G2-B state")
    check(repository.get("pull_request") == bridge.get("candidate", {}).get("pull_request"), "MISSION_BRANCH_OR_PR_MISMATCH", "current candidate PR differs from G2-B state")
    check(mission.get("continuity_origin_issue") == bridge.get("continuity", {}).get("mission_issue"), "MISSION_BRANCH_OR_PR_MISMATCH", "continuity origin issue differs from G2-B state")

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
    check(mission.get("status") == "WAITING_HUMAN_GATE", "CURRENT_STATE_DRIFT", "Task 9 mission must wait at human gate")
    check(current_mission.get("status") == "WAITING_HUMAN_GATE", "CURRENT_STATE_DRIFT", "state/current.yaml mission must wait at human gate")
    check(repository.get("active_branch") == "team/g2b-task9-prebootstrap-gate-20260907", "MISSION_BRANCH_OR_PR_MISMATCH", "unexpected Task 9 branch")
    check(repository.get("pull_request") == 56, "MISSION_BRANCH_OR_PR_MISMATCH", "Task 9 must reference PR #56")
    check(next_step == "HUMAN_REVIEW_AND_NODE01_G2B_BOOTSTRAP", "MISSING_NEXT_EXACT_STEP", "unexpected Task 9 next step")

    check(bridge.get("implementation", {}).get("tasks_1_6") == "COMPLETE_MATERIALLY_REVIEWED", "G2B_TASK_STATE_DRIFT", "Tasks 1-6 changed")
    check(bridge.get("implementation", {}).get("task_7") == "COMPLETE", "G2B_TASK_STATE_DRIFT", "Task 7 must remain COMPLETE after R8 evidence")
    check(bridge.get("implementation", {}).get("task_7_focused_tests", {}).get("pass") == 7, "G2B_TASK_STATE_DRIFT", "Task 7 pass count must remain 7 after R8")
    check(bridge.get("implementation", {}).get("task_7_focused_tests", {}).get("fail") == 0, "G2B_TASK_STATE_DRIFT", "Task 7 fail count must remain 0 after R8")
    check(str(bridge.get("implementation", {}).get("ansible_syntax", "")).startswith("PASS_3_"), "PASS_WITHOUT_EVIDENCE", "Task 7 completion lacks Ansible syntax evidence")
    check(bool(bridge.get("implementation", {}).get("task_7_validation", {}).get("candidate_sha")), "PASS_WITHOUT_EVIDENCE", "Task 7 completion lacks candidate SHA")
    check(bridge.get("implementation", {}).get("task_8") == "COMPLETE_PASS_DISPOSABLE_HOSTED_AND_LAB_13_OF_13", "G2B_TASK_STATE_DRIFT", "Task 8 completion result mismatch")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("disposable_markers_pass") == 13, "PASS_WITHOUT_EVIDENCE", "Task 8 PASS lacks 13 acceptance markers")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("disposable_cleanup") == "PASS", "PASS_WITHOUT_EVIDENCE", "Task 8 PASS lacks bounded cleanup")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("postmerge_source_sha") == "f1be00b8f7623316188a62ce94caf9f3e2feb21f", "PASS_WITHOUT_EVIDENCE", "Task 8 completion lacks exact post-merge SHA")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("postmerge_control_bridge_run") == 34083420595, "PASS_WITHOUT_EVIDENCE", "Task 8 completion lacks control-bridge post-merge run")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("postmerge_foundation_run") == 34083420638, "PASS_WITHOUT_EVIDENCE", "Task 8 completion lacks foundation post-merge run")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("postmerge_docker_run") == 34083420634, "PASS_WITHOUT_EVIDENCE", "Task 8 completion lacks docker post-merge run")
    check(bridge.get("implementation", {}).get("task_8_validation", {}).get("postmerge_shellcheck") == "PASS_16_OF_16", "PASS_WITHOUT_EVIDENCE", "Task 8 completion lacks hosted ShellCheck evidence")
    check(bridge.get("implementation", {}).get("task_9") == "WAITING_HUMAN_GATE", "G2B_TASK_STATE_DRIFT", "Task 9 must stop at the NODE-01 human gate")
    check(bridge.get("implementation", {}).get("task_10") == "NOT_STARTED", "G2B_TASK_STATE_DRIFT", "Task 10 must not start before explicit authorization")
    check(bridge.get("implementation", {}).get("tasks_9_10") == "TASK_9_WAITING_HUMAN_GATE_TASK_10_NOT_STARTED", "G2B_TASK_STATE_DRIFT", "Task 9/10 combined state mismatch")
    check(bridge.get("implementation", {}).get("tasks_8_10") == "TASK_8_COMPLETE_TASK_9_WAITING_HUMAN_GATE_TASK_10_NOT_STARTED", "G2B_TASK_STATE_DRIFT", "combined Task 8-10 state mismatch")
    check(current_bridge.get("g2b_task_7") == "COMPLETE_7_PASS_0_FAIL", "CURRENT_STATE_DRIFT", "state/current.yaml G2-B Task 7 mismatch")
    check(current_bridge.get("g2b_task_8") == "COMPLETE_PASS_DISPOSABLE_HOSTED_AND_LAB_13_OF_13", "CURRENT_STATE_DRIFT", "state/current.yaml Task 8 mismatch")
    check(current_bridge.get("g2b_tasks_9_10") == "TASK_9_WAITING_HUMAN_GATE_TASK_10_NOT_STARTED", "CURRENT_STATE_DRIFT", "state/current.yaml Tasks 9-10 mismatch")
    check(current_bridge.get("g2b_tasks_8_10") == "TASK_8_COMPLETE_TASK_9_WAITING_HUMAN_GATE_TASK_10_NOT_STARTED", "CURRENT_STATE_DRIFT", "state/current.yaml combined Task 8-10 mismatch")
    check(current_bridge.get("g2b_lifecycle") == "LAB_VALIDATED_INACTIVE", "CURRENT_STATE_DRIFT", "state/current.yaml must not activate G2-B from disposable evidence")
    check(bridge.get("status") == "WAITING_FOR_HUMAN_GATE_G2B_NODE01_BOOTSTRAP", "G2B_TASK_STATE_DRIFT", "G2-B must stop at the NODE-01 bootstrap gate")
    check(current_bridge.get("g2b") == "WAITING_FOR_HUMAN_GATE_G2B_NODE01_BOOTSTRAP", "CURRENT_STATE_DRIFT", "state/current.yaml G2-B gate status mismatch")
    check(current_bridge.get("g2b_pr") == "56_DRAFT_DO_NOT_MERGE", "CURRENT_STATE_DRIFT", "state/current.yaml must reference Draft PR #56")

    for gate, value in active.get("human_gates", {}).items():
        if gate == "merge_g2b":
            check(value == "CLOSED_NOT_AUTHORIZED_TASK9_DRAFT", "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "merge must remain closed for the Task 9 draft")
        elif gate == "task8_qemu_tcg_host_packages":
            check(value == "CLOSED_NOT_REQUIRED_AFTER_DISPOSABLE_PASS", "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "obsolete Task 8 QEMU package gate must remain closed")
        elif gate == "publication_g2b":
            check(value == "EXECUTED_DRAFT_PR56_NO_MERGE", "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "Task 9 publication must be limited to Draft PR #56")
        else:
            check(isinstance(value, str) and "NOT_AUTHORIZED" in value, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", f"{gate} is not fail-closed")
    check(bridge.get("evidence", {}).get("real_write") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real write evidence unexpectedly true")
    check(bridge.get("evidence", {}).get("real_rollback") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real rollback evidence unexpectedly true")
    check(bridge.get("evidence", {}).get("real_revocation") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "real revocation evidence unexpectedly true")
    check(bridge.get("evidence", {}).get("mcf_effective_use") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "MCF effective-use evidence unexpectedly true")
    check(bridge.get("candidate", {}).get("push_executed") is True, "CURRENT_STATE_DRIFT", "Task 9 draft publication must be recorded")
    check(bridge.get("candidate", {}).get("pull_request") == 56, "MISSION_BRANCH_OR_PR_MISMATCH", "Task 9 candidate PR must be #56")
    check(bridge.get("candidate", {}).get("merge_authorized") is False, "HUMAN_GATE_BYPASS_OR_AMBIGUITY", "candidate unexpectedly claims merge authorization")
    basis = bridge.get("candidate", {}).get("validation_basis", {})
    check(basis.get("classification") == "VALIDATION_BASIS_SNAPSHOT_BEFORE_CLOSEOUT_METADATA", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis classification mismatch")
    check(basis.get("sha") == "7f1f331cc7309190e5dcc16429d3557cd721eb58", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis SHA mismatch")
    check(basis.get("receipt") == "evidence/CONTROL-BRIDGE-G2B/TASK-9-VALIDATION-BASIS-20260907.yaml", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis receipt path mismatch")
    check(basis.get("control_bridge_run") == 34087239108, "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks control-bridge exact-head run")
    check(basis.get("foundation_run") == 34087241172, "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks foundation exact-head run")
    check(basis.get("docker_run") == 34087243164, "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks docker exact-head run")
    check(basis.get("unit_tests") == "PASS_400_OF_400", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks unit-test evidence")
    check(basis.get("ansible_syntax") == "PASS_9_OF_9", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks Ansible evidence")
    check(basis.get("shellcheck") == "PASS_16_OF_16", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks ShellCheck evidence")
    check(basis.get("g2b_lifecycle") == "PASS_13_OF_13_BOUNDED_CLEANUP", "PASS_WITHOUT_EVIDENCE", "Task 9 validation basis lacks lifecycle evidence")
    check(basis.get("validates_future_closeout_commit") is False, "PASS_WITHOUT_EVIDENCE", "validation basis must not claim future-closeout validation")
    active_validation = active.get("validation", {})
    check(active_validation.get("task9_hosted_ci") == "PASS_THREE_WORKFLOWS_EXACT_HEAD_VALIDATION_BASIS", "PASS_WITHOUT_EVIDENCE", "active mission Task 9 hosted CI status mismatch")
    check(active_validation.get("task9_validation_basis_sha") == "7f1f331cc7309190e5dcc16429d3557cd721eb58", "PASS_WITHOUT_EVIDENCE", "active mission Task 9 basis SHA mismatch")
    check(active_validation.get("task9_validation_basis_receipt") == "evidence/CONTROL-BRIDGE-G2B/TASK-9-VALIDATION-BASIS-20260907.yaml", "PASS_WITHOUT_EVIDENCE", "active mission Task 9 receipt path mismatch")
    check(task9_basis_receipt.get("classification") == basis.get("classification"), "PASS_WITHOUT_EVIDENCE", "Task 9 receipt classification differs from canonical state")
    check(task9_basis_receipt.get("basis_sha") == basis.get("sha"), "PASS_WITHOUT_EVIDENCE", "Task 9 receipt SHA differs from canonical state")
    receipt_runs = task9_basis_receipt.get("hosted_exact_head", {})
    check(receipt_runs.get("control_bridge_g2b_ci", {}).get("run") == basis.get("control_bridge_run"), "PASS_WITHOUT_EVIDENCE", "Task 9 receipt control-bridge run mismatch")
    check(receipt_runs.get("foundation_ci", {}).get("run") == basis.get("foundation_run"), "PASS_WITHOUT_EVIDENCE", "Task 9 receipt foundation run mismatch")
    check(receipt_runs.get("docker_boundary_ci", {}).get("run") == basis.get("docker_run"), "PASS_WITHOUT_EVIDENCE", "Task 9 receipt docker run mismatch")
    check(task9_basis_receipt.get("semantics", {}).get("validates_future_closeout_commit") is False, "PASS_WITHOUT_EVIDENCE", "Task 9 receipt must be a pre-closeout validation snapshot")

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
            check(reconstruction.get("next_exact_step") == "R8_RESUME_G2B_TASK7_FROM_RECOVERED_POINT", "PASS_WITHOUT_EVIDENCE", "historical R7 cold-start next step mismatch")

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
