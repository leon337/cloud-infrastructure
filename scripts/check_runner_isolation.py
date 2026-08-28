#!/usr/bin/env python3
"""Reject GitHub Actions workflows that bypass runner process isolation."""
from __future__ import annotations

import argparse
from pathlib import Path

GUARD_TOKEN = "cloud-infrastructure-runner-isolation-guard"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    root = Path(args.root)
    workflows = root / ".github" / "workflows"
    findings: list[tuple[Path, int, str]] = []
    if workflows.is_dir():
        for path in sorted([*workflows.glob("*.yml"), *workflows.glob("*.yaml")]):
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if "RUNNER_TRACKING_ID" in line:
                    findings.append((path, lineno, "runner-tracking-id-must-not-be-modified"))
            if "self-hosted" in text and GUARD_TOKEN not in text:
                findings.append((path, 0, "self-hosted-workflow-missing-isolation-guard"))
    if findings:
        for path, lineno, rule in findings:
            location = f" line={lineno}" if lineno else ""
            print(f"RUNNER_ISOLATION_POLICY_FAIL file={path.relative_to(root)}{location} rule={rule}")
        return 1
    print("RUNNER_ISOLATION_POLICY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
