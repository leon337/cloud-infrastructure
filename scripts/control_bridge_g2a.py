#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import threading
import time
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_plane.g2a.core import execute
from control_plane.g2a.errors import RefusedError
from control_plane.g2a.protocol import (
    CoreExecution,
    CoreRequest,
    ProjectKey,
    RESULT_PROTOCOL,
    parse_request,
)
from control_plane.g2b.secret_policy import content_findings


_PROTECTED_EXECUTOR = "/usr/local/libexec/mcf-control-g2a-protected-read"
_PROTECTED_ARGV = ["sudo", "-n", "-u", "mcf-workspace", _PROTECTED_EXECUTOR]
_PROTECTED_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"}
_PROTECTED_PROJECT = ProjectKey("leon337", "g2a-smoke", "dev")
_MAX_PIPE_BYTES = 131_072
_MAX_REQUEST_BYTES = 131_072
_MAX_READ_BYTES = 65_536
_TERMINATE_GRACE_SECONDS = 0.25
_WAIT_SLICE_SECONDS = 0.02
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_RESULT_FIELDS = frozenset({
    "protocol", "request_id", "project", "operation", "status",
    "started_at", "finished_at", "result", "error", "evidence",
})


@dataclass(frozen=True)
class ProcessOutcome:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    error: str | None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _project_dict(project: ProjectKey) -> dict[str, str]:
    return {"tenant": project.tenant, "name": project.name, "environment": project.environment}


def _safe_context(value: Any) -> tuple[str, dict[str, str | None], str | None]:
    if not isinstance(value, dict):
        return "UNKNOWN", {"tenant": None, "name": None, "environment": None}, None
    raw_project = value.get("project")
    if not isinstance(raw_project, dict):
        raw_project = {}
    request_id = value.get("request_id")
    operation = value.get("operation")
    return (
        request_id if isinstance(request_id, str) and request_id else "UNKNOWN",
        {name: raw_project.get(name) if isinstance(raw_project.get(name), str) else None
         for name in ("tenant", "name", "environment")},
        operation if isinstance(operation, str) else None,
    )


def _synthetic_execution(
    request: CoreRequest | None,
    *,
    raw_request: Any = None,
    status: str,
    code: str,
) -> CoreExecution:
    if request is None:
        request_id, project, operation = _safe_context(raw_request)
    else:
        request_id = request.request_id
        project = _project_dict(request.project)
        operation = request.operation
    now = _now()
    return CoreExecution(result={
        "protocol": RESULT_PROTOCOL,
        "request_id": request_id,
        "project": project,
        "operation": operation,
        "status": status,
        "started_at": now,
        "finished_at": now,
        "result": {},
        "error": {"code": code},
        "evidence": {},
    })


def _drain_pipe(pipe: Any, destination: bytearray, overflow: threading.Event) -> None:
    try:
        while True:
            chunk = pipe.read(8192)
            if not chunk:
                return
            remaining = _MAX_PIPE_BYTES - len(destination)
            if remaining > 0:
                destination.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow.set()
    except (OSError, ValueError):
        overflow.set()


def _write_stdin(pipe: Any, payload: bytes, failed: threading.Event) -> None:
    try:
        pipe.write(payload)
        pipe.flush()
    except (BrokenPipeError, OSError, ValueError):
        failed.set()
    finally:
        try:
            pipe.close()
        except (OSError, ValueError):
            pass


