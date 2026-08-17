from __future__ import annotations

import pathlib
import unittest

from scripts.compile_network_policy import PolicyError, load_and_validate
from scripts.reconcile_network_scopes import expected_networks


ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = ROOT / "platform/network/f1-2c-policy.disposable.yaml"
SCRIPT = (ROOT / "scripts/reconcile_network_scopes.py").read_text(encoding="utf-8")


class NetworkScopeReconcilerTests(unittest.TestCase):
    def test_disposable_policy_is_explicit_and_not_accepted_by_default_compiler(self):
        with self.assertRaisesRegex(PolicyError, "status is not accepted"):
            load_and_validate(POLICY)
        networks, digest = expected_networks(POLICY)
        self.assertEqual(len(networks), 3)
        self.assertEqual(len(digest), 64)
        self.assertEqual(
            {item["interface"] for item in networks},
            {"cp00000001", "cp00000002", "cp00000003"},
        )

    def test_reconciler_has_narrow_disposable_and_network_boundaries(self):
        required = (
            'choices=("apply", "check", "rollback")',
            "GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY",
            'os.environ.get("GITHUB_ACTIONS") != "true"',
            'os.environ.get("ImageOS") != "ubuntu24"',
            '"real_dev_node_refused"',
            '"route_collision=',
            '"--internal"',
            '"com.docker.network.bridge.enable_icc=false"',
            '"com.docker.network.bridge.host_binding_ipv4=127.0.0.1"',
            'f"network_has_attachments=',
            '"unexpected_custom_networks="',
        )
        for value in required:
            self.assertIn(value, SCRIPT)
        self.assertNotIn("shell=True", SCRIPT)
        self.assertNotIn("rm -rf", SCRIPT)


if __name__ == "__main__":
    unittest.main()
