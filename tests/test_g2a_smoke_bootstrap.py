from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOOTSTRAP = load_module("bootstrap_g2a_smoke_workspace", "scripts/bootstrap_g2a_smoke_workspace.py")

VALID = {
    "protocol": "MCF_G2A_SMOKE_BOOTSTRAP_V1",
    "request_id": "G2A-BOOTSTRAP-TEST-001",
    "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
    "action": "create",
}


def git(path: pathlib.Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


class G2ASmokeBootstrapTests(unittest.TestCase):
    def make_source(self, root: pathlib.Path) -> pathlib.Path:
        source = root / "source"
        source.mkdir()
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        git(source, "config", "user.email", "test@example.invalid")
        git(source, "config", "user.name", "G2A Test")
        (source / "README.md").write_text("fixture\n", encoding="utf-8")
        git(source, "add", "README.md")
        git(source, "commit", "-q", "-m", "fixture")
        return source

    @staticmethod
    def safe_boundary():
        return {
            "sudo_nopasswd": False,
            "docker_group": False,
            "docker_socket_access": False,
        }

    def test_success_copies_exact_clean_git_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = self.make_source(root)
            workspaces = root / "workspaces"
            result = BOOTSTRAP.execute_bootstrap(
                dict(VALID),
                source_root=source,
                workspace_root=workspaces,
                boundary_probe=self.safe_boundary,
            )
            target = workspaces / "leon337" / "g2a-smoke" / "dev"
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["source_head"], git(source, "rev-parse", "HEAD"))
            self.assertEqual(result["workspace_head"], git(target, "rev-parse", "HEAD"))
            self.assertEqual(git(target, "status", "--porcelain=v1"), "")
            self.assertEqual(result["fixture"]["path"], "README.md")
            self.assertEqual(result["fixture"]["size"], len(b"fixture\n"))
            self.assertFalse(result["boundary"]["sudo_nopasswd"])
            self.assertFalse(result["boundary"]["docker_group"])
            self.assertFalse(result["boundary"]["docker_socket_access"])

    def test_refuses_project_or_action_expansion(self):
        wrong_project = dict(VALID)
        wrong_project["project"] = dict(VALID["project"], name="other")
        with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "project_not_allowed"):
            BOOTSTRAP.validate_dispatch(wrong_project)

        wrong_action = dict(VALID, action="delete")
        with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "action_not_allowed"):
            BOOTSTRAP.validate_dispatch(wrong_action)

        extra = dict(VALID, path="/tmp/escape")
        with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "unexpected_dispatch_field"):
            BOOTSTRAP.validate_dispatch(extra)

    def test_refuses_existing_workspace_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = self.make_source(root)
            workspaces = root / "workspaces"
            target = workspaces / "leon337" / "g2a-smoke" / "dev"
            target.mkdir(parents=True)
            sentinel = target / "sentinel.txt"
            sentinel.write_text("preserve\n", encoding="utf-8")
            with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "workspace_already_exists"):
                BOOTSTRAP.execute_bootstrap(
                    dict(VALID),
                    source_root=source,
                    workspace_root=workspaces,
                    boundary_probe=self.safe_boundary,
                )
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve\n")

    def test_refuses_workspace_root_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = self.make_source(root)
            real = root / "real"
            real.mkdir()
            link = root / "workspaces"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "workspace_root_symlink_refused"):
                BOOTSTRAP.execute_bootstrap(
                    dict(VALID),
                    source_root=source,
                    workspace_root=link,
                    boundary_probe=self.safe_boundary,
                )

    def test_boundary_expansion_rolls_back_new_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            source = self.make_source(root)
            workspaces = root / "workspaces"

            def expanded_boundary():
                return {
                    "sudo_nopasswd": True,
                    "docker_group": False,
                    "docker_socket_access": False,
                }

            with self.assertRaisesRegex(BOOTSTRAP.BootstrapError, "sudo_boundary_expanded"):
                BOOTSTRAP.execute_bootstrap(
                    dict(VALID),
                    source_root=source,
                    workspace_root=workspaces,
                    boundary_probe=expanded_boundary,
                )
            target = workspaces / "leon337" / "g2a-smoke" / "dev"
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
