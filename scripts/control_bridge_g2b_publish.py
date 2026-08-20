#!/usr/bin/env python3
"""Publish only allowlisted, compact G2-B receipt metadata."""
from __future__ import annotations

import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any


_MAX_RESULT_BYTES = 8192
_MAX_DISPATCH_BYTES = 131_072
_MAX_MARKDOWN_CHARACTERS = 59_999
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+.!|>\-])")


def _load_json_object(path: Path, *, maximum_bytes: int) -> dict[str, Any]:
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum_bytes:
            raise ValueError("invalid_json_file")
        raw = path.read_bytes()
        if len(raw) > maximum_bytes:
            raise ValueError("invalid_json_file")
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError("invalid_json_file")),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("invalid_json_file") from None
    if not isinstance(value, dict):
        raise ValueError("invalid_json_file")
    return value


def issue_number(envelope: dict[str, Any]) -> int | None:
    transport = envelope.get("transport")
    if not isinstance(transport, dict) or set(transport) != {"issue_number"}:
        return None
    value = transport.get("issue_number")
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return None
    return value


def _safe_scalar(value: Any) -> str:
    if value is None:
        raw = "none"
    elif isinstance(value, bool):
        raw = "true" if value else "false"
    elif isinstance(value, (str, int)) and not isinstance(value, bool):
        raw = str(value)
    else:
        raw = "UNKNOWN"
    raw = raw.replace("\r", "\\r").replace("\n", "\\n")
    return _MARKDOWN_SPECIAL.sub(r"\\\1", html.escape(raw, quote=True))


def _nested_scalar(value: Any, field: str) -> Any:
    return value.get(field) if isinstance(value, dict) else None


def markdown(result: dict[str, Any]) -> str:
    project = result.get("project")
    project_value = "/".join(
        _safe_scalar(_nested_scalar(project, field))
        for field in ("tenant", "name", "environment")
    )
    lines = [
        "## MCF VPS Control Bridge — G2-B Result",
        "",
        f"- request ID: {_safe_scalar(result.get('request_id'))}",
        f"- operation: {_safe_scalar(result.get('operation'))}",
        f"- project: {project_value}",
        f"- relative path: {_safe_scalar(result.get('path'))}",
        f"- status: {_safe_scalar(result.get('status'))}",
        f"- error code: {_safe_scalar(result.get('error'))}",
        f"- grant ID: {_safe_scalar(result.get('grant_id'))}",
        f"- started: {_safe_scalar(result.get('started_at'))}",
        f"- finished: {_safe_scalar(result.get('finished_at'))}",
        f"- before SHA-256: {_safe_scalar(_nested_scalar(result.get('before'), 'sha256'))}",
        f"- after SHA-256: {_safe_scalar(_nested_scalar(result.get('after'), 'sha256'))}",
        f"- replayed: {_safe_scalar(result.get('replayed'))}",
        f"- receipt ID: {_safe_scalar(result.get('receipt_id'))}",
        "",
        "> Compact allowlisted receipt metadata only; content and snapshot bytes are never published.",
    ]
    rendered = "\n".join(lines)[:_MAX_MARKDOWN_CHARACTERS]
    encoded = rendered.encode("utf-8")
    if len(encoded) > _MAX_MARKDOWN_CHARACTERS:
        rendered = encoded[:_MAX_MARKDOWN_CHARACTERS].decode("utf-8", errors="ignore")
    return rendered


def _append_summary(path: Path, body: str) -> None:
    try:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(body + "\n")
    except OSError:
        raise SystemExit("summary_write_failed") from None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatch-file", type=Path, required=True)
    parser.add_argument("--result-file", type=Path, required=True)
    parser.add_argument("--summary-file", type=Path)
    args = parser.parse_args()

    try:
        envelope = _load_json_object(args.dispatch_file, maximum_bytes=_MAX_DISPATCH_BYTES)
        result = _load_json_object(args.result_file, maximum_bytes=_MAX_RESULT_BYTES)
    except ValueError:
        raise SystemExit("invalid_publication_input") from None
    body = markdown(result)

    if args.summary_file is not None:
        _append_summary(args.summary_file, body)

    number = issue_number(envelope)
    if number is None:
        print("CONTROL_BRIDGE_G2B_PUBLISH_SKIP reason=no_issue_number")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository or _REPOSITORY.fullmatch(repository) is None:
        raise SystemExit("missing_or_invalid_github_publication_context")

    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/issues/{number}/comments",
        data=json.dumps({"body": body}, separators=(",", ":")).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "mcf-vps-control-bridge-g2b",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"CONTROL_BRIDGE_G2B_PUBLISH_PASS status={response.status}")
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"publish_failed_http_{exc.code}") from None
    except urllib.error.URLError:
        raise SystemExit("publish_failed_network") from None
    return 0


if __name__ == "__main__":
    sys.exit(main())
