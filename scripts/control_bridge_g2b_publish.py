#!/usr/bin/env python3
"""Publish only allowlisted, compact G2-B receipt metadata."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_plane.g2b.executor import (
    PUBLIC_RESULT_CONTRACT,
    PUBLIC_RESULT_ERROR_CODES,
    PUBLIC_RESULT_FIELDS,
    PUBLIC_RESULT_STATUSES,
)


_MAX_RESULT_BYTES = 8192
_MAX_DISPATCH_BYTES = 131_072
_MAX_MARKDOWN_CHARACTERS = 59_999
_REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]()#+.!|>\-])")
_REQUEST_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,127}$")
_GRANT_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_OPERATIONS = frozenset({"workspace.write", "rollback", "status", "revoke"})
_STATUSES = PUBLIC_RESULT_STATUSES
_SUCCESS_STATUSES = frozenset({"PASS", "ROLLED_BACK", "REVOKED"})
_RESULT_FIELDS = PUBLIC_RESULT_FIELDS
_LOCAL_RESULT_FIELDS = frozenset(
    {
        "request_id", "operation", "project", "path", "status", "error", "grant_id",
        "started_at", "finished_at", "before", "after", "replayed", "receipt_id",
    }
)
_CORE_ERROR_CODES = PUBLIC_RESULT_ERROR_CODES
_LOCAL_ERRORS = frozenset(
    {
        "dormant_request_id", "executor_timeout", "executor_output_too_large",
        "executor_invocation_failed", "executor_boundary_failed", "invalid_executor_result",
    }
)


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


def _utc_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not 1 <= len(value) <= 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _valid_state(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or set(value) != {"exists", "size", "mode", "sha256"}:
        return False
    if not isinstance(value.get("exists"), bool):
        return False
    if value["exists"] is False:
        return all(value.get(field) is None for field in ("size", "mode", "sha256"))
    size = value.get("size")
    return (
        isinstance(size, int)
        and not isinstance(size, bool)
        and 0 <= size <= 65_536
        and value.get("mode") in {384, 416, 420}
        and isinstance(value.get("sha256"), str)
        and _SHA256.fullmatch(value["sha256"]) is not None
    )


def _matches_contract_rule(result: dict[str, Any], rule: Any) -> bool:
    has_grant = result.get("authority") is not None and result.get("grant_id") is not None
    if has_grant is not (rule.grant_context == "present"):
        return False
    before, after = result.get("before"), result.get("after")
    if rule.result_shape == "stateless":
        return before is None and after is None
    if rule.result_shape == "same_state":
        return before is not None and after == before
    if rule.result_shape == "write_mutation":
        if before is None:
            return False
        if result.get("error") == "final_target_indeterminate":
            return after is None
        return result.get("error") != "final_target_mismatch" or after is not None
    if rule.result_shape == "rollback_mutation":
        if before is None or before.get("exists") is not True:
            return False
        if result.get("error") == "final_target_indeterminate":
            return after is None
        return result.get("error") != "final_target_mismatch" or after is not None
    if rule.result_shape == "reconciled_reverted":
        return before is not None and after == before
    if rule.result_shape == "reconciled_indeterminate":
        return before is not None
    return rule.result_shape in {"write_success", "rollback_success"}


def _valid_contract_semantics(
    result: dict[str, Any], operation: str, status: str, error: Any
) -> bool:
    return any(
        _matches_contract_rule(result, rule)
        for rule in PUBLIC_RESULT_CONTRACT
        if operation in rule.operations and status == rule.status and error in rule.errors
    )


def _expected_request(envelope: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(envelope, dict) or set(envelope) != {"transport", "request"}:
        return None
    transport = envelope.get("transport")
    request = envelope.get("request")
    if not isinstance(transport, dict) or set(transport) != {"issue_number"}:
        return None
    issue = transport.get("issue_number")
    if issue is not None and (
        not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0
    ):
        return None
    fields = {
        "protocol", "request_id", "mission_id", "declared_actor", "project",
        "operation", "arguments",
    }
    if not isinstance(request, dict) or set(request) != fields:
        return None
    request_id = request.get("request_id")
    project = request.get("project")
    operation = request.get("operation")
    arguments = request.get("arguments")
    if (
        request.get("protocol") != "MCF_WORKSPACE_MUTATION_V1"
        or not isinstance(request_id, str)
        or _REQUEST_ID.fullmatch(request_id) is None
        or request.get("mission_id") != "CONTROL-BRIDGE-G2B-PILOT"
        or request.get("declared_actor") != "MESTRE_MCF"
        or project != {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"}
        or operation not in _OPERATIONS
        or not isinstance(arguments, dict)
    ):
        return None
    path: str | None = None
    precondition: dict[str, Any] | None = None
    rollback_request_id: str | None = None
    content_size: int | None = None
    content_sha256: str | None = None
    if operation == "workspace.write":
        if set(arguments) != {"path", "content", "precondition"}:
            return None
        path = arguments.get("path")
        content = arguments.get("content")
        precondition = arguments.get("precondition")
        try:
            content_bytes = content.encode("utf-8") if isinstance(content, str) else b""
            content_size = len(content_bytes) if isinstance(content, str) else -1
        except UnicodeEncodeError:
            return None
        if (
            path != "G2B-PILOT.txt"
            or not isinstance(content, str)
            or content_size > 65_536
            or not isinstance(precondition, dict)
        ):
            return None
        if not (
            precondition == {"state": "ABSENT"}
            or (
                set(precondition) == {"sha256"}
                and isinstance(precondition.get("sha256"), str)
                and _SHA256.fullmatch(precondition["sha256"]) is not None
            )
        ):
            return None
        content_sha256 = hashlib.sha256(content_bytes).hexdigest()
    elif operation == "rollback":
        rollback_request_id = arguments.get("original_request_id")
        if (
            set(arguments) != {"original_request_id"}
            or not isinstance(rollback_request_id, str)
            or _REQUEST_ID.fullmatch(rollback_request_id) is None
        ):
            return None
    elif arguments:
        return None
    try:
        encoded = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        return None
    return {
        "request_id": request_id,
        "request_digest": hashlib.sha256(encoded).hexdigest(),
        "project": project,
        "operation": operation,
        "path": path,
        "precondition": precondition,
        "rollback_request_id": rollback_request_id,
        "content_size": content_size,
        "content_sha256": content_sha256,
    }


def _valid_full_result(result: dict[str, Any], expected: dict[str, Any]) -> bool:
    if set(result) != _RESULT_FIELDS:
        return False
    if (
        result.get("protocol") != "MCF_WORKSPACE_MUTATION_RESULT_V1"
        or result.get("request_id") != expected["request_id"]
        or result.get("request_digest") != expected["request_digest"]
        or result.get("mission_id") != "CONTROL-BRIDGE-G2B-PILOT"
        or result.get("declared_actor") != "MESTRE_MCF"
        or result.get("transport_principal") != {"login": "leon337", "actor_id": 25_374_535}
        or result.get("project") != expected["project"]
        or result.get("operation") != expected["operation"]
        or result.get("precondition") != expected["precondition"]
        or not isinstance(result.get("replayed"), bool)
        or not _valid_state(result.get("before"))
        or not _valid_state(result.get("after"))
    ):
        return False
    authority, grant_id = result.get("authority"), result.get("grant_id")
    if (authority is None) != (grant_id is None):
        return False
    if authority is not None and (
        authority != "LEANDRO"
        or not isinstance(grant_id, str)
        or _GRANT_ID.fullmatch(grant_id) is None
    ):
        return False
    started = _utc_timestamp(result.get("started_at"))
    finished = _utc_timestamp(result.get("finished_at"))
    if started is None or finished is None or finished < started:
        return False
    status, error = result.get("status"), result.get("error")
    if status not in _STATUSES:
        return False
    if status in _SUCCESS_STATUSES:
        if error is not None or authority != "LEANDRO":
            return False
    elif (
        not isinstance(error, str)
        or error not in _CORE_ERROR_CODES
    ):
        return False
    if not _valid_contract_semantics(result, expected["operation"], status, error):
        return False

    operation = expected["operation"]
    rollback_link = result.get("rollback_request_id")
    revocation_link = result.get("revocation_request_id")
    if operation == "workspace.write":
        if result.get("path") != expected["path"] or rollback_link is not None or revocation_link is not None:
            return False
        if status == "PASS":
            before, after = result.get("before"), result.get("after")
            if not isinstance(before, dict) or not isinstance(after, dict):
                return False
            if expected["precondition"] == {"state": "ABSENT"}:
                if before != {"exists": False, "size": None, "mode": None, "sha256": None}:
                    return False
                expected_mode = 0o644
            else:
                if not before["exists"] or before["sha256"] != expected["precondition"]["sha256"]:
                    return False
                expected_mode = before["mode"]
            return after == {
                "exists": True,
                "size": expected["content_size"],
                "mode": expected_mode,
                "sha256": expected["content_sha256"],
            }
        if status == "TIMEOUT":
            return result.get("before") is None and result.get("after") is None
        if status in {"REFUSED", "CONFLICT"}:
            before, after = result.get("before"), result.get("after")
            return (before is None) == (after is None) and (before is None or before == after)
        if error == "internal_error":
            return result.get("before") is None and result.get("after") is None
        before, after = result.get("before"), result.get("after")
        if before is None:
            return False
        if error == "mutation_reconciled_reverted" and after != before:
            return False
        if error == "final_target_indeterminate" and after is not None:
            return False
        return error != "final_target_mismatch" or after is not None
    if operation == "rollback":
        if rollback_link != expected["rollback_request_id"] or revocation_link is not None:
            return False
        if status == "ROLLED_BACK":
            return (
                result.get("path") == "G2B-PILOT.txt"
                and result.get("before") is not None
                and result["before"]["exists"] is True
                and result.get("after") is not None
            )
        if status in {"REFUSED", "CONFLICT", "TIMEOUT"}:
            return (
                result.get("path") is None
                and result.get("before") is None
                and result.get("after") is None
            )
        if error == "internal_error":
            return (
                result.get("path") is None
                and result.get("before") is None
                and result.get("after") is None
            )
        valid_mutation_state = (
            result.get("path") == "G2B-PILOT.txt"
            and result.get("before") is not None
            and result["before"]["exists"] is True
        )
        if not valid_mutation_state:
            return False
        if error == "final_target_indeterminate":
            return result.get("after") is None
        return error != "final_target_mismatch" or result.get("after") is not None
    if operation == "status":
        return (
            result.get("path") is None
            and result.get("before") is None
            and result.get("after") is None
            and rollback_link is None
            and revocation_link is None
        )
    return (
        result.get("path") is None
        and result.get("before") is None
        and result.get("after") is None
        and rollback_link is None
        and (revocation_link == expected["request_id"] if status == "REVOKED" else revocation_link is None)
    )


def _valid_local_result(result: dict[str, Any], expected: dict[str, Any]) -> bool:
    if set(result) != _LOCAL_RESULT_FIELDS:
        return False
    error = result.get("error")
    expected_status = {
        "dormant_request_id": "REFUSED",
        "executor_timeout": "TIMEOUT",
        "executor_output_too_large": "FAILED",
        "executor_invocation_failed": "FAILED",
        "executor_boundary_failed": "FAILED",
        "invalid_executor_result": "FAILED",
    }
    return (
        error in _LOCAL_ERRORS
        and result.get("status") == expected_status[error]
        and result.get("request_id") == expected["request_id"]
        and result.get("operation") == expected["operation"]
        and result.get("project") == expected["project"]
        and result.get("path") == expected["path"]
        and result.get("grant_id") is None
        and result.get("started_at") is None
        and result.get("finished_at") is None
        and result.get("before") is None
        and result.get("after") is None
        and result.get("replayed") is False
        and result.get("receipt_id") is None
    )


def _projection(envelope: dict[str, Any], result: dict[str, Any]) -> dict[str, Any] | None:
    expected = _expected_request(envelope)
    if expected is None:
        return None
    if _valid_full_result(result, expected):
        return {
            "request_id": result["request_id"],
            "operation": result["operation"],
            "project": result["project"],
            "path": result["path"],
            "status": result["status"],
            "error": result["error"],
            "grant_id": result["grant_id"],
            "started_at": result["started_at"],
            "finished_at": result["finished_at"],
            "before_hash": _nested_scalar(result["before"], "sha256"),
            "after_hash": _nested_scalar(result["after"], "sha256"),
            "replayed": result["replayed"],
            "receipt_id": None,
        }
    if _valid_local_result(result, expected):
        return {
            "request_id": result["request_id"], "operation": result["operation"],
            "project": result["project"], "path": result["path"],
            "status": result["status"], "error": result["error"],
            "grant_id": None, "started_at": None, "finished_at": None,
            "before_hash": None, "after_hash": None, "replayed": False,
            "receipt_id": None,
        }
    return None


def markdown(envelope: dict[str, Any], result: dict[str, Any]) -> str:
    projection = _projection(envelope, result)
    if projection is None:
        return (
            "## MCF VPS Control Bridge — G2-B Result\n\n"
            "- status: FAILED\n"
            "- error code: invalid_publication_result\n\n"
            "> Result metadata failed strict publication validation; no result values were rendered."
        )
    project = projection["project"]
    project_value = "/".join(
        _safe_scalar(_nested_scalar(project, field))
        for field in ("tenant", "name", "environment")
    )
    lines = [
        "## MCF VPS Control Bridge — G2-B Result",
        "",
        f"- request ID: {_safe_scalar(projection.get('request_id'))}",
        f"- operation: {_safe_scalar(projection.get('operation'))}",
        f"- project: {project_value}",
        f"- relative path: {_safe_scalar(projection.get('path'))}",
        f"- status: {_safe_scalar(projection.get('status'))}",
        f"- error code: {_safe_scalar(projection.get('error'))}",
        f"- grant ID: {_safe_scalar(projection.get('grant_id'))}",
        f"- started: {_safe_scalar(projection.get('started_at'))}",
        f"- finished: {_safe_scalar(projection.get('finished_at'))}",
        f"- before SHA-256: {_safe_scalar(projection.get('before_hash'))}",
        f"- after SHA-256: {_safe_scalar(projection.get('after_hash'))}",
        f"- replayed: {_safe_scalar(projection.get('replayed'))}",
        f"- receipt ID: {_safe_scalar(projection.get('receipt_id'))}",
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
    body = markdown(envelope, result)

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
