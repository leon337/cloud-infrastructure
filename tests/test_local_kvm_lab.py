from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/run_f1_2c_kvm_lab.sh"
IMAGE_ENV = ROOT / "platform/kvm/f1-2c-ubuntu-24.04-amd64.env"


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


if __name__ == "__main__":
    unittest.main()
