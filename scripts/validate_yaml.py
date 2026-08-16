#!/usr/bin/env python3
"""Parse every repository YAML document, excluding ignored local state."""

from __future__ import annotations

import pathlib
import sys

import yaml

from yaml_strict import load_all_strict


ROOT = pathlib.Path(__file__).resolve().parents[1]


def main() -> int:
    files = sorted((*ROOT.rglob("*.yaml"), *ROOT.rglob("*.yml")))
    files = [path for path in files if ".venv" not in path.parts]
    failures: list[str] = []
    for path in files:
        try:
            with path.open(encoding="utf-8") as stream:
                list(load_all_strict(stream))
        except (OSError, yaml.YAMLError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: {exc}")
    if failures:
        for failure in failures:
            print(f"YAML_PARSE_FAIL {failure}", file=sys.stderr)
        return 1
    print(f"YAML_PARSE_PASS count={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
