"""Protected transaction state for the bounded G2-B pilot."""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from datetime import datetime
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import time
from typing import Any, Iterator

from scripts.check_repository_secrets import content_findings

from .errors import RefusedError, TimeoutError
from .protocol import OPERATIONS, RESULT_PROTOCOL


RECEIPT_FIELDS = frozenset(
    {
        "protocol",
        "request_id",
        "request_digest",
        "mission_id",
        "declared_actor",
        "authority",
        "transport_principal",
        "grant_id",
        "project",
        "operation",
        "path",
        "started_at",
        "finished_at",
        "precondition",
        "before",
        "after",
        "status",
        "replayed",
        "rollback_request_id",
        "revocation_request_id",
        "error",
    }
)

_STATE_DIRECTORIES = ("receipts", "snapshots", "recovery", "revocations")
_STATE_MODE = 0o700
_FILE_MODE = 0o600
_MAX_LOCK_SECONDS = 10.0
_MAX_STATE_FILE_BYTES = 256 * 1024
_STATE_FIELDS = frozenset({"exists", "size", "mode", "sha256"})
_EXACT_STATE_FIELDS = frozenset(
    {"exists", "size", "mode", "uid", "device", "inode", "sha256"}
)
_RECOVERY_FIELDS = frozenset(
    {
        "protocol",
        "request_id",
        "request_digest",
        "grant_id",
        "path",
        "expected_after",
        "before",
        "after",
        "resolution",
        "active",
        "snapshot",
        "workspace_recovery_name",
        "observation",
        "rollback_observation",
        "receipt_context",
    }
)
_EXPECTED_STATE_FIELDS = frozenset({"exists", "size", "mode", "uid", "sha256"})
_RECEIPT_CONTEXT_FIELDS = frozenset(
    {
        "mission_id",
        "declared_actor",
        "authority",
        "transport_principal",
        "project",
        "operation",
        "precondition",
        "started_at",
    }
)
_RECOVERY_RESOLUTIONS = frozenset(
    {"PREPARED", "APPLIED", "REVERTED", "INDETERMINATE", "ROLLED_BACK"}
)
_PROJECT_FIELDS = frozenset({"tenant", "name", "environment"})
_PRINCIPAL_FIELDS = frozenset({"login", "actor_id"})
_STATUSES = frozenset(
    {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK", "REVOKED"}
)
_SAFE_CODE_CHARACTERS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
_RENAME_NOREPLACE = 1
_RENAME_UNSUPPORTED_ERRNOS = frozenset(
    {errno.ENOSYS, errno.EOPNOTSUPP, errno.EINVAL, errno.EXDEV}
)


def canonical_request_digest(value: dict[str, Any]) -> str:
    """Return the SHA-256 of compact, sorted, UTF-8 JSON."""
    if not isinstance(value, dict):
        raise RefusedError("invalid_request")
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise RefusedError("invalid_request") from None
    return hashlib.sha256(encoded).hexdigest()


class StateStore:
    """Descriptor-validated storage for receipts, audit, and revocation."""

    def __init__(
        self,
        state_root: str | Path,
        lock_path: str | Path,
        *,
        expected_uid: int,
    ) -> None:
        if not isinstance(expected_uid, int) or isinstance(expected_uid, bool) or expected_uid < 0:
            raise RefusedError("invalid_execution_uid")
        if expected_uid == 0:
            raise RefusedError("root_execution_refused")
        self.state_root = Path(state_root)
        self.lock_path = Path(lock_path)
        self.expected_uid = expected_uid
        with self._root_fd() as root_fd:
            for name in _STATE_DIRECTORIES:
                self._ensure_directory(root_fd, name)
        lock_fd = self._open_lock()
        os.close(lock_fd)

    @contextmanager
    def exclusive_lock(self, *, timeout_seconds: float) -> Iterator[None]:
        if (
            not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool)
            or timeout_seconds < 0
            or timeout_seconds > _MAX_LOCK_SECONDS
        ):
            raise RefusedError("invalid_lock_timeout")
        lock_fd = self._open_lock()
        deadline = time.monotonic() + float(timeout_seconds)
        acquired = False
        try:
            while True:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except OSError as error:
                    if error.errno not in {errno.EACCES, errno.EAGAIN}:
                        raise RefusedError("lock_failed") from None
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("lock_timeout") from None
                    time.sleep(min(0.01, remaining))
            yield
        finally:
            if acquired:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                except OSError:
                    pass
            os.close(lock_fd)

    def lookup_request(self, request_id: str) -> dict[str, Any] | None:
        name = _hashed_name(request_id)
        with self._child_fd("receipts") as receipts_fd:
            raw = self._read_optional(receipts_fd, name)
        if raw is None:
            return None
        value = _decode_json_object(raw, "invalid_receipt")
        _validate_receipt(value, serialized=raw)
        if value["request_id"] != request_id:
            raise RefusedError("receipt_identity_mismatch")
        self._ensure_audit(_receipt_audit_event(value))
        return value

    def record_write(self, receipt: dict[str, Any]) -> None:
        self._record_receipt(receipt, expected_operation=None, audit_event="write")

    def record_rollback(self, receipt: dict[str, Any]) -> None:
        self._record_receipt(receipt, expected_operation="rollback", audit_event="rollback")

    def save_snapshot(self, request_id: str, content: bytes) -> None:
        if not isinstance(content, bytes) or len(content) > 65_536:
            raise RefusedError("invalid_snapshot")
        if next(content_findings(content), None) is not None:
            raise RefusedError("secret_like_snapshot")
        name = _hashed_name(request_id)
        with self._child_fd("snapshots") as snapshots_fd:
            if not self._atomic_create(snapshots_fd, name, content):
                raise RefusedError("snapshot_already_exists")

    def load_snapshot(self, request_id: str) -> bytes | None:
        name = _hashed_name(request_id)
        with self._child_fd("snapshots") as snapshots_fd:
            raw = self._read_optional(snapshots_fd, name)
        if raw is not None and next(content_findings(raw), None) is not None:
            raise RefusedError("secret_like_snapshot")
        return raw

    def delete_snapshot(self, request_id: str) -> None:
        name = _hashed_name(request_id)
        with self._child_fd("snapshots") as snapshots_fd:
            existing = self._read_optional(snapshots_fd, name)
            if existing is None:
                return
            try:
                os.unlink(name, dir_fd=snapshots_fd)
                os.fsync(snapshots_fd)
            except OSError:
                raise RefusedError("snapshot_delete_failed") from None

    def prepare_recovery(self, recovery: dict[str, Any]) -> None:
        serialized = _encode_json(recovery)
        _validate_recovery(recovery, serialized=serialized)
        if recovery["resolution"] != "PREPARED" or recovery["active"] is not True:
            raise RefusedError("invalid_recovery")
        name = _hashed_name(recovery["request_id"])
        with self._child_fd("recovery") as recovery_fd:
            if not self._atomic_create(recovery_fd, name, serialized):
                raise RefusedError("recovery_already_exists")

    def update_recovery(self, recovery: dict[str, Any]) -> None:
        serialized = _encode_json(recovery)
        if not isinstance(recovery, dict) or set(recovery) != _RECOVERY_FIELDS:
            raise RefusedError("invalid_recovery")
        name = _hashed_name(recovery["request_id"])
        with self._child_fd("recovery") as recovery_fd:
            existing = self._read_optional(recovery_fd, name)
            if existing is None:
                raise RefusedError("recovery_missing")
            current = _decode_json_object(existing, "invalid_recovery")
            _validate_recovery(current, serialized=existing)
            if current["request_id"] != recovery["request_id"]:
                raise RefusedError("recovery_identity_mismatch")
            _validate_recovery_transition(current, recovery)
            _validate_recovery(recovery, serialized=serialized)
            self._atomic_replace(recovery_fd, name, serialized)

    def lookup_recovery(self, request_id: str) -> dict[str, Any] | None:
        name = _hashed_name(request_id)
        with self._child_fd("recovery") as recovery_fd:
            raw = self._read_optional(recovery_fd, name)
        if raw is None:
            return None
        value = _decode_json_object(raw, "invalid_recovery")
        _validate_recovery(value, serialized=raw)
        if value["request_id"] != request_id:
            raise RefusedError("recovery_identity_mismatch")
        return value

    def active_recoveries(self, grant_id: str | None = None) -> list[dict[str, Any]]:
        if grant_id is not None and not _safe_identifier(grant_id):
            raise RefusedError("invalid_state_identifier")
        return [
            value
            for value in self.recoveries()
            if (grant_id is None or value["grant_id"] == grant_id) and value["active"] is True
        ]

    def recoveries(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        with self._child_fd("recovery") as recovery_fd:
            try:
                names = sorted(os.listdir(recovery_fd))
            except OSError:
                raise RefusedError("state_read_failed") from None
            for name in names:
                if not _hashed_state_filename(name):
                    raise RefusedError("unsafe_state_file")
                raw = self._read_optional(recovery_fd, name)
                if raw is None:
                    raise RefusedError("unsafe_state_file")
                value = _decode_json_object(raw, "invalid_recovery")
                _validate_recovery(value, serialized=raw)
                result.append(value)
        return result

    def reconcile_abandoned_temporaries(self) -> None:
        for directory in _STATE_DIRECTORIES:
            with self._child_fd(directory) as directory_fd:
                try:
                    names = os.listdir(directory_fd)
                except OSError:
                    raise RefusedError("state_read_failed") from None
                changed = False
                for name in names:
                    if not name.startswith(".g2b-state-"):
                        continue
                    if not _state_temporary_name(name):
                        raise RefusedError("unsafe_state_file")
                    raw = self._read_optional(directory_fd, name)
                    if raw is None:
                        continue
                    try:
                        os.unlink(name, dir_fd=directory_fd)
                    except OSError:
                        raise RefusedError("state_temporary_cleanup_failed") from None
                    changed = True
                if changed:
                    try:
                        os.fsync(directory_fd)
                    except OSError:
                        raise RefusedError("state_temporary_cleanup_failed") from None

    def revoke(self, grant_id: str, *, actor: str, at: datetime) -> None:
        if not _safe_identifier(grant_id) or actor != "MESTRE_MCF" or not _aware_datetime(at):
            raise RefusedError("invalid_revocation")
        value = {
            "protocol": RESULT_PROTOCOL,
            "grant_id": grant_id,
            "actor": actor,
            "revoked_at": at.isoformat(),
        }
        serialized = _encode_json(value)
        if next(content_findings(serialized), None) is not None:
            raise RefusedError("secret_like_revocation")
        name = _hashed_name(grant_id)
        with self._child_fd("revocations") as revocations_fd:
            created = self._atomic_create(revocations_fd, name, serialized)
        event = {
            "event": "revoke",
            "request_id": None,
            "request_digest": None,
            "grant_id": grant_id,
            "operation": "revoke",
            "status": "REVOKED",
            "error": None,
            "at": at.isoformat(),
        }
        if created:
            self._ensure_audit(event)
        else:
            existing = self._read_revocation(grant_id)
            self._ensure_audit(
                dict(event, at=existing["revoked_at"])
            )

    def is_revoked(self, grant_id: str) -> bool:
        value = self._read_revocation(grant_id)
        if value is None:
            return False
        self._ensure_audit(
            {
                "event": "revoke",
                "request_id": None,
                "request_digest": None,
                "grant_id": grant_id,
                "operation": "revoke",
                "status": "REVOKED",
                "error": None,
                "at": value["revoked_at"],
            }
        )
        return True

    def _read_revocation(self, grant_id: str) -> dict[str, Any] | None:
        name = _hashed_name(grant_id)
        with self._child_fd("revocations") as revocations_fd:
            raw = self._read_optional(revocations_fd, name)
        if raw is None:
            return None
        value = _decode_json_object(raw, "invalid_revocation")
        if set(value) != {"protocol", "grant_id", "actor", "revoked_at"}:
            raise RefusedError("invalid_revocation")
        if (
            value.get("protocol") != RESULT_PROTOCOL
            or value.get("grant_id") != grant_id
            or value.get("actor") != "MESTRE_MCF"
            or not _timestamp(value.get("revoked_at"))
        ):
            raise RefusedError("invalid_revocation")
        return value

    def _record_receipt(
        self,
        receipt: dict[str, Any],
        *,
        expected_operation: str | None,
        audit_event: str,
    ) -> None:
        serialized = _encode_json(receipt)
        _validate_receipt(receipt, serialized=serialized)
        if expected_operation is not None and receipt["operation"] != expected_operation:
            raise RefusedError("invalid_receipt_operation")
        name = _hashed_name(receipt["request_id"])
        with self._child_fd("receipts") as receipts_fd:
            created = self._atomic_create(receipts_fd, name, serialized)
            if not created:
                existing = self._read_optional(receipts_fd, name)
                if existing != serialized:
                    raise RefusedError("receipt_already_exists")
        self._ensure_audit(_receipt_audit_event(receipt, event=audit_event))

    @contextmanager
    def _root_fd(self) -> Iterator[int]:
        fd = _open_validated_directory(
            self.state_root,
            expected_uid=self.expected_uid,
            mode=_STATE_MODE,
            error_code="unsafe_state_directory",
            mode_error_code="unsafe_state_mode",
        )
        try:
            yield fd
        finally:
            os.close(fd)

    @contextmanager
    def _child_fd(self, name: str) -> Iterator[int]:
        with self._root_fd() as root_fd:
            fd = self._open_directory_at(root_fd, name)
            try:
                yield fd
            finally:
                os.close(fd)

    def _ensure_directory(self, root_fd: int, name: str) -> None:
        try:
            os.mkdir(name, _STATE_MODE, dir_fd=root_fd)
            os.fsync(root_fd)
        except FileExistsError:
            pass
        except OSError:
            raise RefusedError("unsafe_state_directory") from None
        fd = self._open_directory_at(root_fd, name)
        os.close(fd)

    def _open_directory_at(self, root_fd: int, name: str) -> int:
        try:
            before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
        except OSError:
            raise RefusedError("unsafe_state_directory") from None
        _validate_directory_metadata(
            before,
            expected_uid=self.expected_uid,
            mode=_STATE_MODE,
            error_code="unsafe_state_directory",
            mode_error_code="unsafe_state_mode",
        )
        try:
            fd = os.open(
                name,
                os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=root_fd,
            )
        except OSError:
            raise RefusedError("unsafe_state_directory") from None
        valid = False
        try:
            opened = os.fstat(fd)
            _validate_directory_metadata(
                opened,
                expected_uid=self.expected_uid,
                mode=_STATE_MODE,
                error_code="unsafe_state_directory",
                mode_error_code="unsafe_state_mode",
            )
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise RefusedError("unsafe_state_directory")
            valid = True
        finally:
            if not valid:
                os.close(fd)
        return fd

    def _open_lock(self) -> int:
        try:
            before = os.stat(self.lock_path, follow_symlinks=False)
        except OSError:
            raise RefusedError("unsafe_lock_file") from None
        _validate_file_metadata(
            before,
            expected_uid=self.expected_uid,
            error_code="unsafe_lock_file",
        )
        try:
            fd = os.open(
                self.lock_path,
                os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW,
            )
        except OSError:
            raise RefusedError("unsafe_lock_file") from None
        valid = False
        try:
            opened = os.fstat(fd)
            _validate_file_metadata(
                opened,
                expected_uid=self.expected_uid,
                error_code="unsafe_lock_file",
            )
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise RefusedError("unsafe_lock_file")
            valid = True
        finally:
            if not valid:
                os.close(fd)
        return fd

    def _read_optional(self, directory_fd: int, name: str) -> bytes | None:
        try:
            before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except FileNotFoundError:
            return None
        except OSError:
            raise RefusedError("unsafe_state_file") from None
        _validate_file_metadata(before, expected_uid=self.expected_uid, error_code="unsafe_state_file")
        try:
            fd = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW, dir_fd=directory_fd)
        except OSError:
            raise RefusedError("unsafe_state_file") from None
        try:
            opened = os.fstat(fd)
            _validate_file_metadata(opened, expected_uid=self.expected_uid, error_code="unsafe_state_file")
            if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                raise RefusedError("unsafe_state_file")
            if opened.st_size > _MAX_STATE_FILE_BYTES:
                raise RefusedError("state_file_too_large")
            chunks: list[bytes] = []
            remaining = _MAX_STATE_FILE_BYTES + 1
            while remaining:
                chunk = os.read(fd, min(remaining, 65_536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            raw = b"".join(chunks)
            if len(raw) > _MAX_STATE_FILE_BYTES:
                raise RefusedError("state_file_too_large")
            finished = os.fstat(fd)
            if (
                opened.st_dev,
                opened.st_ino,
                opened.st_size,
                opened.st_mtime_ns,
                opened.st_ctime_ns,
            ) != (
                finished.st_dev,
                finished.st_ino,
                finished.st_size,
                finished.st_mtime_ns,
                finished.st_ctime_ns,
            ):
                raise RefusedError("unsafe_state_file")
            try:
                final_path = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            except OSError:
                raise RefusedError("unsafe_state_file") from None
            _validate_file_metadata(
                final_path,
                expected_uid=self.expected_uid,
                error_code="unsafe_state_file",
            )
            if (finished.st_dev, finished.st_ino) != (final_path.st_dev, final_path.st_ino):
                raise RefusedError("unsafe_state_file")
            return raw
        except OSError:
            raise RefusedError("state_read_failed") from None
        finally:
            os.close(fd)

    def _atomic_create(self, directory_fd: int, name: str, content: bytes) -> bool:
        temporary = f".g2b-state-{secrets.token_hex(16)}.tmp"
        temporary_fd: int | None = None
        try:
            temporary_fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                _FILE_MODE,
                dir_fd=directory_fd,
            )
            os.fchmod(temporary_fd, _FILE_MODE)
            _write_all(temporary_fd, content)
            os.fsync(temporary_fd)
            metadata = os.fstat(temporary_fd)
            _validate_file_metadata(metadata, expected_uid=self.expected_uid, error_code="unsafe_state_file")
            try:
                _rename_noreplace_state(directory_fd, temporary, name)
            except FileExistsError:
                return False
            temporary = ""
            os.fsync(directory_fd)
            return True
        except RefusedError:
            raise
        except OSError:
            raise RefusedError("state_write_failed") from None
        finally:
            if temporary_fd is not None:
                os.close(temporary_fd)
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=directory_fd)
                except OSError:
                    pass

    def _atomic_replace(self, directory_fd: int, name: str, content: bytes) -> None:
        temporary = f".g2b-state-{secrets.token_hex(16)}.tmp"
        temporary_fd: int | None = None
        try:
            temporary_fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
                _FILE_MODE,
                dir_fd=directory_fd,
            )
            os.fchmod(temporary_fd, _FILE_MODE)
            _write_all(temporary_fd, content)
            os.fsync(temporary_fd)
            _validate_file_metadata(
                os.fstat(temporary_fd),
                expected_uid=self.expected_uid,
                error_code="unsafe_state_file",
            )
            os.rename(
                temporary,
                name,
                src_dir_fd=directory_fd,
                dst_dir_fd=directory_fd,
            )
            temporary = ""
            os.fsync(directory_fd)
        except RefusedError:
            raise
        except OSError:
            raise RefusedError("state_write_failed") from None
        finally:
            if temporary_fd is not None:
                os.close(temporary_fd)
            if temporary:
                try:
                    os.unlink(temporary, dir_fd=directory_fd)
                except OSError:
                    pass

    def _append_audit(self, event: dict[str, Any]) -> None:
        serialized = _encode_json(event) + b"\n"
        if len(serialized) > 4096 or next(content_findings(serialized), None) is not None:
            raise RefusedError("unsafe_audit_event")
        with self._root_fd() as root_fd:
            name = "audit.jsonl"
            try:
                before = os.stat(name, dir_fd=root_fd, follow_symlinks=False)
            except FileNotFoundError:
                before = None
            except OSError:
                raise RefusedError("unsafe_audit_file") from None
            if before is not None:
                _validate_file_metadata(before, expected_uid=self.expected_uid, error_code="unsafe_audit_file")
            try:
                fd = os.open(
                    name,
                    os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW,
                    _FILE_MODE,
                    dir_fd=root_fd,
                )
            except OSError:
                raise RefusedError("unsafe_audit_file") from None
            try:
                os.fchmod(fd, _FILE_MODE)
                opened = os.fstat(fd)
                _validate_file_metadata(opened, expected_uid=self.expected_uid, error_code="unsafe_audit_file")
                if before is not None and (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
                    raise RefusedError("unsafe_audit_file")
                _write_all(fd, serialized)
                os.fsync(fd)
                os.fsync(root_fd)
            except OSError:
                raise RefusedError("audit_write_failed") from None
            finally:
                os.close(fd)

    def _ensure_audit(self, event: dict[str, Any]) -> None:
        events = self._read_audit_events()
        if event in events:
            return
        for existing in events:
            same_receipt = (
                event["request_id"] is not None
                and existing["request_id"] == event["request_id"]
            )
            same_revocation = (
                event["event"] == "revoke"
                and existing["event"] == "revoke"
                and existing["grant_id"] == event["grant_id"]
            )
            if same_receipt or same_revocation:
                raise RefusedError("audit_event_conflict")
        self._append_audit(event)

    def _read_audit_events(self) -> list[dict[str, Any]]:
        with self._root_fd() as root_fd:
            raw = self._read_optional(root_fd, "audit.jsonl")
        if raw is None or raw == b"":
            return []
        if not raw.endswith(b"\n"):
            raise RefusedError("invalid_audit_log")
        events: list[dict[str, Any]] = []
        for line in raw.splitlines():
            value = _decode_json_object(line, "invalid_audit_log")
            if set(value) != {
                "event",
                "request_id",
                "request_digest",
                "grant_id",
                "operation",
                "status",
                "error",
                "at",
            }:
                raise RefusedError("invalid_audit_log")
            events.append(value)
        return events


def _open_validated_directory(
    path: Path,
    *,
    expected_uid: int,
    mode: int,
    error_code: str,
    mode_error_code: str,
) -> int:
    try:
        before = os.stat(path, follow_symlinks=False)
    except OSError:
        raise RefusedError(error_code) from None
    _validate_directory_metadata(
        before,
        expected_uid=expected_uid,
        mode=mode,
        error_code=error_code,
        mode_error_code=mode_error_code,
    )
    try:
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW)
    except OSError:
        raise RefusedError(error_code) from None
    valid = False
    try:
        opened = os.fstat(fd)
        _validate_directory_metadata(
            opened,
            expected_uid=expected_uid,
            mode=mode,
            error_code=error_code,
            mode_error_code=mode_error_code,
        )
        if (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino):
            raise RefusedError(error_code)
        valid = True
    finally:
        if not valid:
            os.close(fd)
    return fd


