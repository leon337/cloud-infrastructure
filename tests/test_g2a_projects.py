from __future__ import annotations

import pathlib
import tempfile
import unittest

import yaml

from control_plane.g2a.errors import NotFoundError, RefusedError
from control_plane.g2a.projects import ProjectResolver, project_public_view, workspace_path
from control_plane.g2a.protocol import ProjectKey


def project_manifest(
    tenant: str,
    name: str,
    environment: str,
    *,
    capabilities: list[str] | None = None,
    secret_refs: list[str] | None = None,
) -> dict:
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
            "capabilities": capabilities if capabilities is not None else [],
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
            "secretRefs": secret_refs if secret_refs is not None else [],
            "production": {"promotionAuthorized": False, "humanGate": "LEANDRO"},
        },
    }


def write_manifest(root: pathlib.Path, relative: str, value: dict) -> pathlib.Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")
    return path


class ProjectResolverTests(unittest.TestCase):
    def test_runtime_list_excludes_examples_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_manifest(root, "examples/project.example.yaml", project_manifest("example-tenant", "example-project", "dev"))
            write_manifest(root, "z-project-b.yaml", project_manifest("tenant-b", "project-b", "staging"))
            write_manifest(root, "a-project-a.yaml", project_manifest("tenant-a", "project-a", "dev"))

            resolver = ProjectResolver(root)

            self.assertEqual(
                [record.key for record in resolver.list()],
                [
                    ProjectKey("tenant-a", "project-a", "dev"),
                    ProjectKey("tenant-b", "project-b", "staging"),
                ],
            )

    def test_duplicate_runtime_project_key_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            value = project_manifest("tenant-a", "project-a", "dev")
            write_manifest(root, "one.yaml", value)
            write_manifest(root, "nested/two.yaml", value)

            with self.assertRaises(RefusedError) as caught:
                ProjectResolver(root).list()
            self.assertEqual(caught.exception.code, "duplicate_project_key")

    def test_capabilities_are_not_control_plane_acl(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_manifest(
                root,
                "project.yaml",
                project_manifest("tenant-a", "project-a", "dev", capabilities=[]),
            )

            record = ProjectResolver(root).get(ProjectKey("tenant-a", "project-a", "dev"))
            self.assertEqual(record.key, ProjectKey("tenant-a", "project-a", "dev"))

    def test_missing_project_is_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_manifest(root, "project.yaml", project_manifest("tenant-a", "project-a", "dev"))

            with self.assertRaises(NotFoundError) as caught:
                ProjectResolver(root).get(ProjectKey("tenant-b", "project-b", "dev"))
            self.assertEqual(caught.exception.code, "project_not_found")

    def test_public_view_omits_secret_refs_and_capability_acl_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            write_manifest(
                root,
                "project.yaml",
                project_manifest(
                    "tenant-a",
                    "project-a",
                    "dev",
                    capabilities=["build", "test"],
                    secret_refs=["secret://tenant-a/project-a/database"],
                ),
            )
            record = ProjectResolver(root).get(ProjectKey("tenant-a", "project-a", "dev"))

            view = project_public_view(record)

            self.assertNotIn("secretRefs", view)
            self.assertNotIn("capabilities", view)
            self.assertEqual(view["identity"], {"tenant": "tenant-a", "name": "project-a", "environment": "dev"})
            self.assertEqual(view["source"]["revision"], "main")
            self.assertFalse(view["production"]["promotionAuthorized"])
            self.assertEqual(view["production"]["humanGate"], "LEANDRO")

    def test_workspace_path_is_deterministic_and_does_not_create_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "workspaces"
            key = ProjectKey("tenant-a", "project-a", "dev")

            resolved = workspace_path(root, key)

            self.assertEqual(resolved, root / "tenant-a" / "project-a" / "dev")
            self.assertFalse(resolved.exists())


if __name__ == "__main__":
    unittest.main()
