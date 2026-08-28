#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import importlib.util
import os
import pathlib
import shutil
import subprocess
import tempfile
from types import ModuleType
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "tests/fixtures/mcf_cloud_context_read/mcf_client.py"
ADAPTER_MODULE_PATH = ROOT / "control_plane/g2a/local_context_adapter.py"
ADAPTER_CLI_PATH = ROOT / "platform/control-bridge/mcf-cloud-context-read"
COPY_PATHS = (
    ".mcf/project-capsule.yaml",
    "context/mcf-cloud-context.yaml",
    "control_plane/__init__.py",
    "control_plane/g2a/__init__.py",
    "control_plane/g2a/local_context_adapter.py",
    "platform/control-bridge/mcf-cloud-context-read",
    "platform/control-bridge/mcf-cloud-context-read-config.yaml",
    "platform/manifests/g2a-smoke.yaml",
    "platform/schemas/mcf-cloud-context-read-config.schema.json",
    "platform/schemas/mcf-cloud-context-read-result.schema.json",
    "platform/schemas/mcf-cloud-context.schema.json",
    "platform/schemas/mcf-project-capsule.schema.json",
    "platform/schemas/project.schema.json",
    "scripts/yaml_strict.py",
    "state/control-bridge-g2a.yaml",
    "state/control-bridge-g2b.yaml",
)
MARKERS = (
    "MCF_CLOUD_CONTEXT_DISPOSABLE_LAYOUT_PASS",
    "MCF_CLOUD_CONTEXT_EXACT_REQUEST_PASS",
    "MCF_CLOUD_CONTEXT_RESULT_SCHEMA_PASS",
    "MCF_CLOUD_CONTEXT_STATUS_PASS",
    "MCF_CLOUD_CONTEXT_PROVENANCE_PASS",
    "MCF_CLOUD_CONTEXT_FRESHNESS_PASS",
    "MCF_CLOUD_CONTEXT_ADAPTER_NO_NETWORK_SURFACE_PASS",
    "MCF_CLOUD_CONTEXT_ADAPTER_NO_SUBPROCESS_SURFACE_PASS",
    "MCF_CLOUD_CONTEXT_ADAPTER_NO_SHELL_SURFACE_PASS",
    "MCF_CLOUD_CONTEXT_ADAPTER_NO_FILESYSTEM_WRITE_PASS",
    "MCF_CLOUD_CONTEXT_GIT_FINGERPRINT_PASS",
    "MCF_CLOUD_CONTEXT_FILESYSTEM_FINGERPRINT_PASS",
    "MCF_CLOUD_CONTEXT_CLEANUP_PASS",
)


