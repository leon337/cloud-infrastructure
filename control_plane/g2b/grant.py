from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

from .errors import RefusedError
from .protocol import (
    MAX_CONTENT_BYTES,
    MUTATION_PROTOCOL,
    OPERATIONS,
    PILOT_DECLARED_ACTOR,
    PILOT_MISSION_ID,
    MutationRequest,
    ProjectKey,
)


_GRANT_FIELDS = frozenset(
    {
        "protocol",
        "grant_id",
        "enabled",
        "authority",
        "transport_principal_login",
        "transport_principal_id",
        "declared_actor",
        "mission_id",
        "project",
        "allowed_operations",
        "allowed_paths",
        "max_content_bytes",
        "max_active_mutations",
        "not_before",
        "not_after",
        "executor_sha256",
    }
)
_PILOT_PROJECT = ProjectKey("leon337", "g2a-smoke", "dev")
_PILOT_PATH = "G2B-PILOT.txt"


@dataclass(frozen=True)
class TransportPrincipal:
    login: str
    actor_id: int


@dataclass(frozen=True)
class Grant:
    grant_id: str
    authority: str
    principal: TransportPrincipal
    declared_actor: str
    mission_id: str
    project: ProjectKey
    allowed_operations: frozenset[str]
    allowed_paths: frozenset[str]
    max_content_bytes: int
    max_active_mutations: int
    not_before: datetime
    not_after: datetime
    executor_sha256: str


