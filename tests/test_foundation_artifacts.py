from __future__ import annotations

import pathlib
import subprocess
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FoundationArtifactTests(unittest.TestCase):
    def test_foundation_marker_is_external_and_root_only(self):
        contract = (
            ROOT
            / "automation"
            / "ansible"
            / "roles"
            / "platform_foundation"
            / "vars"
            / "main.yml"
        ).read_text(encoding="utf-8")
        reconcile = (
            ROOT
            / "automation"
            / "ansible"
            / "roles"
            / "platform_foundation"
            / "tasks"
            / "reconcile.yml"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "platform_foundation_marker: /etc/cloud-platform-foundation.managed",
            contract,
        )
        self.assertIn('mode: "0600"', reconcile)
        self.assertIn("group: root", reconcile)
        self.assertNotIn("/etc/cloud-platform/.foundation-managed", contract)

    def test_rollback_deletion_is_non_recursive_and_marker_is_last(self):
        rollback_mutation = (
            ROOT
            / "automation"
            / "ansible"
            / "playbooks"
            / "tasks"
            / "rollback-foundation-mutate.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("argv: [unlink, --", rollback_mutation)
        self.assertIn("argv: [rmdir,", rollback_mutation)
        self.assertNotIn("ansible.builtin.file:", rollback_mutation)
        self.assertLess(
            rollback_mutation.index("daemon_reload: true"),
            rollback_mutation.index("Remove the exact management marker last"),
        )

    def test_local_test_inventory_requires_the_disposable_container_boundary(self):
        preflight = (
            ROOT
            / "automation"
            / "ansible"
            / "playbooks"
            / "controller-preflight.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("path: /.dockerenv", preflight)
        self.assertIn("argv: [systemd-detect-virt, --container]", preflight)
        self.assertIn("/workspace/cloud-infrastructure", preflight)

    def test_ssh_profile_is_identity_only_and_key_bound(self):
        inventory = (
            ROOT / "automation" / "ansible" / "inventory" / "dev" / "hosts.yml"
        ).read_text(encoding="utf-8")
        preflight = (
            ROOT
            / "automation"
            / "ansible"
            / "playbooks"
            / "controller-preflight.yml"
        ).read_text(encoding="utf-8")
        for setting in (
            "IdentitiesOnly=yes",
            "PreferredAuthentications=publickey",
            "PasswordAuthentication=no",
            "KbdInteractiveAuthentication=no",
            "StrictHostKeyChecking=yes",
        ):
            self.assertIn(setting, inventory)
            self.assertIn(setting, preflight)
        self.assertIn("PLATFORM_SSH_KEY_FILE", preflight)

    def test_systemd_slices_have_accounting_but_no_service_or_listener(self):
        for name in ("cloud-platform.slice", "cloud-workloads.slice"):
            content = (ROOT / "platform" / "systemd" / name).read_text(encoding="utf-8")
            self.assertIn("[Slice]", content)
            self.assertIn("CPUAccounting=yes", content)
            self.assertIn("MemoryAccounting=yes", content)
            self.assertNotIn("ExecStart=", content)
            self.assertNotIn("Listen", content)
            self.assertNotIn("MemoryMax=", content)
            self.assertNotIn("CPUQuota=", content)

    def test_runtime_credentials_are_root_only_and_ephemeral(self):
        content = (
            ROOT / "platform" / "tmpfiles.d" / "cloud-platform.conf"
        ).read_text(encoding="utf-8")
        self.assertIn("d /run/cloud-platform/credentials 0700 root root", content)
        self.assertNotIn("/var/lib/cloud-platform/credentials", content)

    def test_inventory_does_not_embed_password_or_key_material(self):
        content = (
            ROOT / "automation" / "ansible" / "inventory" / "dev" / "hosts.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("PLATFORM_SSH_KEY_FILE", content)
        self.assertNotIn("ansible_password", content)
        self.assertNotIn("ansible_become_password", content)
        self.assertNotIn("PRIVATE KEY", content)

    def test_systemd_unit_syntax(self):
        executable = pathlib.Path("/usr/bin/systemd-analyze")
        if not executable.exists():
            self.skipTest("systemd-analyze is not available on this controller")
        result = subprocess.run(
            [
                str(executable),
                "verify",
                str(ROOT / "platform" / "systemd" / "cloud-platform.slice"),
                str(ROOT / "platform" / "systemd" / "cloud-workloads.slice"),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
