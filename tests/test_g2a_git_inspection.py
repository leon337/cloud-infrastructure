from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from control_plane.g2a.errors import OperationTimeout, RefusedError
from control_plane.g2a.git_inspection import (
    _bounded_diff,
    git_branch,
    git_diff,
    git_head,
    git_status,
    validate_git_repository,
)
from control_plane.g2a.protocol import Attachment


def run(*argv: str, cwd: pathlib.Path) -> str:
    completed = subprocess.run(argv, cwd=cwd, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def make_repo(root: pathlib.Path) -> tuple[pathlib.Path, str]:
    repo = root / "repo"
    repo.mkdir()
    run("git", "init", "-q", cwd=repo)
    (repo / "tracked.txt").write_text("base\n", encoding="utf-8")
    (repo / "staged.txt").write_text("base\n", encoding="utf-8")
    run("git", "add", "tracked.txt", "staged.txt", cwd=repo)
    run(
        "git",
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-q",
        "-m",
        "fixture",
        cwd=repo,
    )
    head = run("git", "rev-parse", "HEAD", cwd=repo)
    return repo, head


class GitInspectionTests(unittest.TestCase):
    def test_status_branch_head_and_diff_observe_local_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, expected_head = make_repo(pathlib.Path(tmp))
            (repo / "staged.txt").write_text("staged change\n", encoding="utf-8")
            run("git", "add", "staged.txt", cwd=repo)
            (repo / "tracked.txt").write_text("unstaged change\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("untracked\n", encoding="utf-8")

            status = git_status(repo)
            branch = git_branch(repo)
            head = git_head(repo)
            diff, attachment = git_diff(repo)

            self.assertTrue(status["dirty"])
            self.assertIn("untracked.txt", status["porcelain"])
            self.assertFalse(branch["detached"])
            self.assertIsInstance(branch["branch"], str)
            self.assertEqual(head["head"], expected_head)
            self.assertIn("staged change", diff["content"])
            self.assertIn("unstaged change", diff["content"])
            self.assertIsNone(attachment)

    def test_detached_head_is_reported_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = make_repo(pathlib.Path(tmp))
            run("git", "checkout", "--detach", "-q", "HEAD", cwd=repo)
            observed = git_branch(repo)
            self.assertTrue(observed["detached"])
            self.assertIsNone(observed["branch"])

    def test_external_git_dir_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            external, _ = make_repo(root)
            workspace = root / "workspace"
            workspace.mkdir()
            (workspace / ".git").write_text(f"gitdir: {external / '.git'}\n", encoding="utf-8")

            with self.assertRaises(RefusedError) as caught:
                validate_git_repository(workspace)
            self.assertEqual(caught.exception.code, "external_git_dir")

    def test_subprocess_timeout_maps_to_operation_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = pathlib.Path(tmp)
            with mock.patch(
                "control_plane.g2a.git_inspection.subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd=["git"], timeout=15),
            ):
                with self.assertRaises(OperationTimeout) as caught:
                    git_head(workspace)
            self.assertEqual(caught.exception.code, "git_timeout")

    def test_diff_thresholds_are_exact(self):
        inline, inline_attachment = _bounded_diff(b"a" * 131_072)
        self.assertEqual(len(inline["content"].encode("utf-8")), 131_072)
        self.assertIsNone(inline_attachment)

        large, attachment = _bounded_diff(b"a" * 131_073)
        self.assertIsNone(large["content"])
        self.assertIsInstance(attachment, Attachment)
        self.assertEqual(len(attachment.content), 131_073)

        with self.assertRaises(RefusedError) as caught:
            _bounded_diff(b"a" * 1_048_577)
        self.assertEqual(caught.exception.code, "diff_too_large")

    def test_secret_like_diff_is_refused_without_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = make_repo(pathlib.Path(tmp))
            (repo / "tracked.txt").write_text("password=abcdefghijk\n", encoding="utf-8")

            with self.assertRaises(RefusedError) as caught:
                git_diff(repo)
            self.assertEqual(caught.exception.code, "secret_like_content")
            self.assertNotIn("abcdefghijk", str(caught.exception))

    def test_sensitive_path_in_diff_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, _ = make_repo(pathlib.Path(tmp))
            (repo / ".env.example").write_text("EXAMPLE=placeholder\n", encoding="utf-8")
            run("git", "add", ".env.example", cwd=repo)
            run(
                "git",
                "-c",
                "user.name=Fixture",
                "-c",
                "user.email=fixture@example.invalid",
                "commit",
                "-q",
                "-m",
                "add example",
                cwd=repo,
            )
            (repo / ".env").write_text("SAFE_FIXTURE_TEXT\n", encoding="utf-8")
            run("git", "add", "-f", ".env", cwd=repo)

            with self.assertRaises(RefusedError) as caught:
                git_diff(repo)
            self.assertEqual(caught.exception.code, "sensitive_path_in_diff")


if __name__ == "__main__":
    unittest.main()