def _signal_process_group(process: subprocess.Popen[bytes], signum: int) -> None:
    try:
        os.killpg(process.pid, signum)
    except (OSError, ProcessLookupError):
        try:
            if signum == signal.SIGTERM:
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
    argv: list[str], payload: bytes, *, timeout_seconds: float,
) -> ProcessOutcome:
    if (
        not isinstance(argv, list) or not argv
        or any(not isinstance(item, str) or not item for item in argv)
        or not isinstance(payload, bytes) or len(payload) > _MAX_REQUEST_BYTES
        or not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 15
    ):
        return ProcessOutcome(None, b"", b"", "invocation_failed")
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            env=_PROTECTED_ENV,
            start_new_session=True,
            close_fds=True,
        )
    except OSError:
        return ProcessOutcome(None, b"", b"", "spawn_failed")

    assert process.stdin is not None and process.stdout is not None and process.stderr is not None
    stdout = bytearray()
    stderr = bytearray()
    overflow = threading.Event()
    input_failed = threading.Event()
    threads = [
        threading.Thread(target=_drain_pipe, args=(process.stdout, stdout, overflow), daemon=True),
        threading.Thread(target=_drain_pipe, args=(process.stderr, stderr, overflow), daemon=True),
        threading.Thread(target=_write_stdin, args=(process.stdin, payload, input_failed), daemon=True),
    ]
    for thread in threads:
        thread.start()

    error: str | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        while process.poll() is None:
            if overflow.is_set():
                error = "output_too_large"
                break
            if input_failed.is_set():
                error = "input_failed"
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                error = "timeout"
                break
            overflow.wait(min(_WAIT_SLICE_SECONDS, remaining))
        if error is not None:
            _terminate_kill_reap(process)
        else:
            process.wait()
    except BaseException:
        _terminate_kill_reap(process)
        error = "invocation_failed"
    finally:
        join_deadline = time.monotonic() + _TERMINATE_GRACE_SECONDS
        if not _join_threads_until(threads, join_deadline):
            error = error or "timeout"
            if process.poll() is None:
                _terminate_kill_reap(process)
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except (OSError, ValueError):
                pass
        _join_threads_until(threads, time.monotonic() + _TERMINATE_GRACE_SECONDS)
        if process.poll() is None:
            _terminate_kill_reap(process)
    if overflow.is_set():
        error = "output_too_large"
    return ProcessOutcome(process.returncode, bytes(stdout), bytes(stderr), error)


def _is_protected_request(request: CoreRequest) -> bool:
    if request.project != _PROTECTED_PROJECT:
        return False
    if request.operation == "workspace.stat":
        return request.arguments == {}
    if request.operation == "workspace.read":
        return request.arguments == {"path": "G2B-PILOT.txt"}
    return False


