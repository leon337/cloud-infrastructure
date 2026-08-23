from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"


class PostRestartWaitTests(unittest.TestCase):
    def test_waits_for_network_services_after_docker_restart(self):
        text = HARNESS.read_text()

        expected = (
            "wait_for_unit_active "
            "cloud-platform-network-services.service 90"
        )

        self.assertIn("wait_for_unit_active() {", text)
        self.assertIn(expected, text)

        restart = text.index("sudo systemctl restart docker.service")
        wait = text.index(expected, restart)
        check = text.index('if ! sudo "$SERVICE" check', restart)

        self.assertLess(wait, check)


if __name__ == "__main__":
    unittest.main()
