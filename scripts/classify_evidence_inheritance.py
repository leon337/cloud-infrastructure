#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

import yaml


SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MISSING = object()
POLICY_NAME = "F1_2C_NON_EXECUTABLE_EVIDENCE_INHERITANCE_V1"

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

ALLOWED_STATE_PATHS = {
    "state/current.yaml": {
        "documentation_state",
        "project.phases.future_platform_implementation",
        "project.next_exact_step",
        "status_layer.last_material_checkpoint",
        "status_layer.last_relevant_commit",
        "status_layer.last_ci_run_id",
        "authorization.next_step",
        "codex_execution.active_slice",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.status",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.disposable_integration",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.node_01_services_desired_state",
    },
    "state/components.yaml": {
        "platform_components.network_enforcement.lifecycle",
        "platform_components.network_enforcement.validation.disposable_integration",
        "platform_components.network_enforcement.validation.node_01_services_desired_state",
    },
    "state/platform-discovery.yaml": {
        "phase",
        "implementation.current_slice_status",
        "implementation.next_step",
        "implementation.f1_2c_repo_only.status",
        "implementation.f1_2c_repo_only.disposable_integration",
        "implementation.f1_2c_repo_only.node_01_services_desired_state",
    },
}

PROTECTED_EXPECTED = {
    ("state/current.yaml", "platform_discovery.production_promotion_authorized"): False,
    ("state/current.yaml", "authorization.production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
    ("state/current.yaml", "project.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/current.yaml", "authorization.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/current.yaml", "codex_execution.working_branch"): "codex/mission-001-f1-2c-network-enforcement",
    ("state/current.yaml", "codex_execution.mission"): "docs/CODEX-EXECUTION-MISSION-001.md",
    ("state/platform-discovery.yaml", "production_promotion_authorized"): False,
    ("state/platform-discovery.yaml", "credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/platform-discovery.yaml", "execution_mission"): "docs/CODEX-EXECUTION-MISSION-001.md",
    ("state/platform-discovery.yaml", "implementation.production_promotion"): "NOT_AUTHORIZED",
    ("state/platform-discovery.yaml", "implementation.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/components.yaml", "production.deployment_authorized"): False,
    ("state/components.yaml", "production.promotion_gate"): "LEANDRO",
    ("state/components.yaml", "credential_rotation.status"): "DEFERRED_BY_HUMAN_DECISION",
}


class UsageError(ValueError):
    pass


class EvidenceArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise UsageError(message)


def _git(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _refusal(
    anchor: str,
    candidate: str,
    reason: str,
    paths: list[str] | None = None,
    state_changes: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    return {
        "decision": "REFUSED",
        "reason": reason,
        "anchor": anchor,
        "candidate": candidate,
        "changed_paths": sorted(paths or []),
        "state_changes": state_changes or {},
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
    try:
        tokens = proc.stdout.decode("utf-8", errors="strict").split("\0")
    except UnicodeDecodeError:
        return None
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) % 2:
        return None
    return [(tokens[index], tokens[index + 1]) for index in range(0, len(tokens), 2)]


def _git_show_yaml(repo: pathlib.Path, sha: str, path: str) -> Any:
    proc = _git(repo, "show", f"{sha}:{path}")
    if proc.returncode != 0:
        raise ValueError(f"missing state file: {path}")
    try:
        text = proc.stdout.decode("utf-8", errors="strict")
        return yaml.safe_load(text)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid yaml: {path}") from exc


def diff_yaml_paths(before: Any, after: Any, prefix: str = "") -> list[str]:
    if isinstance(before, dict) and isinstance(after, dict):
        changes: list[str] = []
        for key in sorted(set(before) | set(after), key=str):
            child = f"{prefix}.{key}" if prefix else str(key)
            if key not in before or key not in after:
                changes.append(child)
                continue
            changes.extend(diff_yaml_paths(before[key], after[key], child))
        return changes
    if before != after:
        return [prefix]
    return []


def _get_path(document: Any, dotted: str) -> Any:
    current = document
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return _MISSING
        current = current[part]
    return current


def validate_state_delta(
    repo: pathlib.Path,
    anchor: str,
    candidate: str,
    changed_state_files: list[str],
) -> dict[str, Any]:
    if not changed_state_files:
        return {
            "decision": "PASS",
            "reason": "STATE_UNCHANGED",
            "state_changes": {},
        }

    state_changes: dict[str, list[str]] = {}
    candidate_docs: dict[str, Any] = {}

    try:
        for path in sorted(STATE_FILES):
            candidate_docs[path] = _git_show_yaml(repo, candidate, path)

        for path in sorted(changed_state_files):
            before = _git_show_yaml(repo, anchor, path)
            after = candidate_docs[path]
            changes = sorted(diff_yaml_paths(before, after))
            state_changes[path] = changes
            allowed = ALLOWED_STATE_PATHS[path]
            if any(changed not in allowed for changed in changes):
                return {
                    "decision": "REFUSED",
                    "reason": "REFUSED_PROTECTED_STATE_CHANGE",
                    "state_changes": state_changes,
                }

        for (path, dotted), expected in PROTECTED_EXPECTED.items():
            actual = _get_path(candidate_docs[path], dotted)
            if actual is _MISSING or actual != expected:
                return {
                    "decision": "REFUSED",
                    "reason": "REFUSED_PROTECTED_STATE_CHANGE",
                    "state_changes": state_changes,
                }
    except (KeyError, ValueError):
        return {
            "decision": "REFUSED",
            "reason": "REFUSED_PROTECTED_STATE_CHANGE",
            "state_changes": state_changes,
        }

    return {
        "decision": "PASS",
        "reason": "STATE_GUARDS_UNCHANGED",
        "state_changes": state_changes,
    }


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

    changed_state_files: list[str] = []
    for status, path in entries:
        if status not in {"A", "M"}:
            return _refusal(anchor, candidate, "REFUSED_MATERIAL_DELTA", changed_paths)
        classification = _classify_path(path)
        if classification == "material":
            return _refusal(anchor, candidate, "REFUSED_MATERIAL_DELTA", changed_paths)
        if classification == "unknown":
            return _refusal(anchor, candidate, "REFUSED_UNKNOWN_PATH", changed_paths)
        if path in STATE_FILES:
            changed_state_files.append(path)

    state_result = validate_state_delta(repo, anchor, candidate, changed_state_files)
    if state_result["decision"] != "PASS":
        return _refusal(
            anchor,
            candidate,
            "REFUSED_PROTECTED_STATE_CHANGE",
            changed_paths,
            state_result["state_changes"],
        )

    return {
        "decision": "PASS",
        "reason": "NON_EXECUTABLE_DELTA_GUARDS_UNCHANGED",
        "anchor": anchor,
        "candidate": candidate,
        "changed_paths": sorted(changed_paths),
        "state_changes": state_result["state_changes"],
        "static_evidence": None,
    }


def build_evidence_record(
    repo: pathlib.Path,
    anchor: str,
    candidate: str,
    static_run_id: str,
    static_conclusion: str,
) -> dict[str, Any]:
    delta = classify_repository_delta(repo, anchor, candidate)
    protected_state = "REFUSED" if delta["reason"] == "REFUSED_PROTECTED_STATE_CHANGE" else "PASS"

    record: dict[str, Any] = {
        "schema_version": 1,
        "policy": POLICY_NAME,
        "decision": delta["decision"],
        "reason": delta["reason"],
        "anchor": anchor,
        "candidate": candidate,
        "changed_paths": delta["changed_paths"],
        "state_changes": delta["state_changes"],
        "protected_state": protected_state,
        "static_evidence": None,
    }

    if delta["decision"] != "PASS":
        return record

    if not static_run_id.strip() or static_conclusion != "PASS":
        record["decision"] = "REFUSED"
        record["reason"] = "REFUSED_STATIC_EVIDENCE_MISSING"
        return record

    record["reason"] = "NON_EXECUTABLE_DELTA_GUARDS_UNCHANGED_STATIC_PASS"
    record["static_evidence"] = {
        "run_id": static_run_id,
        "conclusion": "PASS",
    }
    return record


def _parser() -> EvidenceArgumentParser:
    parser = EvidenceArgumentParser(description="Classify F1.2c evidence inheritance")
    parser.add_argument("--anchor", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--static-run-id", required=True)
    parser.add_argument("--static-conclusion", required=True)
    parser.add_argument("--output", type=pathlib.Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
    except UsageError as exc:
        print(f"USAGE_ERROR: {exc}", file=sys.stderr)
        return 64

    try:
        record = build_evidence_record(
            pathlib.Path.cwd(),
            args.anchor,
            args.candidate,
            args.static_run_id,
            args.static_conclusion,
        )
        rendered = json.dumps(record, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            args.output.write_text(rendered, encoding="utf-8")
        sys.stdout.write(rendered)
        return 0 if record["decision"] == "PASS" else 2
    except (OSError, ValueError) as exc:
        print(f"EVIDENCE_CLASSIFIER_ERROR: {exc}", file=sys.stderr)
        return 64


if __name__ == "__main__":
    raise SystemExit(main())
