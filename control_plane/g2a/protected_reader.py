"""Descriptor-confined protected reader for the G2-A protected workspace slice.

This module implements only the read-only protected-reader core required by the
approved design (Task 1).  It opens the fixed protected workspace directory with
``O_RDONLY | O_DIRECTORY | O_NOFOLLOW``, validates the descriptor metadata, then
opens the single accepted pilot target relative to that directory descriptor
with ``O_RDONLY | O_NOFOLLOW``, reads bounded bytes, re-fstats the target
descriptor to reject metadata races, scans for secret-like content, decodes
UTF-8, and computes SHA-256 from the exact bytes read.

Dependency closure is strictly stdlib + ``g2a.protocol`` + ``g2a.errors`` +
``g2b.secret_policy``.  No imports from ``g2a.workspace``, Git modules, or
repository scripts.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import pathlib
import stat
from typing import Any

from .errors import G2AError, NotFoundError, RefusedError
from .protocol import (
    CoreExecution,
    ProjectKey,
    RESULT_PROTOCOL,
    parse_request,
)
from ..g2b.secret_policy import content_findings

# ---------------------------------------------------------------------------
# Fixed production constants
# ---------------------------------------------------------------------------

PROTECTED_PROJECT = ProjectKey("leon337", "g2a-smoke", "dev")
PROTECTED_ROOT = pathlib.Path("/var/lib/mcf-control-bridge/workspaces")
PROTECTED_PATH = "G2B-PILOT.txt"
MAX_READ_BYTES = 65_536
SAFE_FILE_MODES = frozenset({0o600, 0o640, 0o644})

_WORKSPACE_DIR_MODE = 0o700
_APPROVED_OPERATIONS = frozenset({"workspace.stat", "workspace.read"})


# ---------------------------------------------------------------------------
# Local result-formatting helpers (not imported from g2a.core)
# ---------------------------------------------------------------------------

def _now() -> str:
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _project_dict(key: ProjectKey) -> dict[str, str]:
    return {
        "tenant": key.tenant,
        "name": key.name,
        "environment": key.environment,
    }


def _safe_raw_project(value: Any) -> dict[str, str | None]:
    if not isinstance(value, dict):
        return {"tenant": None, "name": None, "environment": None}
    return {
        key: child if isinstance(child, str) else None
        for key, child in (
            ("tenant", value.get("tenant")),
            ("name", value.get("name")),
            ("environment", value.get("environment")),
        )
    }


def _safe_context(
    value: Any,
) -> tuple[str, dict[str, str | None], str | None]:
    if not isinstance(value, dict):
        return "UNKNOWN", _safe_raw_project(None), None
    request_id = value.get("request_id")
    operation = value.get("operation")
    return (
        request_id if isinstance(request_id, str) and request_id else "UNKNOWN",
        _safe_raw_project(value.get("project")),
        operation if isinstance(operation, str) else None,
    )


def _execution_result(
    *,
    request_id: str,
    project: dict[str, Any],
    operation: str | None,
    status: str,
    started_at: str,
    result: dict[str, Any],
    error: dict[str, str] | None,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": request_id,
        "project": project,
        "operation": operation,
        "status": status,
        "started_at": started_at,
        "finished_at": _now(),
        "result": result,
        "error": error,
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Descriptor-confined filesystem helpers
# ---------------------------------------------------------------------------

def _workspace_path(workspace_root: pathlib.Path) -> str:
    return str(
        pathlib.Path(workspace_root)
        / PROTECTED_PROJECT.tenant
        / PROTECTED_PROJECT.name
        / PROTECTED_PROJECT.environment
    )


def _metadata_tuple(st: os.stat_result) -> tuple[Any, ...]:
    """Identity/metadata comparison tuple from a stat result."""
    return (
        st.st_dev,
        st.st_ino,
        st.st_size,
        st.st_mode,
        st.st_uid,
        st.st_nlink,
        st.st_mtime_ns,
        st.st_ctime_ns,
    )


def _open_workspace_dir(workspace_root: pathlib.Path) -> int:
    """Traverse to the protected workspace using directory descriptors.

    Every fixed component is opened relative to the previous directory
    descriptor with O_DIRECTORY | O_NOFOLLOW so ancestor symlinks cannot
    redirect the protected path.
    """
    root = pathlib.Path(workspace_root)
    components = (
        *root.parts,
        PROTECTED_PROJECT.tenant,
        PROTECTED_PROJECT.name,
        PROTECTED_PROJECT.environment,
    )
    current_fd = -1
    try:
        if root.is_absolute():
            current_fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            components = components[1:]
        else:
            current_fd = os.open(".", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for component in components:
            try:
                next_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=current_fd,
                )
            except FileNotFoundError as exc:
                raise NotFoundError("path_not_found") from exc
            except OSError as exc:
                raise RefusedError("protected_workspace_unsafe") from exc
            os.close(current_fd)
            current_fd = next_fd

        workspace_fd = current_fd
        current_fd = -1
        return workspace_fd
    except FileNotFoundError as exc:
        raise NotFoundError("path_not_found") from exc
    except OSError as exc:
        raise RefusedError("protected_workspace_unsafe") from exc
    finally:
        if current_fd >= 0:
            os.close(current_fd)


def _validate_workspace_fd(fd: int) -> os.stat_result:
    """fstat the workspace descriptor and validate owner/mode/type.

    Caller is responsible for closing ``fd``.
    """
    st = os.fstat(fd)
    if not stat.S_ISDIR(st.st_mode):
        raise RefusedError("protected_workspace_unsafe")
    if st.st_uid != os.geteuid():
        raise RefusedError("protected_workspace_unsafe")
    if (st.st_mode & 0o7777) != _WORKSPACE_DIR_MODE:
        raise RefusedError("protected_workspace_unsafe")
    return st


def _validate_target_fd(st: os.stat_result) -> None:
    """Validate metadata obtained from the already-open target descriptor."""
    if not stat.S_ISREG(st.st_mode):
        raise RefusedError("protected_target_unsafe")
    if st.st_nlink != 1:
        raise RefusedError("protected_target_unsafe")
    if st.st_uid != os.geteuid():
        raise RefusedError("protected_target_unsafe")
    if (st.st_mode & 0o7777) not in SAFE_FILE_MODES:
        raise RefusedError("protected_target_unsafe")
    if st.st_size > MAX_READ_BYTES:
        raise RefusedError("file_too_large")


def _read_target(ws_fd: int) -> bytes:
    """Open, validate, and read the fixed pilot target safely until EOF."""
    target_fd = -1
    try:
        try:
            target_fd = os.open(
                PROTECTED_PATH,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=ws_fd,
            )
        except FileNotFoundError as exc:
            raise NotFoundError("path_not_found") from exc
        except OSError as exc:
            raise RefusedError("protected_target_unsafe") from exc

        initial_st = os.fstat(target_fd)
        _validate_target_fd(initial_st)

        chunks: list[bytes] = []
        total = 0
        while True:
            remaining = MAX_READ_BYTES + 1 - total
            chunk = os.read(target_fd, min(8192, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_READ_BYTES:
                raise RefusedError("file_too_large")

        post_st = os.fstat(target_fd)
        if _metadata_tuple(initial_st) != _metadata_tuple(post_st):
            raise RefusedError("protected_target_unsafe")

        data = b"".join(chunks)
        if len(data) != initial_st.st_size:
            raise RefusedError("protected_target_unsafe")
        return data
    finally:
        if target_fd >= 0:
            os.close(target_fd)

def _scan_and_decode(data: bytes) -> str:
    if list(content_findings(data)):
        raise RefusedError("secret_like_content")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RefusedError("binary_or_non_utf8") from exc


# ---------------------------------------------------------------------------
# Operation implementations
# ---------------------------------------------------------------------------

def _do_stat(workspace_root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute workspace.stat.  Returns (payload, evidence)."""
    ws_fd = -1
    try:
        try:
            ws_fd = _open_workspace_dir(workspace_root)
        except NotFoundError:
            payload: dict[str, Any] = {"state": "ABSENT"}
            return payload, {"workspace_state": "ABSENT"}
        st = _validate_workspace_fd(ws_fd)
        payload = {"state": "PRESENT", "mode": st.st_mode & 0o777}
        return payload, {"workspace_state": "PRESENT"}
    finally:
        if ws_fd >= 0:
            os.close(ws_fd)


