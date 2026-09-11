"""Failing RED tests for the G2-A protected-reader core (Task 1).

These tests define the Task 1 contract described in:

- docs/superpowers/specs/2026-09-07-g2a-protected-read-receipt-observability-design.md
- docs/superpowers/plans/2026-09-07-g2a-protected-read-receipt-observability.md (Task 1)
- .superpowers/sdd/2026-09-07-g2a-protected-read-receipt-observability/sofia-task1.report
- .superpowers/sdd/2026-09-07-g2a-protected-read-receipt-observability/ricardo-task1.report

They import ``control_plane.g2a.protected_reader`` and exercise the test-only
``_execute_at_root(request_value, workspace_root)`` helper plus the production
``execute_protected(request_value)`` entry point. The production module does not
exist yet, so the entire suite is expected to fail at import time (valid RED).

Portability notes
-----------------
* The reader compares target/workspace owner against ``os.geteuid()``. On this
  host the effective UID is a non-root user (1000), so most owner checks are
  exercised natively. Cases that require a *different* owner than the current
  process cannot be produced portably without root, so they use targeted
  ``mock.patch`` of ``os.fstat`` to simulate a hostile owner while keeping the
  opened descriptor real. This is documented inline and never silently weakened.
* Metadata-race cases that need the file to change between the initial and final
  ``fstat`` likewise mock ``os.fstat`` for the final probe, because a real
  concurrent writer is not available in a unit test.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import stat
import tempfile
import unittest
from unittest import mock

from control_plane.g2a.protocol import RESULT_PROTOCOL
from control_plane.g2a.protected_reader import (
    PROTECTED_PATH,
    PROTECTED_PROJECT,
    PROTECTED_ROOT,
    SAFE_FILE_MODES,
    MAX_READ_BYTES,
    _execute_at_root,
    execute_protected,
)


PROTECTED_TENANT = "leon337"
PROTECTED_NAME = "g2a-smoke"
PROTECTED_ENV = "dev"

# Exact project tuple the reader must accept.
EXPECTED_PROJECT = {"tenant": PROTECTED_TENANT, "name": PROTECTED_NAME, "environment": PROTECTED_ENV}

# Top-level result schema shared with the existing G2-A protocol.
TOP_LEVEL_FIELDS = {
    "protocol",
    "request_id",
    "project",
    "operation",
    "status",
    "started_at",
    "finished_at",
    "result",
    "error",
    "evidence",
}

# Successful read payload keys (must be exactly these five).
READ_RESULT_FIELDS = {"path", "size", "encoding", "content", "sha256"}

SAFE_PILOT_CONTENT = "G2-B pilot smoke marker\n"
SAFE_PILOT_BYTES = SAFE_PILOT_CONTENT.encode("utf-8")
SAFE_PILOT_SHA = hashlib.sha256(SAFE_PILOT_BYTES).hexdigest()


def protected_request(
    operation: str = "workspace.read",
    *,
    project: dict | None = None,
    arguments: dict | None = None,
    request_id: str = "G2A-PROTECTED-001",
) -> dict:
    return {
        "protocol": "MCF_WORKSPACE_CONTROL_V1",
        "request_id": request_id,
        "project": project if project is not None else dict(EXPECTED_PROJECT),
        "operation": operation,
        "arguments": arguments if arguments is not None else ({"path": "G2B-PILOT.txt"} if operation == "workspace.read" else {}),
    }


class _ProtectedFixture(unittest.TestCase):
    """Shared disposable-root fixture matching the protected project layout."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.workspaces = self.root / "workspaces"
        self.workspaces.mkdir()
        # Workspace path the reader must construct from the project key.
        self.workspace = self.workspaces / PROTECTED_TENANT / PROTECTED_NAME / PROTECTED_ENV
        self.workspace.mkdir(parents=True)
        self.workspace.chmod(0o700)

    def tearDown(self) -> None:
        # Restore broad permissions before cleanup so tempdir removal is reliable.
        try:
            self.workspace.chmod(0o700)
        except OSError:
            pass
        self._tmp.cleanup()

    # --- helpers -------------------------------------------------------

    def _write_pilot(self, data: bytes, mode: int = 0o600) -> pathlib.Path:
        pilot = self.workspace / "G2B-PILOT.txt"
        pilot.write_bytes(data)
        pilot.chmod(mode)
        return pilot

    def _execute(self, request_value: dict):
        return _execute_at_root(request_value, self.workspaces)

    def _assert_redacted(self, result: dict, serialized: str | None = None) -> None:
        """No raw exception text, path, inode, UID, or secret bytes leak."""
        blob = serialized if serialized is not None else json.dumps(result, sort_keys=True)
        self.assertNotIn(str(self.root), blob)
        self.assertNotIn("Traceback", blob)
        self.assertNotIn("inode", blob.lower())
        self.assertNotIn("st_dev", blob)
        self.assertNotIn("descriptor", blob.lower())


