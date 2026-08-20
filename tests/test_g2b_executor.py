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

    def test_execution_requires_the_configured_service_uid(self) -> None:
        with patch("control_plane.g2b.executor.os.geteuid", return_value=self.expected_uid + 1):
            with patch.object(executor_module, "atomic_write") as mutation:
                result = self.execute(write_request("G2B-EXEC-UID-0001"))

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "execution_uid_mismatch")
        mutation.assert_not_called()

    def test_rejected_unapproved_path_is_not_reflected_in_bounded_result(self) -> None:
        request = write_request("G2B-EXEC-BOUNDED-0001")
        request["arguments"]["path"] = "x" * 100_000

        result = self.execute(request)

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], "grant_path_mismatch")
        self.assertIsNone(result["path"])
        self.assertLess(len(json.dumps(result)), 4096)

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

    def execute(self, request: dict[str, object]) -> dict[str, object]:
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
                transport_principal=self.principal,
                grant_path=self.grant_path,
                installed_root=self.bundle,
                workspace_root=self.workspace,
                state_root=self.state_root,
                lock_path=self.lock_path,
                expected_uid=self.expected_uid,
                now=lambda: NOW,
            )

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
