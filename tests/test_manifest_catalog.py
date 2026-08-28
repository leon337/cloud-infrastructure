from __future__ import annotations

import importlib.util
import pathlib
import sys
import tempfile
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

MODULE_PATH = SCRIPTS / "validate_manifests.py"
SPEC = importlib.util.spec_from_file_location("validate_manifests", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def project_manifest(tenant: str, name: str, environment: str) -> dict:
    return {
        "apiVersion": "platform.leandro.dev/v1alpha1",
        "kind": "Project",
        "metadata": {"tenant": tenant, "name": name, "environment": environment},
        "spec": {
            "criticality": "rebuildable",
            "source": {
                "repository": f"https://example.invalid/{tenant}/{name}.git",
                "revision": "main",
            },
            "capabilities": ["build", "test"],
            "persistence": {
                "git": True,
                "devDatabase": False,
                "objectStorage": False,
                "volumes": [],
            },
            "sandbox": {
                "disposable": True,
                "limits": {"cpuMillicores": 1000, "memoryMiB": 1024, "pids": 256},
                "network": {
                    "ingress": "none",
                    "egressProfile": "development-default",
                    "sharedServices": [],
                },
            },
            "preview": {"enabled": False},
            "secretRefs": [],
            "production": {"promotionAuthorized": False, "humanGate": "LEANDRO"},
        },
    }


class ManifestCatalogTests(unittest.TestCase):
    def test_load_validated_manifests_returns_records_with_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            first = root / "a.yaml"
            second = root / "nested" / "b.yaml"
            second.parent.mkdir()
            first.write_text(yaml.safe_dump(project_manifest("tenant-a", "project-a", "dev")), encoding="utf-8")
            second.write_text(yaml.safe_dump(project_manifest("tenant-b", "project-b", "staging")), encoding="utf-8")

            records = MODULE.load_validated_manifests(root)

            self.assertEqual(
                [MODULE.project_key(record.value) for record in records],
                [("tenant-a", "project-a", "dev"), ("tenant-b", "project-b", "staging")],
            )
            self.assertEqual([record.path for record in records], [first.resolve(), second.resolve()])

    def test_invalid_duplicate_yaml_raises_catalog_error_without_echoing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            bad = root / "bad.yaml"
            bad.write_text(
                "apiVersion: platform.leandro.dev/v1alpha1\n"
                "kind: Project\n"
                "metadata:\n"
                "  tenant: tenant-a\n"
                "  name: project-a\n"
                "  environment: dev\n"
                "metadata:\n"
                "  tenant: tenant-b\n"
                "  name: project-b\n"
                "  environment: dev\n"
                "spec:\n"
                "  password: super-secret-value\n",
                encoding="utf-8",
            )

            with self.assertRaises(MODULE.ManifestValidationError) as caught:
                MODULE.load_validated_manifests(root)

            message = str(caught.exception)
            self.assertIn("bad.yaml", message)
            self.assertNotIn("super-secret-value", message)


if __name__ == "__main__":
    unittest.main()
