#!/usr/bin/env python3
"""Normalize one fixed GitHub push and invoke the installed G2-B boundary."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_plane.g2b.errors import RefusedError
from control_plane.g2b.protocol import MutationRequest, parse_request


ACTOR_LOGIN = "leon337"
ACTOR_ID = 25_374_535
BRANCH_REF = "refs/heads/codex/control-bridge-g2b"
DORMANT_REQUEST_ID = "G2B-DORMANT-REPLACE-BEFORE-LIVE"

_MAX_INPUT_BYTES = 131_072
_MAX_RESULT_BYTES = 8192
_MAX_EVENT_BYTES = 2 * 1024 * 1024
_COMMAND_BY_OPERATION = {
    "workspace.write": "execute",
    "rollback": "rollback",
    "status": "status",
    "revoke": "revoke",
}
_EXECUTOR = "/usr/local/libexec/mcf-control-g2b"
_EXECUTOR_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"}


def _load_json_object(path: Path, *, maximum_bytes: int, error: str) -> dict[str, Any]:
    try:
        metadata = os.stat(path, follow_symlinks=False)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise ValueError(error)
        if metadata.st_size > maximum_bytes:
            raise ValueError(error)
        raw = path.read_bytes()
        if len(raw) > maximum_bytes:
            raise ValueError(error)
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError(error)),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(error) from None
    if not isinstance(value, dict):
        raise ValueError(error)
    return value


def validate_envelope(value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError("envelope_must_be_object")
    if set(value) - {"transport", "request"}:
        raise ValueError("unexpected_envelope_field")
    if set(value) != {"transport", "request"}:
        raise ValueError("invalid_envelope")

    transport = value.get("transport")
    request = value.get("request")
    if not isinstance(transport, dict):
        raise ValueError("transport_must_be_object")
    if set(transport) - {"issue_number"}:
        raise ValueError("unexpected_transport_field")
    if set(transport) != {"issue_number"}:
        raise ValueError("invalid_transport")
    issue = transport.get("issue_number")
    if issue is not None and (
        not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0
    ):
        raise ValueError("invalid_issue_number")
    if not isinstance(request, dict):
        raise ValueError("request_must_be_object")
    try:
        parse_request(request)
    except RefusedError as exc:
        raise ValueError(exc.code) from None
    return dict(transport), dict(request)


def validate_push_event(
    event_name: str,
    event_path: Path,
    actor_login: str,
    actor_id: int,
) -> None:
    if event_name != "push":
        raise ValueError("unsupported_event")
    if actor_login != ACTOR_LOGIN or actor_id != ACTOR_ID or isinstance(actor_id, bool):
        raise ValueError("invalid_transport_principal")
    event = _load_json_object(
        event_path,
        maximum_bytes=_MAX_EVENT_BYTES,
        error="invalid_event",
    )
    if event.get("ref") != BRANCH_REF:
        raise ValueError("unexpected_ref")
    sender = event.get("sender")
    if (
        not isinstance(sender, dict)
        or sender.get("login") != actor_login
        or sender.get("id") != actor_id
        or isinstance(sender.get("id"), bool)
    ):
        raise ValueError("event_principal_mismatch")


def _validated_output_path(path: Path) -> tuple[Path, Path]:
    if not path.name or path.name in {".", ".."}:
        raise ValueError("unsafe_output_path")
    parent = path.parent
    try:
        absolute_parent = Path(os.path.abspath(parent))
        resolved_parent = parent.resolve(strict=True)
        parent_metadata = os.stat(parent, follow_symlinks=False)
    except OSError:
        raise ValueError("unsafe_output_path") from None
    if absolute_parent != resolved_parent:
        raise ValueError("unsafe_output_path")
    if (
        not stat.S_ISDIR(parent_metadata.st_mode)
        or parent_metadata.st_uid != os.geteuid()
        or stat.S_IMODE(parent_metadata.st_mode) & 0o022
    ):
        raise ValueError("unsafe_output_path")
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        pass
    except OSError:
        raise ValueError("unsafe_output_path") from None
    else:
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ValueError("unsafe_output_path")
    return resolved_parent, resolved_parent / path.name


def atomic_write_private(path: Path, content: bytes) -> None:
    if not isinstance(content, bytes):
        raise ValueError("invalid_output")
    parent, target = _validated_output_path(path)
    descriptor = -1
    temporary: str | None = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _validated_output_path(path)
        os.replace(temporary, target)
        temporary = None
        directory_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        metadata = os.stat(target, follow_symlinks=False)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_uid != os.geteuid()
            or stat.S_IMODE(metadata.st_mode) != 0o600
        ):
            raise ValueError("unsafe_output_path")
    except OSError:
        raise ValueError("output_write_failed") from None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def _encode_json(value: dict[str, Any], *, maximum_bytes: int, error: str) -> bytes:
    try:
        encoded = (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise ValueError(error) from None
    if len(encoded) > maximum_bytes:
        raise ValueError(error)
    return encoded


def _safe_result(
    parsed: MutationRequest,
    *,
    status: str,
    error: str,
) -> dict[str, Any]:
    return {
        "request_id": parsed.request_id,
        "operation": parsed.operation,
        "project": {
            "tenant": parsed.project.tenant,
            "name": parsed.project.name,
            "environment": parsed.project.environment,
        },
        "path": parsed.path,
        "status": status,
        "error": error,
        "grant_id": None,
        "started_at": None,
        "finished_at": None,
        "before": None,
        "after": None,
        "replayed": False,
        "receipt_id": None,
    }


def _decode_executor_result(raw: bytes) -> dict[str, Any]:
    if len(raw) > _MAX_RESULT_BYTES:
        raise ValueError("executor_output_too_large")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda _value: (_ for _ in ()).throw(
                ValueError("invalid_executor_result")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("invalid_executor_result") from None
    if not isinstance(value, dict):
        raise ValueError("invalid_executor_result")
    return value


def execute_dispatch(
    *,
    event_name: str,
    event_path: Path,
    dispatch_file: Path,
    request_output: Path,
    result_output: Path,
    actor_login: str,
    actor_id: int,
) -> int:
    validate_push_event(event_name, event_path, actor_login, actor_id)
    if request_output == result_output:
        raise ValueError("unsafe_output_path")
    _validated_output_path(request_output)
    _validated_output_path(result_output)

    envelope = _load_json_object(
        dispatch_file,
        maximum_bytes=_MAX_INPUT_BYTES,
        error="invalid_dispatch",
    )
    _transport, request = validate_envelope(envelope)
    try:
        parsed = parse_request(request)
    except RefusedError as exc:
        raise ValueError(exc.code) from None
    command = _COMMAND_BY_OPERATION[parsed.operation]
    normalized = {
        "transport_principal": {"login": actor_login, "actor_id": actor_id},
        "request": request,
    }
    payload = _encode_json(normalized, maximum_bytes=_MAX_INPUT_BYTES, error="executor_input_too_large")
    atomic_write_private(request_output, payload)

    if parsed.request_id == DORMANT_REQUEST_ID:
        result = _safe_result(parsed, status="REFUSED", error="dormant_request_id")
        atomic_write_private(
            result_output,
            _encode_json(result, maximum_bytes=_MAX_RESULT_BYTES, error="invalid_result"),
        )
        return 0

    try:
        completed = subprocess.run(
            ["sudo", "-n", "-u", "mcf-workspace", _EXECUTOR, command],
            input=payload,
            capture_output=True,
            check=False,
            timeout=60,
            shell=False,
            env=_EXECUTOR_ENV,
        )
    except subprocess.TimeoutExpired:
        result = _safe_result(parsed, status="TIMEOUT", error="executor_timeout")
        exit_code = 2
    except OSError:
        result = _safe_result(parsed, status="FAILED", error="executor_invocation_failed")
        exit_code = 2
    else:
        if len(completed.stdout) > _MAX_RESULT_BYTES or len(completed.stderr) > _MAX_RESULT_BYTES:
            result = _safe_result(parsed, status="FAILED", error="executor_output_too_large")
            exit_code = 2
        else:
            try:
                result = _decode_executor_result(completed.stdout)
            except ValueError as exc:
                result = _safe_result(parsed, status="FAILED", error=str(exc))
                exit_code = 2
            else:
                exit_code = 0 if completed.returncode == 0 else 2

    atomic_write_private(
        result_output,
        _encode_json(result, maximum_bytes=_MAX_RESULT_BYTES, error="invalid_result"),
    )
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--dispatch-file", type=Path, required=True)
    parser.add_argument("--request-output", type=Path, required=True)
    parser.add_argument("--result-output", type=Path, required=True)
    parser.add_argument("--actor-login", required=True)
    parser.add_argument("--actor-id", type=int, required=True)
    args = parser.parse_args()

    try:
        return execute_dispatch(
            event_name=args.event_name,
            event_path=args.event_path,
            dispatch_file=args.dispatch_file,
            request_output=args.request_output,
            result_output=args.result_output,
            actor_login=args.actor_login,
            actor_id=args.actor_id,
        )
    except ValueError:
        print("CONTROL_BRIDGE_G2B_ADAPTER_FAIL", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
