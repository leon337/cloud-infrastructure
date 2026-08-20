from __future__ import annotations

import ast
import copy
import importlib.util
import io
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import time
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
    request_value = request(operation)
    digest = hashlib.sha256(
        json.dumps(
            request_value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()
    if operation == "workspace.write":
        content = request_value["arguments"]["content"]
        assert isinstance(content, str)
        path = "G2B-PILOT.txt"
        precondition: dict[str, object] | None = {"state": "ABSENT"}
        before: dict[str, object] | None = {
            "exists": False,
            "size": None,
            "mode": None,
            "sha256": None,
        }
        after: dict[str, object] | None = {
            "exists": True,
            "size": 14,
            "mode": 420,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }
        status = "PASS"
        rollback_request_id = None
        revocation_request_id = None
    elif operation == "rollback":
        path = "G2B-PILOT.txt"
        precondition = None
        before = {"exists": True, "size": 14, "mode": 384, "sha256": "b" * 64}
        after = {"exists": False, "size": None, "mode": None, "sha256": None}
        status = "ROLLED_BACK"
        rollback_request_id = "G2B-ADAPTER-ORIGINAL-0001"
        revocation_request_id = None
    else:
        path = None
        precondition = None
        before = None
        after = None
        status = "REVOKED" if operation == "revoke" else "PASS"
        rollback_request_id = None
        revocation_request_id = "G2B-ADAPTER-0001" if operation == "revoke" else None
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_RESULT_V1",
        "request_id": "G2B-ADAPTER-0001",
        "request_digest": digest,
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "authority": "LEANDRO",
        "transport_principal": {"login": ACTOR_LOGIN, "actor_id": ACTOR_ID},
        "grant_id": "G2B-PILOT-20260820",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": operation,
        "path": path,
        "started_at": "2026-08-20T12:00:00+00:00",
        "finished_at": "2026-08-20T12:00:01+00:00",
        "precondition": precondition,
        "before": before,
        "after": after,
        "status": status,
        "replayed": False,
        "rollback_request_id": rollback_request_id,
        "revocation_request_id": revocation_request_id,
        "error": None,
    }


def executor_result_for_status(operation: str, status: str) -> dict[str, object]:
    value = executor_result(operation)
    errors = {
        "REFUSED": "state_read_failed",
        "CONFLICT": "request_id_conflict",
        "FAILED": "internal_error",
        "TIMEOUT": "lock_timeout",
    }
    value["status"] = status
    value["error"] = errors.get(status)
    if status in errors:
        value["before"] = None
        value["after"] = None
        if operation != "workspace.write":
            value["path"] = None
    if status in {"CONFLICT", "TIMEOUT"}:
        value["authority"] = None
        value["grant_id"] = None
    if operation == "revoke" and status != "REVOKED":
        value["revocation_request_id"] = None
    return value


def executor_result_for_error(operation: str, status: str, error: str) -> dict[str, object]:
    value = executor_result_for_status(operation, status)
    value["error"] = error
    if status == "FAILED" and error != "internal_error":
        if operation == "workspace.write":
            value["before"] = executor_result()["before"]
        elif operation == "rollback":
            value["path"] = "G2B-PILOT.txt"
            value["before"] = executor_result("rollback")["before"]
        if error == "mutation_reconciled_reverted":
            value["after"] = value["before"]
        elif error == "final_target_mismatch":
            value["after"] = executor_result()["after"]
    return value


def executor_result_for_rule(operation: str, rule: object, error: str | None) -> dict[str, object]:
    value = executor_result(operation)
    value["status"] = rule.status
    value["error"] = error
    if rule.grant_context == "absent":
        value["authority"] = None
        value["grant_id"] = None
    else:
        value["authority"] = "LEANDRO"
        value["grant_id"] = "G2B-PILOT-20260820"

    present = {"exists": True, "size": 14, "mode": 420, "sha256": "b" * 64}
    absent = {"exists": False, "size": None, "mode": None, "sha256": None}
    if rule.result_shape == "stateless":
        value["before"] = None
        value["after"] = None
        if operation != "workspace.write":
            value["path"] = None
    elif rule.result_shape == "same_state":
        value["before"] = present
        value["after"] = present
    elif rule.result_shape == "write_mutation":
        value["before"] = absent
        value["after"] = None if error == "final_target_indeterminate" else present
    elif rule.result_shape == "rollback_mutation":
        value["path"] = "G2B-PILOT.txt"
        value["before"] = present
        value["after"] = None if error == "final_target_indeterminate" else absent
    elif rule.result_shape == "reconciled_reverted":
        value["before"] = absent
        value["after"] = absent
    elif rule.result_shape == "reconciled_indeterminate":
        value["before"] = absent
        value["after"] = None
    if operation == "revoke" and rule.status != "REVOKED":
        value["revocation_request_id"] = None
    return value


class G2BGitHubAdapterTests(unittest.TestCase):
    def write_json(self, root: Path, name: str, value: object) -> Path:
        path = root / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def bounded_runner(self):
        runner = getattr(ADAPTER, "run_bounded_process", None)
        self.assertIsNotNone(runner, "bounded concurrent process runner is missing")
        return runner

    def assert_process_gone(self, pid: int) -> None:
        deadline = time.monotonic() + 1.0
        while Path(f"/proc/{pid}").exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(Path(f"/proc/{pid}").exists(), f"child {pid} still exists")

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
                completed = ADAPTER.ProcessOutcome(
                    returncode=0,
                    stdout=(json.dumps(executor_result(operation), separators=(",", ":")) + "\n").encode(),
                    stderr=b"",
                    error=None,
                )

                with patch.object(ADAPTER, "run_bounded_process", return_value=completed) as invoked:
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
                    invoked.call_args.args[1],
                    timeout_seconds=60,
                )
                self.assertEqual(json.loads(invoked.call_args.args[1]), normalized)
                self.assertEqual(
                    json.loads(result_output.read_text(encoding="utf-8"))["status"],
                    executor_result(operation)["status"],
                )

    def test_unknown_operation_is_refused_before_subprocess_selection(self) -> None:
        invalid = envelope()
        invalid["request"]["operation"] = "execute; id"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            event_path = self.write_json(root, "event.json", event())
            dispatch_path = self.write_json(root, "dispatch.json", invalid)
            with patch.object(ADAPTER, "run_bounded_process") as invoked, self.assertRaisesRegex(
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

            with patch.object(ADAPTER, "run_bounded_process") as invoked:
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
        for completed, expected_error in (
            (ADAPTER.ProcessOutcome(-15, b"", b"", "executor_timeout"), "executor_timeout"),
            (
                ADAPTER.ProcessOutcome(-15, b"x" * 8192, b"", "executor_output_too_large"),
                "executor_output_too_large",
            ),
            (
                ADAPTER.ProcessOutcome(-15, b"{}\n", b"x" * 8192, "executor_output_too_large"),
                "executor_output_too_large",
            ),
        ):
            with self.subTest(expected_error=expected_error), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                event_path = self.write_json(root, "event.json", event())
                dispatch_path = self.write_json(root, "dispatch.json", envelope("status"))
                with patch.object(ADAPTER, "run_bounded_process", return_value=completed):
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

    def test_exit_zero_empty_or_request_mismatched_result_fails_closed(self) -> None:
        invalid_results = [
            {},
            {**executor_result(), "request_id": "G2B-DIFFERENT-0001"},
            {**executor_result(), "operation": "status"},
            {
                **executor_result(),
                "transport_principal": {"login": ACTOR_LOGIN, "actor_id": ACTOR_ID + 1},
            },
        ]
        for invalid_result in invalid_results:
            with self.subTest(keys=sorted(invalid_result)), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                event_path = self.write_json(root, "event.json", event())
                dispatch_path = self.write_json(root, "dispatch.json", envelope())
                completed = ADAPTER.ProcessOutcome(
                    returncode=0,
                    stdout=(json.dumps(invalid_result, separators=(",", ":")) + "\n").encode(),
                    stderr=b"",
                    error=None,
                )
                with patch.object(ADAPTER, "run_bounded_process", return_value=completed):
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
                result = json.loads((root / "result.json").read_text(encoding="utf-8"))
                self.assertEqual(result["status"], "FAILED")
                self.assertEqual(result["error"], "invalid_executor_result")

    def test_executor_result_schema_types_semantics_and_correlations_are_exact(self) -> None:
        valid = executor_result()
        mutations = {
            "extra field": lambda value: value.update({"content": "SECRET"}),
            "protocol": lambda value: value.update({"protocol": "WRONG"}),
            "request digest": lambda value: value.update({"request_digest": "a" * 64}),
            "mission": lambda value: value.update({"mission_id": "OTHER"}),
            "declared actor": lambda value: value.update({"declared_actor": "OTHER"}),
            "authority": lambda value: value.update({"authority": "ROOT"}),
            "grant id type": lambda value: value.update({"grant_id": 1}),
            "project": lambda value: value.update(
                {"project": {"tenant": "other", "name": "g2a-smoke", "environment": "dev"}}
            ),
            "path": lambda value: value.update({"path": "../../secret"}),
            "started timestamp": lambda value: value.update({"started_at": "yesterday"}),
            "timestamp order": lambda value: value.update(
                {
                    "started_at": "2026-08-20T12:00:02+00:00",
                    "finished_at": "2026-08-20T12:00:01+00:00",
                }
            ),
            "precondition": lambda value: value.update({"precondition": {"state": "PRESENT"}}),
            "state fields": lambda value: value.update(
                {"after": {"exists": True, "size": 14, "mode": 384, "sha256": "b" * 64, "content": "x"}}
            ),
            "state hash": lambda value: value.update(
                {"after": {"exists": True, "size": 14, "mode": 384, "sha256": "B" * 64}}
            ),
            "after content correlation": lambda value: value.update(
                {"after": {"exists": True, "size": 14, "mode": 384, "sha256": "b" * 64}}
            ),
            "state size": lambda value: value.update(
                {"after": {"exists": True, "size": 65_537, "mode": 384, "sha256": "b" * 64}}
            ),
            "status": lambda value: value.update({"status": "SUCCESS"}),
            "success error": lambda value: value.update({"error": "raw exception payload"}),
            "status error semantics": lambda value: value.update(
                {"status": "FAILED", "error": "grant_missing"}
            ),
            "replayed type": lambda value: value.update({"replayed": "false"}),
            "rollback linkage": lambda value: value.update(
                {"rollback_request_id": "CONTENT-TUNNEL-UNRELATED"}
            ),
            "revocation linkage": lambda value: value.update(
                {"revocation_request_id": "CONTENT-TUNNEL-UNRELATED"}
            ),
        }
        candidates = [("valid", valid, 0)]
        for name, mutate in mutations.items():
            candidate = copy.deepcopy(valid)
            mutate(candidate)
            candidates.append((name, candidate, 2))

        for name, candidate, expected_code in candidates:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                event_path = self.write_json(root, "event.json", event())
                dispatch_path = self.write_json(root, "dispatch.json", envelope())
                completed = ADAPTER.ProcessOutcome(
                    returncode=0,
                    stdout=(json.dumps(candidate, separators=(",", ":")) + "\n").encode(),
                    stderr=b"",
                    error=None,
                )
                with patch.object(ADAPTER, "run_bounded_process", return_value=completed):
                    code = ADAPTER.execute_dispatch(
                        event_name="push",
                        event_path=event_path,
                        dispatch_file=dispatch_path,
                        request_output=root / "request.json",
                        result_output=root / "result.json",
                        actor_login=ACTOR_LOGIN,
                        actor_id=ACTOR_ID,
                    )
                self.assertEqual(code, expected_code)
                if expected_code:
                    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
                    self.assertEqual(result["error"], "invalid_executor_result")

    def test_dynamic_core_error_codes_remain_part_of_the_exact_result_contract(self) -> None:
        dynamic_cases = (
            ("workspace.write", "REFUSED", "unsafe_state_mode"),
            ("workspace.write", "FAILED", "write_cleanup_failed"),
            ("workspace.write", "FAILED", "write_durability_indeterminate"),
            ("workspace.write", "FAILED", "write_state_indeterminate"),
            ("workspace.write", "FAILED", "write_recovery_blocked"),
            ("workspace.write", "FAILED", "write_recovery_failed"),
            ("workspace.write", "FAILED", "write_revert_cleanup_failed"),
            ("workspace.write", "FAILED", "write_revert_durability_indeterminate"),
            ("rollback", "FAILED", "restore_cleanup_failed"),
            ("rollback", "FAILED", "restore_durability_indeterminate"),
            ("rollback", "FAILED", "restore_state_indeterminate"),
            ("rollback", "FAILED", "restore_recovery_blocked"),
            ("rollback", "FAILED", "restore_recovery_failed"),
            ("rollback", "FAILED", "restore_revert_cleanup_failed"),
            ("rollback", "FAILED", "restore_revert_durability_indeterminate"),
            ("rollback", "FAILED", "delete_cleanup_failed"),
            ("rollback", "FAILED", "delete_durability_indeterminate"),
            ("rollback", "FAILED", "delete_recovery_failed"),
        )
        for operation, status, code in dynamic_cases:
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            candidate = executor_result_for_error(operation, status, code)
            with self.subTest(operation=operation, code=code):
                ADAPTER.validate_executor_result(
                    candidate,
                    request_value,
                    parsed,
                    ACTOR_LOGIN,
                    ACTOR_ID,
                )

    def test_impossible_operation_error_reproductions_fail_both_validators(self) -> None:
        cases = (
            ("workspace.write", "delete_cleanup_failed"),
            ("workspace.write", "restore_cleanup_failed"),
            ("status", "write_cleanup_failed"),
        )
        for case in cases:
            operation, error, *explicit_status = case
            status = explicit_status[0] if explicit_status else "FAILED"
            candidate = executor_result_for_error(operation, status, error)
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            with self.subTest(operation=operation, error=error):
                with self.assertRaisesRegex(ValueError, "invalid_executor_result"):
                    ADAPTER.validate_executor_result(
                        candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                    )
                self.assertIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(envelope(operation), candidate),
                )

    def test_task4_error_surface_is_exhaustively_classified(self) -> None:
        from control_plane.g2b import executor as core_executor

        source_errors: set[str] = set()
        for relative in (
            "control_plane/g2b/executor.py", "control_plane/g2b/state.py",
            "control_plane/g2b/grant.py", "control_plane/g2b/protocol.py",
            "control_plane/g2b/workspace.py",
        ):
            tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Raise) or not isinstance(node.exc, ast.Call):
                    continue
                if not isinstance(node.exc.func, ast.Name) or node.exc.func.id not in {
                    "RefusedError", "ConflictError", "TimeoutError", "MutationStateError",
                }:
                    continue
                if not node.exc.args or not isinstance(node.exc.args[0], ast.Constant):
                    continue
                if isinstance(node.exc.args[0].value, str):
                    source_errors.add(node.exc.args[0].value)
        self.assertLessEqual(source_errors, core_executor.PUBLIC_RESULT_ERROR_CODES)
        self.assertIs(ADAPTER._RESULT_ERROR_CODES, core_executor.PUBLIC_RESULT_ERROR_CODES)
        self.assertIs(PUBLISH._CORE_ERROR_CODES, core_executor.PUBLIC_RESULT_ERROR_CODES)

    def test_adapter_task4_operation_status_error_cross_product_is_exact(self) -> None:
        statuses = ("REFUSED", "CONFLICT", "FAILED", "TIMEOUT")
        for operation in ("workspace.write", "rollback", "status", "revoke"):
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            for status in statuses:
                for error in ADAPTER._RESULT_ERROR_CODES:
                    rules = tuple(
                        rule for rule in ADAPTER.PUBLIC_RESULT_CONTRACT
                        if operation in rule.operations
                        and rule.status == status
                        and error in rule.errors
                    )
                    with self.subTest(operation=operation, status=status, error=error):
                        if rules:
                            for rule in rules:
                                ADAPTER.validate_executor_result(
                                    executor_result_for_rule(operation, rule, error),
                                    request_value, parsed, ACTOR_LOGIN, ACTOR_ID,
                                )
                        else:
                            candidate = executor_result_for_error(operation, status, error)
                            with self.assertRaisesRegex(ValueError, "invalid_executor_result"):
                                ADAPTER.validate_executor_result(
                                    candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                                )

    def test_actual_task4_success_and_refusal_results_pass_both_independent_validators(self) -> None:
        from control_plane.g2b.grant import TransportPrincipal
        from tests.test_g2b_executor import G2BExecutorTests

        core = G2BExecutorTests(methodName="test_authorized_absent_write_returns_pass_and_content_free_receipt")
        core.setUp()
        try:
            core.principal = TransportPrincipal(ACTOR_LOGIN, ACTOR_ID)
            core._write_grant(transport_principal_id=ACTOR_ID)
            requests = (
                request("status", "G2B-ACTUAL-STATUS-0001"),
                request("workspace.write", "G2B-ADAPTER-ORIGINAL-0001"),
                request("rollback", "G2B-ACTUAL-ROLLBACK-0001"),
                request("revoke", "G2B-ACTUAL-REVOKE-0001"),
                request("status", "G2B-ACTUAL-REFUSED-0001"),
            )
            observed = [core.execute(value) for value in requests]
        finally:
            core.tearDown()

        self.assertEqual(
            [(value["status"], value["error"]) for value in observed],
            [
                ("PASS", None),
                ("PASS", None),
                ("ROLLED_BACK", None),
                ("REVOKED", None),
                ("REFUSED", "grant_revoked"),
            ],
        )
        for request_value, result in zip(requests, observed, strict=True):
            parsed = ADAPTER.parse_request(request_value)
            ADAPTER.validate_executor_result(
                result, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
            )
            dispatch = {"transport": {"issue_number": None}, "request": request_value}
            self.assertNotIn(
                "invalid_publication_result",
                PUBLISH.markdown(dispatch, result),
            )

    def test_canonical_public_result_contract_is_immutable_and_shared_without_shared_validation(self) -> None:
        from control_plane.g2b import executor as core_executor

        contract = getattr(core_executor, "PUBLIC_RESULT_CONTRACT", None)
        fields = getattr(core_executor, "PUBLIC_RESULT_FIELDS", None)
        self.assertIsNotNone(contract, "Task 4 must publish one canonical result contract")
        self.assertIsInstance(contract, tuple)
        self.assertEqual(len(fields), 21)
        self.assertEqual(fields, ADAPTER.PUBLIC_RESULT_FIELDS)
        self.assertEqual(fields, PUBLISH.PUBLIC_RESULT_FIELDS)
        self.assertIs(contract, ADAPTER.PUBLIC_RESULT_CONTRACT)
        self.assertIs(contract, PUBLISH.PUBLIC_RESULT_CONTRACT)
        self.assertTrue(contract)
        for rule in contract:
            self.assertIsInstance(rule.operations, frozenset)
            self.assertIsInstance(rule.errors, frozenset)
            with self.assertRaises((AttributeError, TypeError)):
                rule.phase = "forged"
        self.assertIsNot(ADAPTER.validate_executor_result, PUBLISH._valid_full_result)

    def test_every_task4_public_result_constructor_declares_a_contract_phase(self) -> None:
        from control_plane.g2b import executor as core_executor

        source = (ROOT / "control_plane" / "g2b" / "executor.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        contract_phases = {rule.phase for rule in core_executor.PUBLIC_RESULT_CONTRACT}
        declared: set[str] = set()
        receipt_calls = 0
        public_result_builders = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            is_receipt = isinstance(node.func, ast.Attribute) and node.func.attr == "receipt"
            is_builder = isinstance(node.func, ast.Name) and node.func.id == "_public_result"
            is_transient = isinstance(node.func, ast.Name) and node.func.id == "_transient_result"
            if not (is_receipt or is_builder or is_transient):
                continue
            if is_receipt:
                receipt_calls += 1
            elif is_builder:
                public_result_builders += 1
            phase = next((keyword.value for keyword in node.keywords if keyword.arg == "phase"), None)
            self.assertIsNotNone(phase, f"unphased public result constructor at line {node.lineno}")
            for value in ast.walk(phase):
                if isinstance(value, ast.Constant) and value.value in contract_phases:
                    declared.add(value.value)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Name) and target.id == "phase" for target in targets):
                continue
            if isinstance(node.value, ast.Constant) and node.value.value in contract_phases:
                declared.add(node.value.value)
        self.assertGreaterEqual(receipt_calls, 8)
        self.assertGreaterEqual(public_result_builders, 3)
        self.assertEqual(declared, contract_phases)

    def test_real_task4_receipt_persistence_errors_are_accepted_with_grant_context(self) -> None:
        from control_plane.g2b.errors import RefusedError
        from control_plane.g2b.grant import TransportPrincipal
        from control_plane.g2b.state import StateStore
        from tests.test_g2b_executor import G2BExecutorTests, action_request

        for operation in ("status", "revoke"):
            with self.subTest(operation=operation):
                core = G2BExecutorTests(methodName="test_authorized_absent_write_returns_pass_and_content_free_receipt")
                core.setUp()
                try:
                    core.principal = TransportPrincipal(ACTOR_LOGIN, ACTOR_ID)
                    core._write_grant(transport_principal_id=ACTOR_ID)
                    original_create = StateStore._atomic_create
                    failed = False

                    def fail_first_create(store, *args, **kwargs):
                        nonlocal failed
                        if not failed:
                            failed = True
                            raise RefusedError("atomic_rename_unsupported")
                        return original_create(store, *args, **kwargs)

                    request_value = action_request(
                        f"G2B-REAL-PERSIST-{operation.upper()}", operation
                    )
                    with patch.object(StateStore, "_atomic_create", new=fail_first_create):
                        result = core.execute(request_value)
                finally:
                    core.tearDown()

                self.assertEqual((result["status"], result["error"]), (
                    "REFUSED", "atomic_rename_unsupported"
                ))
                self.assertEqual((result["authority"], result["grant_id"]), (
                    "LEANDRO", "G2B-PILOT-20260820"
                ))
                parsed = ADAPTER.parse_request(request_value)
                ADAPTER.validate_executor_result(
                    result, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                )
                self.assertNotIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(
                        {"transport": {"issue_number": None}, "request": request_value},
                        result,
                    ),
                )

    def test_real_task4_historical_reconciliation_errors_are_accepted_without_grant_context(self) -> None:
        from control_plane.g2b import executor as core_executor
        from control_plane.g2b.errors import RefusedError
        from control_plane.g2b.grant import TransportPrincipal
        from control_plane.g2b.state import StateStore
        from control_plane.g2b.workspace import inspect_target
        from tests.test_g2b_executor import G2BExecutorTests, write_request

        for operation in ("workspace.write", "rollback", "status", "revoke"):
            with self.subTest(operation=operation):
                core = G2BExecutorTests(methodName="test_authorized_absent_write_returns_pass_and_content_free_receipt")
                core.setUp()
                try:
                    core.principal = TransportPrincipal(ACTOR_LOGIN, ACTOR_ID)
                    core._write_grant(transport_principal_id=ACTOR_ID)
                    target = core.workspace / "G2B-PILOT.txt"
                    target.write_bytes(b"original\n")
                    os.chmod(target, 0o600)
                    before = inspect_target(
                        core.workspace, "G2B-PILOT.txt", expected_uid=core.expected_uid
                    )
                    interrupted = write_request("G2B-HISTORICAL-PREPARED", "mutated\n")
                    interrupted["arguments"]["precondition"] = {"sha256": before.sha256}
                    with patch.object(core_executor, "atomic_write", side_effect=SystemExit):
                        with self.assertRaises(SystemExit):
                            core.execute(interrupted)
                    request_value = (
                        request(operation, f"G2B-REAL-RECONCILE-{operation.upper().replace('.', '-')}")
                    )
                    with patch.object(
                        StateStore,
                        "delete_snapshot",
                        side_effect=RefusedError("snapshot_delete_failed"),
                    ):
                        result = core.execute(request_value)
                finally:
                    core.tearDown()

                self.assertEqual((result["status"], result["error"]), (
                    "REFUSED", "snapshot_delete_failed"
                ))
                self.assertIsNone(result["authority"])
                self.assertIsNone(result["grant_id"])
                parsed = ADAPTER.parse_request(request_value)
                ADAPTER.validate_executor_result(
                    result, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                )
                self.assertNotIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(
                        {"transport": {"issue_number": None}, "request": request_value},
                        result,
                    ),
                )

    def test_reviewed_impossible_phase_context_shapes_fail_both_validators(self) -> None:
        cases = (
            (
                "grant load failure with grant context",
                "status",
                {"status": "REFUSED", "error": "grant_missing"},
            ),
            (
                "lock timeout with grant context",
                "status",
                {"status": "TIMEOUT", "error": "lock_timeout"},
            ),
            (
                "post-grant conflict without grant context",
                "revoke",
                {
                    "status": "CONFLICT", "error": "active_mutation_exists",
                    "authority": None, "grant_id": None,
                },
            ),
            (
                "inspected precondition conflict without states",
                "workspace.write",
                {
                    "status": "CONFLICT", "error": "precondition_mismatch",
                    "before": None, "after": None,
                },
            ),
            (
                "caught fixed recovery operation error",
                "status",
                {"status": "REFUSED", "error": "invalid_recovery_operation"},
            ),
        )
        for name, operation, changes in cases:
            candidate = executor_result_for_status(operation, changes["status"])
            candidate.update(changes)
            if name in {"grant load failure with grant context", "lock timeout with grant context"}:
                candidate.update({"authority": "LEANDRO", "grant_id": "G2B-PILOT-20260820"})
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "invalid_executor_result"):
                    ADAPTER.validate_executor_result(
                        candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                    )
                self.assertIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(envelope(operation), candidate),
                )

    def test_adapter_operation_status_cross_product_is_exact(self) -> None:
        statuses = ("PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK", "REVOKED")
        allowed = {
            "workspace.write": {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT"},
            "rollback": {"REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK"},
            "status": {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT"},
            "revoke": {"REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "REVOKED"},
        }
        for operation, valid_statuses in allowed.items():
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            for status in statuses:
                candidate = executor_result_for_status(operation, status)
                with self.subTest(operation=operation, status=status):
                    if status in valid_statuses:
                        ADAPTER.validate_executor_result(
                            candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                        )
                    else:
                        with self.assertRaisesRegex(ValueError, "invalid_executor_result"):
                            ADAPTER.validate_executor_result(
                                candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                            )

    def test_workspace_write_forged_terminal_statuses_fail_adapter_closed(self) -> None:
        for status in ("ROLLED_BACK", "REVOKED"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                completed = ADAPTER.ProcessOutcome(
                    returncode=0,
                    stdout=(json.dumps(executor_result_for_status("workspace.write", status)) + "\n").encode(),
                    stderr=b"",
                    error=None,
                )
                with patch.object(ADAPTER, "run_bounded_process", return_value=completed):
                    code = ADAPTER.execute_dispatch(
                        event_name="push",
                        event_path=self.write_json(root, "event.json", event()),
                        dispatch_file=self.write_json(root, "dispatch.json", envelope()),
                        request_output=root / "request.json",
                        result_output=root / "result.json",
                        actor_login=ACTOR_LOGIN,
                        actor_id=ACTOR_ID,
                    )
                self.assertEqual(code, 2)
                persisted = json.loads((root / "result.json").read_text(encoding="utf-8"))
                self.assertEqual((persisted["status"], persisted["error"]), (
                    "FAILED", "invalid_executor_result"
                ))

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

    def test_bounded_process_enforces_stdout_and_stderr_hard_limits(self) -> None:
        runner = self.bounded_runner()
        cases = (
            ("import os,time; os.write(1,b'x'*100000); time.sleep(10)", "stdout"),
            ("import os,time; os.write(2,b'x'*100000); time.sleep(10)", "stderr"),
        )
        for program, stream in cases:
            with self.subTest(stream=stream):
                outcome = runner([sys.executable, "-c", program], b"", timeout_seconds=2)
                self.assertEqual(outcome.error, "executor_output_too_large")
                self.assertLessEqual(len(outcome.stdout), 8192)
                self.assertLessEqual(len(outcome.stderr), 8192)
                self.assertIsNotNone(outcome.returncode)

    def test_bounded_process_drains_stdout_and_stderr_concurrently(self) -> None:
        runner = self.bounded_runner()
        program = (
            "import os,threading; "
            "a=threading.Thread(target=lambda:os.write(1,b'a'*8000)); "
            "b=threading.Thread(target=lambda:os.write(2,b'b'*8000)); "
            "a.start();b.start();a.join();b.join()"
        )
        outcome = runner([sys.executable, "-c", program], b"", timeout_seconds=2)
        self.assertIsNone(outcome.error)
        self.assertEqual(outcome.returncode, 0)
        self.assertEqual(outcome.stdout, b"a" * 8000)
        self.assertEqual(outcome.stderr, b"b" * 8000)

    def test_bounded_process_timeout_terminates_and_reaps_child(self) -> None:
        runner = self.bounded_runner()
        program = "import os,time; print(os.getpid(),flush=True); time.sleep(10)"
        outcome = runner([sys.executable, "-c", program], b"", timeout_seconds=0.1)
        self.assertEqual(outcome.error, "executor_timeout")
        pid = int(outcome.stdout.decode("ascii").strip())
        self.assert_process_gone(pid)

    def test_bounded_process_escalates_to_kill_when_termination_is_ignored(self) -> None:
        runner = self.bounded_runner()
        program = (
            "import os,signal,time; "
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); "
            "print(os.getpid(),flush=True); time.sleep(10)"
        )
        started = time.monotonic()
        outcome = runner([sys.executable, "-c", program], b"", timeout_seconds=0.1)
        elapsed = time.monotonic() - started
        self.assertEqual(outcome.error, "executor_timeout")
        self.assertLess(elapsed, 2.0)
        pid = int(outcome.stdout.decode("ascii").strip())
        self.assert_process_gone(pid)

    def test_bounded_process_timeout_covers_inherited_pipes_and_process_group(self) -> None:
        runner = self.bounded_runner()
        grandchild = (
            "import signal,time; "
            "signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(2)"
        )
        program = (
            "import subprocess,sys; "
            f"child=subprocess.Popen([sys.executable,'-c',{grandchild!r}]); "
            "print(child.pid,flush=True)"
        )
        started = time.monotonic()
        outcome = runner([sys.executable, "-c", program], b"", timeout_seconds=0.1)
        elapsed = time.monotonic() - started
        self.assertEqual(outcome.error, "executor_timeout")
        self.assertLess(elapsed, 1.0)
        pid = int(outcome.stdout.decode("ascii").strip())
        self.assert_process_gone(pid)

    def test_bounded_process_uses_exact_environment_and_never_a_shell(self) -> None:
        runner = self.bounded_runner()
        literal = "$(printf SHELL_INTERPOLATED)"
        program = (
            "import json,os,sys; "
            "print(json.dumps({'environment':dict(os.environ),'argument':sys.argv[1]},sort_keys=True))"
        )
        outcome = runner(
            [sys.executable, "-c", program, literal],
            b"",
            timeout_seconds=2,
        )
        self.assertIsNone(outcome.error)
        observed = json.loads(outcome.stdout)
        self.assertEqual(
            observed["environment"],
            {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
        )
        self.assertEqual(observed["argument"], literal)


class G2BPublisherTests(unittest.TestCase):
    def test_publisher_task4_operation_status_error_cross_product_is_exact(self) -> None:
        statuses = ("REFUSED", "CONFLICT", "FAILED", "TIMEOUT")
        for operation in ("workspace.write", "rollback", "status", "revoke"):
            for status in statuses:
                for error in PUBLISH._CORE_ERROR_CODES:
                    rules = tuple(
                        rule for rule in PUBLISH.PUBLIC_RESULT_CONTRACT
                        if operation in rule.operations
                        and rule.status == status
                        and error in rule.errors
                    )
                    with self.subTest(operation=operation, status=status, error=error):
                        if rules:
                            for rule in rules:
                                body = PUBLISH.markdown(
                                    envelope(operation),
                                    executor_result_for_rule(operation, rule, error),
                                )
                                self.assertNotIn("invalid_publication_result", body)
                        else:
                            body = PUBLISH.markdown(
                                envelope(operation),
                                executor_result_for_error(operation, status, error),
                            )
                            self.assertIn("invalid_publication_result", body)

    def test_publisher_operation_status_cross_product_is_exact(self) -> None:
        statuses = ("PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK", "REVOKED")
        allowed = {
            "workspace.write": {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT"},
            "rollback": {"REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "ROLLED_BACK"},
            "status": {"PASS", "REFUSED", "CONFLICT", "FAILED", "TIMEOUT"},
            "revoke": {"REFUSED", "CONFLICT", "FAILED", "TIMEOUT", "REVOKED"},
        }
        for operation, valid_statuses in allowed.items():
            for status in statuses:
                body = PUBLISH.markdown(
                    envelope(operation), executor_result_for_status(operation, status)
                )
                with self.subTest(operation=operation, status=status):
                    if status in valid_statuses:
                        self.assertNotIn("invalid_publication_result", body)
                    else:
                        self.assertIn("invalid_publication_result", body)

    def test_non_success_state_and_linkage_semantics_are_exact_in_both_validators(self) -> None:
        present = {"exists": True, "size": 14, "mode": 420, "sha256": "b" * 64}
        absent = {"exists": False, "size": None, "mode": None, "sha256": None}
        cases = (
            (
                "write conflict states differ",
                "workspace.write",
                {"status": "CONFLICT", "error": "active_mutation_exists", "before": present, "after": absent},
            ),
            (
                "write timeout has state",
                "workspace.write",
                {"status": "TIMEOUT", "error": "lock_timeout", "before": present, "after": present},
            ),
            (
                "write failed after without before",
                "workspace.write",
                {"status": "FAILED", "error": "internal_error", "before": None, "after": present},
            ),
            (
                "write internal failure has mutation state",
                "workspace.write",
                {"status": "FAILED", "error": "internal_error", "before": absent, "after": None},
            ),
            (
                "write mutation failure lacks before state",
                "workspace.write",
                {"status": "FAILED", "error": "write_cleanup_failed", "before": None, "after": None},
            ),
            (
                "write reconciled revert does not return to before state",
                "workspace.write",
                {"status": "FAILED", "error": "mutation_reconciled_reverted", "before": absent, "after": present},
            ),
            (
                "write final target indeterminate exposes after state",
                "workspace.write",
                {"status": "FAILED", "error": "final_target_indeterminate", "before": absent, "after": present},
            ),
            (
                "write final target mismatch omits observed after state",
                "workspace.write",
                {"status": "FAILED", "error": "final_target_mismatch", "before": absent, "after": None},
            ),
            (
                "write mutation failure omits validated grant context",
                "workspace.write",
                {
                    "status": "FAILED", "error": "write_cleanup_failed",
                    "authority": None, "grant_id": None, "before": absent, "after": present,
                },
            ),
            (
                "rollback conflict exposes path",
                "rollback",
                {"status": "CONFLICT", "error": "active_mutation_exists", "path": "G2B-PILOT.txt"},
            ),
            (
                "rollback failed after without before",
                "rollback",
                {
                    "status": "FAILED", "error": "internal_error", "path": "G2B-PILOT.txt",
                    "before": None, "after": present,
                },
            ),
            (
                "rollback internal failure has mutation state",
                "rollback",
                {
                    "status": "FAILED", "error": "internal_error", "path": "G2B-PILOT.txt",
                    "before": present, "after": None,
                },
            ),
            (
                "rollback mutation failure lacks before state",
                "rollback",
                {
                    "status": "FAILED", "error": "restore_cleanup_failed", "path": None,
                    "before": None, "after": None,
                },
            ),
            (
                "rollback mutation before state is absent",
                "rollback",
                {
                    "status": "FAILED", "error": "delete_cleanup_failed", "path": "G2B-PILOT.txt",
                    "before": absent,
                },
            ),
            (
                "rollback final target indeterminate exposes after state",
                "rollback",
                {
                    "status": "FAILED", "error": "final_target_indeterminate", "path": "G2B-PILOT.txt",
                    "before": present, "after": absent,
                },
            ),
            (
                "rollback final target mismatch omits observed after state",
                "rollback",
                {
                    "status": "FAILED", "error": "final_target_mismatch", "path": "G2B-PILOT.txt",
                    "before": present, "after": None,
                },
            ),
            (
                "rollback success before state is absent",
                "rollback",
                {"status": "ROLLED_BACK", "error": None, "before": absent, "after": absent},
            ),
            (
                "rollback missing original linkage",
                "rollback",
                {"status": "FAILED", "error": "internal_error", "rollback_request_id": None},
            ),
            (
                "status failure has state",
                "status",
                {"status": "FAILED", "error": "internal_error", "before": present},
            ),
            (
                "revoke failure has revocation linkage",
                "revoke",
                {
                    "status": "FAILED", "error": "internal_error",
                    "revocation_request_id": "G2B-ADAPTER-0001",
                },
            ),
        )
        for name, operation, changes in cases:
            candidate = executor_result_for_status(operation, changes["status"])
            candidate.update(changes)
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, "invalid_executor_result"):
                    ADAPTER.validate_executor_result(
                        candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                    )
                self.assertIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(envelope(operation), candidate),
                )

    def test_core_non_success_state_shapes_remain_accepted_by_both_validators(self) -> None:
        present = {"exists": True, "size": 14, "mode": 420, "sha256": "b" * 64}
        absent = {"exists": False, "size": None, "mode": None, "sha256": None}
        cases = (
            (
                "write precondition conflict",
                "workspace.write",
                {
                    "status": "CONFLICT", "error": "precondition_mismatch",
                    "authority": "LEANDRO", "grant_id": "G2B-PILOT-20260820",
                    "before": present, "after": present,
                },
            ),
            (
                "write mutation failure",
                "workspace.write",
                {
                    "status": "FAILED", "error": "write_cleanup_failed",
                    "before": absent, "after": present,
                },
            ),
            (
                "rollback mutation failure",
                "rollback",
                {
                    "status": "FAILED", "error": "delete_durability_indeterminate",
                    "path": "G2B-PILOT.txt", "before": present, "after": absent,
                },
            ),
        )
        for name, operation, changes in cases:
            candidate = executor_result_for_status(operation, changes["status"])
            candidate.update(changes)
            request_value = request(operation)
            parsed = ADAPTER.parse_request(request_value)
            with self.subTest(name=name):
                ADAPTER.validate_executor_result(
                    candidate, request_value, parsed, ACTOR_LOGIN, ACTOR_ID
                )
                self.assertNotIn(
                    "invalid_publication_result",
                    PUBLISH.markdown(envelope(operation), candidate),
                )

    def test_dynamic_core_error_code_is_publishable_only_as_a_valid_correlated_receipt(self) -> None:
        candidate = executor_result()
        candidate["status"] = "FAILED"
        candidate["error"] = "write_cleanup_failed"
        body = PUBLISH.markdown(envelope(), candidate)
        self.assertNotIn("invalid_publication_result", body)
        self.assertIn("write\\_cleanup\\_failed", body)

        mismatched = executor_result()
        mismatched["status"] = "FAILED"
        mismatched["error"] = "grant_missing"
        self.assertIn("invalid_publication_result", PUBLISH.markdown(envelope(), mismatched))

        oversized = executor_result()
        oversized["after"]["size"] = 65_537
        self.assertIn("invalid_publication_result", PUBLISH.markdown(envelope(), oversized))

        mismatched_hash = executor_result()
        mismatched_hash["after"]["sha256"] = "b" * 64
        self.assertIn("invalid_publication_result", PUBLISH.markdown(envelope(), mismatched_hash))

    def test_every_allowlisted_value_slot_rejects_arbitrary_payload_tunneling(self) -> None:
        canary = "RAW_EXCEPTION_PAYLOAD_SECRET"
        mutations = {
            "request id": lambda value: value.update({"request_id": canary}),
            "operation": lambda value: value.update({"operation": canary}),
            "project tenant": lambda value: value["project"].update({"tenant": canary}),
            "project name": lambda value: value["project"].update({"name": canary}),
            "project environment": lambda value: value["project"].update({"environment": canary}),
            "path": lambda value: value.update({"path": canary}),
            "status": lambda value: value.update({"status": canary}),
            "error": lambda value: value.update({"status": "FAILED", "error": canary}),
            "grant id": lambda value: value.update({"grant_id": canary}),
            "started timestamp": lambda value: value.update({"started_at": canary}),
            "finished timestamp": lambda value: value.update({"finished_at": canary}),
            "before hash": lambda value: value.update(
                {"before": {"exists": True, "size": 14, "mode": 384, "sha256": canary}}
            ),
            "after hash": lambda value: value.update(
                {"after": {"exists": True, "size": 14, "mode": 384, "sha256": canary}}
            ),
            "replay": lambda value: value.update({"replayed": canary}),
            "receipt id": lambda value: value.update({"receipt_id": canary}),
        }

        for name, mutate in mutations.items():
            candidate = copy.deepcopy(executor_result())
            mutate(candidate)
            with self.subTest(name=name):
                body = PUBLISH.markdown(envelope(), candidate)
                self.assertNotIn(canary, body.replace("\\", ""))
                self.assertIn("invalid_publication_result", body)

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

        body = PUBLISH.markdown(envelope(), result)

        self.assertLess(len(body), 60_000)
        self.assertIn("invalid_publication_result", body)
        self.assertNotIn("<tag>", body)
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
        body = PUBLISH.markdown(envelope(), result)
        self.assertLess(len(body), 60_000)
        self.assertLess(len(body.encode("utf-8")), 60_000)

        invalid_dispatch = envelope()
        invalid_dispatch["request"]["arguments"]["content"] = "\ud800"
        self.assertIn(
            "invalid_publication_result",
            PUBLISH.markdown(invalid_dispatch, executor_result()),
        )

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
