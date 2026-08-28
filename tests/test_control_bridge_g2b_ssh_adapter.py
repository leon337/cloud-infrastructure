from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "platform/control-bridge/mcf-control-g2b-ssh"
EXAMPLE = ROOT / "control/examples/g2b-ssh-request.example.json"
RUNBOOK = ROOT / "runbooks/control-bridge-g2b-ssh.md"
SSH_GRANT_PLAYBOOK = (
    ROOT / "automation/ansible/playbooks/issue-control-bridge-g2b-ssh-grant.yml"
)


def load_adapter():
    loader = importlib.machinery.SourceFileLoader("mcf_control_g2b_ssh", str(ADAPTER))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("adapter loader unavailable")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def request(operation: str = "status") -> dict[str, object]:
    arguments: dict[str, object]
    if operation == "workspace.write":
        arguments = {
            "path": "G2B-PILOT.txt",
            "content": "bounded\n",
            "precondition": {"state": "ABSENT"},
        }
    elif operation == "rollback":
        arguments = {"original_request_id": "G2B-SSH-WRITE-0001"}
    else:
        arguments = {}
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_V1",
        "request_id": "G2B-SSH-REQUEST-0001",
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": operation,
        "arguments": arguments,
    }


def public_result(value: dict[str, object], principal: dict[str, object]) -> dict[str, object]:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    import hashlib

    return {
        "protocol": "MCF_WORKSPACE_MUTATION_RESULT_V1",
        "request_id": value["request_id"],
        "request_digest": hashlib.sha256(encoded).hexdigest(),
        "mission_id": value["mission_id"],
        "declared_actor": value["declared_actor"],
        "authority": "LEANDRO",
        "transport_principal": principal,
        "grant_id": "G2B-SSH-TEST-GRANT",
        "project": value["project"],
        "operation": value["operation"],
        "path": None,
        "started_at": "2026-08-22T09:00:00+00:00",
        "finished_at": "2026-08-22T09:00:00+00:00",
        "precondition": None,
        "before": None,
        "after": None,
        "status": "PASS",
        "replayed": False,
        "rollback_request_id": None,
        "revocation_request_id": None,
        "error": None,
    }