class SuccessfulReadTests(_ProtectedFixture):
    def test_read_returns_exact_content_and_sha256(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["path"], "G2B-PILOT.txt")
        self.assertEqual(result["result"]["size"], len(SAFE_PILOT_BYTES))
        self.assertEqual(result["result"]["encoding"], "utf-8")
        self.assertEqual(result["result"]["content"], SAFE_PILOT_CONTENT)
        self.assertEqual(result["result"]["sha256"], SAFE_PILOT_SHA)

    def test_sha256_matches_exact_bytes_not_characters(self):
        content = "café—unicode marker ✓\n"
        data = content.encode("utf-8")
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["result"]["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(result["result"]["size"], len(data))
        # size is bytes, not characters
        self.assertNotEqual(result["result"]["size"], len(content))

    def test_read_result_has_exact_key_set(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        result = self._execute(protected_request()).result
        self.assertEqual(set(result), TOP_LEVEL_FIELDS)
        self.assertEqual(set(result["result"]), READ_RESULT_FIELDS)

    def test_top_level_protocol_and_correlation(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        result = self._execute(protected_request(request_id="G2A-CORR-42")).result
        self.assertEqual(result["protocol"], RESULT_PROTOCOL)
        self.assertEqual(result["request_id"], "G2A-CORR-42")
        self.assertEqual(result["project"], EXPECTED_PROJECT)
        self.assertEqual(result["operation"], "workspace.read")
        self.assertIsNone(result["error"])
        self.assertIn("started_at", result)
        self.assertIn("finished_at", result)
        self.assertTrue(result["started_at"].endswith("Z"))
        self.assertTrue(result["finished_at"].endswith("Z"))

    def test_read_causes_no_metadata_or_content_mutation(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        pilot = self.workspace / "G2B-PILOT.txt"
        before = pilot.stat()
        before_dir = self.workspace.stat()
        result = self._execute(protected_request()).result
        after = pilot.stat()
        after_dir = self.workspace.stat()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(before.st_dev, after.st_dev)
        self.assertEqual(before.st_ino, after.st_ino)
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(before.st_mode, after.st_mode)
        self.assertEqual(before.st_uid, after.st_uid)
        self.assertEqual(before.st_nlink, after.st_nlink)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(hashlib.sha256(pilot.read_bytes()).hexdigest(), SAFE_PILOT_SHA)
        self.assertEqual(before_dir.st_mtime_ns, after_dir.st_mtime_ns)
        # No auxiliary files created.
        self.assertEqual(sorted(p.name for p in self.workspace.iterdir()), ["G2B-PILOT.txt"])

    def test_attachment_is_none(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        execution = self._execute(protected_request())
        self.assertIsNone(execution.attachment)


class StatTests(_ProtectedFixture):
    def test_stat_present_reports_safe_state(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["state"], "PRESENT")
        self.assertEqual(result["result"]["mode"], 0o700)
        # Evidence mirrors the existing G2-A stat shape.
        self.assertEqual(result["evidence"].get("workspace_state"), "PRESENT")

    def test_stat_genuinely_absent_is_safe_observation(self):
        # Remove the workspace entirely; absence must not create it.
        self.workspace.rmdir()
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["state"], "ABSENT")
        self.assertFalse(self.workspace.exists())
        # No UID/inode/path internals exposed.
        self._assert_redacted(result)

    def test_stat_result_has_exact_key_set(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(set(result), TOP_LEVEL_FIELDS)
        # Stat payload is the existing safe shape: state (+ mode when present).
        self.assertEqual(set(result["result"]), {"state", "mode"})


class MissingTargetTests(_ProtectedFixture):
    def test_missing_pilot_is_not_found_path_not_found(self):
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "NOT_FOUND")
        self.assertEqual(result["error"], {"code": "path_not_found"})
        self.assertEqual(result["result"], {})
        self._assert_redacted(result)


class WrongProjectTests(_ProtectedFixture):
    def _wrong_project_result(self, project: dict) -> dict:
        return self._execute(protected_request(project=project)).result


    def test_wrong_name(self):
        result = self._wrong_project_result({"tenant": PROTECTED_TENANT, "name": "other", "environment": PROTECTED_ENV})
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_project_refused"})

    def test_wrong_environment(self):
        result = self._wrong_project_result({"tenant": PROTECTED_TENANT, "name": PROTECTED_NAME, "environment": "staging"})
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_project_refused"})

    def test_wrong_project_does_not_touch_real_pilot(self):
        pilot = self._write_pilot(SAFE_PILOT_BYTES)
        before = pilot.stat()
        self._wrong_project_result({"tenant": "other", "name": PROTECTED_NAME, "environment": PROTECTED_ENV})
        self.assertEqual(pilot.stat().st_mtime_ns, before.st_mtime_ns)


class NonApprovedOperationTests(_ProtectedFixture):
    def test_every_non_stat_read_operation_is_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        # Every valid protocol operation other than stat/read must be refused.
        for operation in (
            "project.list",
            "project.get",
            "workspace.list",
            "git.status",
            "git.branch",
            "git.head",
            "git.diff",
        ):
            with self.subTest(operation=operation):
                value = protected_request(operation)
                # The plan accepts only stat/read; arguments for read are special-cased.
                if operation != "workspace.read":
                    value["arguments"] = {}
                result = self._execute(value).result
                self.assertEqual(result["status"], "REFUSED", operation)
                self.assertEqual(result["error"], {"code": "protected_operation_refused"}, operation)
                self.assertEqual(result["result"], {}, operation)


class NonLiteralPathTests(_ProtectedFixture):
    NON_LITERAL_PATHS = [
        "/etc/passwd",
        "../G2B-PILOT.txt",
        "a/../G2B-PILOT.txt",
        "~/G2B-PILOT.txt",
        "",
        ".",
        "G2B-PILOT.txt/child",
        "g2b-pilot.txt",  # alternate spelling
        "G2B-PILOT.txt/",  # trailing separator
        "./G2B-PILOT.txt",
        "subdir/G2B-PILOT.txt",
        "G2B-PILOT.txt\x00",
    ]

    def test_non_literal_read_paths_are_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        for path in self.NON_LITERAL_PATHS:
            with self.subTest(path=path):
                value = protected_request("workspace.read", arguments={"path": path})
                result = self._execute(value).result
                self.assertEqual(result["status"], "REFUSED", path)
                self.assertEqual(result["error"], {"code": "protected_path_refused"}, path)
                self.assertEqual(result["result"], {}, path)
                self._assert_redacted(result)


class ArgumentShapeTests(_ProtectedFixture):
    def test_stat_with_nonempty_arguments_is_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        value = protected_request("workspace.stat", arguments={"path": "G2B-PILOT.txt"})
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_operation_refused"})

    def test_read_missing_path_argument(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        value = protected_request("workspace.read", arguments={})
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_path_refused"})

    def test_read_extra_argument(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        value = protected_request("workspace.read", arguments={"path": "G2B-PILOT.txt", "extra": 1})
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_path_refused"})

    def test_read_non_string_path(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        value = protected_request("workspace.read", arguments={"path": 123})
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_path_refused"})


class UnknownFieldTests(_ProtectedFixture):
    def test_caller_selectable_backend_fields_are_rejected_by_parser(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        for field in ("backend", "workspace_root", "sudo", "uid", "cwd", "executable"):
            with self.subTest(field=field):
                value = protected_request()
                value[field] = "attacker"
                result = self._execute(value).result
                self.assertEqual(result["status"], "REFUSED", field)
                self.assertEqual(result["error"], {"code": "unexpected_request_field"}, field)

    def test_unknown_protocol_is_rejected(self):
        value = protected_request()
        value["protocol"] = "MCF_WORKSPACE_CONTROL_V2"
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "invalid_protocol"})

    def test_unknown_operation_is_rejected(self):
        value = protected_request(operation="shell.run")
        result = self._execute(value).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "unknown_operation"})


class ProductionRootTests(unittest.TestCase):
    """The production root is internal and cannot be selected by request data."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.elsewhere = pathlib.Path(self._tmp.name) / "elsewhere"
        self.elsewhere.mkdir()
        ws = self.elsewhere / PROTECTED_TENANT / PROTECTED_NAME / PROTECTED_ENV
        ws.mkdir(parents=True)
        ws.chmod(0o700)
        (ws / "G2B-PILOT.txt").write_bytes(SAFE_PILOT_BYTES)
        (ws / "G2B-PILOT.txt").chmod(0o600)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_production_root_constant_is_fixed(self):
        self.assertEqual(PROTECTED_ROOT, pathlib.Path("/var/lib/mcf-control-bridge/workspaces"))

    def test_production_function_ignores_request_root_fields(self):
        # Even with hostile fields, the production root constant is the only root.
        value = protected_request()
        value["workspace_root"] = str(self.elsewhere)
        # Production root does not exist in CI, so this must fail closed (refused/
        # not_found), never read from the attacker-supplied elsewhere root.
        result = execute_protected(value).result
        self.assertNotIn("PASS", result["status"])
        # The pilot content must not appear anywhere in the redacted result.
        self.assertNotIn(SAFE_PILOT_CONTENT, json.dumps(result))
        self.assertNotIn(SAFE_PILOT_SHA, json.dumps(result["result"]))

    def test_protected_path_constant_is_literal(self):
        self.assertEqual(PROTECTED_PATH, "G2B-PILOT.txt")

    def test_protected_project_constant_is_exact(self):
        self.assertEqual(PROTECTED_PROJECT.tenant, PROTECTED_TENANT)
        self.assertEqual(PROTECTED_PROJECT.name, PROTECTED_NAME)
        self.assertEqual(PROTECTED_PROJECT.environment, PROTECTED_ENV)

    def test_max_read_bytes_constant(self):
        self.assertEqual(MAX_READ_BYTES, 65_536)

    def test_safe_file_modes_constant(self):
        self.assertEqual(SAFE_FILE_MODES, frozenset({0o600, 0o640, 0o644}))


class WorkspaceDescriptorTests(_ProtectedFixture):
    def test_workspace_symlink_is_refused(self):
        real = self.workspaces / PROTECTED_TENANT / PROTECTED_NAME / "dev-real"
        real.mkdir(parents=True)
        real.chmod(0o700)
        (real / "G2B-PILOT.txt").write_bytes(SAFE_PILOT_BYTES)
        (real / "G2B-PILOT.txt").chmod(0o600)
        self.workspace.rmdir()
        self.workspace.symlink_to(real, target_is_directory=True)
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})
        self._assert_redacted(result)

    def test_workspace_non_directory_is_refused(self):
        self.workspace.rmdir()
        self.workspace.write_text("not a dir")
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})

    def test_workspace_wrong_mode_is_refused(self):
        for mode in (0o701, 0o750, 0o770, 0o755, 0o500):
            with self.subTest(mode=oct(mode)):
                self.workspace.chmod(mode)
                result = self._execute(protected_request("workspace.stat")).result
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})

    def test_workspace_wrong_owner_is_refused_via_fstat_mock(self):
        # Portability: without root we cannot create a workspace owned by another
        # UID. Targeted mock of os.fstat simulates a hostile owner while keeping
        # the opened descriptor real. This is documented, not silently weakened.
        self._write_pilot(SAFE_PILOT_BYTES)
        real_stat = os.stat(self.workspace)
        other_uid = os.geteuid() + 1

        def fake_fstat(fd, *, _real=os.fstat):
            st = os.stat_result(tuple(real_stat))
            # Replace only the owner field; everything else stays genuine.
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, other_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime, st.st_ctime)
            )

        with mock.patch("os.fstat", side_effect=fake_fstat):
            result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})
        self._assert_redacted(result)


class AncestorSymlinkTests(_ProtectedFixture):
    """Workspace traversal must not follow symlinked ancestor components."""

    def test_workspaces_root_symlink_is_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        real_workspaces = self.root / "real-workspaces"
        self.workspaces.rename(real_workspaces)
        self.workspaces.symlink_to(real_workspaces, target_is_directory=True)

        result = self._execute(protected_request()).result

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})
        self.assertEqual(result["result"], {})
        self._assert_redacted(result)

    def test_tenant_ancestor_symlink_is_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        tenant = self.workspaces / PROTECTED_TENANT
        real_tenant = self.root / "real-tenant"
        tenant.rename(real_tenant)
        tenant.symlink_to(real_tenant, target_is_directory=True)

        result = self._execute(protected_request()).result

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})
        self.assertEqual(result["result"], {})
        self._assert_redacted(result)

    def test_project_ancestor_symlink_is_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        real_project = self.root / "real-project"
        real_project.mkdir()
        self.workspace.rename(real_project / PROTECTED_ENV)
        project = self.workspaces / PROTECTED_TENANT / PROTECTED_NAME
        project.rmdir()
        project.symlink_to(real_project, target_is_directory=True)

        result = self._execute(protected_request()).result

        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_workspace_unsafe"})
        self.assertEqual(result["result"], {})
        self._assert_redacted(result)


class TargetDescriptorTests(_ProtectedFixture):
    def test_target_symlink_refused(self):
        real = self.workspace / "real-pilot.txt"
        real.write_bytes(SAFE_PILOT_BYTES)
        real.chmod(0o600)
        pilot = self.workspace / "G2B-PILOT.txt"
        pilot.symlink_to(real)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})
        self._assert_redacted(result)

    def test_target_hardlink_refused(self):
        outside = self.root / "outside.txt"
        outside.write_bytes(SAFE_PILOT_BYTES)
        outside.chmod(0o600)
        pilot = self.workspace / "G2B-PILOT.txt"
        os.link(outside, pilot)
        # st_nlink == 2 must trigger refusal.
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_target_nonregular_fifo_refused(self):
        pilot = self.workspace / "G2B-PILOT.txt"
        os.mkfifo(pilot)
        pilot.chmod(0o600)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_target_directory_in_place_of_pilot_refused(self):
        pilot = self.workspace / "G2B-PILOT.txt"
        pilot.mkdir()
        pilot.chmod(0o600)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_target_wrong_owner_refused_via_fstat_mock(self):
        # Portability: targeted mock simulates a pilot owned by another UID.
        self._write_pilot(SAFE_PILOT_BYTES)
        pilot = self.workspace / "G2B-PILOT.txt"
        real_stat = os.stat(pilot)
        other_uid = os.geteuid() + 1

        original_fstat = os.fstat
        call = {"count": 0}

        def fake_fstat(fd):
            call["count"] += 1
            st = original_fstat(fd)
            if call["count"] >= 2:
                # Final post-read probe: report hostile owner.
                return os.stat_result(
                    (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, other_uid, st.st_gid, st.st_size,
                     st.st_atime, st.st_mtime, st.st_ctime)
                )
            return st

        with mock.patch("os.fstat", side_effect=fake_fstat):
            result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})
        self._assert_redacted(result)

    def test_target_unsafe_modes_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        for mode in (0o777, 0o666, 0o700, 0o641, 0o604, 0o000):
            with self.subTest(mode=oct(mode)):
                (self.workspace / "G2B-PILOT.txt").chmod(mode)
                result = self._execute(protected_request()).result
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_setuid_setgid_sticky_bits_refused(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        for extra in (stat.S_ISUID, stat.S_ISGID, stat.S_ISVTX):
            with self.subTest(bit=oct(extra)):
                (self.workspace / "G2B-PILOT.txt").chmod(0o600 | extra)
                result = self._execute(protected_request()).result
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_safe_modes_are_accepted(self):
        for mode in (0o600, 0o640, 0o644):
            with self.subTest(mode=oct(mode)):
                self._write_pilot(SAFE_PILOT_BYTES, mode=mode)
                result = self._execute(protected_request()).result
                self.assertEqual(result["status"], "PASS", oct(mode))
                self.assertEqual(result["result"]["sha256"], SAFE_PILOT_SHA)


class SizeBoundaryTests(_ProtectedFixture):
    def test_exactly_65536_bytes_accepted(self):
        data = b"a" * 65_536
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["size"], 65_536)
        self.assertEqual(result["result"]["sha256"], hashlib.sha256(data).hexdigest())

    def test_65537_bytes_refused(self):
        data = b"a" * 65_537
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "file_too_large"})
        self.assertEqual(result["result"], {})


class SecretLikeContentTests(_ProtectedFixture):
    SECRET_SAMPLES = {
        "private-key-material": b"-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n",
        "github-token": b"ghp_" + b"A" * 36 + b"\n",
        "aws-access-key": b"AKIAIOSFODNN7EXAMPLE\n",
        "credential-in-uri": b"https://user:supersecret@host/path\n",
        "secret-like-assignment": b"password=abcdefghijkl\n",
    }

    def test_each_secret_class_is_refused_without_echoing_bytes(self):
        for name, data in self.SECRET_SAMPLES.items():
            with self.subTest(rule=name):
                self._write_pilot(data)
                result = self._execute(protected_request()).result
                self.assertEqual(result["status"], "REFUSED", name)
                self.assertEqual(result["error"], {"code": "secret_like_content"}, name)
                self.assertEqual(result["result"], {}, name)
                blob = json.dumps(result, sort_keys=True)
                # Matched bytes must not leak.
                for needle in (data.decode("utf-8", "replace"),):
                    if needle:
                        self.assertNotIn(needle, blob)


    def test_secret_precedence_over_utf8_failure(self):
        # Secret-like bytes that are also invalid UTF-8 must be reported as
        # secret_like_content, not binary_or_non_utf8 (plan ordering).
        data = b"password=abcdefghijk\xff\xfe\n"
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "secret_like_content"})

    def test_safe_placeholder_is_accepted(self):
        data = b"EXAMPLE_VALUE=placeholder\n"
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "PASS")


class InvalidUtf8Tests(_ProtectedFixture):
    def test_invalid_utf8_refused(self):
        data = b"\xff\xfe\x00\x01\x02 bad bytes"
        self._write_pilot(data)
        result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "binary_or_non_utf8"})
        self.assertEqual(result["result"], {})
        # No partial content leaks.
        blob = json.dumps(result, sort_keys=True)
        self.assertNotIn("bad bytes", blob)


class OpenRaceTests(_ProtectedFixture):
    """Adversarial path swaps must not redirect an already-open descriptor."""

    @staticmethod
    def _delegate_open(original_open, path, flags, mode, dir_fd):
        if dir_fd is None:
            return original_open(path, flags, mode)
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def test_target_swapped_to_symlink_before_open_is_refused(self):
        pilot = self._write_pilot(SAFE_PILOT_BYTES)
        outside_data = b"outside hostile content\n"
        outside = self.root / "outside-secret.txt"
        outside.write_bytes(outside_data)
        outside.chmod(0o600)
        original_open = os.open
        swapped = {"done": False}

        def swapping_open(path, flags, mode=0o777, *, dir_fd=None):
            if path == PROTECTED_PATH and dir_fd is not None and not swapped["done"]:
                swapped["done"] = True
                pilot.unlink()
                pilot.symlink_to(outside)
            return self._delegate_open(original_open, path, flags, mode, dir_fd)

        with mock.patch("os.open", side_effect=swapping_open):
            result = self._execute(protected_request()).result

        self.assertTrue(swapped["done"])
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})
        self.assertNotIn(outside_data.decode("utf-8"), json.dumps(result))
        self._assert_redacted(result)

    def test_pathname_swap_after_open_cannot_redirect_descriptor(self):
        pilot = self._write_pilot(SAFE_PILOT_BYTES)
        replacement_data = b"replacement public marker\n"
        replacement = self.workspace / "replacement.txt"
        replacement.write_bytes(replacement_data)
        replacement.chmod(0o600)
        original_read = os.read
        original_fstat = os.fstat
        swapped = {"done": False}
        target_stat = {"value": None}

        def swapping_read(fd, count):
            if not swapped["done"]:
                swapped["done"] = True
                pilot.rename(self.workspace / "original-opened.txt")
                replacement.rename(pilot)
            return original_read(fd, count)

        def stable_target_fstat(fd):
            st = original_fstat(fd)
            if stat.S_ISREG(st.st_mode):
                if target_stat["value"] is None:
                    target_stat["value"] = st
                return target_stat["value"]
            return st

        with mock.patch("os.read", side_effect=swapping_read), mock.patch(
            "os.fstat", side_effect=stable_target_fstat
        ):
            result = self._execute(protected_request()).result

        self.assertTrue(swapped["done"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["content"], SAFE_PILOT_CONTENT)
        self.assertEqual(result["result"]["sha256"], SAFE_PILOT_SHA)
        self.assertNotIn(replacement_data.decode("utf-8"), json.dumps(result))


class ShortReadTests(_ProtectedFixture):
    """Short os.read results must not silently truncate the receipt."""

    def test_repeated_short_reads_return_complete_file(self):
        data = b"short-read-safe-marker\n"
        self._write_pilot(data)
        original_read = os.read
        calls = {"count": 0}

        def short_read(fd, count):
            calls["count"] += 1
            return original_read(fd, min(count, 3))

        with mock.patch("os.read", side_effect=short_read):
            result = self._execute(protected_request()).result

        self.assertGreater(calls["count"], 1)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["result"]["content"], data.decode("utf-8"))
        self.assertEqual(result["result"]["size"], len(data))
        self.assertEqual(result["result"]["sha256"], hashlib.sha256(data).hexdigest())


class MetadataRaceTests(_ProtectedFixture):
    """Simulated post-open metadata races via targeted os.fstat mocking.

    A real concurrent writer is not available in a unit test, so the final
    post-read ``fstat`` probe is mocked to report a changed attribute while the
    opened descriptor stays real. This is documented portability handling, not a
    silently weakened case.
    """

    def _run_with_final_fstat(self, mutate) -> dict:
        self._write_pilot(SAFE_PILOT_BYTES)
        pilot = self.workspace / "G2B-PILOT.txt"
        real_stat = os.stat(pilot)
        original_fstat = os.fstat
        call = {"count": 0}

        def fake_fstat(fd):
            call["count"] += 1
            st = original_fstat(fd)
            if call["count"] == 3:
                return mutate(st)
            return st

        with mock.patch("os.fstat", side_effect=fake_fstat):
            return self._execute(protected_request()).result

    def test_post_read_size_change_refused(self):
        def changed_size(st):
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, st.st_size + 1,
                 st.st_atime, st.st_mtime, st.st_ctime)
            )
        result = self._run_with_final_fstat(changed_size)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_mode_change_refused(self):
        def changed_mode(st):
            return os.stat_result(
                (0o777, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime, st.st_ctime)
            )
        result = self._run_with_final_fstat(changed_mode)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_link_count_change_refused(self):
        def changed_nlink(st):
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink + 1, st.st_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime, st.st_ctime)
            )
        result = self._run_with_final_fstat(changed_nlink)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_mtime_change_refused(self):
        def changed_mtime(st):
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime + 1, st.st_ctime)
            )
        result = self._run_with_final_fstat(changed_mtime)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_ctime_change_refused(self):
        def changed_ctime(st):
            return mock.Mock(
                st_dev=st.st_dev, st_ino=st.st_ino, st_size=st.st_size,
                st_mode=st.st_mode, st_uid=st.st_uid, st_nlink=st.st_nlink,
                st_mtime_ns=st.st_mtime_ns, st_ctime_ns=st.st_ctime_ns + 1,
            )
        result = self._run_with_final_fstat(changed_ctime)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_inode_change_refused(self):
        def changed_inode(st):
            return os.stat_result(
                (st.st_mode, st.st_ino + 1, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime, st.st_ctime)
            )
        result = self._run_with_final_fstat(changed_inode)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})

    def test_post_read_ctime_change_refused(self):
        def changed_ctime(st):
            return os.stat_result(
                (st.st_mode, st.st_ino, st.st_dev, st.st_nlink, st.st_uid, st.st_gid, st.st_size,
                 st.st_atime, st.st_mtime, st.st_ctime + 1)
            )
        result = self._run_with_final_fstat(changed_ctime)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "protected_target_unsafe"})


class RedactionTests(_ProtectedFixture):
    def test_failure_responses_do_not_leak_internals(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        # A refused operation must not expose path/inode/uid.
        result = self._execute(protected_request("workspace.list")).result
        blob = json.dumps(result, sort_keys=True)
        self.assertNotIn("inode", blob.lower())
        self.assertNotIn("st_dev", blob)
        self.assertNotIn("descriptor", blob.lower())
        self.assertNotIn(str(self.root), blob)

    def test_internal_error_is_redacted(self):
        # Force an unexpected exception inside the reader path by breaking the
        # project dict so parse_request still passes but later logic explodes.
        # We instead monkeypatch parse_request to raise a RuntimeError carrying
        # sensitive text; the reader must normalize to internal_error.
        import control_plane.g2a.protected_reader as pr

        def boom(_value):
            raise RuntimeError("sensitive internal detail")

        with mock.patch.object(pr, "parse_request", side_effect=boom):
            result = self._execute(protected_request()).result
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error"], {"code": "internal_error"})
        self.assertEqual(result["result"], {})
        self.assertNotIn("sensitive internal detail", json.dumps(result))


class NoMutationCapabilityTests(_ProtectedFixture):
    """No accepted operation may expose write/delete/rename/mkdir/chmod."""

    def test_stat_does_not_create_or_modify(self):
        self.workspace.rmdir()
        result = self._execute(protected_request("workspace.stat")).result
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(self.workspace.exists())

    def test_read_does_not_modify_pilot_or_workspace(self):
        self._write_pilot(SAFE_PILOT_BYTES)
        pilot = self.workspace / "G2B-PILOT.txt"
        before = pilot.stat()
        before_dir = self.workspace.stat()
        self._execute(protected_request())
        after = pilot.stat()
        after_dir = self.workspace.stat()
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)
        self.assertEqual(before_dir.st_mtime_ns, after_dir.st_mtime_ns)
        self.assertEqual(pilot.read_bytes(), SAFE_PILOT_BYTES)


if __name__ == "__main__":
    unittest.main()
