from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
ROLE = ROOT / "automation/ansible/roles/control_bridge_g2b"
VARS = ROLE / "vars/main.yml"
TASKS = ROLE / "tasks/main.yml"
APPLY = ROOT / "automation/ansible/playbooks/apply-control-bridge-g2b.yml"
ISSUE = ROOT / "automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml"
ROLLBACK = ROOT / "automation/ansible/playbooks/rollback-control-bridge-g2b.yml"
RUNBOOK = ROOT / "runbooks/control-bridge-g2b.md"

BUNDLE_SOURCES = (
    "control_plane/__init__.py",
    "control_plane/g2b/__init__.py",
    "control_plane/g2b/errors.py",
    "control_plane/g2b/executor.py",
    "control_plane/g2b/grant.py",
    "control_plane/g2b/protocol.py",
    "control_plane/g2b/secret_policy.py",
    "control_plane/g2b/state.py",
    "control_plane/g2b/workspace.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class G2BBootstrapArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.vars = load_yaml(VARS)
        self.tasks = load_yaml(TASKS)

    def test_immutable_vars_pin_every_reviewed_source_destination_and_hash(self) -> None:
        payloads = self.vars["g2b_install_payloads"]
        by_source = {item["source"]: item for item in payloads}
        self.assertEqual(
            set(by_source),
            set(BUNDLE_SOURCES)
            | {
                "platform/control-bridge/mcf-control-g2b",
                "platform/sudoers/mcf-control-g2b",
                "platform/tmpfiles.d/mcf-control-bridge-g2b.conf",
                "tests/fixtures/g2a/README.md",
            },
        )
        for source, item in by_source.items():
            with self.subTest(source=source):
                self.assertRegex(item["sha256"], r"^[0-9a-f]{64}$")
                self.assertEqual(item["sha256"], sha256(ROOT / source))
                self.assertTrue(item["destination"].startswith("/"))

        destinations = {item["destination"] for item in payloads}
        self.assertEqual(
            destinations,
            {
                "/usr/local/lib/mcf-control-bridge/" + source
                for source in BUNDLE_SOURCES
            }
            | {
                "/usr/local/libexec/mcf-control-g2b",
                "/etc/sudoers.d/mcf-control-g2b",
                "/etc/tmpfiles.d/mcf-control-bridge-g2b.conf",
                "/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev/README.md",
            },
        )
        for path in (
            "/etc/mcf-control-bridge/g2b-grant.json",
            "/etc/mcf-control-bridge-g2b.managed",
            "/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev",
            "/var/lib/mcf-control-bridge/state/g2b",
            "/var/log/mcf-control-bridge/g2b",
        ):
            self.assertIn(path, json.dumps(self.vars, sort_keys=True))

    def test_canonical_bundle_hash_matches_exact_task5_package(self) -> None:
        digest = hashlib.sha256()
        for source in sorted(BUNDLE_SOURCES):
            digest.update(f"{sha256(ROOT / source)}  {source}\n".encode("utf-8"))
        self.assertEqual(self.vars["g2b_executor_bundle_sha256"], digest.hexdigest())

    def test_role_is_marker_gated_installs_no_grant_and_places_marker_last(self) -> None:
        text = TASKS.read_text(encoding="utf-8")
        self.assertIn("follow: false", text)
        self.assertIn("Refuse to adopt any unmarked pre-existing G2-B object", text)
        self.assertIn("Validate exact existing G2-B payload provenance", text)
        self.assertNotIn("/home/ubuntu/mcf-workspaces", text)
        self.assertNotRegex(text, r"(?m)^\s*(?:src|content):.*g2b-grant\.json")
        self.assertNotIn("g2b_grant_not_before", text)

        self.assertIsInstance(self.tasks, list)
        last = self.tasks[-1]
        self.assertEqual(last["name"], "Place the G2-B provenance marker last")
        self.assertIn("ansible.builtin.copy", last)
        self.assertEqual(last["ansible.builtin.copy"]["dest"], "{{ g2b_marker_path }}")
        self.assertEqual(last["when"], "not ansible_check_mode")

    def test_role_enforces_identity_permissions_sudoers_tmpfiles_and_boundary_probes(self) -> None:
        text = TASKS.read_text(encoding="utf-8")
        for literal in (
            "mcf-workspace",
            "/usr/sbin/nologin",
            "password_lock: true",
            "append: false",
            "platform_foundation_privileged_groups",
            "visudo",
            "-cf",
            "systemd-tmpfiles",
            "--create",
            "become_user: ubuntu",
            "sudo",
            "-n",
            "-u",
            "grant_missing",
        ):
            self.assertIn(literal, text)
        self.assertNotIn("ansible.builtin.shell", text)

        roots = self.vars["g2b_root_directories"]
        self.assertTrue(roots)
        for item in roots:
            self.assertEqual((item["owner"], item["group"]), ("root", "root"))
            self.assertEqual(int(item["mode"], 8) & 0o022, 0)
        service = {item["path"]: item for item in self.vars["g2b_service_directories"]}
        for path in (
            "/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev",
            "/var/lib/mcf-control-bridge/state/g2b",
            "/var/log/mcf-control-bridge/g2b",
        ):
            self.assertEqual(service[path]["owner"], "mcf-workspace")
            self.assertEqual(service[path]["group"], "mcf-workspace")
            self.assertEqual(service[path]["mode"], "0700")

    def test_apply_and_grant_issuance_are_separate_host_guarded_playbooks(self) -> None:
        apply = load_yaml(APPLY)
        issue_text = ISSUE.read_text(encoding="utf-8")
        issue = load_yaml(ISSUE)
        self.assertEqual(apply[0]["ansible.builtin.import_playbook"], "controller-preflight.yml")
        self.assertEqual(apply[1]["roles"], [{"role": "control_bridge_g2b"}])
        self.assertEqual(issue[0]["ansible.builtin.import_playbook"], "controller-preflight.yml")
        self.assertIsInstance(issue, list)
        for variable in (
            "g2b_grant_id",
            "g2b_grant_not_before",
            "g2b_grant_not_after",
            "g2b_executor_sha256",
        ):
            self.assertIn(f"{variable} is defined", issue_text)
        for literal in (
            "86400",
            "active",
            "revoked",
            "root",
            'mode: "0644"',
            "validate:",
            "CONTROL-BRIDGE-G2B-PILOT",
            "G2B-PILOT.txt",
            "workspace.write",
            "rollback",
            "status",
            "revoke",
            "25374535",
            "g2b_issue_existing_grant.keys()",
        ):
            self.assertIn(literal, issue_text)
        self.assertNotIn("roles:\n    - role: control_bridge_g2b", issue_text)

    def test_rollback_uses_strict_gates_and_only_exact_leaf_or_rmdir_cleanup(self) -> None:
        text = ROLLBACK.read_text(encoding="utf-8")
        load_yaml(ROLLBACK)
        for gate in (
            "marker",
            "hash",
            "expired",
            "revoked",
            "active mutation",
            "snapshot",
            "unresolved receipt",
            "pilot file",
            "process",
            "open file",
            "baseline",
        ):
            self.assertIn(gate, text.lower())
        for identity_gate in (
            "/usr/sbin/nologin",
            "passwd, -S",
            "platform_foundation_privileged_groups",
            "password state",
        ):
            self.assertIn(identity_gate, text)
        for forbidden in (
            "rm -rf",
            "userdel -r",
            "autoremove",
            "ansible.builtin.find",
            "with_fileglob",
        ):
            self.assertNotIn(forbidden, text)
        self.assertNotRegex(text, r"(?m)^\s*recurse:\s*true")
        self.assertEqual(
            load_yaml(ROLLBACK)[-1]["tasks"][-1]["name"],
            "Remove the G2-B provenance marker last",
        )

    def test_runbook_has_human_gate_sequence_without_credentials_or_real_grant_id(self) -> None:
        text = RUNBOOK.read_text(encoding="utf-8")
        lower = text.lower()
        for phrase in (
            "precheck",
            "impact",
            "second ssh session",
            "sudo",
            "timestamp",
            "--check",
            "idempotence",
            "status",
            "replay",
            "conflict",
            "concurrency",
            "rollback",
            "revoke",
            "reissue",
            "emergency stop",
            "non-goals",
        ):
            self.assertIn(phrase, lower)
        self.assertNotRegex(text, r"gh[pousr]_[A-Za-z0-9_]{20,}")
        self.assertNotRegex(text, r"-----BEGIN (?:OPENSSH|RSA|EC) PRIVATE KEY-----")
        self.assertNotRegex(text, r"G2B-(?:PILOT|NODE01)-20\d{6}-\d+")


if __name__ == "__main__":
    unittest.main()
