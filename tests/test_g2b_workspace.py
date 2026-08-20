from __future__ import annotations

import hashlib
import os
from pathlib import Path
import socket
import stat
import tempfile
import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
