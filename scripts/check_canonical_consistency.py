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
        Path("state/current.yaml"),
        Path("scripts/test.sh"),
    ]
    for path in required:
        if not path.is_file():
            raise AssertionError(f"missing canonical surface: {path}")

    state = yaml.safe_load(Path("state/current.yaml").read_text(encoding="utf-8"))

    for token in (
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
        ):
            require_token(path, token)

    active = state["continuity"]["active_mission_model"]
    if active["status"] == "NOT_ADOPTED" and Path(active["file"]).exists():
        raise AssertionError("state/active-mission.yaml exists despite NOT_ADOPTED decision")

    roadmap = state["continuity"]["roadmap_checklist"]
    if roadmap["status"] == "NOT_ADOPTED" and Path(roadmap["file"]).exists():
        raise AssertionError("ROADMAP-CHECKLIST.md exists despite NOT_ADOPTED decision")

    if state["toolchain"]["canonical_entrypoint"] != "scripts/test.sh":
        raise AssertionError("toolchain entrypoint drift")

    print("CANONICAL_CONSISTENCY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
