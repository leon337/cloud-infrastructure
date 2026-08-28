from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

import yaml

from control_plane.g2a.core import execute
from control_plane.g2a.errors import OperationTimeout
from control_plane.g2a.protocol import RESULT_PROTOCOL


def manifest(tenant: str, name: str, environment: str = "dev") -> dict:
    return {
        "apiVersion": "platform.leandro.dev/v1alpha1",
        "kind": "Project",
        "metadata": {"tenant": tenant, "name": name, "environment": environment},
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
            "secretRefs": [],
            "production": {"promotionAuthorized": False, "humanGate": "LEANDRO"},
        },
    }


def request(operation: str, *, project: dict | None = None, arguments: dict | None = None) -> dict:
    return {
        "protocol": "MCF_WORKSPACE_CONTROL_V1",
        "request_id": f"REQ-{operation.replace('.', '-').upper()}",
        "project": project or {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
        "operation": operation,
        "arguments": arguments if arguments is not None else {},
    }


def git(*args: str, cwd: pathlib.Path) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


class G2ACoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.manifests = self.root / "manifests"
        self.workspaces = self.root / "workspaces"
        self.manifests.mkdir()
        self.workspaces.mkdir()
        (self.manifests / "a.yaml").write_text(yaml.safe_dump(manifest("tenant-a", "project-a")), encoding="utf-8")
        (self.manifests / "b.yaml").write_text(yaml.safe_dump(manifest("tenant-b", "project-b")), encoding="utf-8")

        self.workspace = self.workspaces / "tenant-a" / "project-a" / "dev"
        self.workspace.mkdir(parents=True)
        (self.workspace / "README.txt").write_text("hello g2a\n", encoding="utf-8")
        git("init", "-q", cwd=self.workspace)
        git("add", "README.txt", cwd=self.workspace)
        git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-q", "-m", "base", cwd=self.workspace)
        (self.workspace / "README.txt").write_text("hello g2a changed\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_core(self, value: dict):
        return execute(value, manifest_root=self.manifests, workspace_root=self.workspaces)

    def test_all_nine_operations_return_structured_results(self):
        cases = [
            request("project.list"),
            request("project.get"),
            request("workspace.stat"),
            request("workspace.list"),
            request("workspace.read", arguments={"path": "README.txt"}),
            request("git.status"),
            request("git.branch"),
            request("git.head"),
            request("git.diff"),
        ]
        expected_keys = {
            "protocol", "request_id", "project", "operation", "status",
            "started_at", "finished_at", "result", "error", "evidence",
        }

        for value in cases:
            with self.subTest(operation=value["operation"]):
                execution = self.run_core(value)
                result = execution.result
                self.assertEqual(set(result), expected_keys)
                self.assertEqual(result["protocol"], RESULT_PROTOCOL)
                self.assertEqual(result["status"], "PASS")
                serialized = json.dumps(result, sort_keys=True)
                self.assertNotIn("issue_number", serialized)
                self.assertNotIn("argv", serialized)
                self.assertNotIn(str(self.root), serialized)

    def test_project_list_does_not_require_selected_project_to_exist(self):
        value = request(
            "project.list",
            project={"tenant": "tenant-z", "name": "project-z", "environment": "dev"},
        )
        result = self.run_core(value).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(len(result["result"]["projects"]), 2)

    def test_missing_project_and_workspace_map_to_not_found(self):
        missing_project = request(
            "project.get",
            project={"tenant": "tenant-z", "name": "project-z", "environment": "dev"},
        )
        result_project = self.run_core(missing_project).result
        self.assertEqual(result_project["status"], "NOT_FOUND")
        self.assertEqual(result_project["error"], {"code": "project_not_found"})

        missing_workspace = request(
            "workspace.read",
            project={"tenant": "tenant-b", "name": "project-b", "environment": "dev"},
            arguments={"path": "README.txt"},
        )
        result_workspace = self.run_core(missing_workspace).result
        self.assertEqual(result_workspace["status"], "NOT_FOUND")
        self.assertEqual(result_workspace["error"], {"code": "workspace_not_found"})

    def test_invalid_request_and_confinement_map_to_refused(self):
        invalid = request("shell.run")
        result_invalid = self.run_core(invalid).result
        self.assertEqual(result_invalid["status"], "REFUSED")
        self.assertEqual(result_invalid["error"], {"code": "unknown_operation"})

        traversal = request("workspace.read", arguments={"path": "../escape.txt"})
        result_traversal = self.run_core(traversal).result
        self.assertEqual(result_traversal["status"], "REFUSED")
        self.assertEqual(result_traversal["error"], {"code": "path_escape_refused"})

    def test_workspace_stat_absent_is_a_successful_observation(self):
        value = request(
            "workspace.stat",
            project={"tenant": "tenant-b", "name": "project-b", "environment": "dev"},
        )
        result = self.run_core(value).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["state"], "ABSENT")
        self.assertEqual(result["evidence"]["workspace_state"], "ABSENT")

    def test_timeout_maps_to_timeout_without_raw_exception(self):
        with mock.patch("control_plane.g2a.core.git_head", side_effect=OperationTimeout("git_timeout")):
            result = self.run_core(request("git.head")).result
        self.assertEqual(result["status"], "TIMEOUT")
        self.assertEqual(result["error"], {"code": "git_timeout"})

    def test_unexpected_failure_is_redacted(self):
        with mock.patch("control_plane.g2a.core.ProjectResolver.get", side_effect=RuntimeError("sensitive internal detail")):
            result = self.run_core(request("project.get")).result
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], {"code": "internal_error"})
        self.assertNotIn("sensitive internal detail", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
