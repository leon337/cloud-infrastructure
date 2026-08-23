from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"


class KvmCleanupUnlinkTests(unittest.TestCase):
    def test_cleanup_unlinks_exactly_one_path_per_command(self):
        text = HARNESS.read_text()
        self.assertNotIn(
            'sudo unlink -- "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" "$SERVICE_UNIT"',
            text,
        )
        self.assertNotIn('sudo unlink -- "$BASE" "$BASE_UNIT"', text)
        self.assertIn(
            'for managed_file in "$SERVICE_MARKER" "$SYSCTL" "$SERVICE" "$SERVICE_UNIT"; do',
            text,
        )
        self.assertGreaterEqual(text.count('sudo unlink -- "$managed_file"'), 2)
        self.assertGreaterEqual(text.count('sudo unlink -- "$BASE"'), 1)
        self.assertGreaterEqual(text.count('sudo unlink -- "$BASE_UNIT"'), 1)


if __name__ == "__main__":
    unittest.main()
