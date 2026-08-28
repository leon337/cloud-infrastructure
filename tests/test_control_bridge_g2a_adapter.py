from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = load_module("control_bridge_g2a", "scripts/control_bridge_g2a.py")
PUBLISH = load_module("control_bridge_g2a_publish", "scripts/control_bridge_g2a_publish.py")

VALID_REQUEST = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-EXAMPLE-001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "project.get",
    "arguments": {},
}


class G2AGitHubAdapterTests(unittest.TestCase):
    def test_transport_envelope_never_enters_core_request(self):
        envelope = {"transport": {"issue_number": 12}, "request": dict(VALID_REQUEST)}
        transport, request = ADAPTER.validate_envelope(envelope)
        self.assertEqual(transport, {"issue_number": 12})
        self.assertEqual(request, VALID_REQUEST)
        self.assertNotIn("issue_number", request)

    def test_envelope_rejects_unknown_transport_and_top_level_fields(self):
        with self.assertRaisesRegex(ValueError, "unexpected_envelope_field"):
            ADAPTER.validate_envelope({"transport": {}, "request": VALID_REQUEST, "command": "x"})
        with self.assertRaisesRegex(ValueError, "unexpected_transport_field"):
            ADAPTER.validate_envelope({"transport": {"issue_number": 1, "token": "x"}, "request": VALID_REQUEST})

    def test_load_push_reads_fixed_dispatch_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / "dispatch.json"
            expected = {"transport": {"issue_number": 7}, "request": VALID_REQUEST}
            path.write_text(json.dumps(expected), encoding="utf-8")
            self.assertEqual(ADAPTER.load_envelope("push", path), expected)
            with self.assertRaisesRegex(ValueError, "unsupported_event"):
                ADAPTER.load_envelope("issues", path)

    def test_direct_cli_starts_from_repo_root_without_pythonpath(self):
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        completed = subprocess.run(
            [sys.executable, "scripts/control_bridge_g2a.py", "--help"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_publisher_uses_issue_number_only_from_transport(self):
        envelope = {"transport": {"issue_number": 22}, "request": VALID_REQUEST}
        self.assertEqual(PUBLISH.issue_number(envelope), 22)
        self.assertIsNone(PUBLISH.issue_number({"transport": {}, "request": VALID_REQUEST}))

    def test_markdown_is_compact_escaped_and_never_contains_attachment_bytes(self):
        envelope = {
            "transport": {"issue_number": 22},
            "request": dict(VALID_REQUEST, request_id="<unsafe>"),
        }
        result = {
            "protocol": "MCF_WORKSPACE_CONTROL_RESULT_V1",
            "request_id": "<unsafe>",
            "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
            "operation": "git.diff",
            "status": "PASS",
            "started_at": "2026-08-18T00:00:00Z",
            "finished_at": "2026-08-18T00:00:01Z",
            "result": {"content": None, "size": 200000, "delivery": "attachment"},
            "error": None,
            "evidence": {"workspace_state": "PRESENT"},
        }
        body = PUBLISH.markdown(envelope, result, attachment_present=True)
        self.assertLessEqual(len(body), 60000)
        self.assertIn("&lt;unsafe&gt;", body)
        self.assertNotIn("<unsafe>", body)
        self.assertIn("artifact", body.lower())
        self.assertNotIn("ATTACHMENT_SECRET_BYTES", body)

    def test_versioned_example_and_workflow_are_bounded(self):
        example = json.loads((ROOT / "control" / "examples" / "g2a-request.example.json").read_text(encoding="utf-8"))
        self.assertEqual(example["request"]["protocol"], "MCF_WORKSPACE_CONTROL_V1")

        workflow = (ROOT / ".github" / "workflows" / "control-bridge-g2a.yml").read_text(encoding="utf-8")
        self.assertIn("control/dispatch/g2a.json", workflow)
        self.assertIn("[self-hosted, linux, x64, node-01, mcf-control]", workflow)
        self.assertNotIn("types: [opened]", workflow)
        self.assertIn("issues: write", workflow)
        self.assertNotIn("sudo ", workflow)
        self.assertNotIn("docker ", workflow.lower())
        self.assertIn("actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09", workflow)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", workflow)

    def test_workflow_uses_existing_system_python_without_runtime_package_install(self):
        workflow = (ROOT / ".github" / "workflows" / "control-bridge-g2a.yml").read_text(encoding="utf-8")
        self.assertNotIn("venv", workflow.lower())
        self.assertNotIn("pip", workflow.lower())
        self.assertIn("import jsonschema, yaml", workflow)
        self.assertIn("python3 scripts/control_bridge_g2a.py", workflow)
        self.assertIn("python3 scripts/control_bridge_g2a_publish.py", workflow)


if __name__ == "__main__":
    unittest.main()
