from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "automation/ansible/roles/control_bridge_g2a_protected_read"
VARS = ROLE / "vars/main.yml"
TASKS = ROLE / "tasks/main.yml"
APPLY = ROOT / "automation/ansible/playbooks/apply-control-bridge-g2a-protected-read.yml"
SUDOERS = ROOT / "platform/sudoers/mcf-control-g2a-protected-read"
ROLLBACK = ROOT / "automation/ansible/playbooks/rollback-control-bridge-g2a-protected-read.yml"
RUNBOOK = ROOT / "runbooks/control-bridge-g2a-protected-read.md"

SOURCES = (
    "control_plane/__init__.py",
    "control_plane/g2a/__init__.py",
    "control_plane/g2a/errors.py",
    "control_plane/g2a/protocol.py",
    "control_plane/g2a/protected_reader.py",
    "control_plane/g2b/__init__.py",
    "control_plane/g2b/secret_policy.py",
    "platform/control-bridge/mcf-control-g2a-protected-read",
    "platform/sudoers/mcf-control-g2a-protected-read",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class G2AProtectedBootstrapArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(VARS.is_file())
        self.assertTrue(TASKS.is_file())
        self.assertTrue(APPLY.is_file())
        self.assertTrue(SUDOERS.is_file())
        self.vars = load_yaml(VARS)
        self.tasks = load_yaml(TASKS)

    def test_immutable_inventory_is_exact_and_hash_pinned(self) -> None:
        payloads = self.vars["g2a_protected_install_payloads"]
        by_source = {item["source"]: item for item in payloads}
        self.assertEqual(set(by_source), set(SOURCES))
        bundle = "/usr/local/lib/mcf-control-bridge-g2a-protected/"
        expected_destinations = {
            bundle + source
            for source in SOURCES
            if source.startswith("control_plane/")
        } | {
            "/usr/local/libexec/mcf-control-g2a-protected-read",
            "/etc/sudoers.d/mcf-control-g2a-protected-read",
        }
        self.assertEqual({item["destination"] for item in payloads}, expected_destinations)
        for source, item in by_source.items():
            with self.subTest(source=source):
                self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(item["sha256"], sha256(ROOT / source))
                self.assertEqual((item["owner"], item["group"]), ("root", "root"))
                self.assertEqual(int(item["mode"], 8) & 0o022, 0)
        self.assertEqual(by_source["platform/control-bridge/mcf-control-g2a-protected-read"]["mode"], "0555")
        self.assertEqual(by_source["platform/sudoers/mcf-control-g2a-protected-read"]["mode"], "0440")

    def test_private_paths_are_separate_and_no_mutation_state_is_managed(self) -> None:
        self.assertEqual(self.vars["g2a_protected_bundle_root"], "/usr/local/lib/mcf-control-bridge-g2a-protected")
        self.assertEqual(self.vars["g2a_protected_entrypoint_path"], "/usr/local/libexec/mcf-control-g2a-protected-read")
        self.assertEqual(self.vars["g2a_protected_sudoers_path"], "/etc/sudoers.d/mcf-control-g2a-protected-read")
        self.assertEqual(self.vars["g2a_protected_marker_path"], "/etc/mcf-control-g2a-protected-read.managed")
        self.assertEqual(self.vars["g2a_protected_install_lock"], "/run/lock/mcf-control-g2a-protected-read-install")
        blob = json.dumps(self.vars, sort_keys=True)
        self.assertNotIn('"destination": "/usr/local/lib/mcf-control-bridge/', blob)
        for forbidden in ("g2b-grant.json", "/state/g2b", "/revocations", "mcf-control-bridge-g2b.lock"):
            self.assertNotIn(forbidden, blob)

    def test_sudoers_allows_only_zero_argument_reader(self) -> None:
        self.assertEqual(
            SUDOERS.read_text(encoding="utf-8"),
            'Cmnd_Alias MCF_G2A_PROTECTED_READ = /usr/local/libexec/mcf-control-g2a-protected-read ""\n'
            'ubuntu ALL=(mcf-workspace) NOPASSWD: MCF_G2A_PROTECTED_READ\n',
        )

    def test_apply_is_host_guarded_and_does_not_reapply_g2b(self) -> None:
        playbook = load_yaml(APPLY)
        self.assertEqual(playbook[0]["ansible.builtin.import_playbook"], "controller-preflight.yml")
        self.assertEqual(playbook[1]["roles"], [{"role": "control_bridge_g2a_protected_read"}])
        self.assertNotIn("control_bridge_g2b", json.dumps(playbook))

    def test_role_requires_g2b_baseline_installs_atomically_and_marks_last(self) -> None:
        text = TASKS.read_text(encoding="utf-8")
        for literal in (
            "control_bridge_g2b/vars/main.yml",
            "g2b_marker_path",
            "g2b_workspace_path",
            "tests/fixtures/g2a/README.md",
            "mcf-workspace",
            "/usr/sbin/nologin",
            "passwd, -S",
            "platform_foundation_privileged_groups",
            "follow: false",
            "Acquire the exact G2-A protected-reader installation lock",
            "Validate sudoers before atomic install",
            "/usr/sbin/visudo -cf %s",
            "become_user: ubuntu",
            "sudo",
            "-n",
            "workspace.stat",
            "/var/run/docker.sock",
        ):
            self.assertIn(literal, text)
        for forbidden in (
            "ansible.builtin.user:",
            "ansible.builtin.group:",
            "g2b_grant_path",
            "g2b_state_path",
            "g2b_log_path",
            "systemd-tmpfiles",
            "chmod",
            "chown",
            "rm -rf",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIsInstance(self.tasks, list)
        last = self.tasks[-1]
        self.assertEqual(last["name"], "Place the G2-A protected-reader provenance marker last")
        self.assertEqual(last["ansible.builtin.copy"]["dest"], "{{ g2a_protected_marker_path }}")
        self.assertEqual(last["when"], "not ansible_check_mode")

    def test_rollback_is_exact_leaf_only_and_preserves_g2b_boundary(self) -> None:
        self.assertTrue(ROLLBACK.is_file(), "missing protected-reader rollback playbook")
        text = ROLLBACK.read_text(encoding="utf-8")
        playbook = load_yaml(ROLLBACK)
        self.assertEqual(playbook[0]["ansible.builtin.import_playbook"], "controller-preflight.yml")
        for literal in (
            "g2a_protected_rollback_confirm",
            "g2b_marker_path",
            "g2a_protected_marker_path",
            "g2a_protected_install_payloads",
            "pgrep",
            "lsof",
            "open file",
            "mcf-workspace",
            "/usr/sbin/nologin",
            "rmdir",
        ):
            self.assertIn(literal, text)
        for forbidden in (
            "rm -rf", "ansible.builtin.find", "with_fileglob", "recurse: true",
            "ansible.builtin.user:", "ansible.builtin.group:",
            "g2b_grant_path", "g2b_state_path", "g2b_log_path",
        ):
            self.assertNotIn(forbidden, text)
        self.assertEqual(
            playbook[-1]["tasks"][-1]["name"],
            "Remove the G2-A protected-reader provenance marker last",
        )

    def test_runbook_documents_gated_cross_lifecycle_and_prohibitions(self) -> None:
        self.assertTrue(RUNBOOK.is_file(), "missing protected-reader runbook")
        text = RUNBOOK.read_text(encoding="utf-8").lower()
        for phrase in (
            "read-only precheck",
            "exact-head ci",
            "--check",
            "recovery ssh",
            "leandro",
            "apply 1",
            "apply 2",
            "changed=0",
            "not_found",
            "reissue",
            "g2-a",
            "rollback",
            "package install",
            "permission relaxation",
            "node-01",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
