"""Fail-closed transaction coordinator for the bounded G2-B pilot."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Callable

from scripts.check_repository_secrets import content_findings

from .errors import ConflictError, G2BError, RefusedError
from .grant import TransportPrincipal, load_grant, validate_grant_for_request
from .protocol import MutationRequest, Precondition, RESULT_PROTOCOL, parse_request
from .state import RECEIPT_FIELDS, StateStore, canonical_request_digest
from .workspace import (
    MutationStateError,
    TargetState,
    atomic_delete,
    atomic_restore,
    atomic_write,
    inspect_target,
)


_LOCK_TIMEOUT_SECONDS = 10
_RECOVERY_PROTOCOL = "MCF_WORKSPACE_RECOVERY_V1"
_PILOT_PATH = "G2B-PILOT.txt"
_MAX_RESULT_BYTES = 8192


def execute_request(
    request_value: dict[str, Any],
    *,
    transport_principal: TransportPrincipal,
    grant_path: Path,
    installed_root: Path,
    workspace_root: Path,
    state_root: Path,
    lock_path: Path,
    expected_uid: int,
    now: Callable[[], datetime],
) -> dict[str, Any]:
    """Validate and execute one bounded request, returning only safe fields."""
    result = _execute_request_impl(
        request_value,
        transport_principal=transport_principal,
        grant_path=grant_path,
        installed_root=installed_root,
        workspace_root=workspace_root,
        state_root=state_root,
        lock_path=lock_path,
        expected_uid=expected_uid,
        now=now,
    )
    return _bounded_result(result, transport_principal=transport_principal)


def _execute_request_impl(
    request_value: dict[str, Any],
    *,
    transport_principal: TransportPrincipal,
    grant_path: Path,
    installed_root: Path,
    workspace_root: Path,
    state_root: Path,
    lock_path: Path,
    expected_uid: int,
    now: Callable[[], datetime],
) -> dict[str, Any]:
    started_at: datetime | None = None
    request: MutationRequest | None = None
    request_digest: str | None = None
    try:
        effective_uid = os.geteuid()
        if effective_uid == 0 or expected_uid == 0:
            raise RefusedError("root_execution_refused")
        if not isinstance(expected_uid, int) or isinstance(expected_uid, bool) or expected_uid < 1:
            raise RefusedError("invalid_execution_uid")
        if not _valid_transport_principal(transport_principal):
            raise RefusedError("invalid_transport_principal")
        if effective_uid != expected_uid:
            raise RefusedError("execution_uid_mismatch")
        started_at = _read_clock(now)
        request = parse_request(request_value)
        request_digest = canonical_request_digest(request_value)
        store = StateStore(state_root, lock_path, expected_uid=expected_uid)
        with store.exclusive_lock(timeout_seconds=_LOCK_TIMEOUT_SECONDS):
            store.reconcile_abandoned_temporaries()
            _reconcile_prepared_recoveries(
                store,
                workspace_root=workspace_root,
                expected_uid=expected_uid,
                now=now,
            )
            grant = load_grant(grant_path, now=started_at, installed_root=installed_root)
            validate_grant_for_request(grant, request, transport_principal)

            existing = store.lookup_request(request.request_id)
            if existing is not None:
                if existing["request_digest"] != request_digest:
                    raise ConflictError("request_id_conflict")
                replay = dict(existing)
                replay["replayed"] = True
                return replay

            if store.is_revoked(grant.grant_id):
                raise RefusedError("grant_revoked")

            return _execute_locked(
                request,
                request_digest=request_digest,
                transport_principal=transport_principal,
                grant=grant,
                workspace_root=workspace_root,
                store=store,
                expected_uid=expected_uid,
                started_at=started_at,
                now=now,
            )
    except G2BError as error:
        return _transient_result(
            request,
            request_digest=request_digest,
            transport_principal=transport_principal,
            started_at=started_at,
            status=error.status,
            error=error.code,
        )
    except Exception:
        return _transient_result(
            request,
            request_digest=request_digest,
            transport_principal=transport_principal,
            started_at=started_at,
            status="FAILED",
            error="internal_error",
        )


def _execute_locked(
    request: MutationRequest,
    *,
    request_digest: str,
    transport_principal: TransportPrincipal,
    grant: Any,
    workspace_root: Path,
    store: StateStore,
    expected_uid: int,
    started_at: datetime,
    now: Callable[[], datetime],
) -> dict[str, Any]:
    context = _ReceiptContext(
        request=request,
        request_digest=request_digest,
        transport_principal=transport_principal,
        grant=grant,
        started_at=started_at,
        now=now,
    )
    try:
        if request.operation == "workspace.write":
            return _execute_write(
                context,
                workspace_root=workspace_root,
                store=store,
                expected_uid=expected_uid,
            )
        if request.operation == "rollback":
            return _execute_rollback(
                context,
                workspace_root=workspace_root,
                store=store,
                expected_uid=expected_uid,
            )
        if request.operation == "revoke":
            return _execute_revoke(context, store=store)
        if request.operation == "status":
            receipt = context.receipt(status="PASS")
            _persist_receipt(store, receipt)
            return receipt
        raise RefusedError("unknown_operation")
    except MutationStateError as error:
        return _record_mutation_state_error(context, error=error, store=store)
    except G2BError as error:
        return _record_failure(context, status=error.status, error=error.code, store=store)
    except Exception:
        _mark_recovery_indeterminate(store, request.request_id)
        return _record_failure(context, status="FAILED", error="internal_error", store=store)


class _ReceiptContext:
    def __init__(
        self,
        *,
        request: MutationRequest,
        request_digest: str,
        transport_principal: TransportPrincipal,
        grant: Any,
        started_at: datetime,
        now: Callable[[], datetime],
    ) -> None:
        self.request = request
        self.request_digest = request_digest
        self.transport_principal = transport_principal
        self.grant = grant
        self.started_at = started_at
        self.now = now

    def receipt(
        self,
        *,
        status: str,
        error: str | None = None,
        before: TargetState | None = None,
        after: TargetState | None = None,
        path: str | None = None,
        rollback_request_id: str | None = None,
        revocation_request_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "protocol": RESULT_PROTOCOL,
            "request_id": self.request.request_id,
            "request_digest": self.request_digest,
            "mission_id": self.request.mission_id,
            "declared_actor": self.request.declared_actor,
            "authority": self.grant.authority,
            "transport_principal": {
                "login": self.transport_principal.login,
                "actor_id": self.transport_principal.actor_id,
            },
            "grant_id": self.grant.grant_id,
            "project": {
                "tenant": self.request.project.tenant,
                "name": self.request.project.name,
                "environment": self.request.project.environment,
            },
            "operation": self.request.operation,
            "path": self.request.path if path is None else path,
            "started_at": self.started_at.isoformat(),
            "finished_at": _read_clock(self.now).isoformat(),
            "precondition": _public_precondition(self.request.precondition),
            "before": _public_state(before),
            "after": _public_state(after),
            "status": status,
            "replayed": False,
            "rollback_request_id": rollback_request_id,
            "revocation_request_id": revocation_request_id,
            "error": error,
        }


def _execute_write(
    context: _ReceiptContext,
    *,
    workspace_root: Path,
    store: StateStore,
    expected_uid: int,
) -> dict[str, Any]:
    request = context.request
    assert request.path is not None
    assert request.content is not None
    assert request.precondition is not None
    if store.active_recoveries():
        raise ConflictError("active_mutation_exists")

    before = inspect_target(workspace_root, request.path, expected_uid=expected_uid)
    snapshot = before.exists
    prior: bytes | None = None
    if before.exists:
        prior = _read_exact_target(
            workspace_root,
            request.path,
            expected=before,
            expected_uid=expected_uid,
        )
    recovery = _recovery_value(
        context,
        before=before,
        after=None,
        resolution="PREPARED",
        active=True,
        snapshot=snapshot,
        expected_uid=expected_uid,
    )
    try:
        store.prepare_recovery(recovery)
        if prior is not None:
            store.save_snapshot(request.request_id, prior)
    except Exception:
        if prior is not None:
            try:
                store.delete_snapshot(request.request_id)
            except G2BError:
                pass
        existing = store.lookup_recovery(request.request_id)
        if existing is not None and existing["resolution"] == "PREPARED":
            store.update_recovery(
                dict(
                    existing,
                    observation=_exact_state(before),
                    resolution="REVERTED",
                    active=False,
                )
            )
        raise

    try:
        outcome = atomic_write(
            workspace_root,
            request.path,
            request.content,
            precondition=request.precondition,
            expected_uid=expected_uid,
            max_content_bytes=context.grant.max_content_bytes,
        )
    except MutationStateError as error:
        observed = _exact_state(error.observed_after)
        if error.resolution == "APPLIED" and _matches_expected_target(
            error.observed_after,
            recovery["expected_after"],
        ):
            resolution = "APPLIED"
            committed_after = observed
            active = True
        elif error.resolution == "REVERTED":
            if snapshot:
                store.delete_snapshot(request.request_id)
            resolution = "REVERTED"
            committed_after = None
            active = False
        else:
            resolution = "INDETERMINATE"
            committed_after = None
            active = True
        updated = dict(
            recovery,
            after=committed_after,
            observation=observed,
            resolution=resolution,
            active=active,
            workspace_recovery_name=error.recovery_name,
        )
        store.update_recovery(updated)
        receipt = context.receipt(
            status="FAILED",
            error=error.code,
            before=error.before,
            after=error.observed_after,
            path=error.path,
        )
        _persist_receipt(store, receipt)
        return receipt
    except G2BError as error:
        if snapshot:
            store.delete_snapshot(request.request_id)
        reverted = dict(
            recovery,
            observation=_exact_state(before),
            resolution="REVERTED",
            active=False,
        )
        store.update_recovery(reverted)
        receipt = context.receipt(
            status=error.status,
            error=error.code,
            before=before,
            after=before,
        )
        _persist_receipt(store, receipt)
        return receipt

    updated = dict(
        recovery,
        after=_exact_state(outcome.after),
        observation=_exact_state(outcome.after),
        resolution="APPLIED",
        active=True,
    )
    store.update_recovery(updated)
    receipt = context.receipt(status="PASS", before=outcome.before, after=outcome.after)
    _persist_receipt(store, receipt)
    return receipt


def _execute_rollback(
    context: _ReceiptContext,
    *,
    workspace_root: Path,
    store: StateStore,
    expected_uid: int,
) -> dict[str, Any]:
    request = context.request
    assert request.original_request_id is not None
    recovery = store.lookup_recovery(request.original_request_id)
    if recovery is None:
        raise ConflictError("original_mutation_not_found")
    if recovery["grant_id"] != context.grant.grant_id or recovery["active"] is not True:
        raise ConflictError("mutation_not_active")
    if recovery["after"] is None:
        raise ConflictError("mutation_state_indeterminate")

    expected_after = _target_state(recovery["after"])
    original_before = _target_state(recovery["before"])
    try:
        if original_before.exists:
            snapshot = store.load_snapshot(request.original_request_id)
            if snapshot is None:
                raise ConflictError("snapshot_missing")
            if not _snapshot_matches_before(snapshot, recovery["before"]):
                raise ConflictError("snapshot_mismatch")
            outcome = atomic_restore(
                workspace_root,
                recovery["path"],
                snapshot,
                expected_current=expected_after,
                restore_mode=original_before.mode,
                expected_uid=expected_uid,
                max_content_bytes=context.grant.max_content_bytes,
            )
            rolled_back_after = outcome.after
        else:
            rolled_back_after = atomic_delete(
                workspace_root,
                recovery["path"],
                expected_current=expected_after,
                expected_uid=expected_uid,
            )
    except MutationStateError as error:
        resolution = "INDETERMINATE" if error.resolution == "INDETERMINATE" else recovery["resolution"]
        updated = dict(
            recovery,
            rollback_observation=_exact_state(error.observed_after),
            resolution=resolution,
            active=True,
            workspace_recovery_name=(
                error.recovery_name or recovery["workspace_recovery_name"]
            ),
        )
        store.update_recovery(updated)
        receipt = context.receipt(
            status="FAILED",
            error=error.code,
            before=error.before,
            after=error.observed_after,
            path=recovery["path"],
            rollback_request_id=request.original_request_id,
        )
        _persist_receipt(store, receipt)
        return receipt

    resolved = dict(recovery, resolution="ROLLED_BACK", active=False)
    store.update_recovery(resolved)
    receipt = context.receipt(
        status="ROLLED_BACK",
        before=expected_after,
        after=rolled_back_after,
        path=recovery["path"],
        rollback_request_id=request.original_request_id,
    )
    _persist_receipt(store, receipt)
    if recovery["snapshot"]:
        store.delete_snapshot(request.original_request_id)
    return receipt


def _execute_revoke(context: _ReceiptContext, *, store: StateStore) -> dict[str, Any]:
    if store.active_recoveries():
        raise ConflictError("active_mutation_exists")
    revoked_at = _read_clock(context.now)
    store.revoke(
        context.grant.grant_id,
        actor=context.request.declared_actor,
        at=revoked_at,
    )
    receipt = context.receipt(
        status="REVOKED",
        revocation_request_id=context.request.request_id,
    )
    _persist_receipt(store, receipt)
    return receipt


def _record_mutation_state_error(
    context: _ReceiptContext,
    *,
    error: MutationStateError,
    store: StateStore,
) -> dict[str, Any]:
    recovery = store.lookup_recovery(context.request.request_id)
    if recovery is not None:
        if error.resolution == "APPLIED" and _matches_expected_target(
            error.observed_after,
            recovery["expected_after"],
        ):
            resolution = "APPLIED"
            after = _exact_state(error.observed_after)
            active = True
        elif error.resolution == "REVERTED":
            resolution = "REVERTED"
            after = recovery["after"]
            active = False
        else:
            resolution = "INDETERMINATE"
            after = recovery["after"]
            active = True
        updated = dict(
            recovery,
            after=after,
            observation=_exact_state(error.observed_after),
            resolution=resolution,
            active=active,
            workspace_recovery_name=error.recovery_name,
        )
        store.update_recovery(updated)
    receipt = context.receipt(
        status="FAILED",
        error=error.code,
        before=error.before,
        after=error.observed_after,
        path=error.path,
        rollback_request_id=context.request.original_request_id,
    )
    _persist_receipt(store, receipt)
    return receipt


def _record_failure(
    context: _ReceiptContext,
    *,
    status: str,
    error: str,
    store: StateStore,
) -> dict[str, Any]:
    receipt = context.receipt(
        status=status,
        error=error,
        rollback_request_id=context.request.original_request_id,
    )
    _persist_receipt(store, receipt)
    return receipt


def _store_receipt(store: StateStore, receipt: dict[str, Any]) -> None:
    if receipt["operation"] == "rollback":
        store.record_rollback(receipt)
    else:
        store.record_write(receipt)


def _persist_receipt(store: StateStore, receipt: dict[str, Any]) -> None:
    try:
        _store_receipt(store, receipt)
    except G2BError:
        existing = store.lookup_request(receipt["request_id"])
        if existing == receipt:
            return
        raise


def _mark_recovery_indeterminate(store: StateStore, request_id: str) -> None:
    try:
        recovery = store.lookup_recovery(request_id)
        if recovery is not None and recovery["active"] is True and recovery["resolution"] == "PREPARED":
            store.update_recovery(dict(recovery, resolution="INDETERMINATE"))
    except G2BError:
        pass


def _recovery_value(
    context: _ReceiptContext,
    *,
    before: TargetState,
    after: TargetState | None,
    resolution: str,
    active: bool,
    snapshot: bool,
    expected_uid: int,
) -> dict[str, Any]:
    assert context.request.path is not None
    assert context.request.content is not None
    target_mode = before.mode if before.exists else 0o644
    return {
        "protocol": _RECOVERY_PROTOCOL,
        "request_id": context.request.request_id,
        "request_digest": context.request_digest,
        "grant_id": context.grant.grant_id,
        "path": context.request.path,
        "expected_after": {
            "exists": True,
            "size": len(context.request.content),
            "mode": target_mode,
            "uid": expected_uid,
            "sha256": hashlib.sha256(context.request.content).hexdigest(),
        },
        "before": _exact_state(before),
        "after": _exact_state(after),
        "resolution": resolution,
        "active": active,
        "snapshot": snapshot,
        "workspace_recovery_name": None,
        "observation": None,
        "rollback_observation": None,
        "receipt_context": {
            "mission_id": context.request.mission_id,
            "declared_actor": context.request.declared_actor,
            "authority": context.grant.authority,
            "transport_principal": {
                "login": context.transport_principal.login,
                "actor_id": context.transport_principal.actor_id,
            },
            "project": {
                "tenant": context.request.project.tenant,
                "name": context.request.project.name,
                "environment": context.request.project.environment,
            },
            "operation": context.request.operation,
            "precondition": _public_precondition(context.request.precondition),
            "started_at": context.started_at.isoformat(),
        },
    }


def _reconcile_prepared_recoveries(
    store: StateStore,
    *,
    workspace_root: Path,
    expected_uid: int,
    now: Callable[[], datetime],
) -> None:
    for recovery in store.recoveries():
        if recovery["resolution"] == "PREPARED":
            try:
                observed = inspect_target(
                    workspace_root,
                    recovery["path"],
                    expected_uid=expected_uid,
                )
            except G2BError:
                observed = None
            if observed is not None and _exact_state(observed) == recovery["before"]:
                if recovery["snapshot"]:
                    store.delete_snapshot(recovery["request_id"])
                recovery = dict(
                    recovery,
                    observation=_exact_state(observed),
                    resolution="REVERTED",
                    active=False,
                )
            elif _matches_expected_target(observed, recovery["expected_after"]):
                recovery = dict(
                    recovery,
                    after=_exact_state(observed),
                    observation=_exact_state(observed),
                    resolution="APPLIED",
                    active=True,
                )
            else:
                recovery = dict(
                    recovery,
                    observation=_exact_state(observed),
                    resolution="INDETERMINATE",
                    active=True,
                )
            store.update_recovery(recovery)
        if recovery["resolution"] in {"APPLIED", "REVERTED", "INDETERMINATE"}:
            _ensure_recovery_receipt(store, recovery, now=now)


def _ensure_recovery_receipt(
    store: StateStore,
    recovery: dict[str, Any],
    *,
    now: Callable[[], datetime],
) -> None:
    existing = store.lookup_request(recovery["request_id"])
    if existing is not None:
        return
    context = recovery["receipt_context"]
    if recovery["resolution"] == "APPLIED":
        status = "PASS"
        error = None
        after = recovery["after"]
    elif recovery["resolution"] == "REVERTED":
        status = "FAILED"
        error = "mutation_reconciled_reverted"
        after = recovery["before"]
    else:
        status = "FAILED"
        error = "mutation_state_indeterminate"
        after = recovery["observation"]
    receipt = {
        "protocol": RESULT_PROTOCOL,
        "request_id": recovery["request_id"],
        "request_digest": recovery["request_digest"],
        "mission_id": context["mission_id"],
        "declared_actor": context["declared_actor"],
        "authority": context["authority"],
        "transport_principal": context["transport_principal"],
        "grant_id": recovery["grant_id"],
        "project": context["project"],
        "operation": context["operation"],
        "path": recovery["path"],
        "started_at": context["started_at"],
        "finished_at": _read_clock(now).isoformat(),
        "precondition": context["precondition"],
        "before": _public_state_dict(recovery["before"]),
        "after": _public_state_dict(after),
        "status": status,
        "replayed": False,
        "rollback_request_id": None,
        "revocation_request_id": None,
        "error": error,
    }
    _persist_receipt(store, receipt)


def _public_precondition(value: Precondition | None) -> dict[str, str] | None:
    if value is None:
        return None
    if value.state is not None:
        return {"state": value.state}
    assert value.sha256 is not None
    return {"sha256": value.sha256}


def _public_state(value: TargetState | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "exists": value.exists,
        "size": value.size,
        "mode": value.mode,
        "sha256": value.sha256,
    }


def _public_state_dict(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "exists": value["exists"],
        "size": value["size"],
        "mode": value["mode"],
        "sha256": value["sha256"],
    }


def _exact_state(value: TargetState | None) -> dict[str, Any] | None:
    if value is None:
        return None
    return {
        "exists": value.exists,
        "size": value.size,
        "mode": value.mode,
        "uid": value.uid,
        "device": value.device,
        "inode": value.inode,
        "sha256": value.sha256,
    }


def _target_state(value: dict[str, Any]) -> TargetState:
    return TargetState(
        exists=value["exists"],
        size=value["size"],
        mode=value["mode"],
        uid=value["uid"],
        device=value["device"],
        inode=value["inode"],
        sha256=value["sha256"],
    )


def _matches_expected_target(value: TargetState | None, expected: dict[str, Any]) -> bool:
    if value is None:
        return False
    return (
        value.exists is True
        and value.size == expected["size"]
        and value.mode == expected["mode"]
        and value.uid == expected["uid"]
        and value.sha256 == expected["sha256"]
    )


def _snapshot_matches_before(snapshot: bytes, before: dict[str, Any]) -> bool:
    return (
        before["exists"] is True
        and len(snapshot) == before["size"]
        and hashlib.sha256(snapshot).hexdigest() == before["sha256"]
    )


def _read_exact_target(
    workspace_root: Path,
    relative_path: str,
    *,
    expected: TargetState,
    expected_uid: int,
) -> bytes:
    try:
        workspace_before = os.stat(workspace_root, follow_symlinks=False)
    except OSError:
        raise RefusedError("workspace_inspection_failed") from None
    if (
        not stat.S_ISDIR(workspace_before.st_mode)
        or workspace_before.st_uid != expected_uid
        or stat.S_IMODE(workspace_before.st_mode) & 0o022
    ):
        raise RefusedError("workspace_mode_refused")
    try:
        workspace_fd = os.open(
            workspace_root,
            os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC | os.O_NOFOLLOW,
        )
    except OSError:
        raise RefusedError("workspace_open_failed") from None
    try:
        opened_workspace = os.fstat(workspace_fd)
        if (opened_workspace.st_dev, opened_workspace.st_ino) != (
            workspace_before.st_dev,
            workspace_before.st_ino,
        ):
            raise ConflictError("workspace_changed")
        try:
            target_fd = os.open(
                relative_path,
                os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW,
                dir_fd=workspace_fd,
            )
        except OSError:
            raise ConflictError("target_changed") from None
        try:
            opened = os.fstat(target_fd)
            if _stat_identity(opened) != _target_identity(expected):
                raise ConflictError("target_changed")
            chunks: list[bytes] = []
            remaining = 65_537
            while remaining:
                chunk = os.read(target_fd, min(remaining, 65_536))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            content = b"".join(chunks)
            if len(content) > 65_536 or hashlib.sha256(content).hexdigest() != expected.sha256:
                raise ConflictError("target_changed")
            finished = os.fstat(target_fd)
            if _stat_identity(finished) != _target_identity(expected):
                raise ConflictError("target_changed")
        finally:
            os.close(target_fd)
        final_path = os.stat(relative_path, dir_fd=workspace_fd, follow_symlinks=False)
        if _stat_identity(final_path) != _target_identity(expected):
            raise ConflictError("target_changed")
    except OSError:
        raise ConflictError("target_changed") from None
    finally:
        os.close(workspace_fd)
    if next(content_findings(content), None) is not None:
        raise RefusedError("secret_like_content")
    return content


def _stat_identity(value: os.stat_result) -> tuple[Any, ...]:
    return (
        stat.S_ISREG(value.st_mode),
        value.st_size,
        stat.S_IMODE(value.st_mode),
        value.st_uid,
        value.st_dev,
        value.st_ino,
        value.st_nlink,
    )


def _target_identity(value: TargetState) -> tuple[Any, ...]:
    return (
        value.exists,
        value.size,
        value.mode,
        value.uid,
        value.device,
        value.inode,
        1,
    )


def _read_clock(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RefusedError("invalid_now")
    return value.astimezone(timezone.utc)


def _valid_transport_principal(value: Any) -> bool:
    if not isinstance(value, TransportPrincipal):
        return False
    login = value.login
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    return (
        isinstance(login, str)
        and 1 <= len(login) <= 39
        and login[0] in allowed[:-1]
        and login[-1] in allowed[:-1]
        and all(character in allowed for character in login)
        and isinstance(value.actor_id, int)
        and not isinstance(value.actor_id, bool)
        and 0 < value.actor_id <= 2**63 - 1
    )


def _safe_principal(value: Any) -> dict[str, Any]:
    if not _valid_transport_principal(value):
        return {"login": None, "actor_id": None}
    return {"login": value.login, "actor_id": value.actor_id}


def _bounded_result(
    result: dict[str, Any],
    *,
    transport_principal: TransportPrincipal,
) -> dict[str, Any]:
    try:
        encoded = json.dumps(
            result,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError):
        encoded = b""
    if set(result) == RECEIPT_FIELDS and 0 < len(encoded) <= _MAX_RESULT_BYTES:
        return result
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": None,
        "request_digest": None,
        "mission_id": None,
        "declared_actor": None,
        "authority": None,
        "transport_principal": _safe_principal(transport_principal),
        "grant_id": None,
        "project": None,
        "operation": None,
        "path": None,
        "started_at": None,
        "finished_at": None,
        "precondition": None,
        "before": None,
        "after": None,
        "status": "FAILED",
        "replayed": False,
        "rollback_request_id": None,
        "revocation_request_id": None,
        "error": "result_too_large",
    }


def _transient_result(
    request: MutationRequest | None,
    *,
    request_digest: str | None,
    transport_principal: TransportPrincipal,
    started_at: datetime | None,
    status: str,
    error: str,
) -> dict[str, Any]:
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": request.request_id if request is not None else None,
        "request_digest": request_digest,
        "mission_id": request.mission_id if request is not None else None,
        "declared_actor": request.declared_actor if request is not None else None,
        "authority": None,
        "transport_principal": _safe_principal(transport_principal),
        "grant_id": None,
        "project": (
            {
                "tenant": request.project.tenant,
                "name": request.project.name,
                "environment": request.project.environment,
            }
            if request is not None
            else None
        ),
        "operation": request.operation if request is not None else None,
        "path": (
            request.path
            if request is not None and request.path == _PILOT_PATH
            else None
        ),
        "started_at": started_at.isoformat() if started_at is not None else None,
        "finished_at": started_at.isoformat() if started_at is not None else None,
        "precondition": _public_precondition(request.precondition) if request is not None else None,
        "before": None,
        "after": None,
        "status": status,
        "replayed": False,
        "rollback_request_id": request.original_request_id if request is not None else None,
        "revocation_request_id": None,
        "error": error,
    }
