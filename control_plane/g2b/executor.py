"""Fail-closed transaction coordinator for the bounded G2-B pilot."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any, Callable

from .errors import ConflictError, G2BError, RefusedError
from .grant import TransportPrincipal, load_grant, validate_grant_for_request
from .protocol import MutationRequest, Precondition, RESULT_PROTOCOL, parse_request
from .secret_policy import content_findings
from .state import RECEIPT_FIELDS, StateStore, canonical_request_digest
from .workspace import (
    MutationStateError,
    TargetState,
    atomic_delete,
    atomic_restore,
    atomic_write,
    inspect_target,
    reconcile_write_recovery,
)


_LOCK_TIMEOUT_SECONDS = 10
_RECOVERY_PROTOCOL = "MCF_WORKSPACE_RECOVERY_V1"
_PILOT_PATH = "G2B-PILOT.txt"
_MAX_RESULT_BYTES = 8192


PUBLIC_RESULT_FIELDS = RECEIPT_FIELDS
PUBLIC_RESULT_STATUSES = frozenset(
    {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK", "REVOKED"}
)
PUBLIC_RESULT_ERROR_CODES = frozenset(
    """
    absolute_path_refused active_mutation_exists atomic_rename_failed atomic_rename_unsupported
    atomic_write_failed audit_event_conflict audit_pending_conflict audit_pending_delete_failed
    audit_pending_identity_mismatch audit_pending_source_mismatch audit_pending_source_missing
    audit_repair_failed audit_write_failed binary_or_non_utf8 content_too_large
    delete_durability_indeterminate delete_recovery_blocked delete_recovery_failed
    delete_revert_durability_indeterminate delete_cleanup_failed execution_uid_mismatch
    executor_digest_mismatch executor_root_required final_target_indeterminate
    final_target_mismatch grant_actor_mismatch grant_content_too_large grant_missing
    grant_mission_mismatch grant_not_active grant_operation_mismatch grant_path_mismatch
    grant_principal_mismatch grant_project_mismatch grant_revoked internal_error
    internal_name_collision invalid_arguments invalid_audit_log invalid_audit_pending
    invalid_content invalid_content_limit invalid_declared_actor invalid_environment
    invalid_execution_uid invalid_expected_state invalid_grant invalid_grant_duration
    invalid_lock_timeout invalid_mission_id invalid_now invalid_original_request_id invalid_path
    invalid_precondition invalid_project invalid_protocol invalid_receipt invalid_receipt_operation
    invalid_receipt_schema invalid_recovery invalid_recovery_before_state
    invalid_recovery_expected_state invalid_recovery_name invalid_recovery_name_publisher
    invalid_recovery_operation invalid_recovery_phase_state invalid_recovery_transition
    invalid_relative_path invalid_request invalid_request_id invalid_revocation invalid_snapshot
    invalid_state_identifier invalid_state_value invalid_transport_principal lock_failed
    lock_timeout mutation_not_active mutation_reconciled_reverted mutation_state_indeterminate
    nested_path_refused original_mutation_not_found path_escape_refused precondition_mismatch
    receipt_already_exists receipt_identity_mismatch recovery_already_exists
    recovery_candidate_changed recovery_cleanup_failed recovery_identity_mismatch
    recovery_inspection_failed recovery_missing recovery_name_mismatch request_id_conflict
    request_must_be_object result_too_large root_execution_refused secret_like_content
    secret_like_receipt secret_like_recovery secret_like_revocation secret_like_snapshot
    snapshot_already_exists snapshot_delete_failed snapshot_mismatch snapshot_missing
    state_file_too_large state_read_failed state_temporary_cleanup_failed state_write_failed
    target_changed target_hardlink_refused target_inspection_failed target_mode_refused
    target_not_regular target_owner_mismatch target_read_failed target_symlink_refused
    tilde_path_refused unexpected_arguments_field unexpected_project_field
    unexpected_request_field unknown_operation unsafe_audit_event unsafe_audit_file
    unsafe_executor_bundle unsafe_grant_file unsafe_grant_mode unsafe_grant_owner
    unsafe_lock_file unsafe_state_directory unsafe_state_file unsafe_temporary_file
    workspace_changed workspace_inspection_failed workspace_mode_refused
    workspace_not_directory workspace_not_found workspace_open_failed
    workspace_owner_mismatch workspace_symlink_refused unsafe_state_mode
    write_cleanup_failed write_durability_indeterminate write_state_indeterminate
    write_recovery_blocked write_recovery_failed write_revert_cleanup_failed
    write_revert_durability_indeterminate restore_cleanup_failed
    restore_durability_indeterminate restore_state_indeterminate restore_recovery_blocked
    restore_recovery_failed restore_revert_cleanup_failed restore_revert_durability_indeterminate
    """.split()
)


@dataclass(frozen=True)
class PublicResultRule:
    """One immutable executor phase/outcome shape accepted at the public boundary."""

    phase: str
    operations: frozenset[str | None]
    status: str
    errors: frozenset[str | None]
    grant_context: str
    result_shape: str
    timestamp_shape: str = "instant"
    replayable: bool = False


_ALL_OPERATIONS = frozenset({"workspace.write", "rollback", "status", "revoke"})
_UNCORRELATED_OPERATION = frozenset({None})
_STATE_IO_REFUSED_ERRORS = frozenset(
    """
    atomic_rename_unsupported invalid_state_value state_file_too_large state_read_failed
    state_write_failed unsafe_state_directory unsafe_state_file unsafe_state_mode
    """.split()
)
_AUDIT_REFUSED_ERRORS = frozenset(
    """
    audit_event_conflict audit_pending_conflict audit_pending_delete_failed
    audit_pending_identity_mismatch audit_pending_source_mismatch audit_pending_source_missing
    audit_repair_failed audit_write_failed invalid_audit_log invalid_audit_pending
    unsafe_audit_event unsafe_audit_file
    """.split()
)
_RECEIPT_REFUSED_ERRORS = _STATE_IO_REFUSED_ERRORS | _AUDIT_REFUSED_ERRORS | frozenset(
    {
        "invalid_receipt", "invalid_receipt_operation", "invalid_receipt_schema",
        "receipt_already_exists", "receipt_identity_mismatch", "secret_like_receipt",
    }
)
_RECOVERY_REFUSED_ERRORS = _STATE_IO_REFUSED_ERRORS | frozenset(
    {
        "invalid_recovery", "invalid_recovery_transition", "recovery_already_exists",
        "recovery_identity_mismatch", "recovery_missing", "secret_like_recovery",
    }
)
_WRITE_SNAPSHOT_REFUSED_ERRORS = _STATE_IO_REFUSED_ERRORS | frozenset(
    {
        "invalid_snapshot", "secret_like_snapshot", "snapshot_already_exists",
        "snapshot_delete_failed",
    }
)
_ROLLBACK_SNAPSHOT_REFUSED_ERRORS = _STATE_IO_REFUSED_ERRORS | frozenset(
    {"secret_like_snapshot", "snapshot_delete_failed"}
)
_REVOCATION_REFUSED_ERRORS = _STATE_IO_REFUSED_ERRORS | _AUDIT_REFUSED_ERRORS | frozenset(
    {"invalid_revocation", "secret_like_revocation"}
)
_RECOVERY_READ_UPDATE_ERRORS = _STATE_IO_REFUSED_ERRORS | frozenset(
    {
        "invalid_recovery", "invalid_recovery_transition", "recovery_identity_mismatch",
        "recovery_missing", "secret_like_recovery",
    }
)
_HISTORICAL_RECONCILIATION_ERRORS = (
    _RECEIPT_REFUSED_ERRORS
    | _RECOVERY_READ_UPDATE_ERRORS
    | frozenset(
        {
            "invalid_now", "snapshot_delete_failed", "state_temporary_cleanup_failed",
        }
    )
)
_GRANT_REFUSED_ERRORS = frozenset(
    """
    executor_digest_mismatch executor_root_required grant_actor_mismatch grant_content_too_large
    grant_missing grant_mission_mismatch grant_not_active grant_operation_mismatch
    grant_path_mismatch grant_principal_mismatch grant_project_mismatch invalid_grant
    invalid_grant_duration unsafe_executor_bundle unsafe_grant_file
    unsafe_grant_mode unsafe_grant_owner
    """.split()
)
_BOOTSTRAP_REFUSED_ERRORS = frozenset(
    """
    execution_uid_mismatch invalid_execution_uid invalid_transport_principal
    invalid_now root_execution_refused
    """.split()
)
_REQUEST_VALIDATION_REFUSED_ERRORS = frozenset(
    """
    content_too_large invalid_arguments invalid_content invalid_declared_actor
    invalid_environment invalid_mission_id invalid_original_request_id invalid_path
    invalid_precondition invalid_project invalid_protocol invalid_request invalid_request_id
    request_must_be_object unexpected_arguments_field unexpected_project_field
    unexpected_request_field unknown_operation
    """.split()
)
_WORKSPACE_REFUSED_ERRORS = frozenset(
    """
    atomic_rename_failed atomic_rename_unsupported atomic_write_failed binary_or_non_utf8
    content_too_large internal_name_collision target_hardlink_refused target_inspection_failed
    target_mode_refused target_not_regular target_owner_mismatch target_read_failed
    target_symlink_refused unsafe_temporary_file workspace_inspection_failed
    workspace_mode_refused workspace_not_directory workspace_not_found workspace_open_failed
    workspace_owner_mismatch workspace_symlink_refused
    """.split()
)
_WRITE_MUTATION_ERRORS = frozenset(
    """
    final_target_indeterminate final_target_mismatch target_changed write_cleanup_failed
    write_durability_indeterminate write_recovery_blocked write_recovery_failed
    write_revert_cleanup_failed write_revert_durability_indeterminate write_state_indeterminate
    """.split()
)
_ROLLBACK_MUTATION_ERRORS = frozenset(
    """
    delete_cleanup_failed delete_durability_indeterminate delete_recovery_blocked
    delete_recovery_failed delete_revert_durability_indeterminate final_target_indeterminate
    final_target_mismatch restore_cleanup_failed restore_durability_indeterminate
    restore_recovery_blocked restore_recovery_failed restore_revert_cleanup_failed
    restore_revert_durability_indeterminate restore_state_indeterminate target_changed
    """.split()
)


PUBLIC_RESULT_CONTRACT = (
    PublicResultRule(
        "bootstrap", _UNCORRELATED_OPERATION, "REFUSED", _BOOTSTRAP_REFUSED_ERRORS,
        "absent", "uncorrelated", "optional_instant",
    ),
    PublicResultRule(
        "request_validation", _UNCORRELATED_OPERATION, "REFUSED",
        _REQUEST_VALIDATION_REFUSED_ERRORS, "absent", "uncorrelated",
    ),
    PublicResultRule(
        "state_setup", _ALL_OPERATIONS, "REFUSED",
        frozenset({"unsafe_lock_file", "unsafe_state_directory", "unsafe_state_mode"}),
        "absent", "stateless",
    ),
    PublicResultRule(
        "lock", _ALL_OPERATIONS, "REFUSED",
        frozenset({"lock_failed", "unsafe_lock_file"}), "absent", "stateless",
    ),
    PublicResultRule(
        "lock", _ALL_OPERATIONS, "TIMEOUT", frozenset({"lock_timeout"}),
        "absent", "stateless",
    ),
    PublicResultRule(
        "historical_reconciliation", _ALL_OPERATIONS, "REFUSED",
        _HISTORICAL_RECONCILIATION_ERRORS, "absent", "stateless",
    ),
    PublicResultRule(
        "grant", _ALL_OPERATIONS, "REFUSED", _GRANT_REFUSED_ERRORS,
        "absent", "stateless",
    ),
    PublicResultRule(
        "deduplication", _ALL_OPERATIONS, "CONFLICT", frozenset({"request_id_conflict"}),
        "absent", "stateless",
    ),
    PublicResultRule(
        "deduplication", _ALL_OPERATIONS, "REFUSED", _RECEIPT_REFUSED_ERRORS,
        "absent", "stateless",
    ),
    PublicResultRule(
        "revocation_check", _ALL_OPERATIONS, "REFUSED",
        _REVOCATION_REFUSED_ERRORS | frozenset({"grant_revoked"}), "absent", "stateless",
    ),
    PublicResultRule(
        "operation_escape", _ALL_OPERATIONS, "REFUSED", _RECEIPT_REFUSED_ERRORS,
        "absent", "stateless",
    ),
    PublicResultRule(
        "operation_escape", frozenset({"workspace.write", "rollback"}), "REFUSED",
        _RECOVERY_REFUSED_ERRORS, "absent", "stateless",
    ),
    PublicResultRule(
        "transient_internal", _UNCORRELATED_OPERATION, "FAILED",
        frozenset({"internal_error"}), "absent", "uncorrelated", "optional_instant",
    ),
    PublicResultRule(
        "transient_internal", _ALL_OPERATIONS, "FAILED", frozenset({"internal_error"}),
        "absent", "stateless",
    ),
    PublicResultRule(
        "operation_failure", _ALL_OPERATIONS, "REFUSED", _RECEIPT_REFUSED_ERRORS,
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", _ALL_OPERATIONS, "REFUSED", frozenset({"invalid_now"}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", _ALL_OPERATIONS, "FAILED", frozenset({"internal_error"}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"workspace.write"}), "REFUSED",
        _WORKSPACE_REFUSED_ERRORS
        | _RECOVERY_REFUSED_ERRORS
        | _WRITE_SNAPSHOT_REFUSED_ERRORS
        | frozenset({"recovery_name_mismatch", "secret_like_content"}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"workspace.write"}), "CONFLICT",
        frozenset({"active_mutation_exists", "target_changed", "workspace_changed"}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"rollback"}), "REFUSED",
        _WORKSPACE_REFUSED_ERRORS
        | _RECOVERY_REFUSED_ERRORS
        | _ROLLBACK_SNAPSHOT_REFUSED_ERRORS,
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"rollback"}), "CONFLICT",
        frozenset(
            {
                "mutation_not_active", "mutation_state_indeterminate",
                "original_mutation_not_found", "snapshot_mismatch", "snapshot_missing",
                "target_changed", "workspace_changed",
            }
        ), "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"revoke"}), "CONFLICT",
        frozenset({"active_mutation_exists"}), "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "operation_failure", frozenset({"revoke"}), "REFUSED",
        _RECOVERY_REFUSED_ERRORS | _REVOCATION_REFUSED_ERRORS,
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "write_inspected", frozenset({"workspace.write"}), "REFUSED",
        _WORKSPACE_REFUSED_ERRORS | frozenset({"secret_like_content"}),
        "present", "same_state", "ordered", True,
    ),
    PublicResultRule(
        "write_inspected", frozenset({"workspace.write"}), "CONFLICT",
        frozenset({"precondition_mismatch", "target_changed", "workspace_changed"}),
        "present", "same_state", "ordered", True,
    ),
    PublicResultRule(
        "write_mutation", frozenset({"workspace.write"}), "FAILED",
        _WRITE_MUTATION_ERRORS, "present", "write_mutation", "ordered", True,
    ),
    PublicResultRule(
        "rollback_mutation", frozenset({"rollback"}), "FAILED",
        _ROLLBACK_MUTATION_ERRORS, "present", "rollback_mutation", "ordered", True,
    ),
    PublicResultRule(
        "historical_recovery", frozenset({"workspace.write"}), "PASS", frozenset({None}),
        "present", "write_success", "ordered", True,
    ),
    PublicResultRule(
        "historical_recovery", frozenset({"workspace.write"}), "FAILED",
        frozenset({"mutation_reconciled_reverted"}), "present", "reconciled_reverted",
        "ordered", True,
    ),
    PublicResultRule(
        "historical_recovery", frozenset({"workspace.write"}), "FAILED",
        frozenset({"mutation_state_indeterminate"}), "present", "reconciled_indeterminate",
        "ordered", True,
    ),
    PublicResultRule(
        "write_success", frozenset({"workspace.write"}), "PASS", frozenset({None}),
        "present", "write_success", "ordered", True,
    ),
    PublicResultRule(
        "rollback_success", frozenset({"rollback"}), "ROLLED_BACK", frozenset({None}),
        "present", "rollback_success", "ordered", True,
    ),
    PublicResultRule(
        "status_success", frozenset({"status"}), "PASS", frozenset({None}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "revoke_success", frozenset({"revoke"}), "REVOKED", frozenset({None}),
        "present", "stateless", "ordered", True,
    ),
    PublicResultRule(
        "bounded_fallback", _UNCORRELATED_OPERATION, "FAILED",
        frozenset({"result_too_large"}), "absent", "uncorrelated", "none",
    ),
)


def _public_result(*, phase: str, value: dict[str, Any]) -> dict[str, Any]:
    """Return a phase-valid result or one fixed value-free internal fallback."""
    try:
        if not isinstance(value, dict) or set(value) != PUBLIC_RESULT_FIELDS:
            return _invalid_public_result()
        if value.get("replayed") is not False:
            return _invalid_public_result()
        if not any(
            _matches_public_result_rule(value, rule)
            for rule in PUBLIC_RESULT_CONTRACT
            if rule.phase == phase
        ):
            return _invalid_public_result()
    except Exception:
        return _invalid_public_result()
    return value


def _matches_public_result_rule(value: dict[str, Any], rule: PublicResultRule) -> bool:
    operation = value.get("operation")
    if (
        operation not in rule.operations
        or value.get("status") != rule.status
        or value.get("error") not in rule.errors
        or not _valid_public_identity(value, operation=operation)
        or not _valid_public_grant_context(value, rule.grant_context)
        or not _valid_public_timestamp_shape(value, rule.timestamp_shape)
        or not _matches_public_result_state_shape(value, rule.result_shape)
    ):
        return False
    return _matches_public_result_operation_shape(
        value, operation, rule.result_shape, rule.grant_context
    )


def _valid_public_identity(value: dict[str, Any], *, operation: Any) -> bool:
    if value.get("protocol") != RESULT_PROTOCOL:
        return False
    principal = value.get("transport_principal")
    if not _valid_public_principal(principal):
        return False
    if operation is None:
        return all(
            value.get(field) is None
            for field in (
                "request_id", "request_digest", "mission_id", "declared_actor", "project",
                "path", "precondition", "before", "after", "rollback_request_id",
                "revocation_request_id",
            )
        )
    if operation not in _ALL_OPERATIONS:
        return False
    project = value.get("project")
    return (
        _valid_request_id(value.get("request_id"))
        and _valid_sha256(value.get("request_digest"))
        and value.get("mission_id") == "CONTROL-BRIDGE-G2B-PILOT"
        and value.get("declared_actor") == "MESTRE_MCF"
        and _valid_public_project(project)
        and _valid_correlated_principal(principal)
        and _valid_public_precondition(value.get("precondition"), operation=operation)
        and _valid_public_state(value.get("before"))
        and _valid_public_state(value.get("after"))
    )


def _valid_public_grant_context(value: dict[str, Any], expected: str) -> bool:
    authority = value.get("authority")
    grant_id = value.get("grant_id")
    if expected == "absent":
        return authority is None and grant_id is None
    return expected == "present" and authority == "LEANDRO" and _valid_request_id(grant_id)


def _valid_public_timestamp_shape(value: dict[str, Any], shape: str) -> bool:
    started = _parse_public_timestamp(value.get("started_at"))
    finished = _parse_public_timestamp(value.get("finished_at"))
    if shape == "none":
        return value.get("started_at") is None and value.get("finished_at") is None
    if shape == "optional_instant":
        return (
            value.get("started_at") is None
            and value.get("finished_at") is None
        ) or (started is not None and finished == started)
    if started is None or finished is None:
        return False
    if shape == "instant":
        return finished == started
    return shape == "ordered" and finished >= started


def _matches_public_result_state_shape(value: dict[str, Any], shape: str) -> bool:
    before = value.get("before")
    after = value.get("after")
    error = value.get("error")
    if shape in {"uncorrelated", "stateless"}:
        return before is None and after is None
    if shape == "same_state":
        return before is not None and after == before
    if shape == "write_mutation":
        if before is None:
            return False
        if error == "final_target_indeterminate":
            return after is None
        return error != "final_target_mismatch" or after is not None
    if shape == "rollback_mutation":
        if not isinstance(before, dict) or before.get("exists") is not True:
            return False
        if error == "final_target_indeterminate":
            return after is None
        return error != "final_target_mismatch" or after is not None
    if shape == "reconciled_reverted":
        return before is not None and after == before
    if shape == "reconciled_indeterminate":
        return before is not None
    if shape == "write_success":
        return before is not None and after is not None
    if shape == "rollback_success":
        return isinstance(before, dict) and before.get("exists") is True and after is not None
    return False


def _matches_public_result_operation_shape(
    value: dict[str, Any],
    operation: str | None,
    result_shape: str,
    grant_context: str,
) -> bool:
    rollback_link = value.get("rollback_request_id")
    revocation_link = value.get("revocation_request_id")
    if operation is None:
        return value.get("path") is None and rollback_link is None and revocation_link is None
    if operation == "workspace.write":
        return (
            value.get("path") in (
                {_PILOT_PATH} if grant_context == "present" else {None, _PILOT_PATH}
            )
            and rollback_link is None
            and revocation_link is None
        )
    if operation == "rollback":
        expected_path = (
            _PILOT_PATH
            if result_shape in {"rollback_mutation", "rollback_success"}
            else None
        )
        return (
            value.get("path") == expected_path
            and _valid_request_id(rollback_link)
            and revocation_link is None
        )
    if operation == "status":
        return value.get("path") is None and rollback_link is None and revocation_link is None
    if operation == "revoke":
        expected_revocation = value.get("request_id") if value.get("status") == "REVOKED" else None
        return (
            value.get("path") is None
            and rollback_link is None
            and revocation_link == expected_revocation
        )
    return False


def _valid_public_principal(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"login", "actor_id"}:
        return False
    if value == {"login": None, "actor_id": None}:
        return True
    return _valid_correlated_principal(value)


def _valid_correlated_principal(value: dict[str, Any]) -> bool:
    login = value.get("login")
    actor_id = value.get("actor_id")
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"
    return (
        isinstance(login, str)
        and 1 <= len(login) <= 39
        and login[0] in allowed[:-1]
        and login[-1] in allowed[:-1]
        and all(character in allowed for character in login)
        and isinstance(actor_id, int)
        and not isinstance(actor_id, bool)
        and 0 < actor_id <= 2**63 - 1
    )


def _valid_public_project(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"tenant", "name", "environment"}:
        return False
    tenant = value.get("tenant")
    name = value.get("name")
    return (
        _valid_dns_label(tenant)
        and _valid_dns_label(name)
        and value.get("environment") in {"dev", "staging"}
    )


def _valid_dns_label(value: Any) -> bool:
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 63
        and value[0] in allowed[:-1]
        and value[-1] in allowed[:-1]
        and all(character in allowed for character in value)
    )


def _valid_public_precondition(value: Any, *, operation: str) -> bool:
    if operation != "workspace.write":
        return value is None
    if value == {"state": "ABSENT"}:
        return True
    return isinstance(value, dict) and set(value) == {"sha256"} and _valid_sha256(
        value.get("sha256")
    )


def _valid_public_state(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or set(value) != {"exists", "size", "mode", "sha256"}:
        return False
    if value.get("exists") is False:
        return all(value.get(field) is None for field in ("size", "mode", "sha256"))
    size = value.get("size")
    return (
        value.get("exists") is True
        and isinstance(size, int)
        and not isinstance(size, bool)
        and 0 <= size <= 65_536
        and value.get("mode") in {384, 416, 420}
        and _valid_sha256(value.get("sha256"))
    )


def _valid_request_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= 128
        and value[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        and all(character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" for character in value)
    )


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _parse_public_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not 1 <= len(value) <= 40:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _invalid_public_result() -> dict[str, Any]:
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": None,
        "request_digest": None,
        "mission_id": None,
        "declared_actor": None,
        "authority": None,
        "transport_principal": {"login": None, "actor_id": None},
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
        "error": "internal_error",
    }


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
    phase = "bootstrap"
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
        phase = "request_validation"
        request = parse_request(request_value)
        request_digest = canonical_request_digest(request_value)
        phase = "state_setup"
        store = StateStore(state_root, lock_path, expected_uid=expected_uid)
        phase = "lock"
        with store.exclusive_lock(timeout_seconds=_LOCK_TIMEOUT_SECONDS):
            phase = "historical_reconciliation"
            store.reconcile_abandoned_temporaries()
            _reconcile_prepared_recoveries(
                store,
                workspace_root=workspace_root,
                expected_uid=expected_uid,
                now=now,
            )
            phase = "grant"
            grant = load_grant(grant_path, now=started_at, installed_root=installed_root)
            validate_grant_for_request(grant, request, transport_principal)

            phase = "deduplication"
            existing = store.lookup_request(request.request_id)
            if existing is not None:
                if existing["request_digest"] != request_digest:
                    raise ConflictError("request_id_conflict")
                replay = dict(existing)
                replay["replayed"] = True
                return replay

            phase = "revocation_check"
            if store.is_revoked(grant.grant_id):
                raise RefusedError("grant_revoked")

            phase = "operation_escape"
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
            phase=phase,
        )
    except Exception:
        return _transient_result(
            request,
            request_digest=request_digest,
            transport_principal=transport_principal,
            started_at=started_at,
            status="FAILED",
            error="internal_error",
            phase="transient_internal",
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
            receipt = context.receipt(phase="status_success", status="PASS")
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
        phase: str,
        status: str,
        error: str | None = None,
        before: TargetState | None = None,
        after: TargetState | None = None,
        path: str | None = None,
        rollback_request_id: str | None = None,
        revocation_request_id: str | None = None,
    ) -> dict[str, Any]:
        return _public_result(phase=phase, value={
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
        })


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

    def publish_recovery_name(name: str) -> None:
        nonlocal recovery
        recovery = dict(recovery, workspace_recovery_name=name)
        store.update_recovery(recovery)

    try:
        outcome = atomic_write(
            workspace_root,
            request.path,
            request.content,
            precondition=request.precondition,
            expected_uid=expected_uid,
            max_content_bytes=context.grant.max_content_bytes,
            recovery_name_publisher=publish_recovery_name,
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
            workspace_recovery_name=_merge_recovery_name(
                recovery["workspace_recovery_name"], error.recovery_name
            ),
        )
        store.update_recovery(updated)
        receipt = context.receipt(
            phase="write_mutation",
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
            phase="write_inspected",
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
    receipt = context.receipt(
        phase="write_success", status="PASS", before=outcome.before, after=outcome.after
    )
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
    if recovery["resolution"] != "APPLIED" or recovery["after"] is None:
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
            workspace_recovery_name=recovery["workspace_recovery_name"],
        )
        store.update_recovery(updated)
        receipt = context.receipt(
            phase="rollback_mutation",
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
        phase="rollback_success",
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
        phase="revoke_success",
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
            workspace_recovery_name=_merge_recovery_name(
                recovery["workspace_recovery_name"], error.recovery_name
            ),
        )
        store.update_recovery(updated)
    receipt = context.receipt(
        phase=(
            "rollback_mutation"
            if context.request.operation == "rollback"
            else "write_mutation"
        ),
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
        phase="operation_failure",
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
        recovery = _reconcile_workspace_recovery(
            store,
            recovery,
            workspace_root=workspace_root,
            expected_uid=expected_uid,
        )
        if recovery["resolution"] in {"APPLIED", "REVERTED", "INDETERMINATE"}:
            _ensure_recovery_receipt(store, recovery, now=now)


def _reconcile_workspace_recovery(
    store: StateStore,
    recovery: dict[str, Any],
    *,
    workspace_root: Path,
    expected_uid: int,
) -> dict[str, Any]:
    if recovery["resolution"] not in {"PREPARED", "APPLIED", "INDETERMINATE"}:
        return recovery
    if recovery["resolution"] == "INDETERMINATE":
        return recovery

    def publish_recovery_name(name: str) -> None:
        nonlocal recovery
        recovery = dict(
            recovery,
            workspace_recovery_name=_merge_recovery_name(
                recovery["workspace_recovery_name"], name
            ),
        )
        store.update_recovery(recovery)

    try:
        expected = recovery["expected_after"]
        reconciled = reconcile_write_recovery(
            workspace_root,
            recovery["path"],
            phase=recovery["resolution"],
            published_name=recovery["workspace_recovery_name"],
            before=_target_state(recovery["before"]),
            committed_after=(
                None
                if recovery["after"] is None
                else _target_state(recovery["after"])
            ),
            expected_size=expected["size"],
            expected_mode=expected["mode"],
            expected_sha256=expected["sha256"],
            expected_uid=expected_uid,
            recovery_name_publisher=publish_recovery_name,
        )
    except G2BError:
        return _make_recovery_indeterminate(store, recovery, observed=None)
    observed = reconciled.target

    if recovery["resolution"] == "PREPARED":
        if reconciled.resolution == "REVERTED":
            if recovery["snapshot"]:
                store.delete_snapshot(recovery["request_id"])
            updated = dict(
                recovery,
                observation=_exact_state(observed),
                resolution="REVERTED",
                active=False,
            )
            store.update_recovery(updated)
            return updated
        if reconciled.resolution == "APPLIED":
            updated = dict(
                recovery,
                after=_exact_state(observed),
                observation=_exact_state(observed),
                resolution="APPLIED",
                active=True,
            )
            store.update_recovery(updated)
            return updated
        return _make_recovery_indeterminate(store, recovery, observed=observed)

    if recovery["resolution"] == "APPLIED":
        if reconciled.resolution == "INDETERMINATE" and reconciled.has_candidates:
            return _make_recovery_indeterminate(store, recovery, observed=observed)
        return recovery
    return _make_recovery_indeterminate(store, recovery, observed=observed)


def _make_recovery_indeterminate(
    store: StateStore,
    recovery: dict[str, Any],
    *,
    observed: TargetState | None,
) -> dict[str, Any]:
    if recovery["resolution"] == "INDETERMINATE":
        return recovery
    updated = dict(
        recovery,
        observation=_exact_state(observed),
        resolution="INDETERMINATE",
        active=True,
    )
    store.update_recovery(updated)
    return updated


def _merge_recovery_name(current: str | None, observed: str | None) -> str | None:
    if current is None:
        return observed
    if observed not in {None, current}:
        raise RefusedError("recovery_name_mismatch")
    return current


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
    receipt = _public_result(phase="historical_recovery", value={
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
    })
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
    return _public_result(phase="bounded_fallback", value={
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
    })


def _transient_result(
    request: MutationRequest | None,
    *,
    request_digest: str | None,
    transport_principal: TransportPrincipal,
    started_at: datetime | None,
    status: str,
    error: str,
    phase: str,
) -> dict[str, Any]:
    return _public_result(phase=phase, value={
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
    })