def _valid_timestamp_pair(started: Any, finished: Any) -> bool:
    if not isinstance(started, str) or not isinstance(finished, str):
        return False
    if _TIMESTAMP.fullmatch(started) is None or _TIMESTAMP.fullmatch(finished) is None:
        return False
    try:
        start_time = dt.datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ")
        finish_time = dt.datetime.strptime(finished, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return False
    return finish_time >= start_time


def _validate_protected_result(value: Any, request: CoreRequest) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _RESULT_FIELDS:
        raise ValueError("invalid_protected_result")
    if value["protocol"] != RESULT_PROTOCOL:
        raise ValueError("invalid_protected_result")
    if value["request_id"] != request.request_id:
        raise ValueError("invalid_protected_result")
    if value["project"] != _project_dict(request.project) or value["operation"] != request.operation:
        raise ValueError("invalid_protected_result")
    if not _valid_timestamp_pair(value["started_at"], value["finished_at"]):
        raise ValueError("invalid_protected_result")
    status = value["status"]
    result = value["result"]
    error = value["error"]
    evidence = value["evidence"]
    if status == "NOT_FOUND":
        if (
            request.operation != "workspace.read"
            or result != {}
            or error != {"code": "path_not_found"}
            or evidence != {}
        ):
            raise ValueError("invalid_protected_result")
        return value
    if status != "PASS" or error is not None:
        raise ValueError("invalid_protected_result")
    if request.operation == "workspace.stat":
        if evidence == {"workspace_state": "ABSENT"}:
            if result != {"state": "ABSENT"}:
                raise ValueError("invalid_protected_result")
            return value
        if evidence != {"workspace_state": "PRESENT"} or result != {"state": "PRESENT", "mode": 0o700}:
            raise ValueError("invalid_protected_result")
        return value
    if evidence != {"workspace_state": "PRESENT"}:
        raise ValueError("invalid_protected_result")
    if not isinstance(result, dict) or set(result) != {"path", "encoding", "size", "sha256", "content"}:
        raise ValueError("invalid_protected_result")
    if result["path"] != "G2B-PILOT.txt" or result["encoding"] != "utf-8":
        raise ValueError("invalid_protected_result")
    content = result["content"]
    size = result["size"]
    digest = result["sha256"]
    if not isinstance(content, str) or not isinstance(size, int) or isinstance(size, bool):
        raise ValueError("invalid_protected_result")
    encoded = content.encode("utf-8")
    if size < 0 or size > _MAX_READ_BYTES or size != len(encoded):
        raise ValueError("invalid_protected_result")
    if not isinstance(digest, str) or _SHA256.fullmatch(digest) is None:
        raise ValueError("invalid_protected_result")
    if digest != hashlib.sha256(encoded).hexdigest() or next(content_findings(encoded), None) is not None:
        raise ValueError("invalid_protected_result")
    return value


def _decode_single_result(raw: bytes) -> Any:
    if not raw or len(raw) > _MAX_PIPE_BYTES or not raw.endswith(b"\n") or raw.count(b"\n") != 1:
        raise ValueError("invalid_protected_result")
    try:
        text = raw.decode("utf-8")
        return json.loads(text, parse_constant=lambda _value: (_ for _ in ()).throw(ValueError()))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError("invalid_protected_result") from None


def _execute_protected(request: dict[str, Any], parsed: CoreRequest | None = None) -> CoreExecution:
    parsed_request = parsed if parsed is not None else parse_request(request)
    try:
        payload = (json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    except (TypeError, ValueError):
        return _synthetic_execution(parsed_request, status="FAILED", code="protected_reader_failed")
    if len(payload) > _MAX_REQUEST_BYTES:
        return _synthetic_execution(parsed_request, status="FAILED", code="protected_reader_failed")
    outcome = run_bounded_process(_PROTECTED_ARGV, payload, timeout_seconds=15.0)
    if outcome.error == "timeout":
        return _synthetic_execution(parsed_request, status="TIMEOUT", code="operation_timeout")
    if outcome.error is not None or outcome.returncode != 0 or outcome.stderr:
        return _synthetic_execution(parsed_request, status="FAILED", code="protected_reader_failed")
    try:
        result = _validate_protected_result(_decode_single_result(outcome.stdout), parsed_request)
    except (TypeError, ValueError, UnicodeError):
        return _synthetic_execution(parsed_request, status="FAILED", code="protected_reader_failed")
    return CoreExecution(result=result)


def execute_selected(
    request_value: dict[str, Any],
    *,
    manifest_root: pathlib.Path,
    workspace_root: pathlib.Path,
) -> CoreExecution:
    try:
        parsed = parse_request(request_value)
    except RefusedError as exc:
        return _synthetic_execution(None, raw_request=request_value, status=exc.status, code=exc.code)
    if parsed.project == _PROTECTED_PROJECT and parsed.operation in {"workspace.stat", "workspace.read"}:
        if not _is_protected_request(parsed):
            code = "protected_operation_refused" if parsed.operation == "workspace.stat" else "protected_path_refused"
            return _synthetic_execution(parsed, status="REFUSED", code=code)
        return _execute_protected(request_value, parsed)
    return execute(request_value, manifest_root=manifest_root, workspace_root=workspace_root)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("json_must_be_object")
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
    issue = transport.get("issue_number")
    if issue is not None and (not isinstance(issue, int) or issue <= 0):
        raise ValueError("invalid_issue_number")
    if not isinstance(request, dict):
        raise ValueError("request_must_be_object")
    return dict(transport), dict(request)


def load_envelope(event_name: str, dispatch_file: pathlib.Path) -> dict[str, Any]:
    if event_name != "push":
        raise ValueError("unsupported_event")
    envelope = load_json(dispatch_file)
    validate_envelope(envelope)
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=pathlib.Path, required=True)
    parser.add_argument("--dispatch-file", type=pathlib.Path, required=True)
    parser.add_argument("--envelope-file", type=pathlib.Path, required=True)
    parser.add_argument("--result-file", type=pathlib.Path, required=True)
    parser.add_argument("--attachment-file", type=pathlib.Path, required=True)
    parser.add_argument("--manifest-root", type=pathlib.Path, default=ROOT / "platform" / "manifests")
    parser.add_argument("--workspace-root", type=pathlib.Path, default=pathlib.Path("/home/ubuntu/mcf-workspaces"))
    args = parser.parse_args()

    try:
        envelope = load_envelope(args.event_name, args.dispatch_file)
        transport, request = validate_envelope(envelope)
        execution = execute_selected(
            request,
            manifest_root=args.manifest_root,
            workspace_root=args.workspace_root,
        )
        normalized_envelope = {"transport": transport, "request": request}
        result = execution.result
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc)}, sort_keys=True))
        return 2

    args.envelope_file.parent.mkdir(parents=True, exist_ok=True)
    args.result_file.parent.mkdir(parents=True, exist_ok=True)
    args.envelope_file.write_text(
        json.dumps(normalized_envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.result_file.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if execution.attachment is not None:
        args.attachment_file.parent.mkdir(parents=True, exist_ok=True)
        args.attachment_file.write_bytes(execution.attachment.content)

    print(
        json.dumps(
            {
                "request_id": result.get("request_id", "UNKNOWN"),
                "operation": result.get("operation"),
                "status": result.get("status", "UNKNOWN"),
                "attachment": execution.attachment is not None,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
