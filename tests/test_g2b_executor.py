from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from control_plane.g2b import executor as executor_module
from control_plane.g2b import workspace as workspace_module
from control_plane.g2b.errors import ConflictError, RefusedError
from control_plane.g2b.executor import execute_request
from control_plane.g2b.grant import TransportPrincipal, canonical_bundle_sha256
from control_plane.g2b.protocol import MUTATION_PROTOCOL
from control_plane.g2b.state import StateStore
from control_plane.g2b.workspace import MutationStateError, TargetState, inspect_target


NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
PILOT_PATH = "G2B-PILOT.txt"
GRANT_ID = "G2B-PILOT-20260820"


def write_request(request_id: str, content: str = "pilot\n") -> dict[str, object]:
    return {
        "protocol": MUTATION_PROTOCOL,
        "request_id": request_id,
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": "workspace.write",
        "arguments": {
            "path": PILOT_PATH,
            "content": content,
            "precondition": {"state": "ABSENT"},
        },
    }


def action_request(request_id: str, operation: str, **arguments: object) -> dict[str, object]:
    value = write_request(request_id)
    value["operation"] = operation
    value["arguments"] = arguments
    return value


class G2BExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir(mode=0o755)
        (self.bundle / "executor.py").write_bytes(b"installed bundle\n")
        self.bundle_digest = canonical_bundle_sha256(self.bundle)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(mode=0o700)
        self.state_root = self.root / "state"
        self.state_root.mkdir(mode=0o700)
        self.lock_path = self.root / "g2b.lock"
        self.lock_path.touch(mode=0o600)
        os.chmod(self.lock_path, 0o600)
        self.grant_path = self.root / "grant.json"
        self.expected_uid = os.geteuid()
        self.principal = TransportPrincipal("leon337", 337)
        self._write_grant()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_authorized_absent_write_returns_pass_and_content_free_receipt(self) -> None:
        result = self.execute(write_request("G2B-EXEC-0001"))

        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["error"])
        self.assertFalse(result["before"]["exists"])
        self.assertEqual(result["after"]["sha256"], hashlib.sha256(b"pilot\n").hexdigest())
        self.assertEqual((self.workspace / PILOT_PATH).read_bytes(), b"pilot\n")
        receipt_path = next((self.state_root / "receipts").iterdir())
        rendered = receipt_path.read_text(encoding="utf-8")
        self.assertNotIn('"content"', rendered)
        self.assertNotIn("pilot\\n", rendered)
        self.assertEqual(stat.S_IMODE(receipt_path.stat().st_mode), 0o600)

    def test_identical_request_replays_without_touching_target(self) -> None:
        request = write_request("G2B-EXEC-REPLAY-0001")
        first = self.execute(request)
        target = self.workspace / PILOT_PATH
        before_replay = target.stat()

        second = self.execute(request)
        after_replay = target.stat()

        self.assertEqual(first["status"], "PASS")
        self.assertEqual(second["status"], "PASS")
        self.assertTrue(second["replayed"])
        self.assertEqual(after_replay.st_ino, before_replay.st_ino)
        self.assertEqual(after_replay.st_mtime_ns, before_replay.st_mtime_ns)
        self.assertEqual(len(list((self.state_root / "receipts").iterdir())), 1)

    def test_same_request_id_with_changed_content_conflicts(self) -> None:
        request_id = "G2B-EXEC-ID-CONFLICT-0001"
        self.assertEqual(self.execute(write_request(request_id))["status"], "PASS")

        conflict = self.execute(write_request(request_id, "changed\n"))

        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["error"], "request_id_conflict")
        self.assertEqual((self.workspace / PILOT_PATH).read_bytes(), b"pilot\n")

    def test_second_unresolved_mutation_conflicts(self) -> None:
        self.assertEqual(self.execute(write_request("G2B-EXEC-ACTIVE-0001"))["status"], "PASS")

        conflict = self.execute(write_request("G2B-EXEC-ACTIVE-0002", "other\n"))

        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["error"], "active_mutation_exists")
        self.assertEqual((self.workspace / PILOT_PATH).read_bytes(), b"pilot\n")

    def test_rollback_deletes_exact_new_file_and_resolves_active_mutation(self) -> None:
        original_id = "G2B-EXEC-WRITE-ROLLBACK-0001"
        self.assertEqual(self.execute(write_request(original_id))["status"], "PASS")

        rollback = self.execute(
            action_request(
                "G2B-EXEC-ROLLBACK-0001",
                "rollback",
                original_request_id=original_id,
            )
        )

        self.assertEqual(rollback["status"], "ROLLED_BACK")
        self.assertEqual(rollback["rollback_request_id"], original_id)
        self.assertFalse((self.workspace / PILOT_PATH).exists())
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(store.active_recoveries(GRANT_ID), [])
        self.assertIsNone(store.load_snapshot(original_id))

    def test_overwrite_snapshots_prior_bytes_and_rollback_restores_exact_state(self) -> None:
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"original\n")
        os.chmod(target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        request = write_request("G2B-EXEC-OVERWRITE-0001", "mutated\n")
        request["arguments"]["precondition"] = {"sha256": original.sha256}

        written = self.execute(request)

        self.assertEqual(written["status"], "PASS")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(store.load_snapshot("G2B-EXEC-OVERWRITE-0001"), b"original\n")
        snapshot_path = next((self.state_root / "snapshots").iterdir())
        self.assertEqual(stat.S_IMODE(snapshot_path.stat().st_mode), 0o600)

        rolled_back = self.execute(
            action_request(
                "G2B-EXEC-OVERWRITE-ROLLBACK",
                "rollback",
                original_request_id="G2B-EXEC-OVERWRITE-0001",
            )
        )

        self.assertEqual(rolled_back["status"], "ROLLED_BACK")
        self.assertEqual(target.read_bytes(), b"original\n")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o600)
        self.assertIsNone(store.load_snapshot("G2B-EXEC-OVERWRITE-0001"))

    def test_rollback_target_drift_conflicts_without_deletion(self) -> None:
        original_id = "G2B-EXEC-DRIFT-WRITE-0001"
        self.assertEqual(self.execute(write_request(original_id))["status"], "PASS")
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"drifted\n")
        os.chmod(target, 0o644)

        rollback = self.execute(
            action_request(
                "G2B-EXEC-DRIFT-ROLLBACK-0001",
                "rollback",
                original_request_id=original_id,
            )
        )

        self.assertEqual(rollback["status"], "CONFLICT")
        self.assertEqual(rollback["error"], "target_changed")
        self.assertEqual(target.read_bytes(), b"drifted\n")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(len(store.active_recoveries(GRANT_ID)), 1)

    def test_revocation_after_rollback_succeeds_and_blocks_new_write(self) -> None:
        original_id = "G2B-EXEC-REVOKE-WRITE-0001"
        self.assertEqual(self.execute(write_request(original_id))["status"], "PASS")
        rollback = action_request(
            "G2B-EXEC-REVOKE-ROLLBACK-0001",
            "rollback",
            original_request_id=original_id,
        )
        self.assertEqual(self.execute(rollback)["status"], "ROLLED_BACK")

        revoked = self.execute(action_request("G2B-EXEC-REVOKE-0001", "revoke"))
        refused = self.execute(write_request("G2B-EXEC-POST-REVOKE-0001"))

        self.assertEqual(revoked["status"], "REVOKED")
        self.assertEqual(revoked["revocation_request_id"], "G2B-EXEC-REVOKE-0001")
        self.assertEqual(refused["status"], "REFUSED")
        self.assertEqual(refused["error"], "grant_revoked")
        self.assertFalse((self.workspace / PILOT_PATH).exists())

    def test_revoke_conflicts_while_a_mutation_is_active(self) -> None:
        self.assertEqual(self.execute(write_request("G2B-EXEC-REVOKE-ACTIVE-WRITE"))["status"], "PASS")

        result = self.execute(action_request("G2B-EXEC-REVOKE-ACTIVE", "revoke"))

        self.assertEqual(result["status"], "CONFLICT")
        self.assertEqual(result["error"], "active_mutation_exists")

    def test_expired_future_and_invalid_grants_are_refused(self) -> None:
        cases = (
            (
                "expired",
                {
                    "not_before": (NOW - timedelta(hours=24)).isoformat(),
                    "not_after": NOW.isoformat(),
                },
                "grant_not_active",
            ),
            (
                "future",
                {
                    "not_before": (NOW + timedelta(seconds=1)).isoformat(),
                    "not_after": (NOW + timedelta(hours=24, seconds=1)).isoformat(),
                },
                "grant_not_active",
            ),
            ("invalid", {"max_active_mutations": 2}, "invalid_grant"),
        )
        for index, (name, changes, expected_error) in enumerate(cases, start=1):
            with self.subTest(name=name):
                self._write_grant(**changes)
                result = self.execute(write_request(f"G2B-EXEC-GRANT-{index:04d}"))
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["error"], expected_error)
                self.assertFalse((self.workspace / PILOT_PATH).exists())

    def test_internal_exception_is_redacted_and_preserves_unresolved_recovery(self) -> None:
        raw_exception = "credential-internal-do-not-leak"
        with patch.object(executor_module, "atomic_write", side_effect=RuntimeError(raw_exception)):
            result = self.execute(write_request("G2B-EXEC-INTERNAL-0001"))

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "internal_error")
        rendered = json.dumps(result, sort_keys=True)
        self.assertNotIn(raw_exception, rendered)
        for candidate in self.state_root.rglob("*"):
            if candidate.is_file():
                self.assertNotIn(raw_exception, candidate.read_text(encoding="utf-8"))
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        active = store.active_recoveries(GRANT_ID)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["resolution"], "INDETERMINATE")

    def test_abrupt_exit_after_namespace_commit_is_reconciled_and_receipted(self) -> None:
        request = write_request("G2B-EXEC-CRASH-COMMIT-0001")
        real_atomic_write = executor_module.atomic_write

        def commit_then_exit(*args, **kwargs):
            real_atomic_write(*args, **kwargs)
            raise SystemExit("synthetic process death")

        with patch.object(executor_module, "atomic_write", side_effect=commit_then_exit):
            with self.assertRaises(SystemExit):
                self.execute(request)

        self.assertTrue((self.workspace / PILOT_PATH).exists())
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(store.lookup_recovery(request["request_id"])["resolution"], "PREPARED")
        self.assertIsNone(store.lookup_request(request["request_id"]))

        replay = self.execute(request)

        self.assertEqual(replay["status"], "PASS")
        self.assertTrue(replay["replayed"])
        recovery = store.lookup_recovery(request["request_id"])
        self.assertEqual(recovery["resolution"], "APPLIED")
        self.assertEqual(
            recovery["after"]["sha256"],
            hashlib.sha256(b"pilot\n").hexdigest(),
        )
        self.assertIsNotNone(store.lookup_request(request["request_id"]))

    def test_overwrite_exchange_crash_consumes_exact_displaced_original_before_pass(self) -> None:
        request, recovery_name = self._crash_overwrite_at_exchange(
            "G2B-EXEC-CRASH-EXCHANGE-0001"
        )
        target = self.workspace / PILOT_PATH
        self.assertEqual(target.read_bytes(), b"mutated\n")
        self.assertEqual((self.workspace / recovery_name).read_bytes(), b"original\n")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        prepared = store.lookup_recovery(request["request_id"])
        self.assertEqual(prepared["resolution"], "PREPARED")
        self.assertEqual(prepared["workspace_recovery_name"], recovery_name)

        replay = self.execute(request)

        self.assertEqual(replay["status"], "PASS")
        self.assertTrue(replay["replayed"])
        self.assertFalse((self.workspace / recovery_name).exists())
        recovery = store.lookup_recovery(request["request_id"])
        self.assertEqual(recovery["resolution"], "APPLIED")
        self.assertEqual(recovery["workspace_recovery_name"], recovery_name)

        rollback = self.execute(
            action_request(
                "G2B-EXEC-CRASH-EXCHANGE-ROLLBACK",
                "rollback",
                original_request_id=request["request_id"],
            )
        )
        self.assertEqual(rollback["status"], "ROLLED_BACK")
        self.assertEqual(target.read_bytes(), b"original\n")

    def test_multiple_exchange_recovery_candidates_remain_active_indeterminate(self) -> None:
        request, recovery_name = self._crash_overwrite_at_exchange(
            "G2B-EXEC-CRASH-AMBIGUOUS-0001"
        )
        duplicate_name = ".g2b-write-" + "f" * 32 + ".tmp"
        self.assertNotEqual(recovery_name, duplicate_name)
        duplicate = self.workspace / duplicate_name
        duplicate.write_bytes(b"original\n")
        os.chmod(duplicate, 0o600)

        result = self.execute(request)

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "mutation_state_indeterminate")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery(request["request_id"])
        self.assertEqual(recovery["resolution"], "INDETERMINATE")
        self.assertTrue(recovery["active"])
        self.assertTrue((self.workspace / recovery_name).exists())
        self.assertTrue(duplicate.exists())

    def test_unverifiable_exchange_recovery_candidate_remains_indeterminate(self) -> None:
        request, recovery_name = self._crash_overwrite_at_exchange(
            "G2B-EXEC-CRASH-UNVERIFIABLE-0001"
        )
        candidate = self.workspace / recovery_name
        candidate.unlink()
        candidate.symlink_to(self.workspace / PILOT_PATH)

        result = self.execute(request)

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "mutation_state_indeterminate")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery(request["request_id"])
        self.assertEqual(recovery["resolution"], "INDETERMINATE")
        self.assertTrue(recovery["active"])
        self.assertTrue(candidate.is_symlink())

    def test_ambiguous_candidate_on_applied_overwrite_blocks_rollback(self) -> None:
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"original\n")
        os.chmod(target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        request = write_request("G2B-EXEC-APPLIED-AMBIGUOUS", "mutated\n")
        request["arguments"]["precondition"] = {"sha256": before.sha256}
        self.assertEqual(self.execute(request)["status"], "PASS")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery(request["request_id"])
        first = self.workspace / recovery["workspace_recovery_name"]
        second = self.workspace / (".g2b-write-" + "e" * 32 + ".tmp")
        for candidate in (first, second):
            candidate.write_bytes(b"original\n")
            os.chmod(candidate, 0o600)

        rollback = self.execute(
            action_request(
                "G2B-EXEC-APPLIED-AMBIGUOUS-ROLLBACK",
                "rollback",
                original_request_id=request["request_id"],
            )
        )

        self.assertEqual(rollback["status"], "CONFLICT")
        self.assertEqual(rollback["error"], "mutation_state_indeterminate")
        self.assertEqual(target.read_bytes(), b"mutated\n")
        self.assertTrue(first.exists())
        self.assertTrue(second.exists())

    def test_applied_recovery_preserves_candidate_when_target_inode_is_replaced(self) -> None:
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"original\n")
        os.chmod(target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        request = write_request("G2B-EXEC-APPLIED-REPLACED-INODE", "mutated\n")
        request["arguments"]["precondition"] = {"sha256": before.sha256}
        real_unlink = workspace_module.os.unlink

        def fail_candidate_cleanup(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith(".g2b-write-"):
                raise OSError("synthetic cleanup failure")
            return real_unlink(path, *args, **kwargs)

        with patch.object(
            workspace_module.os, "unlink", side_effect=fail_candidate_cleanup
        ):
            failed = self.execute(request)

        self.assertEqual(failed["status"], "FAILED")
        self.assertEqual(failed["error"], "write_cleanup_failed")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        applied = store.lookup_recovery(request["request_id"])
        self.assertEqual(applied["resolution"], "APPLIED")
        candidate = self.workspace / applied["workspace_recovery_name"]
        self.assertTrue(candidate.exists())
        committed_inode = applied["after"]["inode"]

        displaced_committed = self.workspace / "displaced-committed-target"
        target.rename(displaced_committed)
        target.write_bytes(b"mutated\n")
        os.chmod(target, 0o600)
        replacement = inspect_target(
            self.workspace, PILOT_PATH, expected_uid=self.expected_uid
        )
        self.assertNotEqual(replacement.inode, committed_inode)
        self.assertEqual(replacement.sha256, applied["after"]["sha256"])

        status = self.execute(action_request("G2B-EXEC-APPLIED-REPLACED-STATUS", "status"))

        self.assertEqual(status["status"], "PASS")
        recovery = store.lookup_recovery(request["request_id"])
        self.assertEqual(recovery["resolution"], "INDETERMINATE")
        self.assertTrue(recovery["active"])
        self.assertTrue(candidate.exists())
        self.assertEqual(target.read_bytes(), b"mutated\n")

    def test_precommit_refusal_resolves_journal_and_releases_global_slot(self) -> None:
        with patch.object(
            executor_module,
            "atomic_write",
            side_effect=ConflictError("precondition_mismatch"),
        ):
            refused = self.execute(write_request("G2B-EXEC-PRECOMMIT-0001"))

        self.assertEqual(refused["status"], "CONFLICT")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery("G2B-EXEC-PRECOMMIT-0001")
        self.assertEqual(recovery["resolution"], "REVERTED")
        self.assertFalse(recovery["active"])
        self.assertEqual(store.active_recoveries(), [])

        passed = self.execute(write_request("G2B-EXEC-PRECOMMIT-0002"))
        self.assertEqual(passed["status"], "PASS")

    def test_active_mutation_blocks_write_under_a_reissued_grant(self) -> None:
        self.assertEqual(self.execute(write_request("G2B-EXEC-GLOBAL-WRITE-0001"))["status"], "PASS")
        self._write_grant(grant_id="G2B-PILOT-REISSUED")

        conflict = self.execute(write_request("G2B-EXEC-GLOBAL-WRITE-0002", "other\n"))

        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["error"], "active_mutation_exists")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(len(store.active_recoveries()), 1)

    def test_active_mutation_blocks_revocation_under_a_reissued_grant(self) -> None:
        self.assertEqual(self.execute(write_request("G2B-EXEC-GLOBAL-REVOKE-WRITE"))["status"], "PASS")
        self._write_grant(grant_id="G2B-PILOT-REISSUED")

        conflict = self.execute(action_request("G2B-EXEC-GLOBAL-REVOKE", "revoke"))

        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["error"], "active_mutation_exists")

    def test_corrupt_snapshot_cannot_be_restored_or_resolve_mutation(self) -> None:
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"original\n")
        os.chmod(target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        request = write_request("G2B-EXEC-CORRUPT-SNAPSHOT", "mutated!\n")
        request["arguments"]["precondition"] = {"sha256": original.sha256}
        self.assertEqual(self.execute(request)["status"], "PASS")
        snapshot = next((self.state_root / "snapshots").iterdir())
        snapshot.write_bytes(b"corrupt!\n")
        os.chmod(snapshot, 0o600)

        rollback = self.execute(
            action_request(
                "G2B-EXEC-CORRUPT-ROLLBACK",
                "rollback",
                original_request_id=request["request_id"],
            )
        )

        self.assertEqual(rollback["status"], "CONFLICT")
        self.assertEqual(rollback["error"], "snapshot_mismatch")
        self.assertEqual(target.read_bytes(), b"mutated!\n")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        self.assertEqual(len(store.active_recoveries()), 1)

    def test_indeterminate_rollback_drift_never_replaces_committed_baseline(self) -> None:
        original_id = "G2B-EXEC-ROLLBACK-BASELINE-WRITE"
        self.assertEqual(self.execute(write_request(original_id))["status"], "PASS")
        target = self.workspace / PILOT_PATH
        original_recovery = StateStore(
            self.state_root,
            self.lock_path,
            expected_uid=self.expected_uid,
        ).lookup_recovery(original_id)

        def drift_then_fail(*args, **kwargs):
            expected_current = kwargs["expected_current"]
            target.write_bytes(b"unrelated drift\n")
            os.chmod(target, 0o644)
            observed = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
            raise MutationStateError(
                "delete_durability_indeterminate",
                operation="delete",
                path=PILOT_PATH,
                before=expected_current,
                observed_after=observed,
                resolution="INDETERMINATE",
            )

        with patch.object(executor_module, "atomic_delete", side_effect=drift_then_fail):
            first = self.execute(
                action_request(
                    "G2B-EXEC-ROLLBACK-BASELINE-TRY1",
                    "rollback",
                    original_request_id=original_id,
                )
            )
        self.assertEqual(first["status"], "FAILED")

        recovery = StateStore(
            self.state_root,
            self.lock_path,
            expected_uid=self.expected_uid,
        ).lookup_recovery(original_id)
        self.assertEqual(recovery["after"], original_recovery["after"])

        second = self.execute(
            action_request(
                "G2B-EXEC-ROLLBACK-BASELINE-TRY2",
                "rollback",
                original_request_id=original_id,
            )
        )
        self.assertEqual(second["status"], "CONFLICT")
        self.assertEqual(second["error"], "mutation_state_indeterminate")
        self.assertEqual(target.read_bytes(), b"unrelated drift\n")

    def test_receipt_audit_failure_is_repaired_without_contradicting_pass(self) -> None:
        original_append = StateStore._append_audit
        failed = False

        def fail_once(store, event):
            nonlocal failed
            if event["event"] == "write" and not failed:
                failed = True
                raise RefusedError("synthetic_audit_failure")
            return original_append(store, event)

        with patch.object(StateStore, "_append_audit", new=fail_once):
            result = self.execute(write_request("G2B-EXEC-AUDIT-REPAIR"))

        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["error"])
        events = [
            json.loads(line)
            for line in (self.state_root / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        matching = [event for event in events if event["request_id"] == result["request_id"]]
        self.assertEqual(len(matching), 1)

        replay = self.execute(write_request("G2B-EXEC-AUDIT-REPAIR"))
        self.assertEqual(replay["status"], "PASS")
        self.assertTrue(replay["replayed"])

    def test_execution_requires_the_configured_service_uid(self) -> None:
        with patch("control_plane.g2b.executor.os.geteuid", return_value=self.expected_uid + 1):
            with patch.object(executor_module, "atomic_write") as mutation:
                result = self.execute(write_request("G2B-EXEC-UID-0001"))

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "execution_uid_mismatch")
        mutation.assert_not_called()

    def test_root_execution_is_explicitly_refused_before_state_access(self) -> None:
        with patch("control_plane.g2b.executor.os.geteuid", return_value=0):
            result = self.execute(
                write_request("G2B-EXEC-ROOT-REFUSED"),
                expected_uid=0,
            )

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "root_execution_refused")
        self.assertFalse((self.state_root / "receipts").exists())

    def test_rejected_unapproved_path_is_not_reflected_in_bounded_result(self) -> None:
        request = write_request("G2B-EXEC-BOUNDED-0001")
        request["arguments"]["path"] = "x" * 100_000

        result = self.execute(request)

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "grant_path_mismatch")
        self.assertIsNone(result["path"])
        self.assertLess(len(json.dumps(result)), 4096)

    def test_hostile_transport_principal_is_sanitized_and_result_is_bounded(self) -> None:
        hostile = TransportPrincipal("x" * 1_000_000, 337)

        result = self.execute(
            write_request("G2B-EXEC-HOSTILE-PRINCIPAL"),
            principal=hostile,
        )

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "invalid_transport_principal")
        self.assertIsNone(result["transport_principal"]["login"])
        self.assertLessEqual(len(json.dumps(result, separators=(",", ":"))), 8192)

    def test_applied_mutation_error_is_receipted_active_and_rollbackable(self) -> None:
        request_id = "G2B-EXEC-APPLIED-0001"

        def applied(*args, **kwargs):
            target = self.workspace / PILOT_PATH
            target.write_bytes(b"pilot\n")
            os.chmod(target, 0o644)
            after = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
            raise MutationStateError(
                "write_cleanup_failed",
                operation="write",
                path=PILOT_PATH,
                before=TargetState(False, None, None, None, None, None, None),
                observed_after=after,
                resolution="APPLIED",
                recovery_name=".g2b-write-" + "a" * 32 + ".tmp",
            )

        with patch.object(executor_module, "atomic_write", side_effect=applied):
            result = self.execute(write_request(request_id))

        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], "write_cleanup_failed")
        self.assertEqual(result["after"]["sha256"], hashlib.sha256(b"pilot\n").hexdigest())
        self.assertNotIn("recovery_name", result)
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery(request_id)
        self.assertEqual(recovery["resolution"], "APPLIED")
        self.assertEqual(
            recovery["workspace_recovery_name"],
            ".g2b-write-" + "a" * 32 + ".tmp",
        )

        rollback = self.execute(
            action_request("G2B-EXEC-APPLIED-ROLLBACK", "rollback", original_request_id=request_id)
        )
        self.assertEqual(rollback["status"], "ROLLED_BACK")
        self.assertFalse((self.workspace / PILOT_PATH).exists())

    def test_reverted_mutation_error_does_not_consume_active_slot(self) -> None:
        before = TargetState(False, None, None, None, None, None, None)
        with patch.object(
            executor_module,
            "atomic_write",
            side_effect=MutationStateError(
                "target_changed",
                operation="write",
                path=PILOT_PATH,
                before=before,
                observed_after=before,
                resolution="REVERTED",
            ),
        ):
            failed = self.execute(write_request("G2B-EXEC-REVERTED-0001"))

        passed = self.execute(write_request("G2B-EXEC-REVERTED-0002"))

        self.assertEqual(failed["status"], "FAILED")
        self.assertEqual(failed["error"], "target_changed")
        self.assertEqual(passed["status"], "PASS")

    def test_indeterminate_mutation_error_remains_active_and_fail_closed(self) -> None:
        before = TargetState(False, None, None, None, None, None, None)
        with patch.object(
            executor_module,
            "atomic_write",
            side_effect=MutationStateError(
                "final_target_indeterminate",
                operation="write",
                path=PILOT_PATH,
                before=before,
                observed_after=None,
                resolution="INDETERMINATE",
            ),
        ):
            failed = self.execute(write_request("G2B-EXEC-INDETERMINATE-0001"))

        conflict = self.execute(write_request("G2B-EXEC-INDETERMINATE-0002"))
        rollback = self.execute(
            action_request(
                "G2B-EXEC-INDETERMINATE-ROLLBACK",
                "rollback",
                original_request_id="G2B-EXEC-INDETERMINATE-0001",
            )
        )

        self.assertEqual(failed["status"], "FAILED")
        store = StateStore(self.state_root, self.lock_path, expected_uid=self.expected_uid)
        recovery = store.lookup_recovery("G2B-EXEC-INDETERMINATE-0001")
        self.assertEqual(recovery["expected_after"]["size"], len(b"pilot\n"))
        self.assertEqual(
            recovery["expected_after"]["sha256"],
            hashlib.sha256(b"pilot\n").hexdigest(),
        )
        self.assertEqual(conflict["status"], "CONFLICT")
        self.assertEqual(conflict["error"], "active_mutation_exists")
        self.assertEqual(rollback["status"], "CONFLICT")
        self.assertEqual(rollback["error"], "mutation_state_indeterminate")

    def execute(
        self,
        request: dict[str, object],
        *,
        expected_uid: int | None = None,
        principal: TransportPrincipal | None = None,
    ) -> dict[str, object]:
        original_stat = os.stat

        def root_owned_grant(path, *args, **kwargs):
            result = original_stat(path, *args, **kwargs)
            if not isinstance(path, int) and Path(path) == self.grant_path:
                return os.stat_result(
                    (
                        result.st_mode,
                        result.st_ino,
                        result.st_dev,
                        result.st_nlink,
                        0,
                        result.st_gid,
                        result.st_size,
                        result.st_atime,
                        result.st_mtime,
                        result.st_ctime,
                    )
                )
            return result

        with patch("control_plane.g2b.grant.os.stat", side_effect=root_owned_grant):
            return execute_request(
                request,
                transport_principal=self.principal if principal is None else principal,
                grant_path=self.grant_path,
                installed_root=self.bundle,
                workspace_root=self.workspace,
                state_root=self.state_root,
                lock_path=self.lock_path,
                expected_uid=self.expected_uid if expected_uid is None else expected_uid,
                now=lambda: NOW,
            )

    def _crash_overwrite_at_exchange(self, request_id: str):
        target = self.workspace / PILOT_PATH
        target.write_bytes(b"original\n")
        os.chmod(target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        request = write_request(request_id, "mutated\n")
        request["arguments"]["precondition"] = {"sha256": before.sha256}
        real_exchange = workspace_module._rename_exchange
        real_unlink = os.unlink

        def exchange_then_exit(*args, **kwargs):
            real_exchange(*args, **kwargs)
            raise SystemExit("synthetic death after RENAME_EXCHANGE")

        def preserve_displaced_original(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith(".g2b-write-"):
                raise SystemExit("synthetic process is already dead")
            return real_unlink(path, *args, **kwargs)

        with patch.object(workspace_module, "_rename_exchange", side_effect=exchange_then_exit):
            with patch.object(workspace_module.os, "unlink", side_effect=preserve_displaced_original):
                with self.assertRaises(SystemExit):
                    self.execute(request)

        candidates = sorted(self.workspace.glob(".g2b-write-*.tmp"))
        self.assertEqual(len(candidates), 1)
        return request, candidates[0].name

    def _write_grant(self, **changes: object) -> None:
        value: dict[str, object] = {
            "protocol": MUTATION_PROTOCOL,
            "grant_id": GRANT_ID,
            "enabled": True,
            "authority": "LEANDRO",
            "transport_principal_login": "leon337",
            "transport_principal_id": 337,
            "declared_actor": "MESTRE_MCF",
            "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
            "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
            "allowed_operations": ["workspace.write", "rollback", "status", "revoke"],
            "allowed_paths": [PILOT_PATH],
            "max_content_bytes": 65_536,
            "max_active_mutations": 1,
            "not_before": NOW.isoformat(),
            "not_after": (NOW + timedelta(hours=24)).isoformat(),
            "executor_sha256": self.bundle_digest,
        }
        value.update(changes)
        self.grant_path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(self.grant_path, 0o644)


if __name__ == "__main__":
    unittest.main()
