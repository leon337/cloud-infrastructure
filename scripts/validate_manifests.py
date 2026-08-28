#!/usr/bin/env python3
"""Validate declarative platform manifests and expose a reusable catalog."""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass
from typing import Any

import jsonschema
import yaml

try:
    from .yaml_strict import load_strict
except ImportError:  # direct execution: python3 scripts/validate_manifests.py
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


@dataclass(frozen=True)
class ValidatedManifest:
    path: pathlib.Path
    value: dict[str, Any]


class ManifestValidationError(ValueError):
    def __init__(self, failures: list[str]):
        self.failures = list(failures)
        super().__init__("; ".join(self.failures))


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


def _display_path(path: pathlib.Path, base: pathlib.Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        return resolved.name


def project_key(manifest: dict[str, Any]) -> tuple[str, str, str]:
    metadata = manifest["metadata"]
    return metadata["tenant"], metadata["name"], metadata["environment"]


def semantic_checks(
    path: pathlib.Path,
    manifest: dict[str, Any],
    *,
    display_base: pathlib.Path = ROOT,
) -> list[str]:
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

    rendered = _display_path(path, display_base)
    return [f"{rendered}: {message}" for message in errors]


def _load_schemas() -> tuple[dict[str, dict[str, Any]], list[str]]:
    loaded: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for kind, path in SCHEMAS.items():
        try:
            schema = json.loads(
                path.read_text(encoding="utf-8"),
                object_pairs_hook=reject_duplicate_json_keys,
            )
            jsonschema.Draft202012Validator.check_schema(schema)
        except (OSError, ValueError, json.JSONDecodeError, jsonschema.SchemaError):
            failures.append(f"{_display_path(path, ROOT)}: invalid schema")
            continue
        loaded[kind] = schema
    return loaded, failures


def load_validated_manifests(
    manifest_directory: pathlib.Path = MANIFEST_DIRECTORY,
) -> list[ValidatedManifest]:
    manifest_directory = manifest_directory.resolve()
    manifest_paths = sorted(manifest_directory.rglob("*.yaml"))
    if not manifest_paths:
        raise ManifestValidationError(["no manifests found"])

    loaded_schemas, failures = _load_schemas()
    if failures:
        raise ManifestValidationError(failures)

    format_checker = jsonschema.FormatChecker()
    records: list[ValidatedManifest] = []

    for path in manifest_paths:
        rendered = _display_path(path, manifest_directory)
        try:
            manifest = load_strict(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            failures.append(f"{rendered}: invalid YAML")
            continue
        if not isinstance(manifest, dict):
            failures.append(f"{rendered}: manifest must be a mapping")
            continue

        kind = manifest.get("kind")
        if kind not in loaded_schemas:
            failures.append(f"{rendered}: unsupported kind")
            continue

        validator = jsonschema.Draft202012Validator(
            loaded_schemas[kind], format_checker=format_checker
        )
        schema_errors = sorted(
            validator.iter_errors(manifest), key=lambda item: list(item.path)
        )
        for error in schema_errors:
            location = ".".join(str(item) for item in error.absolute_path) or "<root>"
            failures.append(f"{rendered}:{location}: schema validation failed")
        if schema_errors:
            continue

        semantic_failures = semantic_checks(
            path,
            manifest,
            display_base=manifest_directory,
        )
        if semantic_failures:
            failures.extend(semantic_failures)
            continue

        records.append(ValidatedManifest(path=path.resolve(), value=manifest))

    if failures:
        raise ManifestValidationError(failures)
    return records


def main() -> int:
    try:
        records = load_validated_manifests(MANIFEST_DIRECTORY)
    except ManifestValidationError as exc:
        for failure in exc.failures:
            print(f"MANIFEST_VALIDATION_FAIL {failure}", file=sys.stderr)
        return 1
    print(f"MANIFEST_VALIDATION_PASS count={len(records)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