class G2BSSHAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_adapter()

    def test_posix_principal_is_derived_from_exact_ubuntu_uid_and_gid(self) -> None:
        account = SimpleNamespace(pw_name="ubuntu", pw_uid=1000, pw_gid=1000)
        with (
            patch.object(self.module.os, "geteuid", return_value=1000),
            patch.object(self.module.os, "getegid", return_value=1000),
            patch.object(self.module.pwd, "getpwuid", return_value=account) as by_uid,
            patch.object(self.module.pwd, "getpwnam", return_value=account) as by_name,
        ):
            self.assertEqual(
                self.module.resolve_posix_principal(),
                {"login": "ubuntu", "actor_id": 1000},
            )
        by_uid.assert_called_once_with(1000)
        by_name.assert_called_once_with("ubuntu")

    def test_root_wrong_account_uid_alias_and_wrong_gid_fail_closed(self) -> None:
        cases = (
            (0, 0, SimpleNamespace(pw_name="root", pw_uid=0, pw_gid=0)),
            (1001, 1001, SimpleNamespace(pw_name="attacker", pw_uid=1001, pw_gid=1001)),
            (1001, 1001, SimpleNamespace(pw_name="ubuntu", pw_uid=1000, pw_gid=1000)),
            (1000, 1001, SimpleNamespace(pw_name="ubuntu", pw_uid=1000, pw_gid=1000)),
        )
        for uid, gid, account in cases:
            with self.subTest(uid=uid, gid=gid, account=account.pw_name):
                with (
                    patch.object(self.module.os, "geteuid", return_value=uid),
                    patch.object(self.module.os, "getegid", return_value=gid),
                    patch.object(self.module.pwd, "getpwuid", return_value=account),
                    patch.object(
                        self.module.pwd,
                        "getpwnam",
                        return_value=SimpleNamespace(pw_name="ubuntu", pw_uid=1000, pw_gid=1000),
                    ),
                ):
                    with self.assertRaisesRegex(ValueError, "invalid_posix_principal"):
                        self.module.resolve_posix_principal()

    def test_request_only_input_rejects_a_caller_supplied_principal(self) -> None:
        values = [
            {
                "transport_principal": {"login": "leon337", "actor_id": 25_374_535},
                "request": request(),
            },
            dict(request(), login="leon337"),
            dict(request(), actor_id=25_374_535),
        ]
        for value in values:
            with self.subTest(fields=sorted(value)):
                with patch.object(self.module, "run_bounded_process") as run:
                    code, result = self.module.execute_request_only(value, "status")
                self.assertEqual(code, 2)
                self.assertEqual(result, {"error": "invalid_request", "status": "REFUSED"})
                run.assert_not_called()

    def test_four_operations_select_only_exact_sudo_argv_and_derived_principal(self) -> None:
        principal = {"login": "ubuntu", "actor_id": 1000}
        commands = {
            "workspace.write": "execute",
            "rollback": "rollback",
            "status": "status",
            "revoke": "revoke",
        }
        for operation, command in commands.items():
            with self.subTest(operation=operation):
                value = request(operation)
                result = public_result(value, principal)
                outcome = self.module.ProcessOutcome(
                    0,
                    (json.dumps(result, sort_keys=True) + "\n").encode("utf-8"),
                    b"",
                    None,
                )
                with (
                    patch.object(self.module, "resolve_posix_principal", return_value=principal),
                    patch.object(self.module, "run_bounded_process", return_value=outcome) as run,
                ):
                    code, observed = self.module.execute_request_only(value, command)
                self.assertEqual((code, observed), (0, result))
                argv, payload = run.call_args.args
                self.assertEqual(
                    argv,
                    [
                        "/usr/bin/sudo",
                        "-n",
                        "-u",
                        "mcf-workspace",
                        "/usr/local/libexec/mcf-control-g2b",
                        command,
                    ],
                )
                self.assertEqual(run.call_args.kwargs, {"timeout_seconds": 60})
                envelope = json.loads(payload)
                self.assertEqual(
                    envelope,
                    {"transport_principal": principal, "request": value},
                )

    def test_verb_operation_mismatch_unknown_operation_and_forged_result_fail_closed(self) -> None:
        principal = {"login": "ubuntu", "actor_id": 1000}
        forged = public_result(request(), {"login": "leon337", "actor_id": 25_374_535})
        outcome = self.module.ProcessOutcome(
            0,
            (json.dumps(forged) + "\n").encode("utf-8"),
            b"",
            None,
        )
        with (
            patch.object(self.module, "resolve_posix_principal", return_value=principal),
            patch.object(self.module, "run_bounded_process", return_value=outcome) as run,
        ):
            self.assertEqual(
                self.module.execute_request_only(request(), "execute"),
                (2, {"error": "operation_mismatch", "status": "REFUSED"}),
            )
            invalid = request()
            invalid["operation"] = "shell"
            self.assertEqual(
                self.module.execute_request_only(invalid, "status"),
                (2, {"error": "unknown_operation", "status": "REFUSED"}),
            )
            code, result = self.module.execute_request_only(request(), "status")
        self.assertEqual(code, 2)
        self.assertEqual(result, {"error": "invalid_executor_result", "status": "REFUSED"})
        self.assertEqual(run.call_count, 1)

    def test_timeout_output_stderr_nonzero_and_invalid_json_are_never_forwarded(self) -> None:
        cases = (
            (self.module.ProcessOutcome(None, b"", b"", "executor_timeout"), "executor_timeout"),
            (self.module.ProcessOutcome(0, b"{}", b"x", None), "invalid_executor_result"),
            (self.module.ProcessOutcome(2, b'{"raw":"hidden"}', b"", None), "executor_boundary_failed"),
            (self.module.ProcessOutcome(0, b"not-json", b"", None), "invalid_executor_result"),
        )
        for outcome, error in cases:
            with self.subTest(error=error):
                with (
                    patch.object(
                        self.module,
                        "resolve_posix_principal",
                        return_value={"login": "ubuntu", "actor_id": 1000},
                    ),
                    patch.object(self.module, "run_bounded_process", return_value=outcome),
                ):
                    code, result = self.module.execute_request_only(request(), "status")
                self.assertEqual(code, 2)
                self.assertEqual(result, {"error": error, "status": "REFUSED"})
                self.assertNotIn("raw", json.dumps(result))

    def test_unbounded_or_injected_public_result_fields_are_not_forwarded(self) -> None:
        principal = {"login": "ubuntu", "actor_id": 1000}
        for field, hostile in (
            ("started_at", "secret=" + "x" * 4000),
            ("finished_at", "not-a-timestamp"),
            ("status", "PASS\nsecret"),
        ):
            with self.subTest(field=field):
                forged = public_result(request(), principal)
                forged[field] = hostile
                outcome = self.module.ProcessOutcome(
                    0,
                    (json.dumps(forged) + "\n").encode("utf-8"),
                    b"",
                    None,
                )
                with (
                    patch.object(
                        self.module,
                        "resolve_posix_principal",
                        return_value=principal,
                    ),
                    patch.object(self.module, "run_bounded_process", return_value=outcome),
                ):
                    code, result = self.module.execute_request_only(request(), "status")
                self.assertEqual(code, 2)
                self.assertEqual(
                    result,
                    {"error": "invalid_executor_result", "status": "REFUSED"},
                )
                self.assertNotIn("secret", json.dumps(result))

    def test_process_timeout_and_output_limit_are_enforced_on_real_children(self) -> None:
        oversized = self.module.run_bounded_process(
            [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x' * 9000)"],
            b"",
            timeout_seconds=2,
        )
        self.assertEqual(oversized.error, "executor_output_too_large")
        self.assertLessEqual(len(oversized.stdout), 8192)

        timed_out = self.module.run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            b"",
            timeout_seconds=0.05,
        )
        self.assertEqual(timed_out.error, "executor_timeout")
        self.assertIsNotNone(timed_out.returncode)

    def test_stdin_timeout_and_size_limit_fail_before_executor_invocation(self) -> None:
        input_stream = SimpleNamespace(buffer=SimpleNamespace(fileno=lambda: 123))
        with (
            patch.object(self.module.sys, "stdin", input_stream),
            patch.object(self.module.select, "select", return_value=([], [], [])) as wait,
        ):
            with self.assertRaisesRegex(ValueError, "input_timeout"):
                self.module._read_request()
        self.assertEqual(wait.call_args.args[:3], ([123], [], []))
        self.assertGreater(wait.call_args.args[3], 0)
        self.assertLessEqual(wait.call_args.args[3], 5)

        with tempfile.TemporaryFile() as oversized:
            oversized.write(b"x" * (131_072 + 1))
            oversized.seek(0)
            with patch.object(
                self.module.sys,
                "stdin",
                SimpleNamespace(buffer=oversized),
            ):
                with self.assertRaisesRegex(ValueError, "input_too_large"):
                    self.module._read_request()

    def test_main_reads_one_request_and_emits_one_bounded_json_object(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        expected = {"error": "grant_principal_mismatch", "status": "REFUSED"}
        observed_environment: dict[str, str] = {}

        def execute(value, command):
            observed_environment.update(self.module.os.environ)
            return 0, expected

        with (
            patch.object(self.module.sys, "argv", [str(ADAPTER), "status"]),
            patch.object(self.module.sys, "stdout", stdout),
            patch.object(self.module.sys, "stderr", stderr),
            patch.object(self.module, "_read_request", return_value=request()),
            patch.object(self.module, "execute_request_only", side_effect=execute),
            patch.dict(self.module.os.environ, {"HOSTILE": "must-be-cleared"}, clear=True),
        ):
            code = self.module.main()
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue()), expected)
        self.assertEqual(stdout.getvalue().count("\n"), 1)
        self.assertEqual(stderr.getvalue(), "")
        self.assertEqual(observed_environment, {})

    def test_source_has_no_shell_or_caller_selected_identity(self) -> None:
        text = ADAPTER.read_text(encoding="utf-8")
        self.assertIn("start_new_session=True", text)
        self.assertIn("shell=False", text)
        self.assertIn('pwd.getpwuid(uid)', text)
        self.assertIn('pwd.getpwnam("ubuntu")', text)
        self.assertNotIn("--actor-login", text)
        self.assertNotIn("--actor-id", text)
        self.assertNotIn("shell=True", text)
        self.assertNotIn("os.system", text)

    def test_example_runbook_and_ssh_grant_bind_the_real_posix_principal(self) -> None:
        example = json.loads(EXAMPLE.read_text(encoding="utf-8"))
        self.assertEqual(set(example), set(request()))
        self.assertNotIn("transport", example)
        self.assertNotIn("transport_principal", example)

        runbook = RUNBOOK.read_text(encoding="utf-8")
        for literal in (
            "ubuntu/<runtime POSIX UID>",
            "issue-control-bridge-g2b-ssh-grant.yml",
            "single active pilot grant",
            "HUMAN GATE",
            "/usr/local/libexec/mcf-control-g2b-ssh status",
        ):
            self.assertIn(literal, runbook)

        ssh_grant = SSH_GRANT_PLAYBOOK.read_text(encoding="utf-8")
        for literal in (
            "issue-control-bridge-g2b-grant.yml",
            "g2b_grant_transport_profile: ssh-posix-ubuntu",
        ):
            self.assertIn(literal, ssh_grant)

        grant = (
            ROOT / "automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml"
        ).read_text(encoding="utf-8")
        for literal in (
            "getent, passwd, ubuntu",
            "g2b_ssh_principal_account.stdout.split(':')[0] == 'ubuntu'",
            "g2b_ssh_principal_account.stdout.split(':')[2] | int",
            "'ubuntu' if g2b_issue_transport_profile == 'ssh-posix-ubuntu'",
            "declared_actor: MESTRE_MCF",
            "authority: LEANDRO",
            "g2b_issue_existing_grant.keys()",
            "86400",
        ):
            self.assertIn(literal, grant)
        self.assertNotIn("25374535", ssh_grant)

    def test_grant_reissue_allows_fresh_id_after_revocation_but_never_id_reuse(self) -> None:
        grant = (
            ROOT / "automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("not g2b_issue_requested_revocation.stat.exists", grant)
        self.assertIn("g2b_issue_existing_revocation.stat.exists or", grant)
        self.assertIn("Require safe provenance for an existing revocation sentinel", grant)
        self.assertIn("g2b_issue_existing_revocation.stat.mode == '0600'", grant)
        self.assertIn("g2b_issue_existing_revocation_value.grant_id ==", grant)
        self.assertNotIn(
            "not g2b_issue_existing_revocation.stat.exists",
            grant,
        )
        self.assertIn("fresh ID after revocation or expiry", grant)


if __name__ == "__main__":
    unittest.main()
