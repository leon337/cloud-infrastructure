#!/usr/bin/env python3
"""Normalize one fixed GitHub push and invoke the installed G2-B boundary."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_plane.g2b.errors import RefusedError
from control_plane.g2b.executor import (
    PUBLIC_RESULT_CONTRACT,
    PUBLIC_RESULT_ERROR_CODES,
    PUBLIC_RESULT_FIELDS,
    PUBLIC_RESULT_STATUSES,
)
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
_RESULT_FIELDS = PUBLIC_RESULT_FIELDS
_RESULT_PROTOCOL = "MCF_WORKSPACE_MUTATION_RESULT_V1"
_RESULT_STATUSES = PUBLIC_RESULT_STATUSES
_SUCCESS_STATUSES = frozenset({"PASS", "ROLLED_BACK", "REVOKED"})
_REQUEST_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,127}$")
_GRANT_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_RESULT_ERROR_CODES = PUBLIC_RESULT_ERROR_CODES
_TERMINATE_GRACE_SECONDS = 0.25
_WAIT_SLICE_SECONDS = 0.02


@dataclass(frozen=True)
class ProcessOutcome:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    error: str | None


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


def _canonical_request_digest(value: dict[str, Any]) -> str:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise ValueError("invalid_executor_result") from None
    return hashlib.sha256(encoded).hexdigest()


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


def _valid_public_state(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or set(value) != {"exists", "size", "mode", "sha256"}:
        return False
    exists = value.get("exists")
    if not isinstance(exists, bool):
        return False
    if not exists:
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


def _matches_contract_rule(value: dict[str, Any], rule: Any) -> bool:
    has_grant = value.get("authority") is not None and value.get("grant_id") is not None
    if has_grant is not (rule.grant_context == "present"):
        return False
    if value.get("replayed") is True and rule.replayable is not True:
        return False
    started = _utc_timestamp(value.get("started_at"))
    finished = _utc_timestamp(value.get("finished_at"))
    if rule.timestamp_shape == "instant" and started != finished:
        return False
    if rule.timestamp_shape == "ordered" and (
        started is None or finished is None or finished < started
    ):
        return False
    before, after = value.get("before"), value.get("after")
    if rule.result_shape == "stateless":
        state_matches = before is None and after is None
    elif rule.result_shape == "same_state":
        state_matches = before is not None and after == before
    elif rule.result_shape == "write_mutation":
        if before is None:
            return False
        if value.get("error") == "final_target_indeterminate":
            state_matches = after is None
        else:
            state_matches = value.get("error") != "final_target_mismatch" or after is not None
    elif rule.result_shape == "rollback_mutation":
        if before is None or before.get("exists") is not True:
            return False
        if value.get("error") == "final_target_indeterminate":
            state_matches = after is None
        else:
            state_matches = value.get("error") != "final_target_mismatch" or after is not None
    elif rule.result_shape == "reconciled_reverted":
        state_matches = before is not None and after == before
    elif rule.result_shape == "reconciled_indeterminate":
        state_matches = before is not None
    elif rule.result_shape == "write_success":
        state_matches = before is not None and after is not None
    elif rule.result_shape == "rollback_success":
        state_matches = before is not None and before.get("exists") is True and after is not None
    else:
        return False
    if not state_matches:
        return False

    operation = value.get("operation")
    rollback_link = value.get("rollback_request_id")
    revocation_link = value.get("revocation_request_id")
    if operation == "workspace.write":
        return value.get("path") == "G2B-PILOT.txt" and rollback_link is None and revocation_link is None
    if operation == "rollback":
        expected_path = (
            "G2B-PILOT.txt"
            if rule.result_shape in {"rollback_mutation", "rollback_success"}
            else None
        )
        return value.get("path") == expected_path and rollback_link is not None and revocation_link is None
    if operation == "status":
        return value.get("path") is None and rollback_link is None and revocation_link is None
    if operation == "revoke":
        expected_revocation = value.get("request_id") if value.get("status") == "REVOKED" else None
        return value.get("path") is None and rollback_link is None and revocation_link == expected_revocation
    return False


def _valid_contract_semantics(value: dict[str, Any], operation: str, status: str, error: Any) -> bool:
    return any(
        _matches_contract_rule(value, rule)
        for rule in PUBLIC_RESULT_CONTRACT
        if operation in rule.operations and status == rule.status and error in rule.errors
    )


def validate_executor_result(
    value: dict[str, Any],
    request_value: dict[str, Any],
    parsed: MutationRequest,
    actor_login: str,
    actor_id: int,
) -> None:
    invalid = ValueError("invalid_executor_result")
    if not isinstance(value, dict) or set(value) != _RESULT_FIELDS:
        raise invalid
    expected_project = {
        "tenant": parsed.project.tenant,
        "name": parsed.project.name,
        "environment": parsed.project.environment,
    }
    if (
        value.get("protocol") != _RESULT_PROTOCOL
        or value.get("request_id") != parsed.request_id
        or value.get("request_digest") != _canonical_request_digest(request_value)
        or value.get("mission_id") != parsed.mission_id
        or value.get("declared_actor") != parsed.declared_actor
        or value.get("transport_principal") != {"login": actor_login, "actor_id": actor_id}
        or value.get("project") != expected_project
        or value.get("operation") != parsed.operation
    ):
        raise invalid

    authority = value.get("authority")
    grant_id = value.get("grant_id")
    if authority is None or grant_id is None:
        if authority is not None or grant_id is not None:
            raise invalid
    elif (
        authority != "LEANDRO"
        or not isinstance(grant_id, str)
        or _GRANT_ID.fullmatch(grant_id) is None
    ):
        raise invalid

    started_at = _utc_timestamp(value.get("started_at"))
    finished_at = _utc_timestamp(value.get("finished_at"))
    if started_at is None or finished_at is None or finished_at < started_at:
        raise invalid
    if not _valid_public_state(value.get("before")) or not _valid_public_state(value.get("after")):
        raise invalid
    if not isinstance(value.get("replayed"), bool):
        raise invalid

    status = value.get("status")
    error = value.get("error")
    if status not in _RESULT_STATUSES:
        raise invalid
    if status in _SUCCESS_STATUSES:
        if error is not None or authority != "LEANDRO":
            raise invalid
    elif (
        not isinstance(error, str)
        or error not in _RESULT_ERROR_CODES
    ):
        raise invalid
    if not _valid_contract_semantics(value, parsed.operation, status, error):
        raise invalid

    expected_precondition: dict[str, str] | None
    if parsed.precondition is None:
        expected_precondition = None
    elif parsed.precondition.state is not None:
        expected_precondition = {"state": parsed.precondition.state}
    else:
        expected_precondition = {"sha256": parsed.precondition.sha256}
    if value.get("precondition") != expected_precondition:
        raise invalid

    rollback_link = value.get("rollback_request_id")
    revocation_link = value.get("revocation_request_id")
    if parsed.operation == "workspace.write":
        if value.get("path") != parsed.path or rollback_link is not None or revocation_link is not None:
            raise invalid
        if status == "PASS":
            before = value.get("before")
            after = value.get("after")
            if not isinstance(before, dict) or not isinstance(after, dict) or parsed.content is None:
                raise invalid
            if parsed.precondition is None:
                raise invalid
            if parsed.precondition.state == "ABSENT":
                if before != {"exists": False, "size": None, "mode": None, "sha256": None}:
                    raise invalid
                expected_mode = 0o644
            else:
                if not before["exists"] or before["sha256"] != parsed.precondition.sha256:
                    raise invalid
                expected_mode = before["mode"]
            if after != {
                "exists": True,
                "size": len(parsed.content),
                "mode": expected_mode,
                "sha256": hashlib.sha256(parsed.content).hexdigest(),
            }:
                raise invalid
        elif status == "TIMEOUT":
            if value.get("before") is not None or value.get("after") is not None:
                raise invalid
        elif status in {"REFUSED", "CONFLICT"}:
            before, after = value.get("before"), value.get("after")
            if (before is None) != (after is None) or (before is not None and before != after):
                raise invalid
        elif error == "internal_error":
            if value.get("before") is not None or value.get("after") is not None:
                raise invalid
        else:
            before, after = value.get("before"), value.get("after")
            if before is None:
                raise invalid
            if error == "mutation_reconciled_reverted" and after != before:
                raise invalid
            if error == "final_target_indeterminate" and after is not None:
                raise invalid
            if error == "final_target_mismatch" and after is None:
                raise invalid
    elif parsed.operation == "rollback":
        if rollback_link != parsed.original_request_id or revocation_link is not None:
            raise invalid
        if status == "ROLLED_BACK":
            if (
                value.get("path") != "G2B-PILOT.txt"
                or value.get("before") is None
                or value["before"]["exists"] is not True
                or value.get("after") is None
            ):
                raise invalid
        elif status in {"REFUSED", "CONFLICT", "TIMEOUT"}:
            if (
                value.get("path") is not None
                or value.get("before") is not None
                or value.get("after") is not None
            ):
                raise invalid
        elif error == "internal_error":
            if (
                value.get("path") is not None
                or value.get("before") is not None
                or value.get("after") is not None
            ):
                raise invalid
        elif not (
            value.get("path") == "G2B-PILOT.txt"
            and value.get("before") is not None
            and value["before"]["exists"] is True
        ):
            raise invalid
        elif error == "final_target_indeterminate" and value.get("after") is not None:
            raise invalid
        elif error == "final_target_mismatch" and value.get("after") is None:
            raise invalid
    elif parsed.operation == "status":
        if (
            value.get("path") is not None
            or value.get("before") is not None
            or value.get("after") is not None
            or rollback_link is not None
            or revocation_link is not None
        ):
            raise invalid
    else:
        if (
            value.get("path") is not None
            or value.get("before") is not None
            or value.get("after") is not None
            or rollback_link is not None
            or (status == "REVOKED" and revocation_link != parsed.request_id)
            or (status != "REVOKED" and revocation_link is not None)
        ):
            raise invalid


def _drain_pipe(
    stream: Any,
    output: bytearray,
    overflow: threading.Event,
) -> None:
    try:
        descriptor = stream.fileno()
        while True:
            chunk = os.read(descriptor, 4096)
            if not chunk:
                return
            remaining = _MAX_RESULT_BYTES - len(output)
            if remaining > 0:
                output.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow.set()
                return
    except (OSError, ValueError):
        return


def _write_stdin(stream: Any, payload: bytes) -> None:
    try:
        descriptor = stream.fileno()
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                return
            remaining = remaining[written:]
    except (BrokenPipeError, OSError, ValueError):
        pass
    finally:
        try:
            stream.close()
        except OSError:
            pass


def _signal_process_group(process: subprocess.Popen[bytes], selected_signal: int) -> None:
    try:
        os.killpg(process.pid, selected_signal)
    except (OSError, ProcessLookupError):
        try:
            if selected_signal == signal.SIGTERM:
                process.terminate()
            else:
                process.kill()
        except OSError:
            pass


def _process_group_exists(process: subprocess.Popen[bytes]) -> bool:
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def _terminate_kill_reap(process: subprocess.Popen[bytes]) -> None:
    _signal_process_group(process, signal.SIGTERM)
    deadline = time.monotonic() + _TERMINATE_GRACE_SECONDS
    while _process_group_exists(process) and time.monotonic() < deadline:
        process.poll()
        time.sleep(_WAIT_SLICE_SECONDS)
    if _process_group_exists(process):
        _signal_process_group(process, signal.SIGKILL)
    process.wait()


def _join_threads_until(threads: list[threading.Thread], deadline: float) -> bool:
    for thread in threads:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        thread.join(remaining)
    return all(not thread.is_alive() for thread in threads)


def run_bounded_process(
    argv: list[str],
    payload: bytes,
    *,
    timeout_seconds: float,
) -> ProcessOutcome:
    if (
        not isinstance(argv, list)
        or not argv
        or any(not isinstance(item, str) or not item for item in argv)
        or not isinstance(payload, bytes)
        or not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
        or not 0 < timeout_seconds <= 60
    ):
        return ProcessOutcome(None, b"", b"", "executor_invocation_failed")
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=_EXECUTOR_ENV,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        return ProcessOutcome(None, b"", b"", "executor_invocation_failed")

    assert process.stdin is not None
    assert process.stdout is not None
    assert process.stderr is not None
    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()
    readers = [
        threading.Thread(target=_drain_pipe, args=(process.stdout, stdout, overflow), daemon=True),
        threading.Thread(target=_drain_pipe, args=(process.stderr, stderr, overflow), daemon=True),
    ]
    writer = threading.Thread(target=_write_stdin, args=(process.stdin, payload), daemon=True)
    threads = [*readers, writer]
    for thread in threads:
        thread.start()

    error: str | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        while process.poll() is None:
            if overflow.is_set():
                error = "executor_output_too_large"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                error = "executor_timeout"
                break
            overflow.wait(min(_WAIT_SLICE_SECONDS, remaining))
        if error is not None:
            _terminate_kill_reap(process)
        else:
            process.wait()
    except BaseException:
        _terminate_kill_reap(process)
        error = "executor_invocation_failed"
    finally:
        join_deadline = deadline if error is None else time.monotonic() + _TERMINATE_GRACE_SECONDS
        if not _join_threads_until(threads, join_deadline):
            if error is None:
                error = "executor_timeout"
            _terminate_kill_reap(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
        _join_threads_until(threads, time.monotonic() + _TERMINATE_GRACE_SECONDS)
        if process.poll() is None:
            _terminate_kill_reap(process)

    if overflow.is_set():
        error = "executor_output_too_large"
    return ProcessOutcome(process.returncode, bytes(stdout), bytes(stderr), error)


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

    outcome = run_bounded_process(
        ["sudo", "-n", "-u", "mcf-workspace", _EXECUTOR, command],
        payload,
        timeout_seconds=60,
    )
    if outcome.error is not None:
        status = "TIMEOUT" if outcome.error == "executor_timeout" else "FAILED"
        result = _safe_result(parsed, status=status, error=outcome.error)
        exit_code = 2
    elif outcome.returncode != 0:
        result = _safe_result(parsed, status="FAILED", error="executor_boundary_failed")
        exit_code = 2
    else:
        if outcome.stderr:
            result = _safe_result(parsed, status="FAILED", error="invalid_executor_result")
            exit_code = 2
        else:
            try:
                result = _decode_executor_result(outcome.stdout)
                validate_executor_result(result, request, parsed, actor_login, actor_id)
            except ValueError:
                result = _safe_result(parsed, status="FAILED", error="invalid_executor_result")
                exit_code = 2
            else:
                exit_code = 0

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
