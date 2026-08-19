from __future__ import annotations

import pathlib
import stat
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/run_f1_2c_kvm_lab.sh"
IMAGE_ENV = ROOT / "platform/kvm/f1-2c-ubuntu-24.04-amd64.env"
USER_DATA = ROOT / "platform/kvm/f1-2c-cloud-init-user-data.yaml.in"
META_DATA = ROOT / "platform/kvm/f1-2c-cloud-init-meta-data.yaml.in"
VM_HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"


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

    def test_qemu_uses_kvm_overlay_and_loopback_only_user_networking(self):
        text = LAUNCHER.read_text()
        self.assertIn("-enable-kvm", text)
        self.assertIn("-cpu host", text)
        self.assertIn("-smp 2", text)
        self.assertIn("-m 4096", text)
        self.assertIn("overlay.qcow2", text)
        self.assertIn("hostfwd=tcp:127.0.0.1:", text)
        self.assertIn("-nic", text)
        self.assertIn("user,model=virtio-net-pci", text)
        self.assertIn("guest_readiness_timeout", text)
        self.assertNotIn("pkill qemu", text)
        for forbidden in ("tap,", "-netdev tap", "brctl", "macvtap"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, text)

    def test_disposable_harness_has_separate_github_and_local_kvm_gates(self):
        script = VM_HARNESS.read_text()
        self.assertIn("GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY", script)
        self.assertIn("MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY", script)
        self.assertIn("verify_github_hosted_identity", script)
        self.assertIn("verify_local_kvm_identity", script)
        self.assertIn("MCF_F1_2C_KVM_LAB_V1", script)
        self.assertIn("/etc/mcf-f1-2c-kvm-lab", script)
        self.assertIn("mcf-f1-2c-kvm-", script)
        self.assertIn("VERSION_ID=\"24.04\"", script)
        self.assertIn("systemd-detect-virt", script)
        self.assertIn("vmi3506102", script)
        self.assertIn("sudo -n true", script)

    def test_candidate_transfer_is_exact_bundle_and_fixed_guest_harness(self):
        text = LAUNCHER.read_text()
        self.assertIn('git -C "$ROOT" bundle create "$RUN_ROOT/candidate.bundle" HEAD', text)
        self.assertIn('"$RUN_ROOT/candidate.bundle" mcf-lab@127.0.0.1:/tmp/candidate.bundle', text)
        self.assertIn("git clone /tmp/candidate.bundle /home/mcf-lab/cloud-infrastructure", text)
        self.assertIn('git rev-parse HEAD', text)
        self.assertIn("'$CANDIDATE_SHA'", text)
        self.assertIn(
            "DOCKER_BOUNDARY_TEST_PRIVILEGED_CONFIRM=MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY",
            text,
        )
        self.assertIn("scripts/test_node_network_services_vm.sh", text)
        self.assertNotIn("github.com/leon337/cloud-infrastructure", text)
        self.assertNotIn("GITHUB_TOKEN", text)
        self.assertNotIn("github_pat_", text)


if __name__ == "__main__":
    unittest.main()
