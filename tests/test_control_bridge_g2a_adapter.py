from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

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

from control_plane.g2a import protected_reader as PROTECTED_READER

VALID_REQUEST = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-EXAMPLE-001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "project.get",
    "arguments": {},
}

PROTECTED_PROJECT = {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"}
PROTECTED_ARGV = [
    "sudo", "-n", "-u", "mcf-workspace",
    "/usr/local/libexec/mcf-control-g2a-protected-read",
]
RESULT_FIELDS = {
    "protocol", "request_id", "project", "operation", "status",
    "started_at", "finished_at", "result", "error", "evidence",
}


def protected_request(operation="workspace.read", arguments=None):
    return dict(VALID_REQUEST, project=dict(PROTECTED_PROJECT), operation=operation,
                arguments={"path": "G2B-PILOT.txt"} if arguments is None else arguments)


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


class G2AProtectedRoutingTests(unittest.TestCase):
    def setUp(self):
        self.manifest_root = ROOT / "platform" / "manifests"
        self.workspace_root = pathlib.Path("/deliberately/not/the/protected/root")

    @staticmethod
    def outcome(value, *, returncode=0, stderr=b"", error=None):
        return ADAPTER.ProcessOutcome(
            returncode=returncode,
            stdout=(json.dumps(value, separators=(",", ":")) + "\n").encode(),
            stderr=stderr,
            error=error,
        )

    @staticmethod
    def valid_result(request, *, content="safe pilot content\n"):
        encoded = content.encode("utf-8")
        if request["operation"] == "workspace.stat":
            payload = {"state": "PRESENT", "mode": 0o700}
        else:
            payload = {
                "path": "G2B-PILOT.txt", "encoding": "utf-8",
                "size": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest(),
                "content": content,
            }
        return {
            "protocol": "MCF_WORKSPACE_CONTROL_RESULT_V1",
            "request_id": request["request_id"], "project": dict(request["project"]),
            "operation": request["operation"], "status": "PASS",
            "started_at": "2026-09-07T12:00:00Z",
            "finished_at": "2026-09-07T12:00:01Z",
            "result": payload, "error": None,
            "evidence": {"workspace_state": "PRESENT"},
        }

    def execute(self, request, outcome):
        with patch.object(ADAPTER, "run_bounded_process", return_value=outcome) as invoked:
            execution = ADAPTER.execute_selected(
                request, manifest_root=self.manifest_root, workspace_root=self.workspace_root,
            )
        return execution, invoked

    def assert_failed_closed(self, execution):
        self.assertEqual(execution.result["status"], "FAILED")
        self.assertEqual(execution.result["error"], {"code": "protected_reader_failed"})
        self.assertEqual(execution.result["result"], {})

    def test_protected_stat_and_read_use_only_fixed_sudo_argv(self):
        for request in (
            protected_request("workspace.stat", {}),
            protected_request("workspace.read", {"path": "G2B-PILOT.txt"}),
        ):
            with self.subTest(operation=request["operation"]):
                result = self.valid_result(request)
                execution, invoked = self.execute(request, self.outcome(result))
                self.assertEqual(execution.result, result)
                invoked.assert_called_once()
                self.assertEqual(invoked.call_args.args[0], PROTECTED_ARGV)
                self.assertNotIn(str(self.workspace_root), invoked.call_args.args[0])
                self.assertEqual(json.loads(invoked.call_args.args[1]), request)
                self.assertEqual(invoked.call_args.kwargs, {"timeout_seconds": 15.0})

    def test_invalid_protected_arguments_refuse_before_privileged_spawn(self):
        cases = (
            (protected_request("workspace.stat", {"path": "."}), "protected_operation_refused"),
            (protected_request("workspace.read", {}), "protected_path_refused"),
            (protected_request("workspace.read", {"path": "README.md"}), "protected_path_refused"),
        )
        for request, code in cases:
            with self.subTest(request=request), \
                 patch.object(ADAPTER, "run_bounded_process") as bounded, \
                 patch.object(ADAPTER, "execute") as core:
                execution = ADAPTER.execute_selected(
                    request, manifest_root=self.manifest_root, workspace_root=self.workspace_root,
                )
                bounded.assert_not_called()
                core.assert_not_called()
                self.assertEqual(execution.result["status"], "REFUSED")
                self.assertEqual(execution.result["error"], {"code": code})

    def test_every_ordinary_operation_remains_unprivileged_core(self):
        requests = [
            dict(VALID_REQUEST),
            dict(VALID_REQUEST, operation="git.status"),
            dict(VALID_REQUEST, operation="workspace.stat"),
            dict(VALID_REQUEST, operation="workspace.read", arguments={"path": "README.md"}),
            dict(VALID_REQUEST, project=dict(PROTECTED_PROJECT), operation="git.status"),
        ]
        sentinel = object()
        for request in requests:
            with self.subTest(request=request), \
                 patch.object(ADAPTER, "execute", return_value=sentinel) as core, \
                 patch.object(ADAPTER, "run_bounded_process") as bounded:
                actual = ADAPTER.execute_selected(
                    request, manifest_root=self.manifest_root, workspace_root=self.workspace_root,
                )
                self.assertIs(actual, sentinel)
                core.assert_called_once_with(
                    request, manifest_root=self.manifest_root, workspace_root=self.workspace_root,
                )
                bounded.assert_not_called()

    def test_caller_selectable_execution_fields_are_rejected_before_selection(self):
        for field in ("backend", "workspace_root", "sudo", "uid", "cwd", "executable"):
            request = dict(protected_request(), **{field: "attacker-controlled"})
            with self.subTest(field=field), \
                 patch.object(ADAPTER, "run_bounded_process") as bounded, \
                 patch.object(ADAPTER, "execute") as core:
                execution = ADAPTER.execute_selected(
                    request, manifest_root=self.manifest_root, workspace_root=self.workspace_root,
                )
                bounded.assert_not_called()
                core.assert_not_called()
                self.assertEqual(execution.result["status"], "REFUSED")
                self.assertEqual(execution.result["error"], {"code": "unexpected_request_field"})

    def test_accepts_only_strict_correlated_pass_read(self):
        request = protected_request()
        result = self.valid_result(request)
        execution, _ = self.execute(request, self.outcome(result))
        self.assertEqual(set(execution.result), RESULT_FIELDS)
        self.assertEqual(execution.result, result)
        self.assertIsNone(execution.attachment)

    def test_accepts_only_strict_correlated_read_not_found(self):
        request = protected_request()
        result = self.valid_result(request)
        result.update(status="NOT_FOUND", result={}, error={"code": "path_not_found"})
        result["evidence"] = {}
        execution, _ = self.execute(request, self.outcome(result))
        self.assertEqual(execution.result, result)

    def test_accepts_real_stat_absent_contract(self):
        request = protected_request("workspace.stat", {})
        result = self.valid_result(request)
        result.update(result={"state": "ABSENT"}, evidence={"workspace_state": "ABSENT"})
        execution, _ = self.execute(request, self.outcome(result))
        self.assertEqual(execution.result, result)

    def test_adapter_accepts_real_protected_reader_cross_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspaces = pathlib.Path(temporary) / "workspaces"
            workspaces.mkdir()

            stat_request = protected_request("workspace.stat", {})
            absent = PROTECTED_READER._execute_at_root(stat_request, workspaces).result
            execution, _ = self.execute(stat_request, self.outcome(absent))
            self.assertEqual(execution.result, absent)

            workspace = workspaces / "leon337" / "g2a-smoke" / "dev"
            workspace.mkdir(parents=True)
            workspace.chmod(0o700)

            present = PROTECTED_READER._execute_at_root(stat_request, workspaces).result
            execution, _ = self.execute(stat_request, self.outcome(present))
            self.assertEqual(execution.result, present)

            read_request = protected_request("workspace.read", {"path": "G2B-PILOT.txt"})
            missing = PROTECTED_READER._execute_at_root(read_request, workspaces).result
            execution, _ = self.execute(read_request, self.outcome(missing))
            self.assertEqual(execution.result, missing)

    def test_rejects_not_found_for_workspace_stat(self):
        request = protected_request("workspace.stat", {})
        result = self.valid_result(request)
        result.update(
            status="NOT_FOUND", result={}, error={"code": "path_not_found"},
            evidence={"workspace_state": "ABSENT"},
        )
        execution, _ = self.execute(request, self.outcome(result))
        self.assert_failed_closed(execution)

    def test_rejects_extra_fields_at_every_protected_result_level(self):
        request = protected_request()
        candidates = []
        for location in ("top", "project", "result", "error", "evidence"):
            candidate = json.loads(json.dumps(self.valid_result(request)))
            if location == "top":
                candidate["debug"] = True
            elif location == "error":
                candidate.update(status="NOT_FOUND", result={}, error={"code": "path_not_found", "detail": "x"})
            else:
                candidate[location]["extra"] = "x"
            candidates.append((location, candidate))
        for location, candidate in candidates:
            with self.subTest(location=location):
                execution, _ = self.execute(request, self.outcome(candidate))
                self.assert_failed_closed(execution)

    def test_rejects_mismatched_identity_project_operation_and_path(self):
        request = protected_request()
        mutations = (
            ("request_id", "OTHER-ID"),
            ("project", {"tenant": "other", "name": "project", "environment": "dev"}),
            ("operation", "workspace.stat"),
        )
        for field, value in mutations:
            candidate = self.valid_result(request)
            candidate[field] = value
            with self.subTest(field=field):
                execution, _ = self.execute(request, self.outcome(candidate))
                self.assert_failed_closed(execution)
        candidate = self.valid_result(request)
        candidate["result"]["path"] = "README.md"
        execution, _ = self.execute(request, self.outcome(candidate))
        self.assert_failed_closed(execution)

    def test_rejects_invalid_encoding_size_digest_or_content_correlation(self):
        request = protected_request()
        mutations = (
            ("encoding", "UTF-8"),
            ("size", 65_537),
            ("size", -1),
            ("size", True),
            ("sha256", "A" * 64),
            ("sha256", "0" * 64),
            ("content", 7),
        )
        for field, value in mutations:
            candidate = self.valid_result(request)
            candidate["result"][field] = value
            with self.subTest(field=field, value=value):
                execution, _ = self.execute(request, self.outcome(candidate))
                self.assert_failed_closed(execution)

    def test_rejects_secret_like_protected_content_without_echo(self):
        request = protected_request()
        secret = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcd"
        candidate = self.valid_result(request, content=secret)
        execution, _ = self.execute(request, self.outcome(candidate))
        self.assert_failed_closed(execution)
        self.assertNotIn(secret, json.dumps(execution.result))

    def test_rejects_malformed_or_noncanonical_timestamps(self):
        request = protected_request()
        for field, value in (
            ("started_at", "not-a-time"),
            ("started_at", "2026-09-07T12:00:00+00:00"),
            ("finished_at", "2026-09-07 12:00:01Z"),
            ("finished_at", "2026-09-07T11:59:59Z"),
        ):
            candidate = self.valid_result(request)
            candidate[field] = value
            with self.subTest(field=field, value=value):
                execution, _ = self.execute(request, self.outcome(candidate))
                self.assert_failed_closed(execution)

    def test_raw_stderr_oversized_stdout_and_malformed_json_fail_closed(self):
        request = protected_request()
        outcomes = (
            ADAPTER.ProcessOutcome(0, json.dumps(self.valid_result(request)).encode(), b"raw secret stderr", None),
            ADAPTER.ProcessOutcome(0, b"{" + b"x" * 131_072, b"", "stdout_too_large"),
            ADAPTER.ProcessOutcome(0, b"not-json\n", b"", None),
            ADAPTER.ProcessOutcome(0, b"[]\n", b"", None),
        )
        for outcome in outcomes:
            with self.subTest(outcome=outcome):
                execution, _ = self.execute(request, outcome)
                self.assert_failed_closed(execution)
                self.assertNotIn("raw secret stderr", json.dumps(execution.result))

    def test_timeout_is_bounded_and_content_free(self):
        request = protected_request()
        outcome = ADAPTER.ProcessOutcome(None, b"partial secret", b"raw secret", "timeout")
        execution, _ = self.execute(request, outcome)
        self.assertEqual(execution.result["status"], "TIMEOUT")
        self.assertEqual(execution.result["error"], {"code": "operation_timeout"})
        self.assertEqual(execution.result["result"], {})
        self.assertNotIn("secret", json.dumps(execution.result))

    def test_nonzero_exit_fails_closed_without_subprocess_text(self):
        request = protected_request()
        outcome = ADAPTER.ProcessOutcome(2, b'{"status":"PASS"}\n', b"sudo diagnostic secret", None)
        execution, _ = self.execute(request, outcome)
        self.assert_failed_closed(execution)
        self.assertNotIn("sudo diagnostic secret", json.dumps(execution.result))

    def test_signal_process_group_falls_back_when_killpg_raises_oserror(self):
        process = Mock(pid=4321)
        with patch.object(ADAPTER.os, "killpg", side_effect=OSError("killpg unavailable")):
            ADAPTER._signal_process_group(process, signal.SIGTERM)
            process.terminate.assert_called_once_with()
            process.kill.assert_not_called()

        process.reset_mock()
        with patch.object(ADAPTER.os, "killpg", side_effect=OSError("killpg unavailable")):
            ADAPTER._signal_process_group(process, signal.SIGKILL)
            process.kill.assert_called_once_with()
            process.terminate.assert_not_called()

    def test_bounded_process_uses_exact_popen_boundary(self):
        real_popen = subprocess.Popen
        captured = {}

        def recording_popen(*args, **kwargs):
            captured.update(kwargs)
            return real_popen(*args, **kwargs)

        with patch.object(ADAPTER.subprocess, "Popen", side_effect=recording_popen):
            outcome = ADAPTER.run_bounded_process(
                [sys.executable, "-c", "pass"], b"", timeout_seconds=2,
            )

        self.assertEqual(outcome.returncode, 0)
        self.assertIsNone(outcome.error)
        self.assertEqual(captured["stdin"], subprocess.PIPE)
        self.assertEqual(captured["stdout"], subprocess.PIPE)
        self.assertEqual(captured["stderr"], subprocess.PIPE)
        self.assertIs(captured["shell"], False)
        self.assertEqual(captured["env"], ADAPTER._PROTECTED_ENV)
        self.assertIs(captured["start_new_session"], True)
        self.assertIs(captured["close_fds"], True)


if __name__ == "__main__":
    unittest.main()
