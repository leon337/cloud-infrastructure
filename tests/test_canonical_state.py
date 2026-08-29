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

    def test_document_authority_hierarchy(self):
        freshness = self.state["freshness"]
        self.assertEqual(freshness["canonical_executive_panel"], "README.md")
        self.assertEqual(freshness["mission_operational_checklist"], "ROADMAP-CHECKLIST.md")
        self.assertEqual(freshness["checklist_scope"], "IMPLEMENTACAO_DA_VPS_ONLY")

        roadmap = self.state["continuity"]["roadmap_checklist"]
        self.assertEqual(roadmap["status"], "ADOPTED")
        self.assertEqual(roadmap["file"], "ROADMAP-CHECKLIST.md")
        self.assertEqual(roadmap["authority"], "SUBORDINATE_TO_README_EXECUTIVE_PANEL")
        self.assertEqual(roadmap["scope"], "IMPLEMENTACAO_DA_VPS_ONLY")
        self.assertTrue(Path(roadmap["file"]).is_file())
        self.assertEqual(self.state["source_snapshot"]["main"]["executive_projection"], "README.md")

    def test_f1_2c_live_state_and_future_g2b_are_bounded(self):
        f1 = self.state["platform"]["f1_2c"]
        self.assertEqual(f1["status"], "COMPLETE_LIVE_VERIFIED")
        self.assertTrue(f1["accepted"])
        self.assertFalse(f1["node01_reapply_authorized"])
        self.assertTrue(f1["one_shot_authorization_consumed"])
        self.assertEqual(f1["applied_candidate_sha"], "baaf83908e8e83264baafc032434a4df1952450b")
        self.assertEqual(f1["live_postverify"]["recovery_state"], "RECOVERED")
        evidence = Path(f1["live_postverify"]["evidence_file"])
        self.assertTrue(evidence.is_file())
        evidence_text = evidence.read_text(encoding="utf-8")
        self.assertIn("VERIFIED_LIVE_RECOVERY", evidence_text)
        self.assertIn(f1["applied_candidate_sha"], evidence_text)

        g2b = self.state["control_bridge"]["g2b"]
        self.assertFalse(g2b["accepted"])
        self.assertEqual(g2b["task_8"]["last_terminal_attempt"], "FAILED_ATTEMPT_3_NOT_ACCEPTED")
        self.assertEqual(g2b["task_8"]["root_cause"], "NOT_VERIFIED")
        self.assertEqual(g2b["tasks_9_10"], "NOT_STARTED")

    def test_network_convergence_p2_live_state_and_reboot_boundary(self):
        p2 = self.state["network_convergence_p2"]
        self.assertEqual(p2["status"], "COMPLETE_LIVE_VERIFIED")
        self.assertTrue(p2["accepted"])
        self.assertEqual(p2["route_removal_agent"], "NOT_VERIFIED")
        self.assertEqual(p2["applied_candidate_sha"], "682c3e55d835ebea4bcc2edd297a8b819b2df434")
        self.assertEqual(p2["live_postverify"]["recovery_state"], "RECOVERED")
        self.assertEqual(p2["live_postverify"]["administrative_state"], "configured")
        self.assertFalse(p2["live_postverify"]["systemd_networkd_restarted"])
        self.assertFalse(p2["node01_reapply_authorized"])
        self.assertTrue(p2["one_shot_authorization_consumed"])
        evidence = Path(p2["live_postverify"]["evidence_file"])
        self.assertTrue(evidence.is_file())
        self.assertIn("VERIFIED_LIVE_NETWORK_CONVERGENCE_P2", evidence.read_text(encoding="utf-8"))
        self.assertEqual(self.state["project"]["next_exact_step"], "PRE_REBOOT_CHECKPOINT")
        self.assertEqual(self.state["authorization"]["reboot"], "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED")

    def test_production_remains_closed(self):
        self.assertEqual(
            self.state["authorization"]["production_promotion"],
            "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        )
        self.assertFalse(self.state["boundaries"]["production_promoted"])
        self.assertFalse(self.state["boundaries"]["node01_privileged_operations_currently_authorized"])

    def test_repository_hygiene_revalidation_is_recorded(self):
        hygiene = self.state["repository_hygiene"]
        self.assertEqual(hygiene["status"], "REPOSITORY_HYGIENE_REVALIDATED")
        self.assertEqual(hygiene["revalidation"]["status"], "PASS_AGAINST_CANONICAL_TOOLCHAIN")
        self.assertEqual(hygiene["pr"], 19)
        self.assertEqual(hygiene["revalidation"]["head"], "f34aec6c641fb577d620446df4a743df3ff3fa5d")

    def test_neutral_package_boundary(self):
        toolchain = self.state["toolchain"]
        self.assertFalse(toolchain["functional_lineage_code_imported"])
        self.assertFalse(toolchain["g2b_functional_code_imported"])
        self.assertFalse(toolchain["f1_2c_functional_code_imported"])

    def test_ssh_key_governance_preserves_confirmed_user_workflow(self):
        ssh = self.state["ssh_key_governance"]
        self.assertEqual(ssh["status"], "CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED")
        self.assertEqual(ssh["dsh_key"]["provenance"], "CONFIRMED_UBUNTU_HISTORY_AND_AUTH_LOG")
        self.assertEqual(ssh["dsh_key"]["current_dependency"], "CONFIRMED_BY_LEANDRO_USER_WORKFLOW")
        self.assertEqual(ssh["decision"], "KEEP_REQUIRED_FOR_CURRENT_USER_WORKFLOW")
        self.assertEqual(ssh["fallback_auth"], "PASS_INDEPENDENT_KEY")
        self.assertFalse(ssh["authorized_keys_changed"])
        self.assertEqual(ssh["future_hardening_gate"], "PRESERVE_INTERACTIVE_NOTEBOOK_ACCESS")
        self.assertEqual(self.state["project"]["next_exact_step"], "PRE_REBOOT_CHECKPOINT")

    def test_runner_isolation_state_is_verified_with_hook_restart_pending(self):
        runner = self.state["runner_isolation"]
        self.assertEqual(runner["status"], "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING")
        self.assertEqual(runner["live_cleanup"], "PASS")
        self.assertEqual(runner["cross_job_proof"], "PASS")
        self.assertEqual(runner["workflow_policy"], "PASS")
        self.assertEqual(runner["global_hook"], "CONFIGURED_NOT_ACTIVE_BLOCKED_PRIVILEGE")


if __name__ == "__main__":
    unittest.main()
