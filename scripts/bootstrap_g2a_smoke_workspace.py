#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
from typing import Any, Callable

PROTOCOL = "MCF_G2A_SMOKE_BOOTSTRAP_V1"
PROJECT = {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"}
EXPECTED_FIELDS = frozenset({"protocol", "request_id", "project", "action"})
EXPECTED_PROJECT_FIELDS = frozenset(PROJECT)


class BootstrapError(RuntimeError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def validate_dispatch(value: dict[str, Any]) -> dict[str, Any]:
    if set(value) != EXPECTED_FIELDS:
        raise BootstrapError("unexpected_dispatch_field")
    if value.get("protocol") != PROTOCOL:
        raise BootstrapError("invalid_protocol")
    request_id = value.get("request_id")
    if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
        raise BootstrapError("invalid_request_id")
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != EXPECTED_PROJECT_FIELDS:
        raise BootstrapError("invalid_project")
    if project != PROJECT:
        raise BootstrapError("project_not_allowed")
    if value.get("action") != "create":
        raise BootstrapError("action_not_allowed")
    return value


def git(source: pathlib.Path, *args: str) -> str:
    env = os.environ.copy()
    env["GIT_OPTIONAL_LOCKS"] = "0"
    completed = subprocess.run(
        ["git", "-C", str(source), *args],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    if completed.returncode != 0:
        raise BootstrapError("git_check_failed")
    return completed.stdout.strip()


def default_boundary_probe() -> dict[str, bool]:
    sudo = subprocess.run(
        ["sudo", "-n", "true"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )
    groups = subprocess.run(
        ["id", "-nG"],
        check=False,
        capture_output=True,
        text=True,
        timeout=5,
    )
    if groups.returncode != 0:
        raise BootstrapError("identity_probe_failed")
    docker_group = "docker" in groups.stdout.split()
    docker_socket_access = os.access("/var/run/docker.sock", os.R_OK | os.W_OK)
    return {
        "sudo_nopasswd": sudo.returncode == 0,
        "docker_group": docker_group,
        "docker_socket_access": docker_socket_access,
    }


def file_evidence(path: pathlib.Path) -> dict[str, Any]:
    data = path.read_bytes()
    stat = path.stat()
    return {
        "path": path.name,
        "sha256": hashlib.sha256(data).hexdigest(),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def execute_bootstrap(
    dispatch: dict[str, Any],
    *,
    source_root: pathlib.Path,
    workspace_root: pathlib.Path,
    boundary_probe: Callable[[], dict[str, bool]] = default_boundary_probe,
) -> dict[str, Any]:
    request = validate_dispatch(dispatch)

    source = source_root.resolve(strict=True)
    if source_root.is_symlink() or not (source / ".git").exists():
        raise BootstrapError("invalid_source_checkout")

    if workspace_root.exists() and workspace_root.is_symlink():
        raise BootstrapError("workspace_root_symlink_refused")
    workspace_root.mkdir(parents=True, exist_ok=True)
    root = workspace_root.resolve(strict=True)

    target = root / PROJECT["tenant"] / PROJECT["name"] / PROJECT["environment"]
    if target.exists() or target.is_symlink():
        raise BootstrapError("workspace_already_exists")

    source_head = git(source, "rev-parse", "HEAD")
    created = False
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, symlinks=True)
        created = True

        target_real = target.resolve(strict=True)
        if target_real != target or root not in target_real.parents:
            raise BootstrapError("target_confinement_failed")

        copied_head = git(target, "rev-parse", "HEAD")
        if copied_head != source_head:
            raise BootstrapError("head_mismatch")
        dirty = bool(git(target, "status", "--porcelain=v1"))
        if dirty:
            raise BootstrapError("copied_workspace_dirty")

        readme = target / "README.md"
        if not readme.is_file():
            raise BootstrapError("fixture_file_missing")

        boundary = boundary_probe()
        if boundary.get("sudo_nopasswd"):
            raise BootstrapError("sudo_boundary_expanded")
        if boundary.get("docker_group") or boundary.get("docker_socket_access"):
            raise BootstrapError("docker_boundary_expanded")

        return {
            "protocol": PROTOCOL,
            "request_id": request["request_id"],
            "status": "PASS",
            "project": dict(PROJECT),
            "source_head": source_head,
            "workspace_head": copied_head,
            "git_dirty": False,
            "fixture": file_evidence(readme),
            "boundary": {
                "sudo_nopasswd": False,
                "docker_group": False,
                "docker_socket_access": False,
            },
        }
    except Exception:
        if created and target.exists():
            shutil.rmtree(target, ignore_errors=True)
        raise


def write_result(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatch-file", required=True, type=pathlib.Path)
    parser.add_argument("--source-root", required=True, type=pathlib.Path)
    parser.add_argument("--workspace-root", required=True, type=pathlib.Path)
    parser.add_argument("--result-file", required=True, type=pathlib.Path)
    args = parser.parse_args()

    try:
        dispatch = json.loads(args.dispatch_file.read_text(encoding="utf-8"))
        if not isinstance(dispatch, dict):
            raise BootstrapError("invalid_dispatch")
        result = execute_bootstrap(
            dispatch,
            source_root=args.source_root,
            workspace_root=args.workspace_root,
        )
        write_result(args.result_file, result)
        print("G2A_SMOKE_BOOTSTRAP=PASS")
        return 0
    except BootstrapError as exc:
        write_result(
            args.result_file,
            {
                "protocol": PROTOCOL,
                "status": "REFUSED",
                "error": exc.code,
            },
        )
        print(f"G2A_SMOKE_BOOTSTRAP=REFUSED code={exc.code}")
        return 2
    except Exception:
        write_result(
            args.result_file,
            {
                "protocol": PROTOCOL,
                "status": "FAILED",
                "error": "internal_error",
            },
        )
        print("G2A_SMOKE_BOOTSTRAP=FAILED code=internal_error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
