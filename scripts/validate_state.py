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
        ("continuity", "roadmap_checklist", "status"): "NOT_ADOPTED",
        ("project", "integration_status"): "DOCUMENTATION_AND_INTEGRATION_DRIFT",
        ("platform", "f1_2c", "status"): "REQUIRES_REVIEW",
        ("platform", "f1_2c", "accepted"): False,
        ("platform", "f1_2c", "node01_reapply_authorized"): False,
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
        ("boundaries", "node01_privileged_operations"): False,
        ("boundaries", "production_promoted"): False,
        ("authorization", "production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        ("authorization", "g2b_real_write"): "NOT_AUTHORIZED",
        ("authorization", "f1_2c_node01_reapply"): "NOT_AUTHORIZED",
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
