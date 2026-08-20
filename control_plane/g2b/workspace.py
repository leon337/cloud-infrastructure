"""Confined filesystem primitives for bounded G2-B workspace mutations."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import errno
import hashlib
import os
from pathlib import Path, PurePosixPath
import secrets
import stat
from typing import Iterator

from scripts.check_repository_secrets import content_findings

from .errors import ConflictError, G2BError, RefusedError
from .protocol import MAX_CONTENT_BYTES, Precondition


_SAFE_TARGET_MODES = frozenset({0o600, 0o640, 0o644})
_ABSENT = None
_RENAME_NOREPLACE = 1
_RENAME_EXCHANGE = 2


@dataclass(frozen=True)
class TargetState:
    exists: bool
    size: int | None
    mode: int | None
    uid: int | None
    device: int | None
    inode: int | None
    sha256: str | None


@dataclass(frozen=True)
class WriteOutcome:
    path: str
    before: TargetState
    after: TargetState


class MutationStateError(G2BError):
    """Safe post-mutation failure state for transaction-layer resolution."""

    status = "FAILED"

    def __init__(
        self,
        code: str,
        *,
        operation: str,
        path: str,
        before: TargetState,
        observed_after: TargetState | None,
        resolution: str,
        recovery_name: str | None = None,
    ):
        super().__init__(code)
        self.operation = operation
        self.path = path
        self.before = before
        self.observed_after = observed_after
        self.resolution = resolution
        self.recovery_name = recovery_name


def inspect_target(
    workspace: str | Path,
    relative_path: str,
    *,
    expected_uid: int,
) -> TargetState:
    """Return a validated, content-scanned snapshot without following links."""
    name = _validate_relative_path(relative_path)
    with _open_workspace(workspace, expected_uid) as workspace_fd:
        return _inspect_target_fd(workspace_fd, name, expected_uid)


def atomic_write(
    workspace: str | Path,
    relative_path: str,
    content: bytes,
    *,
    precondition: Precondition,
    expected_uid: int,
    max_content_bytes: int = MAX_CONTENT_BYTES,
) -> WriteOutcome:
    """Atomically replace one confined file after enforcing its precondition."""
    name = _validate_relative_path(relative_path)
    _validate_content(content, max_content_bytes)
    _validate_precondition_shape(precondition)

    with _open_workspace(workspace, expected_uid) as workspace_fd:
        before = _inspect_target_fd(workspace_fd, name, expected_uid)
        _enforce_precondition(before, precondition)
        target_mode = before.mode if before.exists else 0o644
        assert target_mode is not None
        after = _atomic_replace_fd(
            workspace_fd,
            name,
            content,
            operation="write",
            target_mode=target_mode,
            expected_current=before,
            expected_uid=expected_uid,
        )
    return WriteOutcome(path=relative_path, before=before, after=after)


def atomic_restore(
    workspace: str | Path,
    relative_path: str,
    content: bytes,
    *,
    expected_current: TargetState,
    restore_mode: int | None,
    expected_uid: int,
    max_content_bytes: int = MAX_CONTENT_BYTES,
) -> WriteOutcome:
    """Restore safe prior bytes only while the frozen post-write state matches."""
    name = _validate_relative_path(relative_path)
    _validate_content(content, max_content_bytes)
    if restore_mode not in _SAFE_TARGET_MODES:
        raise RefusedError("target_mode_refused")
    if not isinstance(expected_current, TargetState) or not expected_current.exists:
        raise RefusedError("invalid_expected_state")

    with _open_workspace(workspace, expected_uid) as workspace_fd:
        before = _inspect_target_fd(workspace_fd, name, expected_uid)
        if before != expected_current:
            raise ConflictError("target_changed")
        after = _atomic_replace_fd(
            workspace_fd,
            name,
            content,
            operation="restore",
            target_mode=restore_mode,
            expected_current=before,
            expected_uid=expected_uid,
        )
    return WriteOutcome(path=relative_path, before=before, after=after)


def atomic_delete(
    workspace: str | Path,
    relative_path: str,
    *,
    expected_current: TargetState,
    expected_uid: int,
) -> TargetState:
    """Remove one exact frozen target via an internal same-directory tombstone."""
    name = _validate_relative_path(relative_path)
    if not isinstance(expected_current, TargetState) or not expected_current.exists:
        raise RefusedError("invalid_expected_state")

    with _open_workspace(workspace, expected_uid) as workspace_fd:
        before = _inspect_target_fd(workspace_fd, name, expected_uid)
        if before != expected_current:
            raise ConflictError("target_changed")
        current = _inspect_target_fd(workspace_fd, name, expected_uid)
        if current != before:
            raise ConflictError("target_changed")

        tombstone = _internal_name("delete")
        try:
            _rename_noreplace(workspace_fd, name, workspace_fd, tombstone)
        except FileExistsError:
            raise RefusedError("internal_name_collision") from None
        except OSError:
            raise ConflictError("target_changed") from None

        try:
            moved = _inspect_target_fd(workspace_fd, tombstone, expected_uid)
        except G2BError:
            _revert_delete(
                workspace_fd,
                tombstone,
                name,
                before,
                expected_uid,
                code="target_changed",
            )
            raise AssertionError("unreachable")
        if moved != before:
            _revert_delete(
                workspace_fd,
                tombstone,
                name,
                before,
                expected_uid,
                code="target_changed",
            )
            raise AssertionError("unreachable")

        visible = _observe_target_fd(workspace_fd, name, expected_uid)
        if visible is None or visible.exists:
            raise MutationStateError(
                "delete_recovery_blocked",
                operation="delete",
                path=name,
                before=before,
                observed_after=visible,
                resolution="INDETERMINATE",
                recovery_name=tombstone,
            )

        try:
            os.unlink(tombstone, dir_fd=workspace_fd)
        except OSError:
            _revert_delete(
                workspace_fd,
                tombstone,
                name,
                before,
                expected_uid,
                code="delete_cleanup_failed",
            )
            raise AssertionError("unreachable")

        try:
            os.fsync(workspace_fd)
        except OSError:
            raise MutationStateError(
                "delete_durability_indeterminate",
                operation="delete",
                path=name,
                before=before,
                observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
                resolution="INDETERMINATE",
            ) from None

        after = _inspect_target_fd(workspace_fd, name, expected_uid)
        if after.exists:
            raise MutationStateError(
                "final_target_mismatch",
                operation="delete",
                path=name,
                before=before,
                observed_after=after,
                resolution="INDETERMINATE",
            )
        return after


def _validate_relative_path(relative_path: str) -> str:
    if not isinstance(relative_path, str) or not relative_path or "\x00" in relative_path:
        raise RefusedError("invalid_relative_path")
    if relative_path.startswith("~"):
        raise RefusedError("tilde_path_refused")
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute() or os.path.isabs(relative_path):
        raise RefusedError("absolute_path_refused")
    if ".." in candidate.parts:
        raise RefusedError("path_escape_refused")
    if len(candidate.parts) != 1 or candidate.name != relative_path or candidate.name in {".", ".."}:
        raise RefusedError("nested_path_refused")
    return relative_path


@contextmanager
def _open_workspace(workspace: str | Path, expected_uid: int) -> Iterator[int]:
    rendered = os.fspath(workspace)
    try:
        before = os.lstat(rendered)
    except FileNotFoundError:
        raise RefusedError("workspace_not_found") from None
    except OSError:
        raise RefusedError("workspace_inspection_failed") from None
    if stat.S_ISLNK(before.st_mode):
        raise RefusedError("workspace_symlink_refused")
    if not stat.S_ISDIR(before.st_mode):
        raise RefusedError("workspace_not_directory")
    _validate_workspace_metadata(before, expected_uid)

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        workspace_fd = os.open(rendered, flags)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise RefusedError("workspace_symlink_refused") from None
        if error.errno == errno.ENOTDIR:
            raise RefusedError("workspace_not_directory") from None
        raise RefusedError("workspace_open_failed") from None
    try:
        opened = os.fstat(workspace_fd)
        _validate_workspace_metadata(opened, expected_uid)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ConflictError("workspace_changed")
        yield workspace_fd
    finally:
        os.close(workspace_fd)


def _validate_workspace_metadata(metadata: os.stat_result, expected_uid: int) -> None:
    if not stat.S_ISDIR(metadata.st_mode):
        raise RefusedError("workspace_not_directory")
    if metadata.st_uid != expected_uid:
        raise RefusedError("workspace_owner_mismatch")
    if stat.S_IMODE(metadata.st_mode) & 0o022:
        raise RefusedError("workspace_mode_refused")


def _inspect_target_fd(workspace_fd: int, name: str, expected_uid: int) -> TargetState:
    try:
        metadata = os.lstat(name, dir_fd=workspace_fd)
    except FileNotFoundError:
        return TargetState(False, _ABSENT, _ABSENT, _ABSENT, _ABSENT, _ABSENT, _ABSENT)
    except OSError:
        raise RefusedError("target_inspection_failed") from None

    _validate_target_metadata(metadata, expected_uid)
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        target_fd = os.open(name, flags, dir_fd=workspace_fd)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise RefusedError("target_symlink_refused") from None
        raise ConflictError("target_changed") from None

    try:
        opened = os.fstat(target_fd)
        _validate_target_metadata(opened, expected_uid)
        if not _same_file(metadata, opened):
            raise ConflictError("target_changed")
        if opened.st_size > MAX_CONTENT_BYTES:
            raise RefusedError("content_too_large")
        content = _read_bounded(target_fd, MAX_CONTENT_BYTES)
        finished = os.fstat(target_fd)
        if not _same_open_state(opened, finished):
            raise ConflictError("target_changed")
    finally:
        os.close(target_fd)

    try:
        final_path = os.lstat(name, dir_fd=workspace_fd)
    except OSError:
        raise ConflictError("target_changed") from None
    if not _same_open_state(finished, final_path):
        raise ConflictError("target_changed")
    _validate_content(content, MAX_CONTENT_BYTES)
    return TargetState(
        exists=True,
        size=len(content),
        mode=stat.S_IMODE(finished.st_mode),
        uid=finished.st_uid,
        device=finished.st_dev,
        inode=finished.st_ino,
        sha256=hashlib.sha256(content).hexdigest(),
    )


def _validate_target_metadata(metadata: os.stat_result, expected_uid: int) -> None:
    if stat.S_ISLNK(metadata.st_mode):
        raise RefusedError("target_symlink_refused")
    if not stat.S_ISREG(metadata.st_mode):
        raise RefusedError("target_not_regular")
    if metadata.st_nlink != 1:
        raise RefusedError("target_hardlink_refused")
    if metadata.st_uid != expected_uid:
        raise RefusedError("target_owner_mismatch")
    if stat.S_IMODE(metadata.st_mode) not in _SAFE_TARGET_MODES:
        raise RefusedError("target_mode_refused")


def _same_file(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _same_open_state(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_nlink,
        left.st_uid,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_nlink,
        right.st_uid,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _read_bounded(target_fd: int, limit: int) -> bytes:
    chunks: list[bytes] = []
    remaining = limit + 1
    while remaining:
        try:
            chunk = os.read(target_fd, min(remaining, 65_536))
        except InterruptedError:
            continue
        except OSError:
            raise RefusedError("target_read_failed") from None
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    content = b"".join(chunks)
    if len(content) > limit:
        raise RefusedError("content_too_large")
    return content


def _validate_content(content: bytes, max_content_bytes: int) -> None:
    if not isinstance(content, bytes):
        raise RefusedError("invalid_content")
    if (
        not isinstance(max_content_bytes, int)
        or isinstance(max_content_bytes, bool)
        or max_content_bytes < 0
        or max_content_bytes > MAX_CONTENT_BYTES
    ):
        raise RefusedError("invalid_content_limit")
    if len(content) > max_content_bytes:
        raise RefusedError("content_too_large")
    try:
        content.decode("utf-8")
    except UnicodeDecodeError:
        raise RefusedError("binary_or_non_utf8") from None
    if next(content_findings(content), None) is not None:
        raise RefusedError("secret_like_content")


def _validate_precondition_shape(precondition: Precondition) -> None:
    if not isinstance(precondition, Precondition):
        raise RefusedError("invalid_precondition")
    is_absent = precondition.state == "ABSENT" and precondition.sha256 is None
    is_hash = (
        precondition.state is None
        and isinstance(precondition.sha256, str)
        and len(precondition.sha256) == 64
        and all(character in "0123456789abcdef" for character in precondition.sha256)
    )
    if not (is_absent or is_hash):
        raise RefusedError("invalid_precondition")


def _enforce_precondition(before: TargetState, precondition: Precondition) -> None:
    if precondition.state == "ABSENT":
        if before.exists:
            raise ConflictError("precondition_mismatch")
        return
    if not before.exists or before.sha256 != precondition.sha256:
        raise ConflictError("precondition_mismatch")


def _atomic_replace_fd(
    workspace_fd: int,
    name: str,
    content: bytes,
    *,
    operation: str,
    target_mode: int,
    expected_current: TargetState,
    expected_uid: int,
) -> TargetState:
    temporary = _internal_name("write")
    temporary_fd: int | None = None
    cleanup_temporary = True
    namespace_applied = False
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
        temporary_fd = os.open(temporary, flags, 0o600, dir_fd=workspace_fd)
        created = os.fstat(temporary_fd)
        if (
            not stat.S_ISREG(created.st_mode)
            or created.st_nlink != 1
            or created.st_uid != expected_uid
        ):
            raise RefusedError("unsafe_temporary_file")
        _write_all(temporary_fd, content)
        os.fsync(temporary_fd)
        os.fchmod(temporary_fd, target_mode)
        os.fsync(temporary_fd)
        prepared = _inspect_target_fd(workspace_fd, temporary, expected_uid)

        try:
            current = _inspect_target_fd(workspace_fd, name, expected_uid)
        except RefusedError:
            raise ConflictError("target_changed") from None
        if current != expected_current:
            raise ConflictError("target_changed")

        if expected_current.exists:
            _rename_exchange(workspace_fd, temporary, workspace_fd, name)
            namespace_applied = True
            cleanup_temporary = False
            try:
                displaced = _inspect_target_fd(workspace_fd, temporary, expected_uid)
            except G2BError:
                _revert_exchange(
                    workspace_fd,
                    temporary,
                    name,
                    expected_current,
                    prepared,
                    expected_uid,
                    operation=operation,
                )
                raise AssertionError("unreachable")
            if displaced != expected_current:
                _revert_exchange(
                    workspace_fd,
                    temporary,
                    name,
                    expected_current,
                    prepared,
                    expected_uid,
                    operation=operation,
                )
                raise AssertionError("unreachable")
            try:
                os.unlink(temporary, dir_fd=workspace_fd)
            except OSError:
                raise MutationStateError(
                    f"{operation}_cleanup_failed",
                    operation=operation,
                    path=name,
                    before=expected_current,
                    observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
                    resolution="APPLIED",
                    recovery_name=temporary,
                ) from None
        else:
            try:
                _rename_noreplace(workspace_fd, temporary, workspace_fd, name)
            except FileExistsError:
                raise ConflictError("target_changed") from None
            namespace_applied = True
            cleanup_temporary = False

        try:
            os.fsync(workspace_fd)
        except OSError:
            raise MutationStateError(
                f"{operation}_durability_indeterminate",
                operation=operation,
                path=name,
                before=expected_current,
                observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
                resolution="INDETERMINATE",
            ) from None
    except (ConflictError, MutationStateError, RefusedError):
        raise
    except OSError:
        if namespace_applied:
            raise MutationStateError(
                f"{operation}_state_indeterminate",
                operation=operation,
                path=name,
                before=expected_current,
                observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
                resolution="INDETERMINATE",
                recovery_name=temporary if not cleanup_temporary else None,
            ) from None
        raise RefusedError("atomic_write_failed") from None
    finally:
        if temporary_fd is not None:
            os.close(temporary_fd)
        if cleanup_temporary:
            try:
                os.unlink(temporary, dir_fd=workspace_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass

    try:
        after = _inspect_target_fd(workspace_fd, name, expected_uid)
    except G2BError:
        raise MutationStateError(
            "final_target_indeterminate",
            operation=operation,
            path=name,
            before=expected_current,
            observed_after=None,
            resolution="INDETERMINATE",
        ) from None
    expected_digest = hashlib.sha256(content).hexdigest()
    if (
        not after.exists
        or after.size != len(content)
        or after.mode != target_mode
        or after.uid != expected_uid
        or after.sha256 != expected_digest
    ):
        raise MutationStateError(
            "final_target_mismatch",
            operation=operation,
            path=name,
            before=expected_current,
            observed_after=after,
            resolution="INDETERMINATE",
        )
    return after


def _observe_target_fd(
    workspace_fd: int,
    name: str,
    expected_uid: int,
) -> TargetState | None:
    try:
        return _inspect_target_fd(workspace_fd, name, expected_uid)
    except (G2BError, OSError):
        return None


def _write_all(target_fd: int, content: bytes) -> None:
    remaining = memoryview(content)
    while remaining:
        try:
            written = os.write(target_fd, remaining)
        except InterruptedError:
            continue
        if written <= 0:
            raise RefusedError("atomic_write_failed")
        remaining = remaining[written:]


def _internal_name(purpose: str) -> str:
    return f".g2b-{purpose}-{secrets.token_hex(16)}.tmp"


def _revert_exchange(
    workspace_fd: int,
    temporary: str,
    name: str,
    before: TargetState,
    prepared: TargetState,
    expected_uid: int,
    *,
    operation: str,
) -> None:
    if _observe_target_fd(workspace_fd, name, expected_uid) != prepared:
        raise MutationStateError(
            f"{operation}_recovery_blocked",
            operation=operation,
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
            recovery_name=temporary,
        )
    try:
        _rename_exchange(workspace_fd, temporary, workspace_fd, name)
    except OSError:
        raise MutationStateError(
            f"{operation}_recovery_failed",
            operation=operation,
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
            recovery_name=temporary,
        ) from None

    try:
        os.unlink(temporary, dir_fd=workspace_fd)
    except OSError:
        raise MutationStateError(
            f"{operation}_revert_cleanup_failed",
            operation=operation,
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="REVERTED",
            recovery_name=temporary,
        ) from None
    try:
        os.fsync(workspace_fd)
    except OSError:
        raise MutationStateError(
            f"{operation}_revert_durability_indeterminate",
            operation=operation,
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
        ) from None
    raise MutationStateError(
        "target_changed",
        operation=operation,
        path=name,
        before=before,
        observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
        resolution="REVERTED",
    )


def _revert_delete(
    workspace_fd: int,
    tombstone: str,
    name: str,
    before: TargetState,
    expected_uid: int,
    *,
    code: str,
) -> None:
    try:
        _rename_noreplace(workspace_fd, tombstone, workspace_fd, name)
    except FileExistsError:
        raise MutationStateError(
            "delete_recovery_blocked",
            operation="delete",
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
            recovery_name=tombstone,
        ) from None
    except OSError:
        raise MutationStateError(
            "delete_recovery_failed",
            operation="delete",
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
            recovery_name=tombstone,
        ) from None

    try:
        os.fsync(workspace_fd)
    except OSError:
        raise MutationStateError(
            "delete_revert_durability_indeterminate",
            operation="delete",
            path=name,
            before=before,
            observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
            resolution="INDETERMINATE",
        ) from None
    raise MutationStateError(
        code,
        operation="delete",
        path=name,
        before=before,
        observed_after=_observe_target_fd(workspace_fd, name, expected_uid),
        resolution="REVERTED",
    )


def _rename_noreplace(
    source_fd: int,
    source: str,
    destination_fd: int,
    destination: str,
) -> None:
    """Linux descriptor-relative rename that never replaces the destination."""
    _renameat2(source_fd, source, destination_fd, destination, _RENAME_NOREPLACE)


def _rename_exchange(
    source_fd: int,
    source: str,
    destination_fd: int,
    destination: str,
) -> None:
    """Linux descriptor-relative atomic exchange used for verified replacement."""
    _renameat2(source_fd, source, destination_fd, destination, _RENAME_EXCHANGE)


def _renameat2(
    source_fd: int,
    source: str,
    destination_fd: int,
    destination: str,
    flags: int,
) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        renameat2 = libc.renameat2
    except AttributeError:
        raise OSError(errno.ENOSYS, "renameat2 unavailable") from None
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(
        source_fd,
        os.fsencode(source),
        destination_fd,
        os.fsencode(destination),
        flags,
    )
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number))
