from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HELPER = ROOT / "platform/network/cloud-platform-network-services"


class RuntimeLockLifecycleTests(unittest.TestCase):
    def test_helper_recreates_private_runtime_dir_for_out_of_unit_calls(self):
        text = HELPER.read_text()
        self.assertIn(
            "readonly LOCK_DIR=/run/cloud-platform-network-services", text
        )
        self.assertIn("readonly LOCK=$LOCK_DIR/lock", text)
        self.assertIn("ensure_lock_dir() {", text)
        self.assertIn(
            'install -d -o root -g root -m 0700 "$LOCK_DIR"', text
        )
        self.assertIn(
            'ensure_lock_dir\nexec 9>"$LOCK"', text
        )
        self.assertNotIn("/run/lock/cloud-platform-network-services.lock", text)


if __name__ == "__main__":
    unittest.main()
