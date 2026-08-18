from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

from scripts.validate_manifests import ValidatedManifest, load_validated_manifests, project_key

from .errors import NotFoundError, RefusedError
from .protocol import ProjectKey


@dataclass(frozen=True)
class ProjectRecord:
    key: ProjectKey
    manifest_path: pathlib.Path
    manifest: dict[str, Any]


class ProjectResolver:
    def __init__(self, manifest_root: pathlib.Path):
        self.manifest_root = manifest_root.resolve()

    def _records(self) -> list[ProjectRecord]:
        validated = load_validated_manifests(self.manifest_root)
        records: list[ProjectRecord] = []
        seen: set[ProjectKey] = set()

        for record in validated:
            relative = record.path.relative_to(self.manifest_root)
            if relative.parts and relative.parts[0] == "examples":
                continue
            if record.value.get("kind") != "Project":
                continue

            tenant, name, environment = project_key(record.value)
            key = ProjectKey(tenant=tenant, name=name, environment=environment)
            if key in seen:
                raise RefusedError("duplicate_project_key")
            seen.add(key)
            records.append(
                ProjectRecord(
                    key=key,
                    manifest_path=record.path,
                    manifest=record.value,
                )
            )

        return sorted(records, key=lambda item: (item.key.tenant, item.key.name, item.key.environment))

    def list(self) -> list[ProjectRecord]:
        return self._records()

    def get(self, key: ProjectKey) -> ProjectRecord:
        for record in self._records():
            if record.key == key:
                return record
        raise NotFoundError("project_not_found")


def workspace_path(workspace_root: pathlib.Path, key: ProjectKey) -> pathlib.Path:
    return workspace_root / key.tenant / key.name / key.environment


def project_public_view(record: ProjectRecord) -> dict[str, Any]:
    spec = record.manifest["spec"]
    persistence = spec["persistence"]
    sandbox = spec["sandbox"]
    network = sandbox["network"]
    production = spec["production"]

    return {
        "identity": {
            "tenant": record.key.tenant,
            "name": record.key.name,
            "environment": record.key.environment,
        },
        "criticality": spec["criticality"],
        "source": {
            "repository": spec["source"]["repository"],
            "revision": spec["source"]["revision"],
        },
        "persistence": {
            "git": persistence["git"],
            "devDatabase": persistence["devDatabase"],
            "objectStorage": persistence["objectStorage"],
        },
        "sandbox": {
            "disposable": sandbox["disposable"],
            "limits": dict(sandbox["limits"]),
            "network": {
                "ingress": network["ingress"],
                "egressProfile": network["egressProfile"],
                "sharedServices": list(network["sharedServices"]),
            },
        },
        "preview": {"enabled": spec["preview"]["enabled"]},
        "production": {
            "promotionAuthorized": production["promotionAuthorized"],
            "humanGate": production["humanGate"],
        },
    }
