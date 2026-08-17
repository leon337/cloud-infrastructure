#!/usr/bin/python3
"""Guard and remove only the proven-empty Docker runtime trees for SLICE-002B.

The CLI deliberately accepts an action, never a caller-provided path.  Tests may
exercise the pure helpers with temporary roots, while the operational entrypoint
is locked to the two reviewed runtime roots and state files below.
"""

from __future__ import annotations

import json
import os
import pathlib
import stat
import subprocess
import sys
from collections.abc import Iterable, Sequence
from typing import Any


RUNTIME_ROOTS = (
    pathlib.Path("/var/lib/docker"),
    pathlib.Path("/var/lib/containerd"),
)
STATE_ROOT = pathlib.Path("/var/lib/cloud-platform/runtime-boundaries/docker")
BASELINE_PATH = STATE_ROOT / "runtime-tree-baseline.json"
REMOVAL_PATH = STATE_ROOT / "runtime-tree-removal.json"
FIND = "/usr/bin/find"
FINDMNT = "/usr/bin/findmnt"
SCHEMA = 1
ALLOWED_ACTIONS = {"snapshot", "verify", "prepare-removal", "remove"}


class GuardError(RuntimeError):
    """A fail-closed runtime-tree invariant was not met."""


def _kind(mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "file"
    raise GuardError("runtime tree contains a non-regular entry")


def _is_within(path: pathlib.Path, root: pathlib.Path) -> bool:
    return path == root or root in path.parents


def _require_safe_name(path: pathlib.Path) -> None:
    raw = os.fspath(path)
    if any(ord(character) < 32 or ord(character) == 127 for character in raw):
        raise GuardError("runtime path contains a control character")


def _require_not_mountpoint(path: pathlib.Path, findmnt: str | None) -> None:
    if findmnt is None:
        return
    result = subprocess.run(
        [findmnt, "--noheadings", "--mountpoint", os.fspath(path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode == 0:
        raise GuardError(f"runtime path is a mountpoint: {path}")
    if result.returncode != 1:
        raise GuardError(f"findmnt failed for runtime path: {path}")


def _find_paths(root: pathlib.Path, find_binary: str) -> list[pathlib.Path]:
    result = subprocess.run(
        [find_binary, os.fspath(root), "-xdev", "-print0"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise GuardError(
            f"find -xdev failed for literal runtime root {root}: "
            f"exit={result.returncode}"
        )
    raw_paths = [item for item in result.stdout.split(b"\0") if item]
    paths = [pathlib.Path(os.fsdecode(item)) for item in raw_paths]
    if not paths or paths[0] != root or len(paths) != len(set(paths)):
        raise GuardError(f"find returned an invalid path set for {root}")
    return paths


def scan_runtime_trees(
    roots: Sequence[pathlib.Path],
    *,
    expected_uid: int,
    expected_gid: int,
    find_binary: str = FIND,
    findmnt_binary: str | None = FINDMNT,
) -> list[dict[str, Any]]:
    """Return a stable metadata manifest after rejecting unsafe entries."""
    entries: list[dict[str, Any]] = []
    for root in roots:
        if not root.is_absolute():
            raise GuardError("runtime root is not absolute")
        root_stat = root.lstat()
        if not stat.S_ISDIR(root_stat.st_mode):
            raise GuardError(f"runtime root is not a directory: {root}")
        root_device = root_stat.st_dev
        for path in _find_paths(root, find_binary):
            if not _is_within(path, root):
                raise GuardError(f"find escaped literal runtime root: {path}")
            _require_safe_name(path)
            item_stat = path.lstat()
            item_kind = _kind(item_stat.st_mode)
            if item_stat.st_dev != root_device:
                raise GuardError(f"runtime entry crossed a device boundary: {path}")
            if item_stat.st_uid != expected_uid or item_stat.st_gid != expected_gid:
                raise GuardError(f"runtime entry is not owned by the expected identity: {path}")
            if item_stat.st_mode & 0o022:
                raise GuardError(f"runtime entry is group/other writable: {path}")
            if item_kind == "file" and item_stat.st_nlink != 1:
                raise GuardError(f"runtime file has multiple hardlinks: {path}")
            _require_not_mountpoint(path, findmnt_binary)
            entries.append(
                {
                    "path": os.fspath(path),
                    "root": os.fspath(root),
                    "kind": item_kind,
                    "uid": item_stat.st_uid,
                    "gid": item_stat.st_gid,
                    "mode": stat.S_IMODE(item_stat.st_mode),
                    "device": item_stat.st_dev,
                    "inode": item_stat.st_ino,
                }
            )
    return sorted(entries, key=lambda item: item["path"])


def _stable_entries(entries: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    stable_keys = ("path", "root", "kind", "uid", "gid", "mode")
    return [
        {key: entry[key] for key in stable_keys}
        for entry in sorted(entries, key=lambda item: item["path"])
    ]


def _manifest(roots: Sequence[pathlib.Path], entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "roots": [os.fspath(root) for root in roots],
        "entries": entries,
    }


def require_no_open_runtime_path(
    roots: Sequence[pathlib.Path],
    *,
    proc_root: pathlib.Path = pathlib.Path("/proc"),
    strict_permissions: bool,
) -> None:
    """Refuse a process cwd/root/executable/fd that resolves inside a root."""
    for process in proc_root.iterdir():
        if not process.name.isdigit():
            continue
        links = [process / "cwd", process / "root", process / "exe"]
        try:
            links.extend((process / "fd").iterdir())
        except FileNotFoundError:
            continue
        except PermissionError as error:
            if strict_permissions:
                raise GuardError(f"cannot inspect process descriptors: {process.name}") from error
            continue
        for link in links:
            try:
                raw_target = os.readlink(link)
            except FileNotFoundError:
                continue
            except PermissionError as error:
                if strict_permissions:
                    raise GuardError(
                        f"cannot inspect process path: {process.name}/{link.name}"
                    ) from error
                continue
            if raw_target.endswith(" (deleted)"):
                raw_target = raw_target[: -len(" (deleted)")]
            target = pathlib.Path(raw_target)
            if target.is_absolute() and any(
                _is_within(target, root) for root in roots
            ):
                raise GuardError(
                    f"process {process.name} has an open runtime path: {target}"
                )


def _secure_load(
    path: pathlib.Path, *, expected_uid: int, expected_gid: int
) -> dict[str, Any]:
    item_stat = path.lstat()
    if not stat.S_ISREG(item_stat.st_mode) or item_stat.st_nlink != 1:
        raise GuardError(f"manifest is not a single-link regular file: {path}")
    if item_stat.st_uid != expected_uid or item_stat.st_gid != expected_gid:
        raise GuardError(f"manifest ownership differs from the contract: {path}")
    if stat.S_IMODE(item_stat.st_mode) != 0o600:
        raise GuardError(f"manifest mode differs from 0600: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened_stat = os.fstat(descriptor)
        if (
            opened_stat.st_dev != item_stat.st_dev
            or opened_stat.st_ino != item_stat.st_ino
            or opened_stat.st_mode != item_stat.st_mode
            or opened_stat.st_uid != item_stat.st_uid
            or opened_stat.st_gid != item_stat.st_gid
        ):
            raise GuardError(f"manifest changed while opening: {path}")
        chunks: list[bytes] = []
        remaining = 16 * 1024 * 1024 + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(descriptor)
    if len(raw) > 16 * 1024 * 1024:
        raise GuardError("manifest exceeds the reviewed size limit")
    try:
        loaded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise GuardError(f"manifest is not valid UTF-8 JSON: {path}") from error
    if not isinstance(loaded, dict):
        raise GuardError("manifest root must be an object")
    return loaded


def _validate_manifest_shape(
    manifest: dict[str, Any], roots: Sequence[pathlib.Path], *, removal: bool
) -> None:
    expected_keys = {"schema", "roots", "entries"}
    if set(manifest) != expected_keys or manifest.get("schema") != SCHEMA:
        raise GuardError("manifest schema or top-level keys differ from the contract")
    if manifest.get("roots") != [os.fspath(root) for root in roots]:
        raise GuardError("manifest roots differ from the two literal runtime roots")
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise GuardError("manifest entries must be a non-empty list")
    expected_entry_keys = {
        "path",
        "root",
        "kind",
        "uid",
        "gid",
        "mode",
    }
    if removal:
        expected_entry_keys.update({"device", "inode"})
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != expected_entry_keys:
            raise GuardError("manifest entry keys differ from the contract")
        if entry["kind"] not in {"directory", "file"}:
            raise GuardError("manifest entry has an unsupported type")
        path = pathlib.Path(entry["path"])
        root = pathlib.Path(entry["root"])
        if root not in roots or not _is_within(path, root):
            raise GuardError("manifest entry escapes a literal runtime root")
        if entry["path"] in seen:
            raise GuardError("manifest contains a duplicate path")
        seen.add(entry["path"])
    if not {os.fspath(root) for root in roots}.issubset(seen):
        raise GuardError("manifest does not contain both literal runtime roots")


def _atomic_write(path: pathlib.Path, payload: dict[str, Any]) -> None:
    if path.exists() or path.is_symlink():
        raise GuardError(f"refusing to replace an existing manifest: {path}")
    temporary = path.with_name(f".{path.name}.tmp")
    if temporary.exists() or temporary.is_symlink():
        raise GuardError(f"temporary manifest path already exists: {temporary}")
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(temporary, flags, 0o600)
    try:
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(descriptor, remaining)
            if written == 0:
                raise GuardError("short write while creating manifest")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    directory_descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def snapshot(
    roots: Sequence[pathlib.Path],
    output: pathlib.Path,
    *,
    expected_uid: int,
    expected_gid: int,
    find_binary: str = FIND,
    findmnt_binary: str | None = FINDMNT,
) -> int:
    entries = scan_runtime_trees(
        roots,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        find_binary=find_binary,
        findmnt_binary=findmnt_binary,
    )
    _atomic_write(output, _manifest(roots, _stable_entries(entries)))
    return len(entries)


def verify(
    roots: Sequence[pathlib.Path],
    baseline_path: pathlib.Path,
    *,
    expected_uid: int,
    expected_gid: int,
    find_binary: str = FIND,
    findmnt_binary: str | None = FINDMNT,
) -> int:
    baseline = _secure_load(
        baseline_path, expected_uid=expected_uid, expected_gid=expected_gid
    )
    _validate_manifest_shape(baseline, roots, removal=False)
    current = scan_runtime_trees(
        roots,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        find_binary=find_binary,
        findmnt_binary=findmnt_binary,
    )
    if _stable_entries(current) != baseline["entries"]:
        raise GuardError("runtime tree differs from the proven-empty baseline")
    return len(current)


def prepare_removal(
    roots: Sequence[pathlib.Path],
    baseline_path: pathlib.Path,
    removal_path: pathlib.Path,
    *,
    expected_uid: int,
    expected_gid: int,
    find_binary: str = FIND,
    findmnt_binary: str | None = FINDMNT,
) -> int:
    require_no_open_runtime_path(
        roots,
        strict_permissions=expected_uid == 0,
    )
    baseline = _secure_load(
        baseline_path, expected_uid=expected_uid, expected_gid=expected_gid
    )
    _validate_manifest_shape(baseline, roots, removal=False)
    current = scan_runtime_trees(
        roots,
        expected_uid=expected_uid,
        expected_gid=expected_gid,
        find_binary=find_binary,
        findmnt_binary=findmnt_binary,
    )
    if _stable_entries(current) != baseline["entries"]:
        raise GuardError("runtime tree differs from the proven-empty baseline")
    _atomic_write(removal_path, _manifest(roots, current))
    return len(current)


def remove_from_manifest(
    roots: Sequence[pathlib.Path],
    removal_path: pathlib.Path,
    *,
    expected_uid: int,
    expected_gid: int,
) -> int:
    require_no_open_runtime_path(
        roots,
        strict_permissions=expected_uid == 0,
    )
    manifest = _secure_load(
        removal_path, expected_uid=expected_uid, expected_gid=expected_gid
    )
    _validate_manifest_shape(manifest, roots, removal=True)
    entries = sorted(
        manifest["entries"],
        key=lambda item: (len(pathlib.Path(item["path"]).parts), item["path"]),
        reverse=True,
    )
    for entry in entries:
        path = pathlib.Path(entry["path"])
        item_stat = path.lstat()
        item_kind = _kind(item_stat.st_mode)
        if (
            item_kind != entry["kind"]
            or item_stat.st_dev != entry["device"]
            or item_stat.st_ino != entry["inode"]
            or item_stat.st_uid != entry["uid"]
            or item_stat.st_gid != entry["gid"]
            or stat.S_IMODE(item_stat.st_mode) != entry["mode"]
        ):
            raise GuardError(f"runtime entry changed after manifest freeze: {path}")
        if item_kind == "file":
            if item_stat.st_nlink != 1:
                raise GuardError(f"runtime file gained a hardlink: {path}")
            path.unlink()
        else:
            path.rmdir()
    return len(entries)


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2 or argv[1] not in ALLOWED_ACTIONS:
        raise GuardError("usage: runtime_tree_guard.py ACTION")
    action = argv[1]
    if action == "snapshot":
        count = snapshot(RUNTIME_ROOTS, BASELINE_PATH, expected_uid=0, expected_gid=0)
    elif action == "verify":
        count = verify(RUNTIME_ROOTS, BASELINE_PATH, expected_uid=0, expected_gid=0)
    elif action == "prepare-removal":
        count = prepare_removal(
            RUNTIME_ROOTS,
            BASELINE_PATH,
            REMOVAL_PATH,
            expected_uid=0,
            expected_gid=0,
        )
    else:
        count = remove_from_manifest(
            RUNTIME_ROOTS, REMOVAL_PATH, expected_uid=0, expected_gid=0
        )
    print(f"DOCKER_RUNTIME_TREE_GUARD_PASS action={action} entries={count}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except (GuardError, FileNotFoundError, OSError) as error:
        print(f"DOCKER_RUNTIME_TREE_GUARD_REFUSED reason={error}", file=sys.stderr)
        raise SystemExit(65) from error
