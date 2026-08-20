from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ADAPTER = load_module("control_bridge_g2b", "scripts/control_bridge_g2b.py")
PUBLISH = load_module("control_bridge_g2b_publish", "scripts/control_bridge_g2b_publish.py")

ACTOR_LOGIN = "leon337"
ACTOR_ID = 25_374_535
BRANCH_REF = "refs/heads/codex/control-bridge-g2b"


def request(operation: str = "workspace.write", request_id: str = "G2B-ADAPTER-0001") -> dict[str, object]:
    if operation == "workspace.write":
        arguments: dict[str, object] = {
            "path": "G2B-PILOT.txt",
            "content": "bounded pilot\n",
            "precondition": {"state": "ABSENT"},
        }
    elif operation == "rollback":
        arguments = {"original_request_id": "G2B-ADAPTER-ORIGINAL-0001"}
    else:
        arguments = {}
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_V1",
        "request_id": request_id,
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": operation,
        "arguments": arguments,
    }


def envelope(operation: str = "workspace.write", request_id: str = "G2B-ADAPTER-0001") -> dict[str, object]:
    return {"transport": {"issue_number": None}, "request": request(operation, request_id)}


def event() -> dict[str, object]:
    return {
        "ref": BRANCH_REF,
        "sender": {"login": ACTOR_LOGIN, "id": ACTOR_ID},
    }


def executor_result(operation: str = "workspace.write") -> dict[str, object]:
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_RESULT_V1",
        "request_id": "G2B-ADAPTER-0001",
        "request_digest": "a" * 64,
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "authority": "LEANDRO",
        "transport_principal": {"login": ACTOR_LOGIN, "actor_id": ACTOR_ID},
        "grant_id": "G2B-PILOT-20260820",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": operation,
        "path": "G2B-PILOT.txt" if operation == "workspace.write" else None,
        "started_at": "2026-08-20T12:00:00+00:00",
        "finished_at": "2026-08-20T12:00:01+00:00",
        "precondition": {"state": "ABSENT"} if operation == "workspace.write" else None,
        "before": {"exists": False, "size": None, "mode": None, "sha256": None},
        "after": {"exists": True, "size": 14, "mode": 384, "sha256": "b" * 64},
        "status": "PASS",
        "replayed": False,
        "rollback_request_id": None,
        "revocation_request_id": None,
        "error": None,
    }


