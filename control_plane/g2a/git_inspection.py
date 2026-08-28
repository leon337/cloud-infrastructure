from __future__ import annotations

import os
import pathlib
import subprocess
from typing import Any

from scripts.check_repository_secrets import content_findings

from .errors import NotFoundError, OperationTimeout, RefusedError
from .protocol import Attachment
from .workspace import _sensitive_path, _workspace_root

GIT_TIMEOUT_SECONDS = 15
MAX_STATUS_BYTES = 262_144
MAX_DIFF_INLINE_BYTES = 131_072
MAX_DIFF_BYTES = 1_048_576
MAX_NAME_LIST_BYTES = 262_144
GIT_PREFIX = ["git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null"]


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["HOME"] = "/nonexistent"
    env["XDG_CONFIG_HOME"] = "/nonexistent"
    return env


def _run_git_raw(
    workspace: pathlib.Path,
    args: list[str],
    *,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[bytes]:
    root = _workspace_root(workspace)
    try:
        return subprocess.run(
            [*GIT_PREFIX, *args],
            cwd=root,
            env=_git_env(),
            check=False,
            capture_output=True,
            shell=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise OperationTimeout("git_timeout") from None
    except OSError:
        raise NotFoundError("git_unavailable") from None


def _decode(data: bytes, code: str) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise RefusedError(code) from None


def validate_git_repository(
    workspace: pathlib.Path,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> pathlib.Path:
    root = _workspace_root(workspace)
    completed = _run_git_raw(root, ["rev-parse", "--absolute-git-dir"], timeout=timeout)
    if completed.returncode != 0:
        raise NotFoundError("git_repository_not_found")
    rendered = _decode(completed.stdout.strip(), "git_path_non_utf8")
    if not rendered:
        raise NotFoundError("git_repository_not_found")
    git_dir = pathlib.Path(rendered).resolve(strict=False)
    if git_dir != root and root not in git_dir.parents:
        raise RefusedError("external_git_dir")
    return git_dir


def git_status(
    workspace: pathlib.Path,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = _workspace_root(workspace)
    validate_git_repository(root, timeout=timeout)
    completed = _run_git_raw(
        root,
        ["status", "--porcelain=v1", "--branch", "--untracked-files=normal"],
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise NotFoundError("git_status_failed")
    if len(completed.stdout) > MAX_STATUS_BYTES:
        raise RefusedError("git_status_too_large")
    text = _decode(completed.stdout, "git_status_non_utf8")
    lines = text.splitlines()
    dirty = any(line and not line.startswith("##") for line in lines)
    return {"porcelain": text, "dirty": dirty}


def git_branch(
    workspace: pathlib.Path,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = _workspace_root(workspace)
    validate_git_repository(root, timeout=timeout)
    completed = _run_git_raw(
        root,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        timeout=timeout,
    )
    if completed.returncode == 0:
        branch = _decode(completed.stdout.strip(), "git_branch_non_utf8")
        return {"branch": branch, "detached": False}
    if completed.returncode == 1:
        return {"branch": None, "detached": True}
    raise NotFoundError("git_branch_failed")


def git_head(
    workspace: pathlib.Path,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    root = _workspace_root(workspace)
    validate_git_repository(root, timeout=timeout)
    completed = _run_git_raw(root, ["rev-parse", "--verify", "HEAD"], timeout=timeout)
    if completed.returncode != 0:
        raise NotFoundError("git_head_not_found")
    head = _decode(completed.stdout.strip(), "git_head_non_utf8")
    return {"head": head}


def _has_secret_like_diff(data: bytes) -> bool:
    if list(content_findings(data)):
        return True
    for line in data.splitlines():
        if line.startswith((b"+++", b"---")):
            continue
        if line.startswith((b"+", b"-")) and list(content_findings(line[1:] + b"\n")):
            return True
    return False


def _bounded_diff(data: bytes) -> tuple[dict[str, Any], Attachment | None]:
    if len(data) > MAX_DIFF_BYTES:
        raise RefusedError("diff_too_large")
    if _has_secret_like_diff(data):
        raise RefusedError("secret_like_content")
    if len(data) <= MAX_DIFF_INLINE_BYTES:
        return {
            "content": _decode(data, "git_diff_non_utf8"),
            "size": len(data),
            "delivery": "inline",
        }, None
    attachment = Attachment(
        name="g2a-git-diff.patch",
        media_type="text/x-diff",
        content=data,
    )
    return {"content": None, "size": len(data), "delivery": "attachment"}, attachment


def git_diff(
    workspace: pathlib.Path,
    timeout: int = GIT_TIMEOUT_SECONDS,
) -> tuple[dict[str, Any], Attachment | None]:
    root = _workspace_root(workspace)
    validate_git_repository(root, timeout=timeout)

    names = _run_git_raw(root, ["diff", "--name-only", "-z", "HEAD", "--"], timeout=timeout)
    if names.returncode != 0:
        raise NotFoundError("git_diff_failed")
    if len(names.stdout) > MAX_NAME_LIST_BYTES:
        raise RefusedError("git_diff_names_too_large")
    for raw_name in filter(None, names.stdout.split(b"\0")):
        relative_text = _decode(raw_name, "git_path_non_utf8")
        relative = pathlib.PurePosixPath(relative_text)
        if relative.is_absolute() or ".." in relative.parts or _sensitive_path(relative):
            raise RefusedError("sensitive_path_in_diff")

    completed = _run_git_raw(
        root,
        ["diff", "--no-ext-diff", "--no-textconv", "--no-color", "HEAD", "--"],
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise NotFoundError("git_diff_failed")
    return _bounded_diff(completed.stdout)