def _do_read(workspace_root: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute workspace.read of the exact pilot.  Returns (payload, evidence)."""
    ws_fd = -1
    try:
        ws_fd = _open_workspace_dir(workspace_root)
        _validate_workspace_fd(ws_fd)

        data = _read_target(ws_fd)

        content = _scan_and_decode(data)
        digest = hashlib.sha256(data).hexdigest()

        payload: dict[str, Any] = {
            "path": PROTECTED_PATH,
            "size": len(data),
            "encoding": "utf-8",
            "content": content,
            "sha256": digest,
        }
        return payload, {"workspace_state": "PRESENT"}
    finally:
        if ws_fd >= 0:
            os.close(ws_fd)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def _execute_at_root(
    request_value: dict[str, Any],
    workspace_root: pathlib.Path,
) -> CoreExecution:
    started_at = _now()
    safe_request_id, safe_project, safe_operation = _safe_context(request_value)

    try:
        request = parse_request(request_value)
        safe_request_id = request.request_id
        safe_project = _project_dict(request.project)
        safe_operation = request.operation

        if request.project != PROTECTED_PROJECT:
            raise RefusedError("protected_project_refused")

        if request.operation not in _APPROVED_OPERATIONS:
            raise RefusedError("protected_operation_refused")

        if request.operation == "workspace.stat":
            if request.arguments:
                raise RefusedError("protected_operation_refused")
            payload, evidence = _do_stat(workspace_root)
        else:  # workspace.read
            if request.arguments != {"path": PROTECTED_PATH}:
                raise RefusedError("protected_path_refused")
            payload, evidence = _do_read(workspace_root)

        result = _execution_result(
            request_id=request.request_id,
            project=_project_dict(request.project),
            operation=request.operation,
            status="PASS",
            started_at=started_at,
            result=payload,
            error=None,
            evidence=evidence,
        )
        return CoreExecution(result=result, attachment=None)

    except G2AError as exc:
        return CoreExecution(
            result=_execution_result(
                request_id=safe_request_id,
                project=safe_project,
                operation=safe_operation,
                status=exc.status,
                started_at=started_at,
                result={},
                error={"code": exc.code},
                evidence={},
            )
        )
    except Exception:
        return CoreExecution(
            result=_execution_result(
                request_id=safe_request_id,
                project=safe_project,
                operation=safe_operation,
                status="FAILED",
                started_at=started_at,
                result={},
                error={"code": "internal_error"},
                evidence={},
            )
        )


def execute_protected(request_value: dict[str, Any]) -> CoreExecution:
    """Production entry point using the fixed protected root."""
    return _execute_at_root(request_value, PROTECTED_ROOT)
