#!/usr/bin/env python3
from __future__ import annotations

import pathlib
import re
import subprocess
from typing import Any


SHA_RE = re.compile(r"^[0-9a-f]{40}$")

ALLOWED_DOC_EXACT = {
    "CHECKPOINT.md",
    "CONTEXT.md",
    "README.md",
    "docs/45-revised-implementation-roadmap.md",
    "docs/46-technology-mapping-v1.md",
    "docs/superpowers/specs/2026-08-19-evidence-inheritance-non-executable-delta-design.md",
}
ALLOWED_PREFIXES = ("history/", "evidence/SLICE-002C/")
STATE_FILES = {
    "state/current.yaml",
    "state/components.yaml",
    "state/platform-discovery.yaml",
}
MATERIAL_PREFIXES = (
    ".github/workflows/",
    "automation/",
    "scripts/",
    "tests/",
    "platform/",
    "config/",
)
MATERIAL_EXACT = {
    "requirements-dev.lock",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "package.json",
    "package-lock.json",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}


def _git(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _refusal(anchor: str, candidate: str, reason: str, paths: list[str] | None = None) -> dict[str, Any]:
    return {
        "decision": "REFUSED",
        "reason": reason,
        "anchor": anchor,
        "candidate": candidate,
        "changed_paths": sorted(paths or []),
        "state_changes": {},
        "static_evidence": None,
    }


def _classify_path(path: str) -> str:
    if path in STATE_FILES or path in ALLOWED_DOC_EXACT or path.startswith(ALLOWED_PREFIXES):
        return "candidate_non_material"
    if path in MATERIAL_EXACT or path.startswith(MATERIAL_PREFIXES):
        return "material"
    if path.startswith("requirements") and path.endswith(".lock"):
        return "material"
    return "unknown"


def _name_status(repo: pathlib.Path, anchor: str, candidate: str) -> list[tuple[str, str]] | None:
    proc = _git(repo, "diff", "--name-status", "--no-renames", "-z", anchor, candidate, "--")
    if proc.returncode != 0:
        return None
    tokens = proc.stdout.decode("utf-8", errors="strict").split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) % 2:
        return None
    return [(tokens[index], tokens[index + 1]) for index in range(0, len(tokens), 2)]


def classify_repository_delta(repo: pathlib.Path, anchor: str, candidate: str) -> dict[str, Any]:
    repo = pathlib.Path(repo).resolve()
    if not SHA_RE.fullmatch(anchor) or not SHA_RE.fullmatch(candidate):
        return _refusal(anchor, candidate, "REFUSED_INVALID_ANCHOR")

    for sha in (anchor, candidate):
        exists = _git(repo, "cat-file", "-e", f"{sha}^{{commit}}")
        if exists.returncode != 0:
            return _refusal(anchor, candidate, "REFUSED_INVALID_ANCHOR")

    ancestor = _git(repo, "merge-base", "--is-ancestor", anchor, candidate)
    if ancestor.returncode != 0:
        return _refusal(anchor, candidate, "REFUSED_INVALID_ANCHOR")

    entries = _name_status(repo, anchor, candidate)
    if entries is None:
        return _refusal(anchor, candidate, "REFUSED_INVALID_ANCHOR")

    changed_paths = [path for _, path in entries]

    summary = _git(repo, "diff", "--summary", "--no-renames", anchor, candidate, "--")
    if summary.returncode != 0:
        return _refusal(anchor, candidate, "REFUSED_INVALID_ANCHOR", changed_paths)
    if b"mode change " in summary.stdout:
        return _refusal(anchor, candidate, "REFUSED_MATERIAL_DELTA", changed_paths)

    for status, path in entries:
        if status not in {"A", "M"}:
            return _refusal(anchor, candidate, "REFUSED_MATERIAL_DELTA", changed_paths)
        classification = _classify_path(path)
        if classification == "material":
            return _refusal(anchor, candidate, "REFUSED_MATERIAL_DELTA", changed_paths)
        if classification == "unknown":
            return _refusal(anchor, candidate, "REFUSED_UNKNOWN_PATH", changed_paths)

    return {
        "decision": "PASS",
        "reason": "NON_EXECUTABLE_PATH_DELTA",
        "anchor": anchor,
        "candidate": candidate,
        "changed_paths": sorted(changed_paths),
        "state_changes": {},
        "static_evidence": None,
    }
