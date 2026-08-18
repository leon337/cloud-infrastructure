from __future__ import annotations

import pathlib
from typing import Any

from scripts.check_repository_secrets import content_findings, path_is_forbidden

from .errors import NotFoundError, RefusedError

MAX_READ_BYTES = 65_536
MAX_LIST_ENTRIES = 500
EXTRA_SENSITIVE_BASENAMES = frozenset(
    {"credentials.json", "credentials.yaml", "credentials.yml"}
)


def _workspace_root(workspace: pathlib.Path) -> pathlib.Path:
    if workspace.is_symlink():
        raise RefusedError("workspace_symlink_refused")
    if not workspace.exists():
        raise NotFoundError("workspace_not_found")
    if not workspace.is_dir():
        raise RefusedError("workspace_not_directory")
    return workspace.resolve(strict=True)


def resolve_confined(workspace: pathlib.Path, relative_path: str) -> pathlib.Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise RefusedError("invalid_relative_path")
    candidate = pathlib.Path(relative_path)
    if candidate.is_absolute():
        raise RefusedError("absolute_path_refused")
    if relative_path.startswith("~"):
        raise RefusedError("tilde_path_refused")
    if ".." in candidate.parts:
        raise RefusedError("path_escape_refused")

    workspace_real = _workspace_root(workspace)
    try:
        target = (workspace_real / candidate).resolve(strict=True)
    except (FileNotFoundError, NotADirectoryError):
        raise NotFoundError("path_not_found") from None

    if target != workspace_real and workspace_real not in target.parents:
        raise RefusedError("path_escape_refused")
    return target


def workspace_stat(workspace: pathlib.Path) -> dict[str, Any]:
    if workspace.is_symlink():
        return {"state": "INVALID", "reason": "workspace_symlink_refused"}
    if not workspace.exists():
        return {"state": "ABSENT"}
    if not workspace.is_dir():
        return {"state": "INVALID", "reason": "workspace_not_directory"}
    stat = workspace.stat()
    return {
        "state": "PRESENT",
        "mode": stat.st_mode & 0o777,
    }


def _relative_resolved(workspace: pathlib.Path, target: pathlib.Path) -> pathlib.PurePosixPath:
    workspace_real = _workspace_root(workspace)
    try:
        relative = target.relative_to(workspace_real)
    except ValueError:
        raise RefusedError("path_escape_refused") from None
    return pathlib.PurePosixPath(relative.as_posix())


def _sensitive_path(relative: pathlib.PurePosixPath) -> bool:
    if ".git" in relative.parts:
        return True
    if relative.name in EXTRA_SENSITIVE_BASENAMES:
        return True
    return path_is_forbidden(relative.as_posix())


def workspace_read(workspace: pathlib.Path, relative_path: str) -> dict[str, Any]:
    target = resolve_confined(workspace, relative_path)
    if not target.is_file():
        raise RefusedError("path_not_file")

    relative = _relative_resolved(workspace, target)
    if _sensitive_path(relative):
        raise RefusedError("sensitive_path_refused")

    with target.open("rb") as handle:
        data = handle.read(MAX_READ_BYTES + 1)
    if len(data) > MAX_READ_BYTES:
        raise RefusedError("file_too_large")

    if list(content_findings(data)):
        raise RefusedError("secret_like_content")

    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        raise RefusedError("binary_or_non_utf8") from None

    return {
        "path": relative.as_posix(),
        "size": len(data),
        "encoding": "utf-8",
        "content": content,
    }


def workspace_list(
    workspace: pathlib.Path,
    relative_path: str = ".",
) -> dict[str, Any]:
    target = resolve_confined(workspace, relative_path)
    if not target.is_dir():
        raise RefusedError("path_not_directory")

    entries = sorted(target.iterdir(), key=lambda item: item.name)
    if len(entries) > MAX_LIST_ENTRIES:
        raise RefusedError("list_entry_limit")

    rendered: list[dict[str, Any]] = []
    for entry in entries:
        if entry.is_symlink():
            item: dict[str, Any] = {"name": entry.name, "type": "symlink"}
        elif entry.is_dir():
            item = {"name": entry.name, "type": "directory"}
        elif entry.is_file():
            item = {"name": entry.name, "type": "file", "size": entry.stat().st_size}
        else:
            item = {"name": entry.name, "type": "other"}
        rendered.append(item)

    relative = _relative_resolved(workspace, target)
    return {"path": relative.as_posix() or ".", "entries": rendered}
