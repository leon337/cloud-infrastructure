#!/usr/bin/env python3
from __future__ import annotations

import json
import pathlib
from typing import Any

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_yaml(relative: str) -> dict[str, Any]:
    data = yaml.safe_load((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{relative}: expected mapping")
    return data


def reconstruct() -> dict[str, Any]:
    active = load_yaml("state/active-mission.yaml")
    bridge = load_yaml("state/control-bridge-g2b.yaml")
    current = load_yaml("state/current.yaml")

    mission = active["mission"]
    repository = active["repository"]
    g2b = active["control_bridge_g2b"]
    parallel = active["parallel_work"]["f1_2c_systemd_runtime_lock"]

    return {
        "active_mission": mission["id"],
        "mission_status": mission["status"],
        "issue": mission["github_issue"],
        "branch": repository["active_branch"],
        "base_branch": repository["base_branch"],
        "pull_request": repository["pull_request"],
        "pull_request_state": repository["pull_request_state"],
        "tasks_1_6": g2b["tasks_1_6"],
        "task_7": f"{g2b['task_7']}_{g2b['task_7_focused_tests']['pass']}_PASS_{g2b['task_7_focused_tests']['fail']}_FAIL",
        "known_red": g2b["known_red"],
        "tasks_8_10": g2b["tasks_8_10"],
        "f1_2c": parallel["status_for_this_mission"],
        "node01_g2b_gate": active["human_gates"]["node_01_g2b_bootstrap"],
        "real_grant_gate": active["human_gates"]["real_grant_issue_or_reissue"],
        "real_write_gate": active["human_gates"]["real_bounded_write"],
        "merge_gate": active["human_gates"]["merge_g2b"],
        "real_write_executed": bridge["evidence"]["real_write"],
        "roadmap": active["continuity_roadmap"],
        "next_exact_step": active["next_exact_step"],
        "current_state_next_exact_step": current["continuity"]["next_exact_step"],
    }


def main() -> int:
    print(json.dumps(reconstruct(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
