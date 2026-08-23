from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from typing import Any

import jsonschema


REQUEST_ID = "MCF-CLOUD-G2A-E2E-20260823"
REQUEST_LINE = (
    '{"protocol":"MCF_CLOUD_CONTEXT_READ_V1",'
    '"request_id":"MCF-CLOUD-G2A-E2E-20260823",'
    '"project_id":"cloud-infrastructure",'
    '"operation":"context.get","arguments":{}}\n'
)
ADAPTER_COMMAND = (
    sys.executable,
    "-I",
    "platform/control-bridge/mcf-cloud-context-read",
)
ENABLE_ENVIRONMENT = "MCF_CLOUD_CONTEXT_READ_ENABLE"
ENABLE_VALUE = "DISPOSABLE_LOCAL_LAB_ONLY"
RESULT_SCHEMA_PATH = pathlib.PurePosixPath(
    "platform/schemas/mcf-cloud-context-read-result.schema.json"
)


class ClientError(RuntimeError):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ClientError("duplicate_result_key")
        result[key] = value
    return result


def _load_json_object(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_json_object,
    )
    if not isinstance(value, dict):
        raise ClientError("schema_must_be_object")
    return value


def _source_digests(workspace_root: pathlib.Path, paths: list[str]) -> dict[str, str]:
    return {
        path: hashlib.sha256((workspace_root / path).read_bytes()).hexdigest()
        for path in paths
    }


def request_cloud_context(workspace_root: pathlib.Path) -> dict[str, Any]:
    environment = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        ENABLE_ENVIRONMENT: ENABLE_VALUE,
    }
    completed = subprocess.run(
        list(ADAPTER_COMMAND),
        input=REQUEST_LINE,
        text=True,
        capture_output=True,
        cwd=workspace_root,
        env=environment,
        timeout=20,
        check=False,
    )
    if completed.returncode != 0:
        raise ClientError(f"adapter_exit_{completed.returncode}")
    if completed.stderr:
        raise ClientError("adapter_stderr_not_empty")
    if len(completed.stdout.splitlines()) != 1:
        raise ClientError("result_must_be_one_line")

    result = json.loads(
        completed.stdout,
        object_pairs_hook=_unique_json_object,
    )
    if not isinstance(result, dict):
        raise ClientError("result_must_be_object")

    schema = _load_json_object(workspace_root / RESULT_SCHEMA_PATH)
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(
        schema,
        format_checker=jsonschema.FormatChecker(),
    ).validate(result)

    if result.get("status") != "PASS" or result.get("error") is not None:
        raise ClientError("adapter_status_not_pass")
    if result.get("request_id") != REQUEST_ID:
        raise ClientError("request_id_mismatch")
    if result.get("project_id") != "cloud-infrastructure":
        raise ClientError("project_id_mismatch")
    if result.get("operation") != "context.get":
        raise ClientError("operation_mismatch")

    freshness = result.get("freshness")
    if freshness != {
        "observed_at": freshness.get("observed_at") if isinstance(freshness, dict) else None,
        "operational_state": "LIVE_REQUIRED",
        "workspace_observation": "LIVE_LOCAL_DISPOSABLE",
        "source_mode": "READ_AT_REQUEST_TIME",
    }:
        raise ClientError("freshness_mismatch")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        raise ClientError("provenance_missing")
    sources = provenance.get("sources")
    if not isinstance(sources, list):
        raise ClientError("provenance_sources_missing")
    source_paths = [item.get("path") for item in sources if isinstance(item, dict)]
    if len(source_paths) != len(sources) or len(source_paths) != len(set(source_paths)):
        raise ClientError("provenance_paths_invalid")
    expected_digests = _source_digests(workspace_root, source_paths)
    observed_digests = {
        item["path"]: item.get("sha256")
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    if observed_digests != expected_digests:
        raise ClientError("provenance_digest_mismatch")

    adapter = result.get("result", {}).get("adapter")
    if adapter != {
        "transport": "STDIO",
        "operation": "context.get",
        "enabled_by_default": False,
        "read_only": True,
        "network_access": False,
        "external_process": False,
        "arbitrary_path": False,
    }:
        raise ClientError("adapter_boundary_mismatch")
    return result
