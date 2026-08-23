#!/usr/bin/env python3
"""Parse every tracked YAML document in the current repository tree."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


def main() -> int:
    raw = subprocess.check_output(["git", "ls-files", "-z", "*.yaml", "*.yml"])
    paths = [Path(item.decode("utf-8")) for item in raw.split(b"\0") if item]
    failures: list[str] = []
    for path in paths:
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as exc:  # PyYAML exposes multiple parser exception classes.
            failures.append(f"{path}: {exc}")

    if failures:
        for failure in failures:
            print(f"YAML_VALIDATION_FAIL {failure}")
        return 1

    print(f"YAML_VALIDATION_PASS count={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
