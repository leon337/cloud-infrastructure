#!/usr/bin/env python3
"""Check repository-local Markdown links without fetching external resources."""

from __future__ import annotations

import pathlib
import re
import sys
from collections.abc import Iterator
from urllib.parse import unquote


ROOT = pathlib.Path(__file__).resolve().parents[1]
LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"(?m)^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")
EXTERNAL_PREFIXES = ("http://", "https://", "#", "mailto:", "app://")


def markdown_targets(content: str) -> Iterator[str]:
    yield from LINK.findall(content)
    for angle_target, plain_target in REFERENCE_LINK.findall(content):
        yield angle_target or plain_target


def normalize_target(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def local_target_error(source: pathlib.Path, target: str) -> str | None:
    normalized = normalize_target(target)
    if normalized.lower().startswith(EXTERNAL_PREFIXES):
        return None
    relative_target = unquote(normalized.split("#", 1)[0])
    if not relative_target:
        return None
    resolved = (source.parent / relative_target).resolve()
    if resolved != ROOT and ROOT not in resolved.parents:
        return "target escapes repository root"
    if not resolved.exists():
        return "target does not exist"
    return None


def main() -> int:
    failures: list[tuple[pathlib.Path, str, str]] = []
    for path in sorted(ROOT.rglob("*.md")):
        if ".venv" in path.parts or ".git" in path.parts:
            continue
        for target in markdown_targets(path.read_text(encoding="utf-8")):
            error = local_target_error(path, target)
            if error:
                failures.append((path.relative_to(ROOT), target, error))
    if failures:
        for path, target, error in failures:
            print(
                f"LOCAL_MARKDOWN_LINK_FAIL file={path} target={target} reason={error}",
                file=sys.stderr,
            )
        return 1
    print("LOCAL_MARKDOWN_LINKS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