class G2BGitHubAdapterTests(unittest.TestCase):
    def write_json(self, root: Path, name: str, value: object) -> Path:
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_envelope_is_exact_and_transport_metadata_never_enters_core_request(self) -> None:
        value = envelope()
        transport, core_request = ADAPTER.validate_envelope(value)

        self.assertEqual(transport, {"issue_number": None})
        self.assertEqual(core_request, request())
        self.assertNotIn("issue_number", core_request)
        self.assertNotIn("transport_principal", core_request)

        for invalid, error in (
            ({**value, "command": "execute"}, "unexpected_envelope_field"),
            ({"transport": {"issue_number": None, "token": "x"}, "request": request()}, "unexpected_transport_field"),
            ({"transport": {"issue_number": True}, "request": request()}, "invalid_issue_number"),
        ):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                ADAPTER.validate_envelope(invalid)

    def test_only_exact_push_event_branch_and_fixed_transitional_principal_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event_path = self.write_json(root, "event.json", event())
            ADAPTER.validate_push_event("push", event_path, ACTOR_LOGIN, ACTOR_ID)

            cases = (
                ("issues", event_path, ACTOR_LOGIN, ACTOR_ID, "unsupported_event"),
                ("push", event_path, "attacker", ACTOR_ID, "invalid_transport_principal"),
                ("push", event_path, ACTOR_LOGIN, ACTOR_ID + 1, "invalid_transport_principal"),
            )
            for event_name, path, login, actor_id, error in cases:
                with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                    ADAPTER.validate_push_event(event_name, path, login, actor_id)

            wrong_branch = self.write_json(root, "wrong-branch.json", {**event(), "ref": "refs/heads/main"})
            with self.assertRaisesRegex(ValueError, "unexpected_ref"):
                ADAPTER.validate_push_event("push", wrong_branch, ACTOR_LOGIN, ACTOR_ID)

            wrong_sender = self.write_json(
                root,
                "wrong-sender.json",
                {**event(), "sender": {"login": ACTOR_LOGIN, "id": ACTOR_ID + 1}},
            )
            with self.assertRaisesRegex(ValueError, "event_principal_mismatch"):
                ADAPTER.validate_push_event("push", wrong_sender, ACTOR_LOGIN, ACTOR_ID)

    def test_parsed_operations_select_only_four_exact_sudo_argv_arrays(self) -> None:
        expected_commands = {
            "workspace.write": "execute",
            "rollback": "rollback",
            "status": "status",
            "revoke": "revoke",
        }
        for operation, command in expected_commands.items():
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                event_path = self.write_json(root, "event.json", event())
                dispatch_path = self.write_json(root, "dispatch.json", envelope(operation))
                request_output = root / "request.json"
                result_output = root / "result.json"
                completed = subprocess.CompletedProcess(
                    args=[],
                    returncode=0,
                    stdout=(json.dumps(executor_result(operation), separators=(",", ":")) + "\n").encode(),
                    stderr=b"",
                )

                with patch.object(ADAPTER.subprocess, "run", return_value=completed) as invoked:
                    code = ADAPTER.execute_dispatch(
                        event_name="push",
                        event_path=event_path,
                        dispatch_file=dispatch_path,
                        request_output=request_output,
                        result_output=result_output,
                        actor_login=ACTOR_LOGIN,
                        actor_id=ACTOR_ID,
                    )

                self.assertEqual(code, 0)
                normalized = json.loads(request_output.read_text(encoding="utf-8"))
                self.assertEqual(
                    normalized,
                    {
                        "transport_principal": {"login": ACTOR_LOGIN, "actor_id": ACTOR_ID},
                        "request": request(operation),
                    },
                )
                invoked.assert_called_once_with(
                    [
                        "sudo",
                        "-n",
                        "-u",
                        "mcf-workspace",
                        "/usr/local/libexec/mcf-control-g2b",
                        command,
                    ],
                    input=invoked.call_args.kwargs["input"],
                    capture_output=True,
                    check=False,
                    timeout=60,
                    shell=False,
                    env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
                )
                self.assertEqual(json.loads(invoked.call_args.kwargs["input"]), normalized)
                self.assertEqual(json.loads(result_output.read_text(encoding="utf-8"))["status"], "PASS")

    def test_unknown_operation_is_refused_before_subprocess_selection(self) -> None:
        invalid = envelope()
        invalid["request"]["operation"] = "execute; id"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event_path = self.write_json(root, "event.json", event())
            dispatch_path = self.write_json(root, "dispatch.json", invalid)
            with patch.object(ADAPTER.subprocess, "run") as invoked, self.assertRaisesRegex(
                ValueError, "unknown_operation"
            ):
                ADAPTER.execute_dispatch(
                    event_name="push",
                    event_path=event_path,
                    dispatch_file=dispatch_path,
                    request_output=root / "request.json",
                    result_output=root / "result.json",
                    actor_login=ACTOR_LOGIN,
                    actor_id=ACTOR_ID,
                )
            invoked.assert_not_called()

    def test_committed_dormant_sentinel_writes_private_result_without_invoking_executor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event_path = self.write_json(root, "event.json", event())
            dispatch_path = self.write_json(
                root,
                "dispatch.json",
                envelope(request_id=ADAPTER.DORMANT_REQUEST_ID),
            )
            request_output = root / "request.json"
            result_output = root / "result.json"

            with patch.object(ADAPTER.subprocess, "run") as invoked:
                code = ADAPTER.execute_dispatch(
                    event_name="push",
                    event_path=event_path,
                    dispatch_file=dispatch_path,
                    request_output=request_output,
                    result_output=result_output,
                    actor_login=ACTOR_LOGIN,
                    actor_id=ACTOR_ID,
                )

            self.assertEqual(code, 0)
            invoked.assert_not_called()
            result = json.loads(result_output.read_text(encoding="utf-8"))
            self.assertEqual(result["status"], "REFUSED")
            self.assertEqual(result["error"], "dormant_request_id")
            self.assertEqual(stat.S_IMODE(request_output.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(result_output.stat().st_mode), 0o600)

    def test_private_atomic_outputs_refuse_symlink_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            protected = root / "protected.json"
            protected.write_text("unchanged", encoding="utf-8")
            link = root / "request.json"
            link.symlink_to(protected)

            with self.assertRaisesRegex(ValueError, "unsafe_output_path"):
                ADAPTER.atomic_write_private(link, b"replacement\n")
            self.assertEqual(protected.read_text(encoding="utf-8"), "unchanged")

    def test_executor_timeout_and_oversized_streams_are_bounded_safe_results(self) -> None:
        for side_effect, completed, expected_error in (
            (subprocess.TimeoutExpired(cmd="fixed", timeout=60), None, "executor_timeout"),
            (None, subprocess.CompletedProcess([], 2, b"x" * 8193, b""), "executor_output_too_large"),
            (None, subprocess.CompletedProcess([], 2, b"{}\n", b"x" * 8193), "executor_output_too_large"),
        ):
            with self.subTest(expected_error=expected_error), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                event_path = self.write_json(root, "event.json", event())
                dispatch_path = self.write_json(root, "dispatch.json", envelope("status"))
                kwargs = {"side_effect": side_effect} if side_effect is not None else {"return_value": completed}
                with patch.object(ADAPTER.subprocess, "run", **kwargs):
                    code = ADAPTER.execute_dispatch(
                        event_name="push",
                        event_path=event_path,
                        dispatch_file=dispatch_path,
                        request_output=root / "request.json",
                        result_output=root / "result.json",
                        actor_login=ACTOR_LOGIN,
                        actor_id=ACTOR_ID,
                    )
                self.assertEqual(code, 2)
                value = json.loads((root / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(value["status"], "TIMEOUT" if expected_error == "executor_timeout" else "FAILED")
                self.assertEqual(value["error"], expected_error)
                self.assertNotIn("fixed", json.dumps(value))
                self.assertLessEqual((root / "result.json").stat().st_size, 8192)

    def test_cli_starts_from_repository_root_without_pythonpath(self) -> None:
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        completed = subprocess.run(
            [sys.executable, "scripts/control_bridge_g2b.py", "--help"],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=15,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


class G2BPublisherTests(unittest.TestCase):
    def test_markdown_escapes_all_safe_fields_and_never_serializes_forbidden_payloads(self) -> None:
        hostile = "<tag>`*_[]()#!|>\nnext"
        result = executor_result()
        for field in (
            "request_id",
            "operation",
            "path",
            "status",
            "error",
            "grant_id",
            "started_at",
            "finished_at",
            "receipt_id",
        ):
            result[field] = hostile
        result["project"] = {"tenant": hostile, "name": hostile, "environment": hostile}
        result["before"] = {"sha256": hostile, "content": "BEFORE_SECRET_BYTES"}
        result["after"] = {"sha256": hostile, "snapshot": "AFTER_SECRET_BYTES"}
        result["content"] = "TOP_LEVEL_SECRET_BYTES"
        result["snapshot"] = "TOP_LEVEL_SNAPSHOT_BYTES"
        result["exception"] = "RAW_EXCEPTION_SECRET"

        body = PUBLISH.markdown(result)

        self.assertLess(len(body), 60_000)
        self.assertIn("&lt;tag&gt;", body)
        self.assertNotIn("<tag>", body)
        self.assertNotIn("\nnext", body)
        for forbidden in (
            "BEFORE_SECRET_BYTES",
            "AFTER_SECRET_BYTES",
            "TOP_LEVEL_SECRET_BYTES",
            "TOP_LEVEL_SNAPSHOT_BYTES",
            "RAW_EXCEPTION_SECRET",
        ):
            self.assertNotIn(forbidden, body)

    def test_markdown_is_strictly_capped_below_sixty_thousand_characters(self) -> None:
        result = executor_result()
        result["request_id"] = "🙂" * 100_000
        body = PUBLISH.markdown(result)
        self.assertLess(len(body), 60_000)
        self.assertLess(len(body.encode("utf-8")), 60_000)

    def test_issue_number_is_read_only_from_exact_transport_and_null_skips_publication(self) -> None:
        self.assertEqual(PUBLISH.issue_number({"transport": {"issue_number": 6}, "request": request()}), 6)
        self.assertIsNone(PUBLISH.issue_number({"transport": {"issue_number": None}, "request": request()}))
        self.assertIsNone(PUBLISH.issue_number({"transport": {"issue_number": True}, "request": request()}))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            dispatch_path = root / "dispatch.json"
            result_path = root / "result.json"
            summary_path = root / "summary.md"
            dispatch_path.write_text(json.dumps(envelope()), encoding="utf-8")
            result_path.write_text(json.dumps(executor_result()), encoding="utf-8")
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", [
                    "control_bridge_g2b_publish.py",
                    "--dispatch-file", str(dispatch_path),
                    "--result-file", str(result_path),
                    "--summary-file", str(summary_path),
                ]),
                patch.object(sys, "stdout", stdout),
                patch.dict(os.environ, {}, clear=True),
            ):
                code = PUBLISH.main()

            self.assertEqual(code, 0)
            self.assertIn("reason=no_issue_number", stdout.getvalue())
            self.assertIn("G2-B Result", summary_path.read_text(encoding="utf-8"))


class G2BWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = ROOT / ".github" / "workflows" / "control-bridge-g2b.yml"
        cls.text = cls.path.read_text(encoding="utf-8")
        cls.workflow = yaml.load(cls.text, Loader=yaml.BaseLoader)

    def test_dispatch_and_example_are_exact_and_committed_dispatch_is_dormant(self) -> None:
        dispatch = json.loads((ROOT / "control" / "dispatch" / "g2b.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / "control" / "examples" / "g2b-request.example.json").read_text(encoding="utf-8"))

        for value in (dispatch, example):
            self.assertEqual(set(value), {"transport", "request"})
            self.assertEqual(set(value["transport"]), {"issue_number"})
            self.assertEqual(value["request"]["protocol"], "MCF_WORKSPACE_MUTATION_V1")
        self.assertIsNone(dispatch["transport"]["issue_number"])
        self.assertEqual(dispatch["request"]["request_id"], ADAPTER.DORMANT_REQUEST_ID)
        ADAPTER.validate_envelope(dispatch)

    def test_workflow_trigger_permissions_runner_timeout_and_concurrency_are_semantically_exact(self) -> None:
        trigger = self.workflow["on"]
        self.assertEqual(set(trigger), {"push"})
        self.assertEqual(trigger["push"]["branches"], ["codex/control-bridge-g2b"])
        self.assertEqual(trigger["push"]["paths"], ["control/dispatch/g2b.json"])
        self.assertEqual(self.workflow["permissions"], {"contents": "read", "issues": "write"})
        self.assertEqual(self.workflow["concurrency"]["cancel-in-progress"], "false")

        self.assertEqual(set(self.workflow["jobs"]), {"mutate"})
        job = self.workflow["jobs"]["mutate"]
        self.assertEqual(job["runs-on"], ["self-hosted", "linux", "x64", "node-01", "mcf-control"])
        self.assertLessEqual(int(job["timeout-minutes"]), 10)

    def test_checkout_actor_transport_and_outcome_preservation_are_semantically_bounded(self) -> None:
        steps = self.workflow["jobs"]["mutate"]["steps"]
        checkout = next(step for step in steps if step.get("uses", "").startswith("actions/checkout@"))
        self.assertEqual(checkout["with"]["persist-credentials"], "false")

        execute = next(step for step in steps if step.get("id") == "execute")
        self.assertEqual(execute["continue-on-error"], "true")
        self.assertEqual(execute["env"]["CONTROL_BRIDGE_EVENT_NAME"], "${{ github.event_name }}")
        self.assertEqual(execute["env"]["CONTROL_BRIDGE_ACTOR_LOGIN"], "${{ github.actor }}")
        self.assertEqual(execute["env"]["CONTROL_BRIDGE_ACTOR_ID"], "${{ github.actor_id }}")
        self.assertIn("python3 scripts/control_bridge_g2b.py", execute["run"])

        publish = next(step for step in steps if step.get("id") == "publish")
        self.assertEqual(publish["if"], "always()")
        self.assertEqual(publish["continue-on-error"], "true")
        preserve = next(step for step in steps if step.get("id") == "preserve-executor-outcome")
        self.assertIn("steps.execute.outcome == 'failure'", preserve["if"])

        for step in steps:
            run = step.get("run", "")
            self.assertNotIn("request_id", run)
            self.assertNotIn("arguments", run)
            self.assertNotIn("content", run)
            self.assertNotIn("operation", run)
            self.assertNotIn("sudo ", run)


if __name__ == "__main__":
    unittest.main()
