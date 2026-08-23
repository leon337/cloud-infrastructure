from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
UNIT = ROOT / "platform/systemd/cloud-platform-network-services.service"


class NetworkServicesSystemdSandboxTests(unittest.TestCase):
    def test_network_services_unit_allows_only_base_enforcement_lock(self):
        text = UNIT.read_text()
        self.assertIn(
            "ReadWritePaths=/run/lock/cloud-platform-network-enforcement.lock\n",
            text,
        )
        self.assertNotIn("\nReadWritePaths=/run/lock\n", text)


if __name__ == "__main__":
    unittest.main()
