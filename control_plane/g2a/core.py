from __future__ import annotations

import datetime as dt
import pathlib
from typing import Any

from .errors import G2AError, RefusedError
from .git_inspection import git_branch, git_diff, git_head, git_status
from .projects import ProjectResolver, project_public_view, workspace_path
from .protocol import CoreExecution, ProjectKey, RESULT_PROTOCOL, parse_request
from .workspace import workspace_list, workspace_read, workspace_stat


def _now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
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


def _safe_context(value: Any) -> tuple[str, dict[str, str | None], str | None]:
    if not isinstance(value, dict):
        return "UNKNOWN", _safe_raw_project(None), None
    request_id = value.get("request_id")
    operation = value.get("operation")
    return (
        request_id if isinstance(request_id, str) and request_id else "UNKNOWN",
        _safe_raw_project(value.get("project")),
        operation if isinstance(operation, str) else None,
    )


def _validate_arguments(operation: str, arguments: dict[str, Any]) -> None:
    no_arguments = {
        "project.list",
        "project.get",
        "workspace.stat",
        "git.status",
        "git.branch",
        "git.head",
        "git.diff",
    }
    if operation in no_arguments:
        if arguments:
            raise RefusedError("invalid_arguments")
        return
    if operation == "workspace.list":
        if set(arguments) - {"path"}:
            raise RefusedError("invalid_arguments")
        if "path" in arguments and not isinstance(arguments["path"], str):
            raise RefusedError("invalid_arguments")
        return
    if operation == "workspace.read":
        if set(arguments) != {"path"} or not isinstance(arguments["path"], str):
            raise RefusedError("invalid_arguments")
        return
    raise RefusedError("unknown_operation")


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


def execute(
    request_value: dict[str, Any],
    *,
    manifest_root: pathlib.Path,
    workspace_root: pathlib.Path,
) -> CoreExecution:
    started_at = _now()
    safe_request_id, safe_project, safe_operation = _safe_context(request_value)

    try:
        request = parse_request(request_value)
        _validate_arguments(request.operation, request.arguments)
        safe_request_id = request.request_id
        safe_project = _project_dict(request.project)
        safe_operation = request.operation
        resolver = ProjectResolver(manifest_root)
        attachment = None
        evidence: dict[str, Any] = {}

        if request.operation == "project.list":
            payload = {
                "projects": [project_public_view(record) for record in resolver.list()]
            }
        else:
            record = resolver.get(request.project)
            if request.operation == "project.get":
                payload = project_public_view(record)
            else:
                workspace = workspace_path(workspace_root, request.project)
                if request.operation == "workspace.stat":
                    payload = workspace_stat(workspace)
                    evidence["workspace_state"] = payload["state"]
                elif request.operation == "workspace.list":
                    payload = workspace_list(workspace, request.arguments.get("path", "."))
                    evidence["workspace_state"] = "PRESENT"
                elif request.operation == "workspace.read":
                    payload = workspace_read(workspace, request.arguments["path"])
                    evidence["workspace_state"] = "PRESENT"
                elif request.operation == "git.status":
                    payload = git_status(workspace)
                    evidence.update(
                        workspace_state="PRESENT",
                        dirty=payload["dirty"],
                    )
                elif request.operation == "git.branch":
                    payload = git_branch(workspace)
                    evidence["workspace_state"] = "PRESENT"
                elif request.operation == "git.head":
                    payload = git_head(workspace)
                    evidence.update(
                        workspace_state="PRESENT",
                        git_head=payload["head"],
                    )
                elif request.operation == "git.diff":
                    payload, attachment = git_diff(workspace)
                    evidence["workspace_state"] = "PRESENT"
                else:
                    raise RefusedError("unknown_operation")

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
        return CoreExecution(result=result, attachment=attachment)
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
