from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import stat
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evidence_inheritance", ROOT / "scripts" / "classify_evidence_inheritance.py"
)
assert SPEC and SPEC.loader
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)


class GitRepoFixture:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.run("git", "init", "-q")
        self.run("git", "config", "user.name", "Evidence Test")
        self.run("git", "config", "user.email", "evidence@example.invalid")

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=self.root,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write(self, path: str, content: str, mode: int | None = None) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if mode is not None:
            target.chmod(mode)

    def commit(self, message: str) -> str:
        self.run("git", "add", "-A")
        self.run("git", "commit", "-q", "-m", message)
        return self.run("git", "rev-parse", "HEAD").stdout.strip()


class EvidenceInheritancePathTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        return GitRepoFixture(root), root

    def seed(self, repo: GitRepoFixture) -> str:
        repo.write("README.md", "baseline\n")
        repo.write("history/SESSION.md", "baseline\n")
        repo.write("scripts/example.sh", "#!/bin/sh\nexit 0\n", 0o755)
        return repo.commit("baseline")

    def classify(self, root: pathlib.Path, anchor: str, candidate: str):
        return EVIDENCE.classify_repository_delta(root, anchor, candidate)

    def test_history_only_delta_is_candidate_non_material(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("history/SESSION-2.md", "evidence\n")
        candidate = repo.commit("history")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "PASS")

    def test_checkpoint_modify_is_candidate_non_material(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("CHECKPOINT.md", "checkpoint\n")
        candidate = repo.commit("checkpoint")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "PASS")

    def test_script_change_is_refused_material_delta(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("scripts/example.sh", "#!/bin/sh\necho changed\n", 0o755)
        candidate = repo.commit("script")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "REFUSED")
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_workflow_change_is_refused_material_delta(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write(".github/workflows/new.yml", "name: unsafe\n")
        candidate = repo.commit("workflow")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_unknown_path_is_refused_unknown_path(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("mystery/value.txt", "unknown\n")
        candidate = repo.commit("unknown")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_UNKNOWN_PATH")

    def test_deleted_document_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        (root / "README.md").unlink()
        candidate = repo.commit("delete")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_rename_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        self.assertTrue((root / "README.md").exists())
        (root / "README.md").rename(root / "CONTEXT.md")
        candidate = repo.commit("rename")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_executable_bit_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        readme = root / "README.md"
        readme.chmod(readme.stat().st_mode | stat.S_IXUSR)
        candidate = repo.commit("mode")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_non_ancestor_candidate_is_refused_invalid_anchor(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.run("git", "checkout", "-q", "--orphan", "other")
        repo.run("git", "rm", "-q", "-rf", ".")
        repo.write("history/other.md", "other\n")
        candidate = repo.commit("other")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_INVALID_ANCHOR")


if __name__ == "__main__":
    unittest.main()
