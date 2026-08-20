from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

from control_plane.g2b.errors import RefusedError, TimeoutError
from control_plane.g2b.state import RECEIPT_FIELDS, StateStore, canonical_request_digest


NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def receipt(request_id: str = "G2B-STATE-0001") -> dict[str, object]:
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_RESULT_V1",
        "request_id": request_id,
        "request_digest": "a" * 64,
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "authority": "LEANDRO",
        "transport_principal": {"login": "leon337", "actor_id": 337},
        "grant_id": "G2B-PILOT-20260820",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": "workspace.write",
        "path": "G2B-PILOT.txt",
        "started_at": "2026-08-20T12:00:00+00:00",
        "finished_at": "2026-08-20T12:00:00+00:00",
        "precondition": {"state": "ABSENT"},
        "before": {"exists": False, "size": None, "mode": None, "sha256": None},
        "after": {"exists": True, "size": 6, "mode": 420, "sha256": "b" * 64},
        "status": "PASS",
        "replayed": False,
        "rollback_request_id": None,
        "revocation_request_id": None,
        "error": None,
    }


class G2BStateStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.state_root = self.root / "state"
        self.state_root.mkdir(mode=0o700)
        self.lock_path = self.root / "g2b.lock"
        self.lock_path.touch(mode=0o600)
        os.chmod(self.lock_path, 0o600)
        self.expected_uid = os.geteuid()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def store(self) -> StateStore:
        return StateStore(
            self.state_root,
            self.lock_path,
            expected_uid=self.expected_uid,
        )

    def test_initializes_only_private_real_directories_and_validates_lock(self) -> None:
        self.store()

        self.assertEqual(stat.S_IMODE(self.state_root.stat().st_mode), 0o700)
        for name in ("receipts", "snapshots", "recovery", "revocations"):
            child = self.state_root / name
            self.assertTrue(child.is_dir())
            self.assertFalse(child.is_symlink())
            self.assertEqual(child.stat().st_uid, self.expected_uid)
            self.assertEqual(stat.S_IMODE(child.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(self.lock_path.stat().st_mode), 0o600)

    def test_refuses_unsafe_state_root_child_and_lock_objects(self) -> None:
        os.chmod(self.state_root, 0o755)
        with self.assertRaises(RefusedError) as root_mode:
            self.store()
        self.assertEqual(root_mode.exception.code, "unsafe_state_mode")
        os.chmod(self.state_root, 0o700)

        (self.state_root / "receipts").symlink_to(self.root)
        with self.assertRaises(RefusedError) as child_link:
            self.store()
        self.assertEqual(child_link.exception.code, "unsafe_state_directory")
        (self.state_root / "receipts").unlink()

        self.lock_path.unlink()
        self.lock_path.symlink_to(self.state_root)
        with self.assertRaises(RefusedError) as lock_link:
            self.store()
        self.assertEqual(lock_link.exception.code, "unsafe_lock_file")

    def test_exclusive_lock_times_out_without_proceeding_unlocked(self) -> None:
        first = self.store()
        second = self.store()

        with first.exclusive_lock(timeout_seconds=1):
            with self.assertRaises(TimeoutError) as caught:
                with second.exclusive_lock(timeout_seconds=0.02):
                    self.fail("contended lock must never be entered")

        self.assertEqual(caught.exception.code, "lock_timeout")

    def test_canonical_digest_uses_compact_sorted_utf8_json(self) -> None:
        expected = hashlib.sha256(b'{"a":"\xc3\xa9","b":1}').hexdigest()

        self.assertEqual(canonical_request_digest({"b": 1, "a": "é"}), expected)

    def test_receipt_lookup_uses_hashed_name_exact_schema_and_private_mode(self) -> None:
        store = self.store()
        value = receipt("G2B-STATE-PATH-0001")

        store.record_write(value)

        self.assertEqual(store.lookup_request("G2B-STATE-PATH-0001"), value)
        files = list((self.state_root / "receipts").iterdir())
        self.assertEqual(len(files), 1)
        expected_name = hashlib.sha256(b"G2B-STATE-PATH-0001").hexdigest() + ".json"
        self.assertEqual(files[0].name, expected_name)
        self.assertNotIn("G2B-STATE-PATH-0001", files[0].name)
        self.assertEqual(stat.S_IMODE(files[0].stat().st_mode), 0o600)
        self.assertEqual(set(json.loads(files[0].read_text())), RECEIPT_FIELDS)
        self.assertEqual(list((self.state_root / "receipts").glob("*.tmp")), [])

    def test_write_and_rollback_receipts_are_create_only(self) -> None:
        store = self.store()
        write = receipt()
        store.record_write(write)

        replacement = dict(write)
        replacement["status"] = "FAILED"
        replacement["error"] = "changed"
        with self.assertRaises(RefusedError) as duplicate:
            store.record_write(replacement)
        self.assertEqual(duplicate.exception.code, "receipt_already_exists")
        self.assertEqual(store.lookup_request(write["request_id"]), write)

        rollback = receipt("G2B-ROLLBACK-0001")
        rollback.update(
            operation="rollback",
            path="G2B-PILOT.txt",
            status="ROLLED_BACK",
            rollback_request_id=write["request_id"],
        )
        store.record_rollback(rollback)
        self.assertEqual(store.lookup_request("G2B-ROLLBACK-0001"), rollback)

    def test_create_only_receipt_commit_never_uses_a_hardlink_window(self) -> None:
        store = self.store()

        with patch("control_plane.g2b.state.os.link", side_effect=AssertionError("hardlink forbidden")):
            store.record_write(receipt("G2B-STATE-NOREPLACE-0001"))

        self.assertIsNotNone(store.lookup_request("G2B-STATE-NOREPLACE-0001"))

    def test_identical_receipt_repairs_missing_audit_idempotently(self) -> None:
        store = self.store()
        value = receipt("G2B-STATE-AUDIT-REPAIR-0001")
        original_append = store._append_audit
        failed = False

        def fail_once(event):
            nonlocal failed
            if not failed:
                failed = True
                raise RefusedError("synthetic_audit_failure")
            return original_append(event)

        with patch.object(store, "_append_audit", side_effect=fail_once):
            with self.assertRaises(RefusedError):
                store.record_write(value)
            store.record_write(value)

        self.assertEqual(store.lookup_request(value["request_id"]), value)
        events = (self.state_root / "audit.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(events), 1)

    def test_recovery_baselines_and_committed_after_are_immutable(self) -> None:
        store = self.store()
        value = self._recovery("G2B-STATE-MONOTONIC-0001")
        value["before"] = {
            "exists": True,
            "size": 8,
            "mode": 420,
            "uid": self.expected_uid,
            "device": 11,
            "inode": 22,
            "sha256": "b" * 64,
        }
        store.prepare_recovery(value)
        committed = dict(
            value,
            after={
                "exists": True,
                "size": 6,
                "mode": 420,
                "uid": self.expected_uid,
                "device": 11,
                "inode": 33,
                "sha256": "c" * 64,
            },
            resolution="APPLIED",
        )
        store.update_recovery(committed)

        changed_before = dict(committed)
        changed_before["before"] = dict(committed["before"], inode=44)
        with self.assertRaises(RefusedError) as before_error:
            store.update_recovery(changed_before)
        self.assertEqual(before_error.exception.code, "invalid_recovery_transition")

        changed_after = dict(committed)
        changed_after["after"] = dict(committed["after"], sha256="e" * 64)
        with self.assertRaises(RefusedError) as after_error:
            store.update_recovery(changed_after)
        self.assertEqual(after_error.exception.code, "invalid_recovery_transition")

    def test_recognized_abandoned_state_temporary_is_removed_under_lock(self) -> None:
        store = self.store()
        abandoned = self.state_root / "recovery" / (".g2b-state-" + "a" * 32 + ".tmp")
        abandoned.write_bytes(b"incomplete")
        os.chmod(abandoned, 0o600)

        with store.exclusive_lock(timeout_seconds=1):
            store.reconcile_abandoned_temporaries()

        self.assertFalse(abandoned.exists())

    def test_receipts_reject_schema_expansion_and_secret_like_material(self) -> None:
        store = self.store()
        expanded = receipt()
        expanded["content"] = "benign"
        with self.assertRaises(RefusedError) as schema:
            store.record_write(expanded)
        self.assertEqual(schema.exception.code, "invalid_receipt_schema")

        secret_like = receipt("G2B-STATE-SECRET-0001")
        secret_like["grant_id"] = "gh" + "p_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"
        with self.assertRaises(RefusedError) as secret:
            store.record_write(secret_like)
        self.assertEqual(secret.exception.code, "secret_like_receipt")
        self.assertIsNone(store.lookup_request("G2B-STATE-SECRET-0001"))

    def test_audit_is_private_jsonl_content_free_and_uses_safe_error_codes(self) -> None:
        store = self.store()
        failed = receipt()
        failed["status"] = "FAILED"
        failed["error"] = "internal_error"
        store.record_write(failed)

        audit_path = self.state_root / "audit.jsonl"
        self.assertEqual(stat.S_IMODE(audit_path.stat().st_mode), 0o600)
        lines = audit_path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(
            set(event),
            {"event", "request_id", "request_digest", "grant_id", "operation", "status", "error", "at"},
        )
        rendered = lines[0]
        self.assertNotIn("content", rendered)
        self.assertNotIn("traceback", rendered.lower())
        self.assertNotIn("exception", rendered.lower())

    def test_revocation_sentinel_is_hashed_private_and_irreversible(self) -> None:
        store = self.store()
        store.revoke("G2B-PILOT-20260820", actor="MESTRE_MCF", at=NOW)
        sentinels = list((self.state_root / "revocations").iterdir())
        self.assertEqual(len(sentinels), 1)
        expected = hashlib.sha256(b"G2B-PILOT-20260820").hexdigest() + ".json"
        self.assertEqual(sentinels[0].name, expected)
        self.assertEqual(stat.S_IMODE(sentinels[0].stat().st_mode), 0o600)
        original_inode = sentinels[0].stat().st_ino
        original_bytes = sentinels[0].read_bytes()

        store.revoke(
            "G2B-PILOT-20260820",
            actor="MESTRE_MCF",
            at=datetime(2026, 8, 20, 13, 0, tzinfo=timezone.utc),
        )

        self.assertTrue(store.is_revoked("G2B-PILOT-20260820"))
        self.assertEqual(sentinels[0].stat().st_ino, original_inode)
        self.assertEqual(sentinels[0].read_bytes(), original_bytes)

    def test_snapshot_and_exact_recovery_state_are_private_and_separate(self) -> None:
        store = self.store()
        request_id = "G2B-STATE-RECOVERY-0001"
        store.save_snapshot(request_id, b"safe prior bytes\n")
        recovery = self._recovery(request_id)
        recovery.update(
            before={
                "exists": True,
                "size": 17,
                "mode": 420,
                "uid": self.expected_uid,
                "device": 11,
                "inode": 22,
                "sha256": "b" * 64,
            },
            snapshot=True,
        )
        store.prepare_recovery(recovery)

        snapshot_files = list((self.state_root / "snapshots").iterdir())
        recovery_files = list((self.state_root / "recovery").iterdir())
        self.assertEqual(len(snapshot_files), 1)
        self.assertEqual(len(recovery_files), 1)
        self.assertEqual(stat.S_IMODE(snapshot_files[0].stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(recovery_files[0].stat().st_mode), 0o600)
        self.assertEqual(store.load_snapshot(request_id), b"safe prior bytes\n")
        self.assertEqual(store.lookup_recovery(request_id), recovery)
        self.assertEqual(store.active_recoveries("G2B-PILOT-20260820"), [recovery])
        self.assertEqual(list((self.state_root / "receipts").iterdir()), [])

        applied = dict(
            recovery,
            after={
                "exists": True,
                "size": 6,
                "mode": 420,
                "uid": self.expected_uid,
                "device": 11,
                "inode": 33,
                "sha256": "c" * 64,
            },
            resolution="APPLIED",
        )
        store.update_recovery(applied)
        resolved = dict(applied, active=False, resolution="ROLLED_BACK")
        store.update_recovery(resolved)
        store.delete_snapshot(request_id)
        self.assertEqual(store.lookup_recovery(request_id), resolved)
        self.assertEqual(store.active_recoveries("G2B-PILOT-20260820"), [])
        self.assertIsNone(store.load_snapshot(request_id))

    def _recovery(self, request_id: str) -> dict[str, object]:
        return {
            "protocol": "MCF_WORKSPACE_RECOVERY_V1",
            "request_id": request_id,
            "request_digest": "a" * 64,
            "grant_id": "G2B-PILOT-20260820",
            "path": "G2B-PILOT.txt",
            "expected_after": {
                "exists": True,
                "size": 6,
                "mode": 420,
                "uid": self.expected_uid,
                "sha256": "c" * 64,
            },
            "before": {
                "exists": True,
                "size": 17,
                "mode": 420,
                "uid": self.expected_uid,
                "device": 11,
                "inode": 22,
                "sha256": "b" * 64,
            },
            "after": None,
            "resolution": "PREPARED",
            "active": True,
            "snapshot": True,
            "workspace_recovery_name": None,
            "observation": None,
            "rollback_observation": None,
            "receipt_context": {
                "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
                "declared_actor": "MESTRE_MCF",
                "authority": "LEANDRO",
                "transport_principal": {"login": "leon337", "actor_id": 337},
                "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
                "operation": "workspace.write",
                "precondition": {"state": "ABSENT"},
                "started_at": "2026-08-20T12:00:00+00:00",
            },
        }


if __name__ == "__main__":
    unittest.main()
