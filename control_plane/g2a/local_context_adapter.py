from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import stat
from collections.abc import Mapping
from typing import Any

import jsonschema
import yaml

from scripts.yaml_strict import load_strict


REQUEST_PROTOCOL = "MCF_CLOUD_CONTEXT_READ_V1"
RESULT_PROTOCOL = "MCF_CLOUD_CONTEXT_READ_RESULT_V1"
ENABLE_ENVIRONMENT = "MCF_CLOUD_CONTEXT_READ_ENABLE"
ENABLE_VALUE = "DISPOSABLE_LOCAL_LAB_ONLY"
PROJECT_ID = "cloud-infrastructure"
OPERATION = "context.get"
MAX_INPUT_BYTES = 4_096
MAX_OUTPUT_BYTES = 65_536
MAX_SOURCE_BYTES = 262_144
REQUEST_FIELDS = frozenset(
    {"protocol", "request_id", "project_id", "operation", "arguments"}
)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")

CONFIG_PATH = "platform/control-bridge/mcf-cloud-context-read-config.yaml"
CONFIG_SCHEMA_PATH = "platform/schemas/mcf-cloud-context-read-config.schema.json"
RESULT_SCHEMA_PATH = "platform/schemas/mcf-cloud-context-read-result.schema.json"
ADAPTER_MODULE_PATH = "control_plane/g2a/local_context_adapter.py"
ADAPTER_CLI_PATH = "platform/control-bridge/mcf-cloud-context-read"
ALLOWED_SOURCE_PATHS = (
    ".mcf/project-capsule.yaml",
    "context/mcf-cloud-context.yaml",
    "platform/manifests/g2a-smoke.yaml",
    "platform/schemas/mcf-cloud-context.schema.json",
    "platform/schemas/mcf-project-capsule.schema.json",
    "platform/schemas/project.schema.json",
    "state/control-bridge-g2a.yaml",
    "state/control-bridge-g2b.yaml",
)
PROVENANCE_PATHS = tuple(
    sorted(
        (
            CONFIG_PATH,
            CONFIG_SCHEMA_PATH,
            RESULT_SCHEMA_PATH,
            ADAPTER_MODULE_PATH,
            ADAPTER_CLI_PATH,
            *ALLOWED_SOURCE_PATHS,
        )
    )
)


class AdapterError(Exception):
    def __init__(self, code: str, status: str = "REFUSED"):
        self.code = code
        self.status = status
        super().__init__(code)


