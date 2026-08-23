from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"


class PostRestartDiagnosticsTests(unittest.TestCase):
    def test_harness_captures_post_restart_root_cause_before_failure(self):
        text = HARNESS.read_text()
        self.assertIn("diagnose_post_restart_failure() {", text)
        for marker in (
            "=== POST_RESTART_DOCKER_STATUS ===",
            "=== POST_RESTART_BASE_STATUS ===",
            "=== POST_RESTART_BASE_CHECK ===",
            "=== POST_RESTART_SERVICES_STATUS ===",
            "=== POST_RESTART_SERVICES_JOURNAL ===",
            "=== POST_RESTART_SERVICES_CHECK ===",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, text)
        self.assertGreaterEqual(text.count("diagnose_post_restart_failure"), 4)


if __name__ == "__main__":
    unittest.main()
