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

    def test_live_reconciliation_records_verified_network_and_unintegrated_g2b(self):
        f1 = self.state["platform"]["f1_2c"]
        self.assertEqual(f1["status"], "COMPLETE_LIVE_VERIFIED")
        self.assertTrue(f1["accepted"])
        self.assertEqual(f1["applied_candidate_sha"], "baaf83908e8e83264baafc032434a4df1952450b")
        self.assertEqual(f1["live_postverify"]["status"], "PASS")
        self.assertTrue(f1["live_postverify"]["service_active"])
        self.assertFalse(f1["node01_reapply_authorized"])

        network = self.state["network_convergence_p2"]
        self.assertEqual(network["status"], "COMPLETE_LIVE_VERIFIED")
        self.assertTrue(network["accepted"])
        self.assertEqual(network["applied_candidate_sha"], "682c3e55d835ebea4bcc2edd297a8b819b2df434")
        self.assertEqual(network["live_postverify"]["administrative_state"], "configured")
        self.assertEqual(network["live_postverify"]["gateway_host_route"], "169.58.128.1/32_SCOPE_LINK")
        self.assertFalse(network["node01_reapply_authorized"])

        g2b = self.state["control_bridge"]["g2b"]
        self.assertFalse(g2b["accepted"])
        self.assertEqual(g2b["task_8"]["last_terminal_attempt"], "TECHNICAL_PASS_DRAFT_UNINTEGRATED")
        self.assertTrue(g2b["task_8"]["acceptance_markers_proven"])
        self.assertEqual(g2b["task_8"]["diagnostic_head"], "f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8")
        self.assertEqual(g2b["task_8"]["diagnostic_status"], "TECHNICAL_PASS_DRAFT_UNINTEGRATED")
        self.assertEqual(g2b["tasks_9_10"], "NOT_STARTED")
        self.assertEqual(g2b["merge_status"], "TASK_8_TECHNICAL_PASS_DRAFT_UNINTEGRATED")

    def test_production_remains_closed(self):
        self.assertEqual(
            self.state["authorization"]["production_promotion"],
            "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        )
        self.assertFalse(self.state["boundaries"]["production_promoted"])

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
        self.assertEqual(
            self.state["project"]["next_exact_step"],
            "HUMAN_GATE_EXTERNAL_OWNER_CHANNEL_WINDOW",
        )

    def test_reboot_gate_requires_fresh_checkpoint_and_external_coordination(self):
        checkpoint = self.state["pre_reboot_checkpoint"]
        self.assertEqual(checkpoint["status"], "FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH")
        self.assertFalse(checkpoint["accepted_for_current_reboot"])
        self.assertFalse(checkpoint["refresh_required_before_reboot"])
        self.assertTrue(checkpoint["live_snapshot_fresh"])
        self.assertEqual(checkpoint["blocking_reason"], "EXTERNAL_OWNER_CHANNEL_WINDOW_NOT_VERIFIED")
        self.assertEqual(checkpoint["latest_onhost_config_backup"], "cloud-infrastructure-config-20260906T030657Z.tar.gz")
        self.assertEqual(checkpoint["latest_onhost_config_backup_integrity"], "PASS")
        self.assertEqual(checkpoint["offhost_recovery"]["latest_complete_dir"], "20260906T185928Z")
        self.assertEqual(checkpoint["offhost_recovery"]["sha256_status"], "PASS_6_OF_6")
        self.assertTrue(checkpoint["offhost_recovery"]["current_day_recovery_present"])
        self.assertEqual(checkpoint["offhost_recovery"]["freshness"], "FRESH_FOR_2026_09_06_REBOOT_GATE")
        self.assertEqual(checkpoint["offhost_recovery"]["recovery_format"], "RECOVERY-P2-v1")
        self.assertEqual(checkpoint["offhost_recovery"]["root_backup"], "cloud-infrastructure-config-20260906T030657Z.tar.gz")
        self.assertEqual(checkpoint["offhost_recovery"]["root_backup_sha256"], "ec5d83ddcf8ef72d92d2d52590e6d8a4329fdce6893088ee16520ebb0c5816f4")
        self.assertEqual(checkpoint["offhost_recovery"]["restore_smoke"], "PASS")
        self.assertEqual(checkpoint["offhost_recovery"]["secret_scan"], "PASS")
        self.assertEqual(checkpoint["offhost_recovery"]["archive_path_safety"], "PASS")
        self.assertEqual(checkpoint["offhost_recovery"]["archive_link_safety"], "PASS")
        self.assertEqual(checkpoint["offhost_recovery"]["root_cause_missing_current_day"], "NOT_VERIFIED")
        self.assertEqual(checkpoint["current_kernel"], "6.8.0-138-generic")
        self.assertEqual(checkpoint["target_kernel"], "6.8.0-139-generic")
        self.assertTrue(checkpoint["reboot_required"])

        self.assertEqual(
            self.state["authorization"]["pre_reboot_checkpoint"],
            "FRESH_READ_ONLY_COMPLETED_OFFHOST_RECOVERY_FRESH",
        )

        sentinel = self.state["sentinelx_direct_connectivity"]
        self.assertEqual(sentinel["status"], "INTERMITTENT_NOT_CLOSED")
        self.assertEqual(sentinel["root_cause"], "NOT_VERIFIED")

        coordination = self.state["reboot_coordination"]
        self.assertEqual(coordination["status"], "BLOCKED_EXTERNAL_OWNER_CHANNEL_WINDOW_AND_HUMAN_GATE")
        self.assertFalse(coordination["checkpoint_refresh_required"])
        self.assertFalse(coordination["offhost_recovery_freshness_required"])
        self.assertTrue(coordination["external_service_coordination_required"])
        self.assertTrue(coordination["coordination_attempted"])
        self.assertEqual(coordination["coordination_gate_result"], "BLOCKED_NO_VERIFIED_OWNER_CHANNEL_WINDOW")
        self.assertEqual(coordination["external_owner_status"], "NOT_VERIFIED")
        self.assertEqual(coordination["external_contact_channel_status"], "NOT_VERIFIED")
        self.assertEqual(coordination["maintenance_window_status"], "NOT_SCHEDULED")
        self.assertFalse(coordination["contact_attempt_sent"])
        self.assertEqual(coordination["contact_attempt_reason"], "NO_VERIFIED_RECIPIENT")
        self.assertTrue(coordination["host_reboot_would_interrupt_external_services"])
        self.assertEqual(coordination["deepseek_harness"], "EXTERNALLY_MANAGED_OBSERVE_ONLY")
        self.assertEqual(coordination["ninerouter"], "EXTERNALLY_MANAGED_OBSERVE_ONLY")
        self.assertEqual(self.state["authorization"]["updates"], "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED")
        self.assertEqual(self.state["authorization"]["reboot"], "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED")

    def test_runner_isolation_state_records_active_verified_global_hook(self):
        runner = self.state["runner_isolation"]
        self.assertEqual(runner["status"], "CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED")
        self.assertEqual(runner["live_cleanup"], "PASS")
        self.assertEqual(runner["cross_job_proof"], "PASS")
        self.assertEqual(runner["workflow_policy"], "PASS")
        self.assertEqual(runner["global_hook"], "ACTIVE_VERIFIED")
        self.assertFalse(runner["global_hook_restart_required"])
        self.assertTrue(runner["global_hook_activation_authorized"])
        self.assertEqual(runner["global_hook_last_probe_run"], 33998487949)
        self.assertEqual(runner["global_hook_last_probe_result"], "PASS_ACTIVE_VERIFIED")
        self.assertEqual(runner["cross_job_proof_run"], 33998487949)
        self.assertEqual(runner["next_exact_step"], "NONE")


if __name__ == "__main__":
    unittest.main()