def _validate_directory_metadata(
    metadata: os.stat_result,
    *,
    expected_uid: int,
    mode: int,
    error_code: str,
    mode_error_code: str,
) -> None:
    if not stat.S_ISDIR(metadata.st_mode) or metadata.st_uid != expected_uid:
        raise RefusedError(error_code)
    if stat.S_IMODE(metadata.st_mode) != mode:
        raise RefusedError(mode_error_code)


def _validate_file_metadata(
    metadata: os.stat_result,
    *,
    expected_uid: int,
    error_code: str,
) -> None:
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != expected_uid
        or stat.S_IMODE(metadata.st_mode) != _FILE_MODE
    ):
        raise RefusedError(error_code)


def _validate_receipt(value: Any, *, serialized: bytes) -> None:
    if not isinstance(value, dict) or set(value) != RECEIPT_FIELDS:
        raise RefusedError("invalid_receipt_schema")
    if next(content_findings(serialized), None) is not None:
        raise RefusedError("secret_like_receipt")
    if value.get("protocol") != RESULT_PROTOCOL:
        raise RefusedError("invalid_receipt")
    if not _safe_identifier(value.get("request_id")) or not _sha256(value.get("request_digest")):
        raise RefusedError("invalid_receipt")
    for field in ("mission_id", "declared_actor", "authority", "grant_id"):
        if not _safe_identifier(value.get(field)):
            raise RefusedError("invalid_receipt")
    principal = value.get("transport_principal")
    if (
        not isinstance(principal, dict)
        or set(principal) != _PRINCIPAL_FIELDS
        or not _safe_identifier(principal.get("login"))
        or not isinstance(principal.get("actor_id"), int)
        or isinstance(principal.get("actor_id"), bool)
        or principal["actor_id"] < 1
    ):
        raise RefusedError("invalid_receipt")
    project = value.get("project")
    if not isinstance(project, dict) or set(project) != _PROJECT_FIELDS:
        raise RefusedError("invalid_receipt")
    if any(not _safe_identifier(project.get(field)) for field in _PROJECT_FIELDS):
        raise RefusedError("invalid_receipt")
    if value.get("operation") not in OPERATIONS:
        raise RefusedError("invalid_receipt")
    if value.get("path") is not None and not isinstance(value.get("path"), str):
        raise RefusedError("invalid_receipt")
    if not _timestamp(value.get("started_at")) or not _timestamp(value.get("finished_at")):
        raise RefusedError("invalid_receipt")
    _validate_precondition(value.get("precondition"))
    _validate_public_state(value.get("before"))
    _validate_public_state(value.get("after"))
    if value.get("status") not in _STATUSES or not isinstance(value.get("replayed"), bool):
        raise RefusedError("invalid_receipt")
    for field in ("rollback_request_id", "revocation_request_id"):
        if value.get(field) is not None and not _safe_identifier(value.get(field)):
            raise RefusedError("invalid_receipt")
    error = value.get("error")
    if error is not None and not _safe_error_code(error):
        raise RefusedError("invalid_receipt")


