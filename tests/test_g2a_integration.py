from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest

import yaml

from control_plane.g2a.core import execute


def project_manifest(tenant: str, name: str, *, secret_refs: list[str] | None = None) -> dict:
    return {
        "apiVersion": "platform.leandro.dev/v1alpha1",
        "kind": "Project",
        "metadata": {"tenant": tenant, "name": name, "environment": "dev"},
        "spec": {
            "criticality": "rebuildable",
            "source": {"repository": f"https://example.invalid/{tenant}/{name}.git", "revision": "main"},
            "capabilities": [],
            "persistence": {"git": True, "devDatabase": False, "objectStorage": False, "volumes": []},
            "sandbox": {
                "disposable": True,
                "limits": {"cpuMillicores": 1000, "memoryMiB": 1024, "pids": 256},
                "network": {"ingress": "none", "egressProfile": "development-default", "sharedServices": []},
            },
            "preview": {"enabled": False},
            "secretRefs": secret_refs or [],
            "production": {"promotionAuthorized": False, "humanGate": "LEANDRO"},
        },
    }


def git(cwd: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def init_repo(path: pathlib.Path, label: str) -> str:
    path.mkdir(parents=True)
    git(path, "init", "-q")
    (path / "README.txt").write_text(f"{label} base\n", encoding="utf-8")
    (path / "large.txt").write_text("small base\n", encoding="utf-8")
    git(path, "add", "README.txt", "large.txt")
    git(path, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "base")
    return git(path, "rev-parse", "HEAD")


def request(tenant: str, name: str, operation: str, arguments: dict | None = None) -> dict:
    return {
        "protocol": "MCF_WORKSPACE_CONTROL_V1",
        "request_id": f"INT-{tenant}-{name}-{operation}",
        "project": {"tenant": tenant, "name": name, "environment": "dev"},
        "operation": operation,
        "arguments": arguments or {},
    }


class G2AIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.manifests = self.root / "manifests"
        self.workspaces = self.root / "workspaces"
        self.manifests.mkdir()
        self.workspaces.mkdir()

        examples = self.manifests / "examples"
        examples.mkdir()
        (examples / "project.example.yaml").write_text(
            yaml.safe_dump(project_manifest("example-tenant", "example-project")),
            encoding="utf-8",
        )
        (self.manifests / "a.yaml").write_text(
            yaml.safe_dump(
                project_manifest(
                    "tenant-a",
                    "project-a",
                    secret_refs=["secret://tenant-a/project-a/database"],
                )
            ),
            encoding="utf-8",
        )
        (self.manifests / "b.yaml").write_text(
            yaml.safe_dump(project_manifest("tenant-b", "project-b")),
            encoding="utf-8",
        )

        self.a = self.workspaces / "tenant-a" / "project-a" / "dev"
        self.b = self.workspaces / "tenant-b" / "project-b" / "dev"
        self.a_head = init_repo(self.a, "A")
        self.b_head = init_repo(self.b, "B")
        (self.a / "README.txt").write_text("A local change\n", encoding="utf-8")
        (self.b / "README.txt").write_text("B local change\n", encoding="utf-8")
        (self.a / "escape-to-b").symlink_to(self.b / "README.txt")
        (self.a / "notes.txt").write_text("password=abcdefghijk\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def execute(self, value: dict):
        return execute(value, manifest_root=self.manifests, workspace_root=self.workspaces)

    def test_complete_multi_project_read_only_boundary(self):
        listed = self.execute(request("tenant-a", "project-a", "project.list")).result
        identities = [item["identity"] for item in listed["result"]["projects"]]
        self.assertEqual(
            identities,
            [
                {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
                {"tenant": "tenant-b", "name": "project-b", "environment": "dev"},
            ],
        )

        project = self.execute(request("tenant-a", "project-a", "project.get")).result
        self.assertEqual(project["status"], "PASS")
        self.assertNotIn("secretRefs", project["result"])

        for tenant, name in (("tenant-a", "project-a"), ("tenant-b", "project-b")):
            stat = self.execute(request(tenant, name, "workspace.stat")).result
            self.assertEqual(stat["result"]["state"], "PRESENT")
            status = self.execute(request(tenant, name, "git.status")).result
            self.assertTrue(status["result"]["dirty"])
            branch = self.execute(request(tenant, name, "git.branch")).result
            self.assertEqual(branch["status"], "PASS")
            head = self.execute(request(tenant, name, "git.head")).result
            self.assertEqual(head["result"]["head"], self.a_head if tenant == "tenant-a" else self.b_head)
            diff = self.execute(request(tenant, name, "git.diff"))
            self.assertEqual(diff.result["status"], "PASS")
            self.assertIn("local change", diff.result["result"]["content"])

        traversal = self.execute(
            request("tenant-a", "project-a", "workspace.read", {"path": "../../../../tenant-b/project-b/dev/README.txt"})
        ).result
        self.assertEqual((traversal["status"], traversal["error"]["code"]), ("REFUSED", "path_escape_refused"))

        symlink = self.execute(
            request("tenant-a", "project-a", "workspace.read", {"path": "escape-to-b"})
        ).result
        self.assertEqual((symlink["status"], symlink["error"]["code"]), ("REFUSED", "path_escape_refused"))

        sensitive = self.execute(
            request("tenant-a", "project-a", "workspace.read", {"path": "notes.txt"})
        ).result
        self.assertEqual((sensitive["status"], sensitive["error"]["code"]), ("REFUSED", "secret_like_content"))
        self.assertNotIn("abcdefghijk", json.dumps(sensitive))

        serialized = json.dumps(listed, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn("issue_number", serialized)

    def test_large_safe_diff_becomes_attachment_and_external_gitdir_is_refused(self):
        safe_lines = "".join(f"safe-line-{index:06d} abcdefghijklmnopqrstuvwxyz\n" for index in range(5000))
        (self.a / "large.txt").write_text(safe_lines, encoding="utf-8")
        execution = self.execute(request("tenant-a", "project-a", "git.diff"))
        self.assertEqual(execution.result["status"], "PASS")
        self.assertEqual(execution.result["result"]["delivery"], "attachment")
        self.assertIsNotNone(execution.attachment)
        self.assertGreater(len(execution.attachment.content), 131_072)

        external = self.root / "external-git-dir"
        original = self.b / ".git"
        original.rename(external)
        (self.b / ".git").write_text(f"gitdir: {external}\n", encoding="utf-8")
        refused = self.execute(request("tenant-b", "project-b", "git.head")).result
        self.assertEqual((refused["status"], refused["error"]["code"]), ("REFUSED", "external_git_dir"))


if __name__ == "__main__":
    unittest.main()
