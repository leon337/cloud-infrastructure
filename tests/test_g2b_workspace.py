from __future__ import annotations

import hashlib
import errno
import os
from pathlib import Path
import socket
import stat
import tempfile
import unittest
from unittest.mock import patch

from control_plane.g2b import workspace as workspace_module
from control_plane.g2b.errors import ConflictError, RefusedError
from control_plane.g2b.protocol import MAX_CONTENT_BYTES, Precondition
from control_plane.g2b.workspace import (
    TargetState,
    atomic_delete,
    atomic_restore,
    atomic_write,
    inspect_target,
)


PILOT_PATH = "G2B-PILOT.txt"


class G2BWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "workspace"
        self.workspace.mkdir(mode=0o700)
        self.expected_uid = os.getuid()
        self.target = self.workspace / PILOT_PATH

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_absent_target_is_created_atomically_with_verified_state(self) -> None:
        state = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)

        outcome = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"pilot\n",
            precondition=Precondition(state="ABSENT"),
            expected_uid=self.expected_uid,
        )

        self.assertEqual(state, TargetState(False, None, None, None, None, None, None))
        self.assertFalse(outcome.before.exists)
        self.assertEqual(outcome.path, PILOT_PATH)
        self.assertEqual(outcome.after.sha256, hashlib.sha256(b"pilot\n").hexdigest())
        self.assertEqual(outcome.after.size, 6)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o644)
        self.assertEqual(self.target.read_bytes(), b"pilot\n")
        self.assertEqual(list(self.workspace.glob(".g2b-*")), [])

    def test_hash_precondition_overwrite_preserves_validated_mode(self) -> None:
        self.target.write_bytes(b"old\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)

        outcome = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"new\n",
            precondition=Precondition(sha256=before.sha256),
            expected_uid=self.expected_uid,
        )

        self.assertEqual(outcome.before, before)
        self.assertEqual(outcome.after.sha256, hashlib.sha256(b"new\n").hexdigest())
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)

    def test_overwrite_publishes_generated_recovery_name_before_exchange(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        published: list[str] = []

        def publish(name: str) -> None:
            self.assertEqual(self.target.read_bytes(), b"original\n")
            self.assertEqual((self.workspace / name).read_bytes(), b"mutated\n")
            published.append(name)

        outcome = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=before.sha256),
            expected_uid=self.expected_uid,
            recovery_name_publisher=publish,
        )

        self.assertEqual(outcome.after.sha256, hashlib.sha256(b"mutated\n").hexdigest())
        self.assertEqual(len(published), 1)
        self.assertRegex(published[0], r"^\.g2b-write-[0-9a-f]{32}\.tmp$")
        self.assertFalse((self.workspace / published[0]).exists())

    def test_no_public_caller_selected_recovery_deletion_capability_exists(self) -> None:
        self.assertFalse(hasattr(workspace_module, "RecoveryCandidate"))
        self.assertFalse(hasattr(workspace_module, "list_recovery_candidates"))
        self.assertFalse(hasattr(workspace_module, "cleanup_recovery_candidate"))

    def test_transaction_reconciliation_internally_selects_unique_exact_candidate(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        candidate_name = ".g2b-write-" + "a" * 32 + ".tmp"
        self.target.rename(self.workspace / candidate_name)
        self.target.write_bytes(b"mutated\n")
        os.chmod(self.target, 0o600)
        published: list[str] = []

        result = workspace_module.reconcile_write_recovery(
            self.workspace,
            PILOT_PATH,
            phase="PREPARED",
            published_name=None,
            before=before,
            committed_after=None,
            expected_size=len(b"mutated\n"),
            expected_mode=0o600,
            expected_sha256=hashlib.sha256(b"mutated\n").hexdigest(),
            expected_uid=self.expected_uid,
            recovery_name_publisher=published.append,
        )

        self.assertEqual(result.resolution, "APPLIED")
        self.assertEqual(published, [candidate_name])
        self.assertEqual(self.target.read_bytes(), b"mutated\n")
        self.assertFalse((self.workspace / candidate_name).exists())

    def test_transaction_reconciliation_refuses_ambiguity_and_boundary_replacement(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        first_name = ".g2b-write-" + "b" * 32 + ".tmp"
        second_name = ".g2b-write-" + "c" * 32 + ".tmp"
        self.target.rename(self.workspace / first_name)
        self.target.write_bytes(b"mutated\n")
        os.chmod(self.target, 0o600)
        second = self.workspace / second_name
        second.write_bytes(b"original\n")
        os.chmod(second, 0o600)
        published: list[str] = []

        ambiguous = workspace_module.reconcile_write_recovery(
            self.workspace,
            PILOT_PATH,
            phase="PREPARED",
            published_name=None,
            before=before,
            committed_after=None,
            expected_size=len(b"mutated\n"),
            expected_mode=0o600,
            expected_sha256=hashlib.sha256(b"mutated\n").hexdigest(),
            expected_uid=self.expected_uid,
            recovery_name_publisher=published.append,
        )

        self.assertEqual(ambiguous.resolution, "INDETERMINATE")
        self.assertEqual(published, [])
        self.assertTrue((self.workspace / first_name).exists())
        self.assertTrue(second.exists())

        second.unlink()
        original_candidate = self.workspace / first_name
        displaced = self.workspace / "displaced-outside-reserved-name"

        def replace_at_boundary(name: str) -> None:
            self.assertEqual(name, first_name)
            original_candidate.rename(displaced)
            original_candidate.write_bytes(b"original\n")
            os.chmod(original_candidate, 0o600)

        with self.assertRaises(ConflictError) as changed:
            workspace_module.reconcile_write_recovery(
                self.workspace,
                PILOT_PATH,
                phase="PREPARED",
                published_name=None,
                before=before,
                committed_after=None,
                expected_size=len(b"mutated\n"),
                expected_mode=0o600,
                expected_sha256=hashlib.sha256(b"mutated\n").hexdigest(),
                expected_uid=self.expected_uid,
                recovery_name_publisher=replace_at_boundary,
            )

        self.assertEqual(changed.exception.code, "recovery_candidate_changed")
        self.assertTrue(original_candidate.exists())
        self.assertTrue(displaced.exists())

    def test_reconciliation_validates_phase_and_committed_state_combinations(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.target.write_bytes(b"mutated\n")
        committed_after = inspect_target(
            self.workspace, PILOT_PATH, expected_uid=self.expected_uid
        )
        expected = {
            "expected_size": len(b"mutated\n"),
            "expected_mode": 0o600,
            "expected_sha256": hashlib.sha256(b"mutated\n").hexdigest(),
        }

        cases = (
            ("UNKNOWN", None),
            ("PREPARED", committed_after),
            ("APPLIED", None),
            ("APPLIED", before),
        )
        for phase, after in cases:
            with self.subTest(phase=phase, after=after):
                with self.assertRaises(RefusedError) as caught:
                    workspace_module.reconcile_write_recovery(
                        self.workspace,
                        PILOT_PATH,
                        phase=phase,
                        published_name=None,
                        before=before,
                        committed_after=after,
                        expected_uid=self.expected_uid,
                        **expected,
                    )
                self.assertEqual(caught.exception.code, "invalid_recovery_phase_state")

    def test_applied_reconciliation_revalidates_exact_pairing_at_cleanup_boundary(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        candidate_name = ".g2b-write-" + "d" * 32 + ".tmp"
        self.target.rename(self.workspace / candidate_name)
        self.target.write_bytes(b"mutated\n")
        os.chmod(self.target, 0o600)
        committed_after = inspect_target(
            self.workspace, PILOT_PATH, expected_uid=self.expected_uid
        )
        displaced_committed = self.workspace / "displaced-committed-target"

        def replace_target_at_boundary(name: str) -> None:
            self.assertEqual(name, candidate_name)
            self.target.rename(displaced_committed)
            self.target.write_bytes(b"mutated\n")
            os.chmod(self.target, 0o600)

        with self.assertRaises(ConflictError) as changed:
            workspace_module.reconcile_write_recovery(
                self.workspace,
                PILOT_PATH,
                phase="APPLIED",
                published_name=None,
                before=before,
                committed_after=committed_after,
                expected_size=len(b"mutated\n"),
                expected_mode=0o600,
                expected_sha256=hashlib.sha256(b"mutated\n").hexdigest(),
                expected_uid=self.expected_uid,
                recovery_name_publisher=replace_target_at_boundary,
            )

        self.assertEqual(changed.exception.code, "recovery_candidate_changed")
        self.assertTrue((self.workspace / candidate_name).exists())
        self.assertTrue(displaced_committed.exists())

    def test_absolute_traversal_tilde_and_nested_paths_are_refused(self) -> None:
        cases = (
            (str(self.target), "absolute_path_refused"),
            ("../G2B-PILOT.txt", "path_escape_refused"),
            ("~/G2B-PILOT.txt", "tilde_path_refused"),
            ("nested/G2B-PILOT.txt", "nested_path_refused"),
        )
        for relative_path, code in cases:
            with self.subTest(relative_path=relative_path):
                with self.assertRaises(RefusedError) as caught:
                    inspect_target(
                        self.workspace,
                        relative_path,
                        expected_uid=self.expected_uid,
                    )
                self.assertEqual(caught.exception.code, code)

    def test_workspace_symlink_non_directory_and_wrong_owner_are_refused(self) -> None:
        link = self.root / "workspace-link"
        link.symlink_to(self.workspace, target_is_directory=True)
        with self.assertRaises(RefusedError) as symlink:
            inspect_target(link, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(symlink.exception.code, "workspace_symlink_refused")

        regular = self.root / "regular"
        regular.write_bytes(b"x")
        with self.assertRaises(RefusedError) as non_directory:
            inspect_target(regular, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(non_directory.exception.code, "workspace_not_directory")

        with self.assertRaises(RefusedError) as owner:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid + 1)
        self.assertEqual(owner.exception.code, "workspace_owner_mismatch")

    def test_target_symlink_and_hardlink_are_refused(self) -> None:
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside\n")
        self.target.symlink_to(outside)
        with self.assertRaises(RefusedError) as symlink:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(symlink.exception.code, "target_symlink_refused")
        self.assertEqual(outside.read_bytes(), b"outside\n")

        self.target.unlink()
        self.target.write_bytes(b"linked\n")
        hardlink = self.root / "hardlink.txt"
        os.link(self.target, hardlink)
        with self.assertRaises(RefusedError) as linked:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(linked.exception.code, "target_hardlink_refused")

    def test_fifo_socket_directory_and_device_targets_are_refused(self) -> None:
        def assert_real_special_refused(kind: str, create) -> None:
            with self.subTest(kind=kind):
                create()
                try:
                    with self.assertRaises(RefusedError) as caught:
                        inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
                    self.assertEqual(caught.exception.code, "target_not_regular")
                finally:
                    if self.target.is_dir():
                        self.target.rmdir()
                    else:
                        self.target.unlink(missing_ok=True)

        assert_real_special_refused("fifo", lambda: os.mkfifo(self.target))

        def create_socket() -> None:
            sock = socket.socket(socket.AF_UNIX)
            self.addCleanup(sock.close)
            sock.bind(str(self.target))

        assert_real_special_refused("socket", create_socket)
        assert_real_special_refused("directory", self.target.mkdir)

        self.target.write_bytes(b"placeholder")
        original_lstat = os.lstat

        def device_lstat(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if path == PILOT_PATH and kwargs.get("dir_fd") is not None:
                values = list(result)
                values[0] = stat.S_IFCHR | 0o600
                return os.stat_result(values)
            return result

        with patch("control_plane.g2b.workspace.os.lstat", side_effect=device_lstat):
            with self.assertRaises(RefusedError) as device:
                inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(device.exception.code, "target_not_regular")

    def test_wrong_target_owner_and_unsafe_mode_are_refused(self) -> None:
        self.target.write_bytes(b"pilot\n")
        original_lstat = os.lstat

        def foreign_owner_lstat(path, *args, **kwargs):
            result = original_lstat(path, *args, **kwargs)
            if path == PILOT_PATH and kwargs.get("dir_fd") is not None:
                values = list(result)
                values[4] = self.expected_uid + 1
                return os.stat_result(values)
            return result

        with patch("control_plane.g2b.workspace.os.lstat", side_effect=foreign_owner_lstat):
            with self.assertRaises(RefusedError) as owner:
                inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(owner.exception.code, "target_owner_mismatch")

        os.chmod(self.target, 0o664)
        with self.assertRaises(RefusedError) as mode:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(mode.exception.code, "target_mode_refused")

    def test_requested_and_existing_secret_like_content_are_refused_without_echo(self) -> None:
        secret_like = b"password=abcdefghijk\n"
        with self.assertRaises(RefusedError) as requested:
            atomic_write(
                self.workspace,
                PILOT_PATH,
                secret_like,
                precondition=Precondition(state="ABSENT"),
                expected_uid=self.expected_uid,
            )
        self.assertEqual(requested.exception.code, "secret_like_content")
        self.assertNotIn("abcdefghijk", str(requested.exception))
        self.assertFalse(self.target.exists())

        self.target.write_bytes(secret_like)
        os.chmod(self.target, 0o644)
        with self.assertRaises(RefusedError) as existing:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(existing.exception.code, "secret_like_content")
        self.assertNotIn("abcdefghijk", str(existing.exception))

    def test_invalid_utf8_and_size_overflow_are_refused(self) -> None:
        for content, code in (
            (b"\xff\xfe", "binary_or_non_utf8"),
            (b"a" * (MAX_CONTENT_BYTES + 1), "content_too_large"),
        ):
            with self.subTest(code=code):
                with self.assertRaises(RefusedError) as caught:
                    atomic_write(
                        self.workspace,
                        PILOT_PATH,
                        content,
                        precondition=Precondition(state="ABSENT"),
                        expected_uid=self.expected_uid,
                    )
                self.assertEqual(caught.exception.code, code)
                self.assertFalse(self.target.exists())

        self.target.write_bytes(b"\xff\xfe")
        os.chmod(self.target, 0o644)
        with self.assertRaises(RefusedError) as existing:
            inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        self.assertEqual(existing.exception.code, "binary_or_non_utf8")

    def test_absent_and_sha256_precondition_mismatches_are_conflicts(self) -> None:
        self.target.write_bytes(b"current\n")
        os.chmod(self.target, 0o644)
        for precondition in (
            Precondition(state="ABSENT"),
            Precondition(sha256="0" * 64),
        ):
            with self.subTest(precondition=precondition):
                with self.assertRaises(ConflictError) as caught:
                    atomic_write(
                        self.workspace,
                        PILOT_PATH,
                        b"replacement\n",
                        precondition=precondition,
                        expected_uid=self.expected_uid,
                    )
                self.assertEqual(caught.exception.code, "precondition_mismatch")
                self.assertEqual(self.target.read_bytes(), b"current\n")

    def test_invalid_precondition_contract_is_refused(self) -> None:
        for precondition in (
            Precondition(),
            Precondition(state="ABSENT", sha256="0" * 64),
            Precondition(state="PRESENT"),
        ):
            with self.subTest(precondition=precondition):
                with self.assertRaises(RefusedError) as caught:
                    atomic_write(
                        self.workspace,
                        PILOT_PATH,
                        b"pilot\n",
                        precondition=precondition,
                        expected_uid=self.expected_uid,
                    )
                self.assertEqual(caught.exception.code, "invalid_precondition")

    def test_target_replacement_between_inspection_and_rename_is_a_conflict(self) -> None:
        self.target.write_bytes(b"old\n")
        os.chmod(self.target, 0o644)
        before = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_fsync = os.fsync
        replaced = False

        def replace_on_first_fsync(fd: int) -> None:
            nonlocal replaced
            if not replaced:
                replaced = True
                self.target.unlink()
                self.target.write_bytes(b"raced\n")
            real_fsync(fd)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=replace_on_first_fsync):
            with self.assertRaises(ConflictError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"new\n",
                    precondition=Precondition(sha256=before.sha256),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(self.target.read_bytes(), b"raced\n")
        self.assertEqual(list(self.workspace.glob(".g2b-*")), [])

    def test_absent_target_creation_at_rename_boundary_is_not_overwritten(self) -> None:
        real_noreplace = workspace_module._rename_noreplace

        def create_target_then_rename(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            if source.startswith(".g2b-write-"):
                self.target.write_bytes(b"raced\n")
                os.chmod(self.target, 0o644)
            real_noreplace(source_fd, source, destination_fd, destination)

        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=create_target_then_rename,
        ):
            with self.assertRaises(ConflictError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(state="ABSENT"),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(self.target.read_bytes(), b"raced\n")
        self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_absent_write_rename_disappearance_is_a_conflict(self) -> None:
        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=FileNotFoundError(errno.ENOENT, "synthetic rename race"),
        ):
            with self.assertRaises(ConflictError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(state="ABSENT"),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertFalse(self.target.exists())
        self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_absent_write_unsupported_and_io_rename_errors_are_refused(self) -> None:
        for error_number, expected_code in (
            (errno.ENOSYS, "atomic_rename_unsupported"),
            (errno.EIO, "atomic_rename_failed"),
        ):
            with self.subTest(error_number=error_number):
                with patch.object(
                    workspace_module,
                    "_rename_noreplace",
                    side_effect=OSError(error_number, "synthetic rename failure"),
                ):
                    with self.assertRaises(RefusedError) as caught:
                        atomic_write(
                            self.workspace,
                            PILOT_PATH,
                            b"pilot\n",
                            precondition=Precondition(state="ABSENT"),
                            expected_uid=self.expected_uid,
                        )
                self.assertEqual(caught.exception.code, expected_code)
                self.assertFalse(self.target.exists())
                self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_existing_target_replacement_at_exchange_boundary_is_reverted(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_exchange = getattr(workspace_module, "_rename_exchange", None)
        injected = False

        def replace_then_exchange(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            nonlocal injected
            if source.startswith(".g2b-write-") and not injected:
                injected = True
                self.target.unlink()
                self.target.write_bytes(b"raced\n")
                os.chmod(self.target, 0o644)
            assert real_exchange is not None
            real_exchange(source_fd, source, destination_fd, destination)

        with patch.object(
            workspace_module,
            "_rename_exchange",
            side_effect=replace_then_exchange,
            create=True,
        ):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(sha256=expected.sha256),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(caught.exception.resolution, "REVERTED")
        self.assertEqual(self.target.read_bytes(), b"raced\n")
        self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_write_exchange_disappearance_is_a_precommit_conflict(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)

        with patch.object(
            workspace_module,
            "_rename_exchange",
            side_effect=FileNotFoundError(errno.ENOENT, "synthetic exchange race"),
        ):
            with self.assertRaises(ConflictError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(sha256=expected.sha256),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(self.target.read_bytes(), b"original\n")
        self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_restore_exchange_disappearance_is_a_precommit_conflict(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        written = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=original.sha256),
            expected_uid=self.expected_uid,
        )

        with patch.object(
            workspace_module,
            "_rename_exchange",
            side_effect=FileNotFoundError(errno.ENOENT, "synthetic exchange race"),
        ):
            with self.assertRaises(ConflictError) as caught:
                atomic_restore(
                    self.workspace,
                    PILOT_PATH,
                    b"original\n",
                    expected_current=written.after,
                    restore_mode=original.mode,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(self.target.read_bytes(), b"mutated\n")
        self.assertEqual(list(self.workspace.glob(".g2b-write-*")), [])

    def test_write_exchange_unsupported_error_is_refused(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)

        with patch.object(
            workspace_module,
            "_rename_exchange",
            side_effect=OSError(errno.EOPNOTSUPP, "synthetic unsupported exchange"),
        ):
            with self.assertRaises(RefusedError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(sha256=expected.sha256),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "atomic_rename_unsupported")
        self.assertEqual(self.target.read_bytes(), b"original\n")

    def test_restore_exchange_io_error_is_refused(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        written = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=original.sha256),
            expected_uid=self.expected_uid,
        )

        with patch.object(
            workspace_module,
            "_rename_exchange",
            side_effect=OSError(errno.EIO, "synthetic exchange I/O failure"),
        ):
            with self.assertRaises(RefusedError) as caught:
                atomic_restore(
                    self.workspace,
                    PILOT_PATH,
                    b"original\n",
                    expected_current=written.after,
                    restore_mode=original.mode,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "atomic_rename_failed")
        self.assertEqual(self.target.read_bytes(), b"mutated\n")

    def test_write_directory_fsync_failure_reports_indeterminate_applied_state(self) -> None:
        real_fsync = os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError(errno.EIO, "synthetic directory fsync failure")
            real_fsync(fd)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=fail_directory_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(state="ABSENT"),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "write_durability_indeterminate")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertFalse(caught.exception.before.exists)
        self.assertEqual(
            caught.exception.observed_after.sha256,
            hashlib.sha256(b"pilot\n").hexdigest(),
        )
        self.assertEqual(str(caught.exception), "write_durability_indeterminate")

    def test_restore_directory_fsync_failure_reports_indeterminate_applied_state(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        written = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=original.sha256),
            expected_uid=self.expected_uid,
        )
        real_fsync = os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError(errno.EIO, "synthetic directory fsync failure")
            real_fsync(fd)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=fail_directory_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_restore(
                    self.workspace,
                    PILOT_PATH,
                    b"original\n",
                    expected_current=written.after,
                    restore_mode=original.mode,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "restore_durability_indeterminate")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(caught.exception.before, written.after)
        self.assertEqual(caught.exception.observed_after.sha256, original.sha256)

    def test_write_final_verification_failure_carries_observed_after_state(self) -> None:
        real_fsync = os.fsync
        raced = False

        def replace_after_directory_fsync(fd: int) -> None:
            nonlocal raced
            real_fsync(fd)
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not raced:
                raced = True
                self.target.unlink()
                self.target.write_bytes(b"raced\n")
                os.chmod(self.target, 0o644)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=replace_after_directory_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_write(
                    self.workspace,
                    PILOT_PATH,
                    b"pilot\n",
                    precondition=Precondition(state="ABSENT"),
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "final_target_mismatch")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(
            caught.exception.observed_after.sha256,
            hashlib.sha256(b"raced\n").hexdigest(),
        )

    def test_restore_final_verification_failure_carries_observed_after_state(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        written = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=original.sha256),
            expected_uid=self.expected_uid,
        )
        real_fsync = os.fsync
        raced = False

        def replace_after_directory_fsync(fd: int) -> None:
            nonlocal raced
            real_fsync(fd)
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not raced:
                raced = True
                self.target.unlink()
                self.target.write_bytes(b"raced\n")
                os.chmod(self.target, 0o600)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=replace_after_directory_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_restore(
                    self.workspace,
                    PILOT_PATH,
                    b"original\n",
                    expected_current=written.after,
                    restore_mode=original.mode,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "final_target_mismatch")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(
            caught.exception.observed_after.sha256,
            hashlib.sha256(b"raced\n").hexdigest(),
        )

    def test_atomic_restore_replaces_only_the_expected_current_state(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o600)
        original = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        written = atomic_write(
            self.workspace,
            PILOT_PATH,
            b"mutated\n",
            precondition=Precondition(sha256=original.sha256),
            expected_uid=self.expected_uid,
        )

        restored = atomic_restore(
            self.workspace,
            PILOT_PATH,
            b"original\n",
            expected_current=written.after,
            restore_mode=original.mode,
            expected_uid=self.expected_uid,
        )

        self.assertEqual(restored.before, written.after)
        self.assertEqual(restored.after.sha256, original.sha256)
        self.assertEqual(restored.after.mode, 0o600)

    def test_atomic_delete_requires_exact_frozen_state_and_fsyncs_removal(self) -> None:
        self.target.write_bytes(b"pilot\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        mismatched = TargetState(
            exists=True,
            size=expected.size,
            mode=expected.mode,
            uid=expected.uid,
            device=expected.device,
            inode=expected.inode,
            sha256="0" * 64,
        )
        with self.assertRaises(ConflictError) as conflict:
            atomic_delete(
                self.workspace,
                PILOT_PATH,
                expected_current=mismatched,
                expected_uid=self.expected_uid,
            )
        self.assertEqual(conflict.exception.code, "target_changed")
        self.assertTrue(self.target.exists())

        after = atomic_delete(
            self.workspace,
            PILOT_PATH,
            expected_current=expected,
            expected_uid=self.expected_uid,
        )
        self.assertFalse(after.exists)
        self.assertFalse(self.target.exists())

    def test_delete_target_replacement_immediately_before_rename_is_reverted(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_noreplace = getattr(workspace_module, "_rename_noreplace", None)

        def replace_then_rename(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            if source == PILOT_PATH:
                self.target.unlink()
                self.target.write_bytes(b"replacement\n")
                os.chmod(self.target, 0o644)
            assert real_noreplace is not None
            real_noreplace(source_fd, source, destination_fd, destination)

        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=replace_then_rename,
            create=True,
        ):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(caught.exception.resolution, "REVERTED")
        self.assertEqual(self.target.read_bytes(), b"replacement\n")
        self.assertEqual(list(self.workspace.glob(".g2b-delete-*")), [])

    def test_delete_move_rename_errno_classification_is_fail_closed(self) -> None:
        cases = (
            (errno.ENOENT, ConflictError, "target_changed"),
            (errno.EEXIST, RefusedError, "internal_name_collision"),
            (errno.EINVAL, RefusedError, "atomic_rename_unsupported"),
            (errno.EXDEV, RefusedError, "atomic_rename_unsupported"),
            (errno.EIO, RefusedError, "atomic_rename_failed"),
        )
        for error_number, error_type, expected_code in cases:
            with self.subTest(error_number=error_number):
                self.target.write_bytes(b"original\n")
                os.chmod(self.target, 0o644)
                expected = inspect_target(
                    self.workspace,
                    PILOT_PATH,
                    expected_uid=self.expected_uid,
                )
                with patch.object(
                    workspace_module,
                    "_rename_noreplace",
                    side_effect=OSError(error_number, "synthetic delete move failure"),
                ):
                    with self.assertRaises(error_type) as caught:
                        atomic_delete(
                            self.workspace,
                            PILOT_PATH,
                            expected_current=expected,
                            expected_uid=self.expected_uid,
                        )
                self.assertEqual(caught.exception.code, expected_code)
                self.assertEqual(self.target.read_bytes(), b"original\n")
                self.target.unlink()

    def test_delete_recovery_unsupported_errno_remains_post_mutation_state(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_noreplace = workspace_module._rename_noreplace
        calls = 0

        def fail_recovery_only(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            nonlocal calls
            calls += 1
            if calls == 1:
                real_noreplace(source_fd, source, destination_fd, destination)
                os.chmod(destination, 0o664, dir_fd=destination_fd, follow_symlinks=False)
                return
            raise OSError(errno.EOPNOTSUPP, "synthetic recovery unsupported")

        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=fail_recovery_only,
        ):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "delete_recovery_failed")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertFalse(self.target.exists())
        self.assertIsNotNone(caught.exception.recovery_name)
        self.assertTrue((self.workspace / caught.exception.recovery_name).exists())

    def test_delete_unsafe_moved_entry_is_restored_without_stranding(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_noreplace = getattr(workspace_module, "_rename_noreplace", None)

        def make_moved_entry_unsafe(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            assert real_noreplace is not None
            real_noreplace(source_fd, source, destination_fd, destination)
            os.chmod(destination, 0o664, dir_fd=destination_fd, follow_symlinks=False)

        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=make_moved_entry_unsafe,
            create=True,
        ):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "target_changed")
        self.assertEqual(caught.exception.resolution, "REVERTED")
        self.assertEqual(self.target.read_bytes(), b"original\n")
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o664)
        self.assertEqual(list(self.workspace.glob(".g2b-delete-*")), [])

    def test_delete_never_overwrites_recreated_target_and_retains_recovery_entry(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_noreplace = getattr(workspace_module, "_rename_noreplace", None)

        def recreate_target_after_move(
            source_fd: int,
            source: str,
            destination_fd: int,
            destination: str,
        ) -> None:
            assert real_noreplace is not None
            real_noreplace(source_fd, source, destination_fd, destination)
            self.target.write_bytes(b"recreated\n")
            os.chmod(self.target, 0o644)

        with patch.object(
            workspace_module,
            "_rename_noreplace",
            side_effect=recreate_target_after_move,
            create=True,
        ):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "delete_recovery_blocked")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(self.target.read_bytes(), b"recreated\n")
        self.assertIsNotNone(caught.exception.recovery_name)
        recovery = self.workspace / caught.exception.recovery_name
        self.assertEqual(recovery.read_bytes(), b"original\n")

    def test_delete_unlink_failure_is_reverted_and_reported(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_unlink = os.unlink

        def fail_tombstone_unlink(path, *args, **kwargs):
            if isinstance(path, str) and path.startswith(".g2b-delete-"):
                raise OSError(errno.EIO, "synthetic unlink failure")
            return real_unlink(path, *args, **kwargs)

        with patch("control_plane.g2b.workspace.os.unlink", side_effect=fail_tombstone_unlink):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "delete_cleanup_failed")
        self.assertEqual(caught.exception.resolution, "REVERTED")
        self.assertEqual(self.target.read_bytes(), b"original\n")
        self.assertEqual(list(self.workspace.glob(".g2b-delete-*")), [])

    def test_delete_directory_fsync_failure_reports_indeterminate_applied_state(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_fsync = os.fsync

        def fail_directory_fsync(fd: int) -> None:
            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError(errno.EIO, "synthetic directory fsync failure")
            real_fsync(fd)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=fail_directory_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "delete_durability_indeterminate")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertFalse(caught.exception.observed_after.exists)
        self.assertFalse(self.target.exists())

    def test_delete_symlink_recreated_after_fsync_preserves_mutation_context(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        outside = self.root / "outside.txt"
        outside.write_bytes(b"outside-private-material\n")
        real_fsync = os.fsync
        recreated = False

        def recreate_symlink_after_fsync(fd: int) -> None:
            nonlocal recreated
            real_fsync(fd)
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not recreated:
                recreated = True
                self.target.symlink_to(outside)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=recreate_symlink_after_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "final_target_indeterminate")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(caught.exception.before, expected)
        self.assertIsNone(caught.exception.observed_after)
        self.assertEqual(str(caught.exception), "final_target_indeterminate")
        self.assertNotIn("outside-private-material", str(caught.exception))
        self.assertTrue(self.target.is_symlink())

    def test_delete_unsafe_file_recreated_after_fsync_preserves_mutation_context(self) -> None:
        self.target.write_bytes(b"original\n")
        os.chmod(self.target, 0o644)
        expected = inspect_target(self.workspace, PILOT_PATH, expected_uid=self.expected_uid)
        real_fsync = os.fsync
        recreated = False

        def recreate_unsafe_file_after_fsync(fd: int) -> None:
            nonlocal recreated
            real_fsync(fd)
            if stat.S_ISDIR(os.fstat(fd).st_mode) and not recreated:
                recreated = True
                self.target.write_bytes(b"unsafe-recreated\n")
                os.chmod(self.target, 0o664)

        with patch("control_plane.g2b.workspace.os.fsync", side_effect=recreate_unsafe_file_after_fsync):
            with self.assertRaises(workspace_module.MutationStateError) as caught:
                atomic_delete(
                    self.workspace,
                    PILOT_PATH,
                    expected_current=expected,
                    expected_uid=self.expected_uid,
                )

        self.assertEqual(caught.exception.code, "final_target_indeterminate")
        self.assertEqual(caught.exception.resolution, "INDETERMINATE")
        self.assertEqual(caught.exception.before, expected)
        self.assertIsNone(caught.exception.observed_after)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o664)


if __name__ == "__main__":
    unittest.main()
