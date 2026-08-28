from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .errors import RefusedError

CORE_PROTOCOL = "MCF_WORKSPACE_CONTROL_V1"
RESULT_PROTOCOL = "MCF_WORKSPACE_CONTROL_RESULT_V1"

OPERATIONS = frozenset(
    {
        "project.list",
        "project.get",
        "workspace.stat",
        "workspace.list",
        "workspace.read",
        "git.status",
        "git.branch",
        "git.head",
        "git.diff",
    }
)

REQUEST_FIELDS = frozenset({"protocol", "request_id", "project", "operation", "arguments"})
PROJECT_FIELDS = frozenset({"tenant", "name", "environment"})
ENVIRONMENTS = frozenset({"dev", "staging"})
DNS_LABEL = re.compile(r"^[a-z][a-z0-9-]*[a-z0-9]$")


@dataclass(frozen=True)
class ProjectKey:
    tenant: str
    name: str
    environment: str


@dataclass(frozen=True)
class CoreRequest:
    protocol: str
    request_id: str
    project: ProjectKey
    operation: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Attachment:
    name: str
    media_type: str
    content: bytes


@dataclass(frozen=True)
class CoreExecution:
    result: dict[str, Any]
    attachment: Attachment | None = None


def _valid_dns_label(value: Any) -> bool:
    return (
        isinstance(value, str)
        and 2 <= len(value) <= 63
        and DNS_LABEL.fullmatch(value) is not None
    )


def parse_request(value: dict[str, Any]) -> CoreRequest:
    if not isinstance(value, dict):
        raise RefusedError("request_must_be_object")

    unexpected = set(value) - REQUEST_FIELDS
    if unexpected:
        raise RefusedError("unexpected_request_field")

    if value.get("protocol") != CORE_PROTOCOL:
        raise RefusedError("invalid_protocol")

    request_id = value.get("request_id")
    if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
        raise RefusedError("invalid_request_id")

    raw_project = value.get("project")
    if not isinstance(raw_project, dict):
        raise RefusedError("invalid_project")
    unexpected_project = set(raw_project) - PROJECT_FIELDS
    if unexpected_project:
        raise RefusedError("unexpected_project_field")
    if set(raw_project) != PROJECT_FIELDS:
        raise RefusedError("invalid_project")

    tenant = raw_project.get("tenant")
    name = raw_project.get("name")
    environment = raw_project.get("environment")
    if not _valid_dns_label(tenant) or not _valid_dns_label(name):
        raise RefusedError("invalid_project")
    if environment not in ENVIRONMENTS:
        raise RefusedError("invalid_environment")

    operation = value.get("operation")
    if not isinstance(operation, str) or operation not in OPERATIONS:
        raise RefusedError("unknown_operation")

    arguments = value.get("arguments")
    if not isinstance(arguments, dict):
        raise RefusedError("invalid_arguments")

    return CoreRequest(
        protocol=CORE_PROTOCOL,
        request_id=request_id,
        project=ProjectKey(tenant=tenant, name=name, environment=environment),
        operation=operation,
        arguments=dict(arguments),
    )
