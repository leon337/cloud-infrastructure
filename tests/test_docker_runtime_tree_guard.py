from __future__ import annotations

import importlib.util
import os
import pathlib
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
GUARD_PATH = (
    ROOT
    / "automation"
    / "ansible"
    / "roles"
    / "docker_runtime"
    / "files"
    / "runtime_tree_guard.py"
)
SPEC = importlib.util.spec_from_file_location("runtime_tree_guard", GUARD_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime_tree_guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_tree_guard)


class DockerRuntimeTreeGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = pathlib.Path(self.temporary.name)
        self.docker_root = self.base / "docker"
        self.containerd_root = self.base / "containerd"
        self.docker_root.mkdir()
        self.containerd_root.mkdir()
        self.docker_root.chmod(0o750)
        self.containerd_root.chmod(0o750)
        self.roots = (self.docker_root, self.containerd_root)
        self.baseline = self.base / "baseline.json"
        self.removal = self.base / "removal.json"
        self.uid = os.getuid()
        self.gid = os.getgid()

    def _snapshot(self) -> int:
        return runtime_tree_guard.snapshot(
            self.roots,
            self.baseline,
            expected_uid=self.uid,
            expected_gid=self.gid,
            findmnt_binary=None,
        )

    def test_snapshot_and_verify_exact_empty_runtime_metadata(self) -> None:
        (self.docker_root / "network").mkdir()
        (self.docker_root / "network").chmod(0o750)
        (self.docker_root / "network" / "local-kv.db").write_bytes(b"fixture")
        (self.docker_root / "network" / "local-kv.db").chmod(0o640)
        (self.containerd_root / "metadata.db").write_bytes(b"fixture")
        (self.containerd_root / "metadata.db").chmod(0o640)

        self.assertEqual(self._snapshot(), 5)
        self.assertEqual(
            runtime_tree_guard.verify(
                self.roots,
                self.baseline,
                expected_uid=self.uid,
                expected_gid=self.gid,
                findmnt_binary=None,
            ),
            5,
        )

        (self.docker_root / "unexpected").write_bytes(b"drift")
        (self.docker_root / "unexpected").chmod(0o640)
        with self.assertRaisesRegex(
            runtime_tree_guard.GuardError, "differs from the proven-empty baseline"
        ):
            runtime_tree_guard.verify(
                self.roots,
                self.baseline,
                expected_uid=self.uid,
                expected_gid=self.gid,
                findmnt_binary=None,
            )

    def test_symlinks_and_hardlinks_are_refused(self) -> None:
        outside = self.base / "outside"
        outside.write_bytes(b"preserve")
        outside.chmod(0o640)
        (self.docker_root / "escape").symlink_to(outside)
        with self.assertRaisesRegex(
            runtime_tree_guard.GuardError,
            r"non-regular entry: path=.*escape type_bits=0o120000",
        ):
            self._snapshot()
        (self.docker_root / "escape").unlink()

        first = self.docker_root / "first"
        second = self.docker_root / "second"
        first.write_bytes(b"linked")
        first.chmod(0o640)
        os.link(first, second)
        with self.assertRaisesRegex(runtime_tree_guard.GuardError, "hardlinks"):
            self._snapshot()
        self.assertEqual(outside.read_bytes(), b"preserve")

    def test_prepare_and_remove_consumes_only_frozen_exact_paths(self) -> None:
        nested = self.docker_root / "network" / "files"
        nested.mkdir(parents=True)
        (self.docker_root / "network").chmod(0o750)
        nested.chmod(0o750)
        (nested / "local-kv.db").write_bytes(b"fixture")
        (nested / "local-kv.db").chmod(0o640)
        (self.containerd_root / "metadata.db").write_bytes(b"fixture")
        (self.containerd_root / "metadata.db").chmod(0o640)
        outside = self.base / "outside"
        outside.write_bytes(b"preserve")
        outside.chmod(0o640)

        entry_count = self._snapshot()
        self.assertEqual(
            runtime_tree_guard.prepare_removal(
                self.roots,
                self.baseline,
                self.removal,
                expected_uid=self.uid,
                expected_gid=self.gid,
                findmnt_binary=None,
            ),
            entry_count,
        )
        self.assertEqual(
            runtime_tree_guard.remove_from_manifest(
                self.roots,
                self.removal,
                expected_uid=self.uid,
                expected_gid=self.gid,
            ),
            entry_count,
        )
        self.assertFalse(self.docker_root.exists())
        self.assertFalse(self.containerd_root.exists())
        self.assertEqual(outside.read_bytes(), b"preserve")

    def test_inode_change_after_manifest_freeze_is_refused(self) -> None:
        target = self.docker_root / "metadata.db"
        target.write_bytes(b"first")
        target.chmod(0o640)
        self._snapshot()
        runtime_tree_guard.prepare_removal(
            self.roots,
            self.baseline,
            self.removal,
            expected_uid=self.uid,
            expected_gid=self.gid,
            findmnt_binary=None,
        )
        replacement = self.base / "replacement"
        replacement.write_bytes(b"replacement")
        replacement.chmod(0o640)
        target.unlink()
        replacement.rename(target)

        with self.assertRaisesRegex(runtime_tree_guard.GuardError, "changed after"):
            runtime_tree_guard.remove_from_manifest(
                self.roots,
                self.removal,
                expected_uid=self.uid,
                expected_gid=self.gid,
            )
        self.assertEqual(target.read_bytes(), b"replacement")

    def test_open_runtime_file_blocks_removal_manifest_creation(self) -> None:
        target = self.docker_root / "metadata.db"
        target.write_bytes(b"open")
        target.chmod(0o640)
        self._snapshot()

        with target.open("rb") as open_file:
            self.assertEqual(open_file.read(1), b"o")
            with self.assertRaisesRegex(
                runtime_tree_guard.GuardError, "open runtime path"
            ):
                runtime_tree_guard.prepare_removal(
                    self.roots,
                    self.baseline,
                    self.removal,
                    expected_uid=self.uid,
                    expected_gid=self.gid,
                    findmnt_binary=None,
                )
        self.assertFalse(self.removal.exists())

    def test_operational_cli_has_literal_roots_and_no_path_arguments(self) -> None:
        source = GUARD_PATH.read_text(encoding="utf-8")
        self.assertIn('pathlib.Path("/var/lib/docker")', source)
        self.assertIn('pathlib.Path("/var/lib/containerd")', source)
        self.assertIn("len(argv) != 2", source)
        self.assertNotIn("rmtree", source)
        self.assertNotIn("rm -rf", source)


if __name__ == "__main__":
    unittest.main()
