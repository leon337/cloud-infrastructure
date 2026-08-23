from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
USER_DATA = ROOT / "platform/kvm/f1-2c-cloud-init-user-data.yaml.in"


class KvmComposeDependencyTests(unittest.TestCase):
    def test_cloud_init_installs_compose_v2_for_network_services(self):
        self.assertIn("  - docker-compose-v2\n", USER_DATA.read_text())


if __name__ == "__main__":
    unittest.main()
