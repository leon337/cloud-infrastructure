from pathlib import Path
import unittest

import yaml


class CanonicalStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = yaml.safe_load(Path("state/current.yaml").read_text(encoding="utf-8"))

    def test_main_identity(self):
        self.assertEqual(self.state["canonical_repository"], "leon337/cloud-infrastructure")
        self.assertEqual(self.state["canonical_branch"], "main")

    def test_future_state_is_not_promoted(self):
        f1 = self.state["platform"]["f1_2c"]
        self.assertEqual(f1["status"], "REQUIRES_REVIEW")
        self.assertFalse(f1["accepted"])
        self.assertFalse(f1["node01_reapply_authorized"])

        g2b = self.state["control_bridge"]["g2b"]
        self.assertFalse(g2b["accepted"])
        self.assertEqual(g2b["task_8"]["last_terminal_attempt"], "FAILED_ATTEMPT_3_NOT_ACCEPTED")
        self.assertEqual(g2b["task_8"]["root_cause"], "NOT_VERIFIED")
        self.assertEqual(g2b["tasks_9_10"], "NOT_STARTED")

    def test_production_remains_closed(self):
        self.assertEqual(
            self.state["authorization"]["production_promotion"],
            "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        )
        self.assertFalse(self.state["boundaries"]["production_promoted"])

    def test_neutral_package_boundary(self):
        toolchain = self.state["toolchain"]
        self.assertFalse(toolchain["functional_lineage_code_imported"])
        self.assertFalse(toolchain["g2b_functional_code_imported"])
        self.assertFalse(toolchain["f1_2c_functional_code_imported"])


if __name__ == "__main__":
    unittest.main()
