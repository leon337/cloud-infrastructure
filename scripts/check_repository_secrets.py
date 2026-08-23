#!/usr/bin/env python3
"""Fail closed on high-confidence secret material without printing its value."""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from control_plane.g2b.secret_policy import CONTENT_RULES, content_findings


MAX_SCAN_BYTES = 8 * 1024 * 1024

# A historical state field used a secret-shaped key for a non-secret status.
# The value is not reproduced here; only the SHA-256 of the normalized line is
# allowlisted. All other assignment-shaped history remains scanned.
HISTORICAL_NON_SECRET_ASSIGNMENT_LINE_SHA256 = {
    "5a01f4f54c233a03be979b009a24c7e80206334dd860304710c953ac931ece6e",
}

ALLOWED_SECRETISH_PATHS = {
    ".env.example",
}

FORBIDDEN_PATH_PATTERNS = (
    re.compile(r"(^|/)\.env(?:\..+)?$"),
    re.compile(r"(^|/)id_(?:rsa|dsa|ecdsa|ed25519)$"),
    re.compile(r"\.(?:key|p12|pfx|jks|keystore)$", re.IGNORECASE),
    re.compile(r"(^|/)(?:secrets?|credentials?)(?:/|$)", re.IGNORECASE),
)

def repository_files() -> Iterable[pathlib.Path]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    for raw_path in result.stdout.split(b"\0"):
        if raw_path:
            yield pathlib.Path(raw_path.decode("utf-8", errors="strict"))


def path_is_forbidden(rendered: str) -> bool:
    """Return whether a repository path is intrinsically secret-bearing."""
    if pathlib.PurePosixPath(rendered).name in ALLOWED_SECRETISH_PATHS:
        return False
    return any(rule.search(rendered) for rule in FORBIDDEN_PATH_PATTERNS)


def read_repository_file(relative_path: pathlib.Path) -> bytes | None:
    """Read without following a worktree symlink outside the repository."""
    absolute_path = ROOT / relative_path
    if absolute_path.is_symlink():
        return os.readlink(absolute_path).encode("utf-8", errors="surrogateescape")
    if not absolute_path.is_file():
        return None
    size = absolute_path.stat().st_size
    if size > MAX_SCAN_BYTES:
        return None
    return absolute_path.read_bytes()


def reachable_history_blobs() -> Iterator[tuple[str, int]]:
    """Yield every reachable Git blob and its size, including merge ancestry."""
    object_ids = subprocess.run(
        ["git", "rev-list", "--objects", "--all", "--no-object-names"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if not object_ids:
        return

    unique_ids = sorted(set(object_ids))
    metadata = subprocess.run(
        ["git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        cwd=ROOT,
        check=True,
        input="\n".join(unique_ids) + "\n",
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for line in metadata:
        object_id, object_type, raw_size = line.split()
        if object_type == "blob":
            yield object_id, int(raw_size)


def scan() -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for relative_path in repository_files():
        rendered = relative_path.as_posix()
        if path_is_forbidden(rendered):
            findings.append((rendered, "forbidden-secret-path"))

        absolute_path = ROOT / relative_path
        if absolute_path.exists() and not absolute_path.is_symlink():
            if absolute_path.is_file() and absolute_path.stat().st_size > MAX_SCAN_BYTES:
                findings.append((rendered, "unscanned-large-file"))
                continue
        content = read_repository_file(relative_path)
        if content is None:
            continue
        for rule_name in content_findings(content):
            findings.append((rendered, rule_name))

    for object_id, size in reachable_history_blobs():
        rendered = f"<git-history-blob:{object_id[:12]}>"
        if size > MAX_SCAN_BYTES:
            findings.append((rendered, "unscanned-large-blob"))
            continue
        content = subprocess.run(
            ["git", "cat-file", "blob", object_id],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        for rule_name in content_findings(
            content,
            allowed_assignment_line_hashes=frozenset(
                HISTORICAL_NON_SECRET_ASSIGNMENT_LINE_SHA256
            ),
        ):
            findings.append((rendered, rule_name))
    return findings


def main() -> int:
    findings = scan()
    if findings:
        for path, rule_name in sorted(set(findings)):
            print(f"SECRET_POLICY_FAIL file={path} rule={rule_name}", file=sys.stderr)
        return 1
    print("SECRET_POLICY_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