def _validate_precondition(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict):
        raise RefusedError("invalid_receipt")
    if set(value) == {"state"} and value.get("state") == "ABSENT":
        return
    if set(value) == {"sha256"} and _sha256(value.get("sha256")):
        return
    raise RefusedError("invalid_receipt")


def _validate_public_state(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != _STATE_FIELDS or not isinstance(value.get("exists"), bool):
        raise RefusedError("invalid_receipt")
    if value["exists"]:
        if (
            not isinstance(value.get("size"), int)
            or isinstance(value.get("size"), bool)
            or value["size"] < 0
            or value.get("mode") not in {384, 416, 420}
            or not _sha256(value.get("sha256"))
        ):
            raise RefusedError("invalid_receipt")
    elif any(value.get(field) is not None for field in ("size", "mode", "sha256")):
        raise RefusedError("invalid_receipt")


def _validate_recovery(value: Any, *, serialized: bytes) -> None:
    if not isinstance(value, dict) or set(value) != _RECOVERY_FIELDS:
        raise RefusedError("invalid_recovery")
    if next(content_findings(serialized), None) is not None:
        raise RefusedError("secret_like_recovery")
    if (
        value.get("protocol") != "MCF_WORKSPACE_RECOVERY_V1"
        or not _safe_identifier(value.get("request_id"))
        or not _sha256(value.get("request_digest"))
        or not _safe_identifier(value.get("grant_id"))
        or value.get("path") != "G2B-PILOT.txt"
        or value.get("resolution") not in _RECOVERY_RESOLUTIONS
        or not isinstance(value.get("active"), bool)
        or not isinstance(value.get("snapshot"), bool)
    ):
        raise RefusedError("invalid_recovery")
    _validate_expected_state(value.get("expected_after"))
    _validate_exact_state(value.get("before"))
    if value.get("after") is not None:
        _validate_exact_state(value.get("after"))
    if value.get("observation") is not None:
        _validate_exact_state(value.get("observation"))
    if value.get("rollback_observation") is not None:
        _validate_exact_state(value.get("rollback_observation"))
    _validate_receipt_context(value.get("receipt_context"))
    if value["resolution"] == "PREPARED" and value.get("after") is not None:
        raise RefusedError("invalid_recovery")
    if value["resolution"] == "ROLLED_BACK" and value["active"] is not False:
        raise RefusedError("invalid_recovery")
    expected_active = value["resolution"] not in {"REVERTED", "ROLLED_BACK"}
    if value["active"] is not expected_active:
        raise RefusedError("invalid_recovery")
    if value["resolution"] == "APPLIED":
        if value["after"] is None or not _matches_expected_state(
            value["after"], value["expected_after"]
        ):
            raise RefusedError("invalid_recovery")
    if value["resolution"] in {"PREPARED", "REVERTED"} and value["after"] is not None:
        raise RefusedError("invalid_recovery")
    if value["snapshot"] is not value["before"]["exists"]:
        raise RefusedError("invalid_recovery")
    if not _workspace_recovery_name(value.get("workspace_recovery_name")):
        raise RefusedError("invalid_recovery")


def _validate_recovery_transition(current: dict[str, Any], updated: dict[str, Any]) -> None:
    immutable_fields = {
        "protocol",
        "request_id",
        "request_digest",
        "grant_id",
        "path",
        "expected_after",
        "before",
        "snapshot",
        "receipt_context",
    }
    if any(current[field] != updated[field] for field in immutable_fields):
        raise RefusedError("invalid_recovery_transition")
    if current["after"] is not None and updated["after"] != current["after"]:
        raise RefusedError("invalid_recovery_transition")
    if current["after"] is None and updated["after"] is not None:
        if updated["resolution"] != "APPLIED":
            raise RefusedError("invalid_recovery_transition")
        if not _matches_expected_state(updated["after"], current["expected_after"]):
            raise RefusedError("invalid_recovery_transition")
    if current["workspace_recovery_name"] is not None and updated["workspace_recovery_name"] not in {
        current["workspace_recovery_name"],
        None,
    }:
        raise RefusedError("invalid_recovery_transition")
    transitions = {
        "PREPARED": {"PREPARED", "APPLIED", "REVERTED", "INDETERMINATE"},
        "APPLIED": {"APPLIED", "INDETERMINATE", "ROLLED_BACK"},
        "INDETERMINATE": {"INDETERMINATE", "ROLLED_BACK"},
        "REVERTED": {"REVERTED"},
        "ROLLED_BACK": {"ROLLED_BACK"},
    }
    if updated["resolution"] not in transitions[current["resolution"]]:
        raise RefusedError("invalid_recovery_transition")
    expected_active = updated["resolution"] not in {"REVERTED", "ROLLED_BACK"}
    if updated["active"] is not expected_active:
        raise RefusedError("invalid_recovery_transition")


def _matches_expected_state(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return all(actual.get(field) == expected.get(field) for field in _EXPECTED_STATE_FIELDS)


def _validate_receipt_context(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != _RECEIPT_CONTEXT_FIELDS:
        raise RefusedError("invalid_recovery")
    if (
        value.get("mission_id") != "CONTROL-BRIDGE-G2B-PILOT"
        or value.get("declared_actor") != "MESTRE_MCF"
        or value.get("authority") != "LEANDRO"
        or value.get("operation") != "workspace.write"
        or not _timestamp(value.get("started_at"))
    ):
        raise RefusedError("invalid_recovery")
    principal = value.get("transport_principal")
    if not isinstance(principal, dict) or set(principal) != _PRINCIPAL_FIELDS:
        raise RefusedError("invalid_recovery")
    if (
        not _safe_identifier(principal.get("login"))
        or not isinstance(principal.get("actor_id"), int)
        or isinstance(principal.get("actor_id"), bool)
        or principal["actor_id"] < 1
    ):
        raise RefusedError("invalid_recovery")
    project = value.get("project")
    if project != {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"}:
        raise RefusedError("invalid_recovery")
    _validate_precondition(value.get("precondition"))


def _validate_expected_state(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != _EXPECTED_STATE_FIELDS:
        raise RefusedError("invalid_recovery")
    if value.get("exists") is not True:
        raise RefusedError("invalid_recovery")
    for field in ("size", "mode", "uid"):
        if (
            not isinstance(value.get(field), int)
            or isinstance(value.get(field), bool)
            or value[field] < 0
        ):
            raise RefusedError("invalid_recovery")
    if value["mode"] not in {384, 416, 420} or not _sha256(value.get("sha256")):
        raise RefusedError("invalid_recovery")


def _validate_exact_state(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != _EXACT_STATE_FIELDS:
        raise RefusedError("invalid_recovery")
    if not isinstance(value.get("exists"), bool):
        raise RefusedError("invalid_recovery")
    if value["exists"]:
        integer_fields = ("size", "mode", "uid", "device", "inode")
        if any(
            not isinstance(value.get(field), int)
            or isinstance(value.get(field), bool)
            or value[field] < 0
            for field in integer_fields
        ):
            raise RefusedError("invalid_recovery")
        if value["mode"] not in {384, 416, 420} or not _sha256(value.get("sha256")):
            raise RefusedError("invalid_recovery")
    elif any(
        value.get(field) is not None
        for field in ("size", "mode", "uid", "device", "inode", "sha256")
    ):
        raise RefusedError("invalid_recovery")


def _encode_json(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise RefusedError("invalid_state_value") from None
    if len(encoded) > _MAX_STATE_FILE_BYTES:
        raise RefusedError("state_file_too_large")
    return encoded


def _decode_json_object(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RefusedError(code) from None
    if not isinstance(value, dict):
        raise RefusedError(code)
    return value


def _hashed_name(identifier: str) -> str:
    if not _safe_identifier(identifier):
        raise RefusedError("invalid_state_identifier")
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest() + ".json"


def _hashed_state_filename(value: str) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 69
        and value.endswith(".json")
        and all(character in "0123456789abcdef" for character in value[:-5])
    )


def _state_temporary_name(value: str) -> bool:
    prefix = ".g2b-state-"
    suffix = ".tmp"
    if not value.startswith(prefix) or not value.endswith(suffix):
        return False
    token = value[len(prefix) : -len(suffix)]
    return len(token) == 32 and all(character in "0123456789abcdef" for character in token)


def _workspace_recovery_name(value: Any) -> bool:
    if value is None:
        return True
    prefixes = (".g2b-write-", ".g2b-restore-", ".g2b-delete-")
    for prefix in prefixes:
        if value.startswith(prefix) and value.endswith(".tmp"):
            token = value[len(prefix) : -4]
            return len(token) == 32 and all(character in "0123456789abcdef" for character in token)
    return False


def _safe_identifier(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value.encode("utf-8")) <= 256 and "\x00" not in value


def _safe_error_code(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 64
        and all(character in _SAFE_CODE_CHARACTERS for character in value)
    )


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return _aware_datetime(parsed)


def _aware_datetime(value: Any) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def _write_all(fd: int, content: bytes) -> None:
    remaining = memoryview(content)
    while remaining:
        try:
            written = os.write(fd, remaining)
        except InterruptedError:
            continue
        if written <= 0:
            raise RefusedError("state_write_failed")
        remaining = remaining[written:]


def _receipt_audit_event(receipt: dict[str, Any], *, event: str | None = None) -> dict[str, Any]:
    return {
        "event": event or ("rollback" if receipt["operation"] == "rollback" else "write"),
        "request_id": receipt["request_id"],
        "request_digest": receipt["request_digest"],
        "grant_id": receipt["grant_id"],
        "operation": receipt["operation"],
        "status": receipt["status"],
        "error": receipt["error"],
        "at": receipt["finished_at"],
    }


def _rename_noreplace_state(directory_fd: int, source: str, destination: str) -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise RefusedError("atomic_rename_unsupported")
    renameat2.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    ]
    renameat2.restype = ctypes.c_int
    result = renameat2(
        directory_fd,
        os.fsencode(source),
        directory_fd,
        os.fsencode(destination),
        _RENAME_NOREPLACE,
    )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        raise FileExistsError(error_number, os.strerror(error_number))
    if error_number in _RENAME_UNSUPPORTED_ERRNOS:
        raise RefusedError("atomic_rename_unsupported")
    raise RefusedError("state_write_failed")