def load_grant(
    path: str | Path,
    now: datetime | None = None,
    installed_root: str | Path | None = None,
) -> Grant:
    grant_path = Path(path)
    _validate_grant_file(grant_path)
    try:
        raw = json.loads(grant_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise RefusedError("invalid_grant") from None
    grant = _parse_grant(raw)
    effective_now = _utc_now() if now is None else _normalize_now(now)
    if not grant.not_before <= effective_now < grant.not_after:
        raise RefusedError("grant_not_active")
    if installed_root is not None and canonical_bundle_sha256(installed_root) != grant.executor_sha256:
        raise RefusedError("executor_digest_mismatch")
    return grant


def validate_grant_for_request(
    grant: Grant,
    request: MutationRequest,
    transport_principal: TransportPrincipal,
) -> None:
    if transport_principal != grant.principal:
        raise RefusedError("grant_principal_mismatch")
    if request.declared_actor != grant.declared_actor:
        raise RefusedError("grant_actor_mismatch")
    if request.mission_id != grant.mission_id:
        raise RefusedError("grant_mission_mismatch")
    if request.project != grant.project:
        raise RefusedError("grant_project_mismatch")
    if request.operation not in grant.allowed_operations:
        raise RefusedError("grant_operation_mismatch")
    if request.path is not None and request.path not in grant.allowed_paths:
        raise RefusedError("grant_path_mismatch")
    if request.content is not None and len(request.content) > grant.max_content_bytes:
        raise RefusedError("grant_content_too_large")


def canonical_bundle_sha256(installed_root: str | Path) -> str:
    root = Path(installed_root)
    if root.is_symlink() or not root.is_dir():
        raise RefusedError("unsafe_executor_bundle")
    root = root.resolve()
    records: list[tuple[str, Path]] = []
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise RefusedError("unsafe_executor_bundle")
        try:
            metadata = os.stat(candidate, follow_symlinks=False)
        except OSError:
            raise RefusedError("unsafe_executor_bundle") from None
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise RefusedError("unsafe_executor_bundle")
        try:
            relative = candidate.relative_to(root).as_posix()
        except ValueError:
            raise RefusedError("unsafe_executor_bundle") from None
        if not relative or relative.startswith("../"):
            raise RefusedError("unsafe_executor_bundle")
        records.append((relative, candidate))

    digest = hashlib.sha256()
    for relative, candidate in sorted(records):
        try:
            content_digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        except OSError:
            raise RefusedError("unsafe_executor_bundle") from None
        digest.update(f"{content_digest}  {relative}\n".encode("utf-8"))
    return digest.hexdigest()


def _validate_grant_file(path: Path) -> None:
    try:
        metadata = os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        raise RefusedError("grant_missing") from None
    except OSError:
        raise RefusedError("unsafe_grant_file") from None
    if not stat.S_ISREG(metadata.st_mode):
        raise RefusedError("unsafe_grant_file")
    if metadata.st_uid != 0:
        raise RefusedError("unsafe_grant_owner")
    if stat.S_IMODE(metadata.st_mode) != 0o644:
        raise RefusedError("unsafe_grant_mode")


def _parse_grant(value: Any) -> Grant:
    if not isinstance(value, dict) or set(value) != _GRANT_FIELDS:
        raise RefusedError("invalid_grant")
    if value.get("protocol") != MUTATION_PROTOCOL or value.get("enabled") is not True:
        raise RefusedError("invalid_grant")
    if not isinstance(value.get("grant_id"), str) or not value["grant_id"]:
        raise RefusedError("invalid_grant")
    if value.get("authority") != "LEANDRO":
        raise RefusedError("invalid_grant")
    principal = _parse_principal(value)
    if value.get("declared_actor") != PILOT_DECLARED_ACTOR or value.get("mission_id") != PILOT_MISSION_ID:
        raise RefusedError("invalid_grant")
    if value.get("project") != {
        "tenant": _PILOT_PROJECT.tenant,
        "name": _PILOT_PROJECT.name,
        "environment": _PILOT_PROJECT.environment,
    }:
        raise RefusedError("invalid_grant")
    allowed_operations = _parse_exact_set(value.get("allowed_operations"), OPERATIONS)
    allowed_paths = _parse_exact_set(value.get("allowed_paths"), frozenset({_PILOT_PATH}))
    if value.get("max_content_bytes") != MAX_CONTENT_BYTES or isinstance(value.get("max_content_bytes"), bool):
        raise RefusedError("invalid_grant")
    if value.get("max_active_mutations") != 1 or isinstance(value.get("max_active_mutations"), bool):
        raise RefusedError("invalid_grant")
    not_before = _parse_timestamp(value.get("not_before"))
    not_after = _parse_timestamp(value.get("not_after"))
    if not_after - not_before != timedelta(hours=24):
        raise RefusedError("invalid_grant_duration")
    executor_sha256 = value.get("executor_sha256")
    if not _is_sha256(executor_sha256):
        raise RefusedError("invalid_grant")
    return Grant(
        grant_id=value["grant_id"],
        authority="LEANDRO",
        principal=principal,
        declared_actor=PILOT_DECLARED_ACTOR,
        mission_id=PILOT_MISSION_ID,
        project=_PILOT_PROJECT,
        allowed_operations=allowed_operations,
        allowed_paths=allowed_paths,
        max_content_bytes=MAX_CONTENT_BYTES,
        max_active_mutations=1,
        not_before=not_before,
        not_after=not_after,
        executor_sha256=executor_sha256,
    )


def _parse_principal(value: dict[str, Any]) -> TransportPrincipal:
    login, actor_id = value.get("transport_principal_login"), value.get("transport_principal_id")
    if not isinstance(login, str) or not login or not isinstance(actor_id, int) or isinstance(actor_id, bool) or actor_id < 1:
        raise RefusedError("invalid_grant")
    return TransportPrincipal(login=login, actor_id=actor_id)


def _parse_exact_set(value: Any, expected: frozenset[str]) -> frozenset[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise RefusedError("invalid_grant")
    result = frozenset(value)
    if result != expected or len(value) != len(expected):
        raise RefusedError("invalid_grant")
    return result


def _parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise RefusedError("invalid_grant")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise RefusedError("invalid_grant") from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RefusedError("invalid_grant")
    return parsed.astimezone(timezone.utc)


def _normalize_now(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise RefusedError("invalid_now")
    return value.astimezone(timezone.utc)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(character in "0123456789abcdef" for character in value)
