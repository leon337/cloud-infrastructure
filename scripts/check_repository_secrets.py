#!/usr/bin/env python3
"""Fail closed on high-confidence secret material without printing its value."""

from __future__ import annotations

import os
import hashlib
import pathlib
import re
import subprocess
import sys
from collections.abc import Iterable, Iterator


ROOT = pathlib.Path(__file__).resolve().parents[1]
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

CONTENT_RULES = {
    "private-key-material": re.compile(
        rb"-----BEGIN (?:(?:OPENSSH|RSA|EC|DSA|ENCRYPTED) )?PRIVATE KEY-----"
    ),
    "pgp-private-key-material": re.compile(
        rb"-----BEGIN PGP PRIVATE " rb"KEY BLOCK-----"
    ),
    "age-secret-key": re.compile(rb"\bAGE-SECRET-KEY-1[0-9A-Z]{20,}\b"),
    "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "github-token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "github-fine-grained-token": re.compile(rb"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "gitlab-token": re.compile(rb"\bglpat-[A-Za-z0-9_-]{20,}\b"),
    "openai-token": re.compile(rb"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b"),
    "slack-token": re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    "jwt": re.compile(
        rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    ),
    "secret-like-assignment": re.compile(
        rb"(?im)^[ \t]*(?:export[ \t]+)?"
        rb"(?:[a-z0-9]+[_-])*"
        rb"(?:password[_-]?hash|password|passphrase|client[_-]?secret|"
        rb"api[_-]?key|access[_-]?token|refresh[_-]?token|secret[_-]?key|"
        rb"private[_-]?key|credential|secret)[ \t]*[:=][ \t]*[\"']?"
        rb"(?!(?:\$|\{\{|secret://|env://|<|"
        rb"false\b|true\b|null\b|none\b|example\b|placeholder\b|redacted\b|"
        rb"disabled(?:\b|[-_])|deferred(?:\b|[-_])|pending(?:\b|[-_])|"
        rb"change[-_]?me\b|not-a-real-secret\b))"
        rb"[^\s\"'#]{8,}",
        re.IGNORECASE,
    ),
    "credential-in-uri": re.compile(
        rb"\b(?:https?|postgres(?:ql)?|mysql|redis|amqps?)://"
        rb"[^\s/:@]+:[^\s/@]+@",
        re.IGNORECASE,
    ),
}


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


def content_findings(
    content: bytes,
    *,
    allowed_assignment_line_hashes: frozenset[str] = frozenset(),
) -> Iterator[str]:
    for rule_name, rule in CONTENT_RULES.items():
        if rule_name != "secret-like-assignment":
            if rule.search(content):
                yield rule_name
            continue

        unapproved_match = False
        for match in rule.finditer(content):
            line_start = content.rfind(b"\n", 0, match.start()) + 1
            line_end = content.find(b"\n", match.end())
            if line_end < 0:
                line_end = len(content)
            normalized_line = content[line_start:line_end].strip()
            line_sha256 = hashlib.sha256(normalized_line).hexdigest()
            if line_sha256 not in allowed_assignment_line_hashes:
                unapproved_match = True
                break
        if unapproved_match:
            yield rule_name


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
