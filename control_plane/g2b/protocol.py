from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .errors import RefusedError


MUTATION_PROTOCOL = "MCF_WORKSPACE_MUTATION_V1"
RESULT_PROTOCOL = "MCF_WORKSPACE_MUTATION_RESULT_V1"
OPERATIONS = frozenset({"workspace.write", "rollback", "status", "revoke"})
MAX_CONTENT_BYTES = 65_536

PILOT_MISSION_ID = "CONTROL-BRIDGE-G2B-PILOT"
PILOT_DECLARED_ACTOR = "MESTRE_MCF"

_REQUEST_FIELDS = frozenset(
    {"protocol", "request_id", "mission_id", "declared_actor", "project", "operation", "arguments"}
)
_PROJECT_FIELDS = frozenset({"tenant", "name", "environment"})
_WRITE_ARGUMENT_FIELDS = frozenset({"path", "content", "precondition"})
_ROLLBACK_ARGUMENT_FIELDS = frozenset({"original_request_id"})
_REQUEST_ID = re.compile(r"^[A-Z0-9][A-Z0-9-]{0,127}$")
_DNS_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ProjectKey:
    tenant: str
    name: str
    environment: str


@dataclass(frozen=True)
class Precondition:
    state: str | None = None
    sha256: str | None = None


@dataclass(frozen=True)
class MutationRequest:
    protocol: str
    request_id: str
    mission_id: str
    declared_actor: str
    project: ProjectKey
    operation: str
    path: str | None
    content: bytes | None
    precondition: Precondition | None
    original_request_id: str | None


def parse_request(value: dict[str, Any]) -> MutationRequest:
    if not isinstance(value, dict):
        raise RefusedError("request_must_be_object")
    if set(value) - _REQUEST_FIELDS:
        raise RefusedError("unexpected_request_field")
    if set(value) != _REQUEST_FIELDS:
        raise RefusedError("invalid_request")
    if value.get("protocol") != MUTATION_PROTOCOL:
        raise RefusedError("invalid_protocol")

    request_id = value.get("request_id")
    if not _valid_request_id(request_id):
        raise RefusedError("invalid_request_id")
    if value.get("mission_id") != PILOT_MISSION_ID:
        raise RefusedError("invalid_mission_id")
    if value.get("declared_actor") != PILOT_DECLARED_ACTOR:
        raise RefusedError("invalid_declared_actor")

    project = _parse_project(value.get("project"))
    operation = value.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise RefusedError("unknown_operation")
    arguments = value.get("arguments")
    if not isinstance(arguments, dict):
        raise RefusedError("invalid_arguments")

    if operation == "workspace.write":
        path, content, precondition = _parse_write_arguments(arguments)
        original_request_id = None
    elif operation == "rollback":
        path, content, precondition, original_request_id = _parse_rollback_arguments(arguments)
    else:
        if arguments:
            raise RefusedError("unexpected_arguments_field")
        path = content = precondition = original_request_id = None

    return MutationRequest(
        protocol=MUTATION_PROTOCOL,
        request_id=request_id,
        mission_id=PILOT_MISSION_ID,
        declared_actor=PILOT_DECLARED_ACTOR,
        project=project,
        operation=operation,
        path=path,
        content=content,
        precondition=precondition,
        original_request_id=original_request_id,
    )


def _parse_project(value: Any) -> ProjectKey:
    if not isinstance(value, dict):
        raise RefusedError("invalid_project")
    if set(value) - _PROJECT_FIELDS:
        raise RefusedError("unexpected_project_field")
    if set(value) != _PROJECT_FIELDS:
        raise RefusedError("invalid_project")
    tenant, name, environment = value.get("tenant"), value.get("name"), value.get("environment")
    if not _valid_dns_label(tenant) or not _valid_dns_label(name):
        raise RefusedError("invalid_project")
    if environment not in {"dev", "staging"}:
        raise RefusedError("invalid_environment")
    return ProjectKey(tenant=tenant, name=name, environment=environment)


def _parse_write_arguments(arguments: dict[str, Any]) -> tuple[str, bytes, Precondition]:
    if set(arguments) - _WRITE_ARGUMENT_FIELDS:
        raise RefusedError("unexpected_arguments_field")
    if set(arguments) != _WRITE_ARGUMENT_FIELDS:
        raise RefusedError("invalid_arguments")
    path = arguments.get("path")
    if not isinstance(path, str) or not path:
        raise RefusedError("invalid_path")
    content = arguments.get("content")
    if not isinstance(content, str):
        raise RefusedError("invalid_content")
    try:
        encoded = content.encode("utf-8")
    except UnicodeEncodeError:
        raise RefusedError("invalid_content") from None
    if len(encoded) > MAX_CONTENT_BYTES:
        raise RefusedError("content_too_large")
    return path, encoded, _parse_precondition(arguments.get("precondition"))


def _parse_rollback_arguments(
    arguments: dict[str, Any],
) -> tuple[None, None, None, str]:
    if set(arguments) - _ROLLBACK_ARGUMENT_FIELDS:
        raise RefusedError("unexpected_arguments_field")
    if set(arguments) != _ROLLBACK_ARGUMENT_FIELDS:
        raise RefusedError("invalid_arguments")
    original_request_id = arguments.get("original_request_id")
    if not _valid_request_id(original_request_id):
        raise RefusedError("invalid_original_request_id")
    return None, None, None, original_request_id


def _parse_precondition(value: Any) -> Precondition:
    if not isinstance(value, dict):
        raise RefusedError("invalid_precondition")
    if set(value) == {"state"} and value.get("state") == "ABSENT":
        return Precondition(state="ABSENT")
    if set(value) == {"sha256"} and isinstance(value.get("sha256"), str) and _SHA256.fullmatch(value["sha256"]):
        return Precondition(sha256=value["sha256"])
    raise RefusedError("invalid_precondition")


def _valid_request_id(value: Any) -> bool:
    return isinstance(value, str) and _REQUEST_ID.fullmatch(value) is not None


def _valid_dns_label(value: Any) -> bool:
    return isinstance(value, str) and 1 <= len(value) <= 63 and _DNS_LABEL.fullmatch(value) is not None