def _now() -> str:
    return (
        dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _safe_context(value: Any) -> tuple[str, str | None, str | None]:
    if not isinstance(value, dict):
        return "UNKNOWN", None, None
    request_id = value.get("request_id")
    project_id = value.get("project_id")
    operation = value.get("operation")
    return (
        request_id
        if isinstance(request_id, str) and REQUEST_ID_PATTERN.fullmatch(request_id)
        else "UNKNOWN",
        project_id if project_id == PROJECT_ID else None,
        operation if operation == OPERATION else None,
    )


def decode_request(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_INPUT_BYTES:
        raise AdapterError("request_too_large")
    if not raw or b"\x00" in raw:
        raise AdapterError("invalid_json")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise AdapterError("invalid_json") from None
    if not isinstance(value, dict):
        raise AdapterError("request_must_be_object")
    return value


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("duplicate_json_key")
        value[key] = child
    return value


def parse_request(value: dict[str, Any]) -> tuple[str, str, str]:
    if set(value) != REQUEST_FIELDS:
        if set(value) - REQUEST_FIELDS:
            raise AdapterError("unexpected_request_field")
        raise AdapterError("invalid_request")
    if value.get("protocol") != REQUEST_PROTOCOL:
        raise AdapterError("invalid_request")
    request_id = value.get("request_id")
    if not isinstance(request_id, str) or not REQUEST_ID_PATTERN.fullmatch(request_id):
        raise AdapterError("invalid_request")
    if value.get("project_id") != PROJECT_ID:
        raise AdapterError("invalid_project_id")
    if value.get("operation") != OPERATION:
        raise AdapterError("unknown_operation")
    if value.get("arguments") != {}:
        raise AdapterError("invalid_arguments")
    return request_id, PROJECT_ID, OPERATION


def enabled_from_environment(environment: Mapping[str, str]) -> bool:
    raw = environment.get(ENABLE_ENVIRONMENT)
    if raw is None or raw == "":
        return False
    if raw != ENABLE_VALUE:
        raise AdapterError("invalid_enable_value")
    return True


def _repository_root(root: pathlib.Path) -> pathlib.Path:
    if root.is_symlink() or not root.is_dir():
        raise AdapterError("repository_layout_refused")
    try:
        resolved = root.resolve(strict=True)
    except OSError:
        raise AdapterError("repository_layout_refused") from None
    if tuple(resolved.parts[-3:]) != ("leon337", "g2a-smoke", "dev"):
        raise AdapterError("repository_layout_refused")
    return resolved


def _read_confined_file(root: pathlib.Path, relative: str) -> bytes:
    if relative not in PROVENANCE_PATHS:
        raise AdapterError("source_boundary_refused")
    candidate = root / pathlib.PurePosixPath(relative)
    cursor = candidate
    while cursor != root:
        if cursor.is_symlink():
            raise AdapterError("source_boundary_refused")
        cursor = cursor.parent
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        raise AdapterError("source_boundary_refused") from None
    if root not in resolved.parents:
        raise AdapterError("source_boundary_refused")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(resolved, flags)
    except OSError:
        raise AdapterError("source_boundary_refused") from None
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_SOURCE_BYTES:
            raise AdapterError("source_boundary_refused")
        chunks: list[bytes] = []
        remaining = MAX_SOURCE_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > MAX_SOURCE_BYTES:
            raise AdapterError("source_boundary_refused")
        return data
    finally:
        os.close(descriptor)


def _json_document(data: bytes) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise AdapterError("source_contract_invalid") from None
    if not isinstance(value, dict):
        raise AdapterError("source_contract_invalid")
    return value


def _yaml_document(data: bytes) -> dict[str, Any]:
    try:
        value = load_strict(data.decode("utf-8"))
    except (UnicodeDecodeError, yaml.YAMLError):
        raise AdapterError("source_contract_invalid") from None
    if not isinstance(value, dict):
        raise AdapterError("source_contract_invalid")
    return value


def _validate(schema: dict[str, Any], value: dict[str, Any]) -> None:
    try:
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.Draft202012Validator(
            schema,
            format_checker=jsonschema.FormatChecker(),
        ).validate(value)
    except (jsonschema.SchemaError, jsonschema.ValidationError):
        raise AdapterError("source_contract_invalid") from None


def _validate_config(config: dict[str, Any]) -> None:
    expected = {
        "schema_version": 1,
        "enabled_by_default": False,
        "transport": "STDIO",
        "request_protocol": REQUEST_PROTOCOL,
        "result_protocol": RESULT_PROTOCOL,
        "enable_environment": {
            "name": ENABLE_ENVIRONMENT,
            "value": ENABLE_VALUE,
        },
        "project_id": PROJECT_ID,
        "cloud_project_key": {
            "tenant": "leon337",
            "name": "g2a-smoke",
            "environment": "dev",
        },
        "operation": OPERATION,
        "source_paths": list(ALLOWED_SOURCE_PATHS),
        "limits": {
            "input_bytes": MAX_INPUT_BYTES,
            "output_bytes": MAX_OUTPUT_BYTES,
            "source_bytes_each": MAX_SOURCE_BYTES,
        },
    }
    if config != expected:
        raise AdapterError("source_contract_invalid")


def _workspace_view(root: pathlib.Path) -> dict[str, Any]:
    try:
        metadata = root.stat()
    except OSError:
        raise AdapterError("source_boundary_refused") from None
    if not stat.S_ISDIR(metadata.st_mode):
        raise AdapterError("repository_layout_refused")
    return {
        "state": "PRESENT",
        "mode": stat.S_IMODE(metadata.st_mode),
        "layout": "ALLOWLISTED_CLOUD_PROJECT_KEY",
    }


def _success_result(
    *,
    manifest: dict[str, Any],
    capsule: dict[str, Any],
    context: dict[str, Any],
    g2a_state: dict[str, Any],
    g2b_state: dict[str, Any],
    workspace: dict[str, Any],
) -> dict[str, Any]:
    mapping = context["mapping"]
    g2a = context["capabilities"]["g2a"]
    g2b = context["capabilities"]["g2b"]
    spec = manifest["spec"]
    if capsule.get("project_id") != PROJECT_ID:
        raise AdapterError("source_contract_invalid")
    if mapping.get("from", {}).get("context_project_id") != PROJECT_ID:
        raise AdapterError("source_contract_invalid")
    if mapping.get("to") != manifest.get("metadata"):
        raise AdapterError("source_contract_invalid")
    if g2a_state.get("capabilities") != g2a.get("operations"):
        raise AdapterError("source_contract_invalid")
    if g2b_state.get("status") != "TASK_8_LAB_PASS_INACTIVE_TASKS_9_10_NOT_STARTED":
        raise AdapterError("source_contract_invalid")
    if g2a.get("mutation") is not False or g2a.get("operational_freshness") != "LIVE_REQUIRED":
        raise AdapterError("source_contract_invalid")
    if g2b.get("lifecycle") != "LAB_VALIDATED_INACTIVE" or g2b.get("activation") != "NOT_AUTHORIZED":
        raise AdapterError("source_contract_invalid")
    return {
        "mapping": {
            "cloud_project_key": dict(mapping["to"]),
            "canonical_cloud_key": mapping["canonical_cloud_key"],
            "identity_authority": mapping["identity_authority"],
        },
        "project": {
            "criticality": spec["criticality"],
            "source": dict(spec["source"]),
            "workload_capabilities": list(spec["capabilities"]),
            "production_authorized": spec["production"]["promotionAuthorized"],
        },
        "workspace": workspace,
        "control_bridge": {
            "g2a": {
                "lifecycle": g2a["lifecycle"],
                "state": g2a["state"],
                "operational_freshness": g2a["operational_freshness"],
                "operations": list(g2a["operations"]),
            },
            "g2b": {
                "lifecycle": g2b["lifecycle"],
                "state": g2b["state"],
                "activation": g2b["activation"],
                "tasks_9_10": g2b["tasks_9_10"],
                "production_authorized": g2b["production_authorized"],
            },
        },
        "adapter": {
            "transport": "STDIO",
            "operation": OPERATION,
            "enabled_by_default": False,
            "read_only": True,
            "network_access": False,
            "external_process": False,
            "arbitrary_path": False,
        },
        "capsule": {
            "lifecycle": capsule["lifecycle"],
            "current_status": capsule["snapshot"]["current_status"],
        },
    }


def _base_response(
    request_value: Any,
    *,
    status: str,
    result: dict[str, Any] | None,
    error_code: str | None,
    sources: list[dict[str, str]],
) -> dict[str, Any]:
    request_id, project_id, operation = _safe_context(request_value)
    observed = status == "PASS"
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": request_id,
        "project_id": project_id,
        "operation": operation,
        "status": status,
        "result": result,
        "error": None if error_code is None else {"code": error_code},
        "freshness": {
            "observed_at": _now(),
            "operational_state": "LIVE_REQUIRED",
            "workspace_observation": "LIVE_LOCAL_DISPOSABLE" if observed else "NOT_OBSERVED",
            "source_mode": "READ_AT_REQUEST_TIME" if observed else "NOT_READ",
        },
        "provenance": {
            "repository": "leon337/cloud-infrastructure",
            "adapter_config": CONFIG_PATH,
            "sources": sources if observed else [],
        },
    }


def failure_response(request_value: Any, code: str, status: str = "REFUSED") -> dict[str, Any]:
    return _base_response(
        request_value,
        status=status,
        result=None,
        error_code=code,
        sources=[],
    )


def execute_local_context_read(
    request_value: dict[str, Any],
    *,
    repository_root: pathlib.Path,
    enabled: bool,
) -> dict[str, Any]:
    try:
        parse_request(request_value)
        if not enabled:
            raise AdapterError("adapter_disabled")
        root = _repository_root(repository_root)
        raw = {path: _read_confined_file(root, path) for path in PROVENANCE_PATHS}

        config = _yaml_document(raw[CONFIG_PATH])
        config_schema = _json_document(raw[CONFIG_SCHEMA_PATH])
        _validate(config_schema, config)
        _validate_config(config)

        capsule = _yaml_document(raw[".mcf/project-capsule.yaml"])
        capsule_schema = _json_document(raw["platform/schemas/mcf-project-capsule.schema.json"])
        _validate(capsule_schema, capsule)

        context = _yaml_document(raw["context/mcf-cloud-context.yaml"])
        context_schema = _json_document(raw["platform/schemas/mcf-cloud-context.schema.json"])
        _validate(context_schema, context)

        manifest = _yaml_document(raw["platform/manifests/g2a-smoke.yaml"])
        project_schema = _json_document(raw["platform/schemas/project.schema.json"])
        _validate(project_schema, manifest)

        g2a_state = _yaml_document(raw["state/control-bridge-g2a.yaml"])
        g2b_state = _yaml_document(raw["state/control-bridge-g2b.yaml"])
        result = _success_result(
            manifest=manifest,
            capsule=capsule,
            context=context,
            g2a_state=g2a_state,
            g2b_state=g2b_state,
            workspace=_workspace_view(root),
        )
        sources = [
            {"path": path, "sha256": hashlib.sha256(raw[path]).hexdigest()}
            for path in PROVENANCE_PATHS
        ]
        response = _base_response(
            request_value,
            status="PASS",
            result=result,
            error_code=None,
            sources=sources,
        )
        result_schema = _json_document(raw[RESULT_SCHEMA_PATH])
        try:
            _validate(result_schema, response)
        except AdapterError:
            raise AdapterError("result_contract_invalid", status="FAILED") from None
        rendered = json.dumps(response, separators=(",", ":"), sort_keys=True).encode("utf-8")
        if len(rendered) > MAX_OUTPUT_BYTES:
            raise AdapterError("result_contract_invalid", status="FAILED")
        return response
    except AdapterError as exc:
        return failure_response(request_value, exc.code, exc.status)
    except Exception:
        return failure_response(request_value, "internal_error", "FAILED")
