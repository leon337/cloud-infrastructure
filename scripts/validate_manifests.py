#!/usr/bin/env python3
"""Validate declarative platform manifests and cross-field guardrails."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

import jsonschema
import yaml

from yaml_strict import load_strict


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_DIRECTORY = ROOT / "platform" / "schemas"
MANIFEST_DIRECTORY = ROOT / "platform" / "manifests"

SCHEMAS = {
    "ExecutionNode": SCHEMA_DIRECTORY / "node.schema.json",
    "Project": SCHEMA_DIRECTORY / "project.schema.json",
}

FORBIDDEN_SECRET_KEYS = {
    "password",
    "passphrase",
    "token",
    "apikey",
    "api_key",
    "privatekey",
    "private_key",
    "connectionstring",
    "connection_string",
}


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def iter_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_keys(child)


def semantic_checks(path: pathlib.Path, manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    normalized_keys = {key.lower().replace("-", "_") for key in iter_keys(manifest)}
    secret_keys = normalized_keys.intersection(FORBIDDEN_SECRET_KEYS)
    if secret_keys:
        errors.append(f"inline secret-like keys are forbidden: {sorted(secret_keys)}")

    spec = manifest["spec"]
    if manifest["kind"] == "ExecutionNode":
        capacity = spec["capacityPolicy"]
        allocated = sum(
            capacity[key]
            for key in (
                "hostReserveMemoryMiB",
                "platformHighWaterMemoryMiB",
                "workloadPoolMemoryMiB",
                "uncommittedMemoryMiB",
            )
        )
        if allocated > 24_000:
            errors.append(f"declared memory envelope exceeds node baseline: {allocated} MiB")
        if spec["productionPromotion"]["authorized"] is not False:
            errors.append("production promotion must remain disabled")

    if manifest["kind"] == "Project":
        preview = spec["preview"]["enabled"]
        ingress = spec["sandbox"]["network"]["ingress"]
        capabilities = spec["capabilities"]
        if preview and (ingress != "preview-gateway" or "preview" not in capabilities):
            errors.append("enabled preview requires preview capability and preview-gateway ingress")
        if not preview and ingress == "preview-gateway":
            errors.append("preview-gateway ingress requires preview.enabled=true")
        if spec["production"]["promotionAuthorized"] is not False:
            errors.append("production promotion must remain disabled")
        for reference in spec["secretRefs"]:
            if not reference.startswith("secret://"):
                errors.append("secrets must be symbolic secret:// references")

    return [f"{path.relative_to(ROOT)}: {message}" for message in errors]


def main() -> int:
    failures: list[str] = []
    manifests = sorted(MANIFEST_DIRECTORY.rglob("*.yaml"))
    if not manifests:
        print("MANIFEST_VALIDATION_FAIL no manifests found", file=sys.stderr)
        return 1

    loaded_schemas: dict[str, dict[str, Any]] = {}
    for kind, path in SCHEMAS.items():
        try:
            schema = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=reject_duplicate_json_keys,
            )
            jsonschema.Draft202012Validator.check_schema(schema)
        except (OSError, ValueError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: invalid schema: {exc}")
            continue
        loaded_schemas[kind] = schema

    if failures:
        for failure in failures:
            print(f"MANIFEST_VALIDATION_FAIL {failure}", file=sys.stderr)
        return 1

    format_checker = jsonschema.FormatChecker()

    for path in manifests:
        try:
            manifest = load_strict(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            failures.append(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
            continue
        if not isinstance(manifest, dict):
            failures.append(f"{path.relative_to(ROOT)}: manifest must be a mapping")
            continue
        kind = manifest.get("kind")
        if kind not in loaded_schemas:
            failures.append(f"{path.relative_to(ROOT)}: unsupported kind {kind!r}")
            continue
        validator = jsonschema.Draft202012Validator(
            loaded_schemas[kind], format_checker=format_checker
        )
        schema_errors = sorted(
            validator.iter_errors(manifest), key=lambda item: list(item.path)
        )
        for error in schema_errors:
            location = ".".join(str(item) for item in error.absolute_path) or "<root>"
            failures.append(f"{path.relative_to(ROOT)}:{location}: {error.message}")
        if not schema_errors:
            failures.extend(semantic_checks(path, manifest))

    if failures:
        for failure in failures:
            print(f"MANIFEST_VALIDATION_FAIL {failure}", file=sys.stderr)
        return 1
    print(f"MANIFEST_VALIDATION_PASS count={len(manifests)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