def _load_client() -> ModuleType:
    spec = importlib.util.spec_from_file_location("mcf_cloud_context_client", CLIENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("MCF fixture client could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git_fingerprint() -> str:
    environment = dict(os.environ)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    commands = (
        ("git", "rev-parse", "HEAD"),
        (
            "git",
            "--no-optional-locks",
            "status",
            "--porcelain=v2",
            "--branch",
            "--untracked-files=all",
        ),
    )
    digest = hashlib.sha256()
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            check=False,
            timeout=20,
        )
        if completed.returncode != 0 or completed.stderr:
            raise RuntimeError("read-only Git fingerprint failed")
        digest.update(b"\x00".join(part.encode("utf-8") for part in command))
        digest.update(b"\x00")
        digest.update(completed.stdout)
    return digest.hexdigest()


def _filesystem_fingerprint(root: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        metadata = path.lstat()
        digest.update(relative)
        digest.update(f"\x00{metadata.st_mode:o}\x00".encode("ascii"))
        if path.is_symlink():
            digest.update(b"L\x00")
            digest.update(os.readlink(path).encode("utf-8"))
        elif path.is_file():
            digest.update(b"F\x00")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        elif path.is_dir():
            digest.update(b"D\x00")
        else:
            raise RuntimeError(f"unsupported fixture entry: {relative!r}")
    return digest.hexdigest()


def _copy_fixture(workspace_root: pathlib.Path) -> None:
    for relative in COPY_PATHS:
        source = ROOT / relative
        target = workspace_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _adapter_surface() -> dict[str, bool]:
    imported: set[str] = set()
    calls: set[str] = set()
    texts: list[str] = []
    for path in (ADAPTER_MODULE_PATH, ADAPTER_CLI_PATH):
        text = path.read_text(encoding="utf-8")
        texts.append(text)
        tree = ast.parse(text)
        imported.update(
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)
    joined = "\n".join(texts)
    return {
        "network": imported.isdisjoint({"socket", "urllib", "http", "requests"}),
        "subprocess": "subprocess" not in imported and calls.isdisjoint(
            {"Popen", "run", "call", "check_call", "check_output"}
        ),
        "shell": "shell=True" not in joined
        and "os.system(" not in joined
        and "popen(" not in joined.lower()
        and "ssh " not in joined
        and "curl " not in joined,
        "write": calls.isdisjoint(
            {
                "write_text",
                "write_bytes",
                "touch",
                "unlink",
                "remove",
                "rename",
                "mkdir",
                "rmdir",
                "chmod",
                "chown",
                "symlink_to",
            }
        )
        and "sys.addaudithook(_read_only_audit_hook)" in joined,
    }


def run_e2e() -> tuple[list[str], dict[str, Any]]:
    git_before = _git_fingerprint()
    temporary_root = pathlib.Path(tempfile.mkdtemp(prefix="mcf-cloud-context-e2e-"))
    workspace_root = temporary_root / "workspaces/leon337/g2a-smoke/dev"
    markers: list[str] = []
    result: dict[str, Any] | None = None
    try:
        workspace_root.mkdir(parents=True)
        _copy_fixture(workspace_root)
        if tuple(workspace_root.parts[-3:]) != ("leon337", "g2a-smoke", "dev"):
            raise RuntimeError("disposable layout mismatch")
        markers.append(MARKERS[0])

        filesystem_before = _filesystem_fingerprint(workspace_root)
        client = _load_client()
        if client.REQUEST_LINE != (
            '{"protocol":"MCF_CLOUD_CONTEXT_READ_V1",'
            '"request_id":"MCF-CLOUD-G2A-E2E-20260823",'
            '"project_id":"cloud-infrastructure",'
            '"operation":"context.get","arguments":{}}\n'
        ):
            raise RuntimeError("fixture client request differs from exact contract")
        if tuple(client.ADAPTER_COMMAND[1:]) != (
            "-I",
            "platform/control-bridge/mcf-cloud-context-read",
        ):
            raise RuntimeError("fixture client command differs from exact contract")
        markers.append(MARKERS[1])

        result = client.request_cloud_context(workspace_root)
        markers.extend(MARKERS[2:6])

        surface = _adapter_surface()
        if not all(surface.values()):
            raise RuntimeError(f"adapter surface is not read-only: {surface}")
        markers.extend(MARKERS[6:10])

        if _git_fingerprint() != git_before:
            raise RuntimeError("source Git fingerprint changed")
        markers.append(MARKERS[10])
        if _filesystem_fingerprint(workspace_root) != filesystem_before:
            raise RuntimeError("disposable filesystem fingerprint changed")
        markers.append(MARKERS[11])
    finally:
        shutil.rmtree(temporary_root)
    if temporary_root.exists():
        raise RuntimeError("disposable fixture cleanup failed")
    markers.append(MARKERS[12])
    if markers != list(MARKERS):
        raise RuntimeError("E2E marker sequence incomplete")
    if result is None:
        raise RuntimeError("E2E result missing")
    return markers, result


def main() -> int:
    markers, _ = run_e2e()
    for marker in markers:
        print(marker)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
