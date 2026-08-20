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

from control_plane.g2b.errors import RefusedError
from control_plane.g2b.grant import (
    Grant,
    TransportPrincipal,
    canonical_bundle_sha256,
    load_grant,
    validate_grant_for_request,
)
from control_plane.g2b.protocol import MUTATION_PROTOCOL, parse_request


NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


def valid_grant(bundle_digest: str) -> dict[str, object]:
    return {
        "protocol": MUTATION_PROTOCOL,
        "grant_id": "G2B-PILOT-20260820",
        "enabled": True,
        "authority": "LEANDRO",
        "transport_principal_login": "leon337",
        "transport_principal_id": 337,
        "declared_actor": "MESTRE_MCF",
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "allowed_operations": ["workspace.write", "rollback", "status", "revoke"],
        "allowed_paths": ["G2B-PILOT.txt"],
        "max_content_bytes": 65536,
        "max_active_mutations": 1,
        "not_before": "2026-08-20T12:00:00+00:00",
        "not_after": "2026-08-21T12:00:00+00:00",
        "executor_sha256": bundle_digest,
    }


class G2BGrantTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        (self.bundle / "executor.py").write_bytes(b"executor\n")
        self.digest = canonical_bundle_sha256(self.bundle)
        self.grant_path = self.root / "g2b-grant.json"
        self._write_grant(valid_grant(self.digest))

    def tearDown(self):
        self.temporary.cleanup()

    def test_loads_root_owned_exact_24_hour_grant_and_validates_request(self):
        with self._root_owned_grant_stat():
            grant = load_grant(self.grant_path, now=NOW, installed_root=self.bundle)

        self.assertIsInstance(grant, Grant)
        self.assertEqual(grant.principal, TransportPrincipal("leon337", 337))
        request = parse_request({
            "protocol": MUTATION_PROTOCOL,
            "request_id": "G2B-TEST-0001",
            "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
            "declared_actor": "MESTRE_MCF",
            "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
            "operation": "workspace.write",
            "arguments": {"path": "G2B-PILOT.txt", "content": "pilot\n", "precondition": {"state": "ABSENT"}},
        })
        validate_grant_for_request(grant, request, TransportPrincipal("leon337", 337))

    def test_missing_future_expired_overlong_and_overly_writable_grants_are_refused(self):
        with self.assertRaises(RefusedError) as missing:
            load_grant(self.root / "missing.json", now=NOW)
        self.assertEqual(missing.exception.code, "grant_missing")

        cases = (
            ("future", {"not_before": "2026-08-20T12:00:01+00:00", "not_after": "2026-08-21T12:00:01+00:00"}, "grant_not_active"),
            ("expired", {"not_before": "2026-08-19T12:00:00+00:00", "not_after": "2026-08-20T12:00:00+00:00"}, "grant_not_active"),
            ("overlong", {"not_after": "2026-08-21T12:00:01+00:00"}, "invalid_grant_duration"),
        )
        for name, changes, expected in cases:
            with self.subTest(name=name):
                value = valid_grant(self.digest)
                value.update(changes)
                self._write_grant(value)
                with self._root_owned_grant_stat():
                    with self.assertRaises(RefusedError) as caught:
                        load_grant(self.grant_path, now=NOW)
                self.assertEqual(caught.exception.code, expected)

        self._write_grant(valid_grant(self.digest))
        with patch("control_plane.g2b.grant.os.stat", return_value=_stat_result(0o664, 0)):
            with self.assertRaises(RefusedError) as writable:
                load_grant(self.grant_path, now=NOW)
        self.assertEqual(writable.exception.code, "unsafe_grant_mode")

    def test_non_root_or_nonregular_grant_is_refused(self):
        with patch("control_plane.g2b.grant.os.stat", return_value=_stat_result(0o644, 1000)):
            with self.assertRaises(RefusedError) as owner:
                load_grant(self.grant_path, now=NOW)
        self.assertEqual(owner.exception.code, "unsafe_grant_owner")

        with patch("control_plane.g2b.grant.os.stat", return_value=_stat_result(0o644, 0, file_type=stat.S_IFLNK)):
            with self.assertRaises(RefusedError) as symlink:
                load_grant(self.grant_path, now=NOW)
        self.assertEqual(symlink.exception.code, "unsafe_grant_file")

    def test_changed_project_path_and_bundle_digest_are_refused(self):
        with self._root_owned_grant_stat():
            grant = load_grant(self.grant_path, now=NOW)

        request = parse_request({
            "protocol": MUTATION_PROTOCOL,
            "request_id": "G2B-TEST-0002",
            "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
            "declared_actor": "MESTRE_MCF",
            "project": {"tenant": "leon337", "name": "other", "environment": "dev"},
            "operation": "workspace.write",
            "arguments": {"path": "G2B-PILOT.txt", "content": "pilot\n", "precondition": {"state": "ABSENT"}},
        })
        with self.assertRaises(RefusedError) as project:
            validate_grant_for_request(grant, request, TransportPrincipal("leon337", 337))
        self.assertEqual(project.exception.code, "grant_project_mismatch")

        path_request = parse_request({
            "protocol": MUTATION_PROTOCOL,
            "request_id": "G2B-TEST-0003",
            "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
            "declared_actor": "MESTRE_MCF",
            "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
            "operation": "workspace.write",
            "arguments": {"path": "other.txt", "content": "pilot\n", "precondition": {"state": "ABSENT"}},
        })
        with self.assertRaises(RefusedError) as path:
            validate_grant_for_request(grant, path_request, TransportPrincipal("leon337", 337))
        self.assertEqual(path.exception.code, "grant_path_mismatch")

        with self._root_owned_grant_stat():
            with self.assertRaises(RefusedError) as digest:
                load_grant(self.grant_path, now=NOW, installed_root=self.root)
        self.assertEqual(digest.exception.code, "executor_digest_mismatch")

    def test_bundle_digest_is_canonical_and_refuses_symlinks(self):
        (self.bundle / "a.txt").write_bytes(b"a")
        nested = self.bundle / "nested"
        nested.mkdir()
        (nested / "z.txt").write_bytes(b"z")
        expected = hashlib.sha256()
        for relative in ("a.txt", "executor.py", "nested/z.txt"):
            content = (self.bundle / relative).read_bytes()
            expected.update(f"{hashlib.sha256(content).hexdigest()}  {relative}\n".encode())
        self.assertEqual(canonical_bundle_sha256(self.bundle), expected.hexdigest())

        (self.bundle / "link").symlink_to("a.txt")
        with self.assertRaises(RefusedError) as caught:
            canonical_bundle_sha256(self.bundle)
        self.assertEqual(caught.exception.code, "unsafe_executor_bundle")

    def _write_grant(self, value: dict[str, object]) -> None:
        self.grant_path.write_text(json.dumps(value), encoding="utf-8")
        os.chmod(self.grant_path, 0o644)

    def _root_owned_grant_stat(self):
        original_stat = os.stat

        def root_owned_only(path, *args, **kwargs):
            if Path(path) == self.grant_path:
                return _stat_result(0o644, 0)
            return original_stat(path, *args, **kwargs)

        return patch("control_plane.g2b.grant.os.stat", side_effect=root_owned_only)


def _stat_result(permissions: int, uid: int, file_type: int = stat.S_IFREG):
    return os.stat_result((file_type | permissions, 0, 0, 1, uid, 0, 0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
