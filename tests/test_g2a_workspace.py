from __future__ import annotations

import os
import pathlib
import tempfile
import unittest

from control_plane.g2a.errors import NotFoundError, RefusedError
from control_plane.g2a.workspace import (
    resolve_confined,
    workspace_list,
    workspace_read,
    workspace_stat,
)


class WorkspaceInspectionTests(unittest.TestCase):
    def test_stat_distinguishes_present_and_absent_without_creating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            present = root / "present"
            absent = root / "absent"
            present.mkdir()

            self.assertEqual(workspace_stat(present)["state"], "PRESENT")
            self.assertEqual(workspace_stat(absent)["state"], "ABSENT")
            self.assertFalse(absent.exists())

    def test_absolute_tilde_and_cross_project_traversal_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_a = root / "project-a"
            project_b = root / "project-b"
            project_a.mkdir()
            project_b.mkdir()
            (project_b / "private.txt").write_text("private", encoding="utf-8")

            cases = [
                ("/etc/passwd", "absolute_path_refused"),
                ("~/file", "tilde_path_refused"),
                ("../project-b/private.txt", "path_escape_refused"),
            ]
            for relative, code in cases:
                with self.subTest(relative=relative):
                    with self.assertRaises(RefusedError) as caught:
                        resolve_confined(project_a, relative)
                    self.assertEqual(caught.exception.code, code)

    def test_workspace_symlink_root_and_external_symlink_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            project_a = root / "project-a"
            project_b = root / "project-b"
            project_a.mkdir()
            project_b.mkdir()
            (project_a / "inside.txt").write_text("inside", encoding="utf-8")
            (project_b / "outside.txt").write_text("outside", encoding="utf-8")

            workspace_link = root / "workspace-link"
            workspace_link.symlink_to(project_a, target_is_directory=True)
            with self.assertRaises(RefusedError) as caught_root:
                resolve_confined(workspace_link, "inside.txt")
            self.assertEqual(caught_root.exception.code, "workspace_symlink_refused")

            (project_a / "outside-link").symlink_to(project_b / "outside.txt")
            with self.assertRaises(RefusedError) as caught_escape:
                resolve_confined(project_a, "outside-link")
            self.assertEqual(caught_escape.exception.code, "path_escape_refused")

            (project_a / "inside-link").symlink_to(project_a / "inside.txt")
            self.assertEqual(resolve_confined(project_a, "inside-link"), (project_a / "inside.txt").resolve())

    def test_missing_target_is_not_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            with self.assertRaises(NotFoundError) as caught:
                resolve_confined(workspace, "missing.txt")
            self.assertEqual(caught.exception.code, "path_not_found")

    def test_read_limits_encoding_and_secret_like_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            (workspace / "exact.txt").write_bytes(b"a" * 65536)
            (workspace / "large.txt").write_bytes(b"a" * 65537)
            (workspace / "binary.txt").write_bytes(b"\xff\xfe\x00")
            (workspace / "notes.txt").write_text("password=abcdefghijk\n", encoding="utf-8")

            self.assertEqual(len(workspace_read(workspace, "exact.txt")["content"].encode("utf-8")), 65536)

            for path, code in (
                ("large.txt", "file_too_large"),
                ("binary.txt", "binary_or_non_utf8"),
                ("notes.txt", "secret_like_content"),
            ):
                with self.subTest(path=path):
                    with self.assertRaises(RefusedError) as caught:
                        workspace_read(workspace, path)
                    self.assertEqual(caught.exception.code, code)
                    self.assertNotIn("abcdefghijk", str(caught.exception))

    def test_sensitive_paths_are_refused_and_env_example_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            sensitive = [
                ".git/config",
                ".env",
                "secrets/token.txt",
                "credentials.json",
                "credentials.yaml",
                "credentials.yml",
                "id_ed25519",
                "certificate.key",
            ]
            for relative in sensitive:
                path = workspace / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("safe fixture text", encoding="utf-8")

            for relative in sensitive:
                with self.subTest(relative=relative):
                    with self.assertRaises(RefusedError) as caught:
                        workspace_read(workspace, relative)
                    self.assertEqual(caught.exception.code, "sensitive_path_refused")

            (workspace / ".env.example").write_text("EXAMPLE_VALUE=placeholder\n", encoding="utf-8")
            self.assertIn("EXAMPLE_VALUE", workspace_read(workspace, ".env.example")["content"])

    def test_list_is_single_level_sorted_and_capped_at_500(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            (workspace / "b.txt").write_text("b", encoding="utf-8")
            (workspace / "a-dir").mkdir()
            (workspace / "c-link").symlink_to(workspace / "b.txt")

            listing = workspace_list(workspace)
            self.assertEqual([entry["name"] for entry in listing["entries"]], ["a-dir", "b.txt", "c-link"])
            self.assertEqual([entry["type"] for entry in listing["entries"]], ["directory", "file", "symlink"])
            self.assertNotIn("size", listing["entries"][0])
            self.assertEqual(listing["entries"][1]["size"], 1)
            self.assertNotIn("size", listing["entries"][2])

        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            for index in range(501):
                (workspace / f"f-{index:03d}").write_text("x", encoding="utf-8")
            with self.assertRaises(RefusedError) as caught:
                workspace_list(workspace)
            self.assertEqual(caught.exception.code, "list_entry_limit")


if __name__ == "__main__":
    unittest.main()
