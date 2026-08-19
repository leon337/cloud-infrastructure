from __future__ import annotations

import pathlib
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/run_f1_2c_kvm_lab.sh"
IMAGE_ENV = ROOT / "platform/kvm/f1-2c-ubuntu-24.04-amd64.env"
USER_DATA = ROOT / "platform/kvm/f1-2c-cloud-init-user-data.yaml.in"
META_DATA = ROOT / "platform/kvm/f1-2c-cloud-init-meta-data.yaml.in"


class LocalKvmLabTests(unittest.TestCase):
    def test_image_is_release_pinned_by_url_and_sha256(self):
        text = IMAGE_ENV.read_text()
        self.assertIn(
            "MCF_KVM_IMAGE_URL=https://cloud-images.ubuntu.com/releases/noble/release-20260814/ubuntu-24.04-server-cloudimg-amd64.img",
            text,
        )
        self.assertIn(
            "MCF_KVM_IMAGE_SHA256=6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733",
            text,
        )
        self.assertNotIn("/current/", text)

    def test_launcher_has_one_fixed_candidate_argument_and_no_arbitrary_command(self):
        text = LAUNCHER.read_text()
        self.assertIn("[[ $# -eq 1 ]] || refuse exactly_one_candidate_sha_required", text)
        self.assertIn("[[ $1 =~ ^[0-9a-f]{40}$ ]] || refuse invalid_candidate_sha", text)
        self.assertNotIn("eval ", text)
        self.assertNotIn('bash -c "$' , text)

    def test_host_preflight_is_fail_closed_and_unprivileged(self):
        text = LAUNCHER.read_text()
        for command in (
            "qemu-system-x86_64",
            "qemu-img",
            "cloud-localds",
            "ssh",
            "scp",
            "ssh-keygen",
            "git",
            "curl",
            "sha256sum",
        ):
            with self.subTest(command=command):
                self.assertIn(command, text)
        self.assertIn("/dev/kvm", text)
        self.assertIn("vmi3506102", text)
        self.assertIn("node-01", text)
        self.assertIn("git -C \"$ROOT\" status --porcelain", text)
        self.assertIn("mcf-f1-2c-kvm.", text)
        self.assertNotRegex(text, r"(?m)^\s*sudo\b")
        self.assertNotRegex(text, r"(?m)^\s*(iptables|ip6tables|docker)\b")
        self.assertNotIn("-netdev tap", text)
        self.assertNotIn("brctl", text)
        self.assertTrue(LAUNCHER.stat().st_mode & stat.S_IXUSR)

    def test_cloud_init_creates_only_ephemeral_lab_identity(self):
        user_data = USER_DATA.read_text()
        meta = META_DATA.read_text()
        self.assertIn("name: mcf-lab", user_data)
        self.assertIn("sudo: ALL=(ALL) NOPASSWD:ALL", user_data)
        self.assertIn("ssh_pwauth: false", user_data)
        self.assertIn("__MCF_KVM_SSH_PUBLIC_KEY__", user_data)
        self.assertIn("/etc/mcf-f1-2c-kvm-lab", user_data)
        self.assertIn("MCF_F1_2C_KVM_LAB_V1", user_data)
        self.assertIn("docker.io", user_data)
        self.assertIn("hostname: mcf-f1-2c-kvm-__MCF_KVM_RUN_ID__", meta)
        self.assertNotIn("github_pat_", user_data)
        self.assertNotIn("BEGIN OPENSSH PRIVATE KEY", user_data)


if __name__ == "__main__":
    unittest.main()
