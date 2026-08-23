#!/usr/bin/env python3
"""Fail on high-confidence secret material in the currently tracked tree."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:OPENSSH|RSA|EC|DSA) PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
}


def tracked_files() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z"])
    return [Path(item.decode("utf-8")) for item in raw.split(b"\0") if item]


def main() -> int:
    findings: list[str] = []
    scanned = 0
    for path in tracked_files():
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        scanned += 1
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path}:{name}")

    if findings:
        for finding in findings:
            print(f"SECRET_SCAN_FAIL {finding}")
        return 1

    print(f"CURRENT_TREE_SECRET_SCAN_PASS files={scanned} patterns={len(PATTERNS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
