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
        self.assertEqual(hygiene["status"], "PR_BRANCH_HYGIENE_CLASSIFIED")
        self.assertEqual(hygiene["pr_semantics"], "HISTORICAL_SANITIZATION_LINEAGE")
        self.assertEqual(hygiene["classification_pr"], 53)
        self.assertEqual(hygiene["classification_merge_sha"], "78a4106aaa7a4cbbe3b6c78525bf7991d05a83a7")
        self.assertEqual(hygiene["revalidation"]["status"], "PASS_AGAINST_CANONICAL_TOOLCHAIN")
        self.assertEqual(hygiene["pr"], 19)
        self.assertEqual(hygiene["revalidation"]["head"], "f34aec6c641fb577d620446df4a743df3ff3fa5d")
        self.assertFalse(hygiene["legacy_pr_classification_pending"])
        self.assertEqual(hygiene["remote_branch_count"], 68)
        self.assertEqual(hygiene["branch_deletions"], 0)
        self.assertEqual(hygiene["active_prs_retained"], [21])
        self.assertEqual(hygiene["legacy_prs_closed"], [1, 2, 3, 7, 8, 23, 41, 45])
        self.assertEqual(hygiene["deletion_gate"], "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED")

        receipt_path = Path(hygiene["classification_receipt"])
        self.assertTrue(receipt_path.is_file())
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["protocol"], "MCF-PR-BRANCH-HYGIENE-v1")
        self.assertEqual(receipt["observed_main"], "ec9bc8cbac143197ab8d8102da23d3cb54fcd43a")
        self.assertEqual(receipt["remote_branch_count"], 68)
        self.assertEqual(receipt["branch_deletions"], 0)
        self.assertEqual(receipt["active_open_prs"], [21])
        self.assertEqual(receipt["closed_legacy_prs"], [1, 2, 3, 7, 8, 23, 41, 45])
        self.assertEqual([row["number"] for row in receipt["pr_actions"]], [1, 2, 3, 7, 8, 23, 41, 45])
        self.assertTrue(all(row["action"] == "CLOSED_PRESERVE_EVIDENCE" for row in receipt["pr_actions"]))
        self.assertTrue(all(row["branch_deleted"] is False for row in receipt["pr_actions"]))
        self.assertEqual(receipt["retained_active_pr"]["number"], 21)
        self.assertEqual(receipt["retained_active_pr"]["state"], "OPEN_DRAFT")
        self.assertEqual(receipt["retained_active_pr"]["head"], "f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8")
        self.assertEqual(len(receipt["branches"]), 68)
        allowed = {
            "ACTIVE_RETAIN",
            "INTEGRATED_IN_MAIN",
            "COVERED_BY_OPERATIONAL_LINEAGE",
            "HISTORICAL_EVIDENCE_RETAIN",
            "REVIEW_REQUIRED",
        }
        self.assertEqual({row["classification"] for row in receipt["branches"]} - allowed, set())
        self.assertTrue(all(row["deletion_authorized"] is False for row in receipt["branches"]))
        by_name = {row["name"]: row for row in receipt["branches"]}
        self.assertEqual(by_name["main"]["classification"], "ACTIVE_RETAIN")
        self.assertEqual(by_name["team/g2b-task8-20260822"]["classification"], "ACTIVE_RETAIN")
        self.assertEqual(by_name["codex/control-bridge-g2b"]["classification"], "ACTIVE_RETAIN")
        self.assertEqual(by_name["fix/f1-2c-systemd-runtime-lock"]["classification"], "ACTIVE_RETAIN")

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
            "HUMAN_GATE_REPOSITORY_HISTORY_SECRET_POLICY_REMEDIATION",
        )

    def test_reboot_gate_requires_fresh_checkpoint_and_external_coordination(self):
        checkpoint = self.state["pre_reboot_checkpoint"]
        self.assertEqual(checkpoint["status"], "FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH")
        self.assertFalse(checkpoint["accepted_for_current_reboot"])
        self.assertFalse(checkpoint["refresh_required_before_reboot"])
        self.assertTrue(checkpoint["live_snapshot_fresh"])
        self.assertEqual(checkpoint["blocking_reason"], "HUMAN_UPDATE_REBOOT_AUTHORIZATION_PENDING")
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
        self.assertEqual(coordination["status"], "MAINTENANCE_COMPLETED_POST_REBOOT_LIVE_VERIFIED")
        self.assertFalse(coordination["checkpoint_refresh_required"])
        self.assertFalse(coordination["offhost_recovery_freshness_required"])
        self.assertFalse(coordination["external_service_coordination_required"])
        self.assertTrue(coordination["coordination_attempted"])
        self.assertEqual(coordination["coordination_gate_result"], "PASS_ACTIVE_CHAT_CONSUMERS_CHECKPOINTED")
        self.assertEqual(coordination["external_owner_status"], "NOT_RESOLVED_NOT_GATE_BLOCKING_AFTER_LEANDRO_CLARIFICATION")
        self.assertEqual(coordination["external_contact_channel_status"], "GUI_CHAT_CHANNEL_VERIFIED")
        self.assertEqual(coordination["maintenance_window_status"], "COMPLETED")
        self.assertTrue(coordination["contact_attempt_sent"])
        self.assertEqual(coordination["contact_attempt_reason"], "ACTIVE_CHAT_CONSUMERS_COORDINATED_VIA_GUI")
        self.assertTrue(coordination["host_reboot_would_interrupt_external_services"])
        self.assertEqual(coordination["deepseek_harness"], "EXTERNALLY_MANAGED_OBSERVE_ONLY")
        self.assertEqual(coordination["ninerouter"], "EXTERNALLY_MANAGED_OBSERVE_ONLY")
        self.assertTrue(coordination["active_consumers_ready"])
        self.assertFalse(coordination["post_reboot_validation_required"])
        self.assertFalse(coordination["reboot_authorized"])
        self.assertFalse(coordination["updates_authorized"])
        execution = coordination["maintenance_execution"]
        self.assertEqual(execution["status"], "PASS_POST_REBOOT_LIVE_VERIFIED")
        self.assertEqual(execution["authorization_choice"], "B_UPDATES_AND_REBOOT")
        self.assertEqual(execution["current_kernel"], "6.8.0-139-generic")
        self.assertEqual(execution["post_reboot_checker_candidate"], "9070c24e637e6d571bc53c66d0c54d3825340ffb")
        self.assertEqual(execution["post_reboot_checker_result"], "NETWORK_CONVERGENCE_CHECK_PASS_RECOVERED")
        self.assertEqual(execution["independent_postverify"], "PASS")
        self.assertEqual(coordination["coordination_channel"], "CHATGPT_GUI")
        self.assertEqual(coordination["active_consumers"]["hy4_teste"]["status"], "READY_FOR_NODE01_MAINTENANCE")
        self.assertEqual(coordination["active_consumers"]["dsh_gpt"]["status"], "PAUSED_SAFE_CHECKPOINT_NO_NEW_DSH_9ROUTER_EXECUTIONS")
        self.assertEqual(self.state["authorization"]["external_service_coordination_gate"], "AUTHORIZED_EXECUTED_PASS_ACTIVE_CONSUMERS_CHECKPOINTED")
        self.assertEqual(self.state["authorization"]["updates"], "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED")
        self.assertEqual(self.state["authorization"]["reboot"], "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED")
        integration = self.state["post_reboot_integration"]
        self.assertEqual(integration["status"], "PR51_OPERATIONAL_AND_PR50_CANONICAL_INTEGRATED")
        self.assertEqual(integration["operational_fix"]["pr"], 51)
        self.assertEqual(integration["operational_fix"]["branch"], "fix/f1-2c-systemd-runtime-lock")
        self.assertEqual(integration["operational_fix"]["candidate_head"], "9070c24e637e6d571bc53c66d0c54d3825340ffb")
        self.assertEqual(integration["operational_fix"]["merge_sha"], "d5508e1ed417b85bd4863ae5771605079d15aa99")
        self.assertEqual(integration["operational_fix"]["tree_sha"], "b0a51bef522bbb6c872baf5f4ef15116d6f584b0")
        self.assertEqual(integration["operational_fix"]["postmerge_validation"], "PASS_166_OF_166")
        self.assertEqual(integration["canonical_reconciliation"]["pr"], 50)
        self.assertEqual(integration["canonical_reconciliation"]["merge_status"], "MERGED")
        self.assertEqual(integration["canonical_reconciliation"]["merge_sha"], "c7315e43e86beedae5a921e39b1ab7103f4da276")
        self.assertEqual(integration["canonical_reconciliation"]["tree_sha"], "9dd8c3031c9d0ace580685ba08e6a00c88f14f2d")
        self.assertEqual(integration["canonical_reconciliation"]["postmerge_validation"], "PASS_35_OF_35")
        self.assertEqual(integration["canonical_reconciliation"]["postmerge_ci_run"], 34065344230)
        self.assertNotIn("closeout", integration)
        self.assertEqual(self.state["authorization"]["pr50_canonical_merge"], "COMPLETED_ONE_SHOT_AUTHORIZATION_CONSUMED")
        self.assertNotIn("post_reboot_closeout_merge", self.state["authorization"])

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


    def test_final_transversal_audit_closeout_is_current_and_non_recursive(self):
        state = self.state
        self.assertEqual(state["source_snapshot"]["main"]["sha"], "78a4106aaa7a4cbbe3b6c78525bf7991d05a83a7")
        self.assertEqual(state["source_snapshot"]["main"]["latest_integrated_pr"], 53)
        self.assertEqual(state["toolchain"]["hosted_canonical_latest_run"], 34068890016)
        audit = state["final_transversal_audit"]
        self.assertEqual(audit["status"], "EXECUTED_REMEDIATION_PREPARED")
        self.assertEqual(audit["live_remote_branch_count"], 69)
        self.assertEqual(audit["historical_hygiene_snapshot_branch_count"], 68)
        self.assertEqual(audit["branch_deletions"], 0)
        self.assertEqual(audit["g2b_pr21"], "DRAFT_UNINTEGRATED_FRESH_HOSTED_CI_BLOCKED_BY_HISTORY_SECRET_POLICY")
        self.assertEqual(audit["sentinelx_direct"], "INTERMITTENT_NOT_CLOSED_SERVICE_ACTIVE")
        self.assertEqual(audit["capsule"], "RECONSTRUCTED_FROM_CURRENT_STATE_PENDING_MERGE")
        self.assertEqual(audit["capability_registry"], "SOURCE_OF_TRUTH_MCF_MAIN_0825BBC")
        self.assertEqual(state["project"]["next_exact_step"], "HUMAN_GATE_REPOSITORY_HISTORY_SECRET_POLICY_REMEDIATION")

    def test_final_transversal_audit_receipt_is_fail_closed(self):
        audit = self.state["final_transversal_audit"]
        receipt_path = Path(audit["evidence_file"])
        self.assertTrue(receipt_path.is_file())
        receipt = yaml.safe_load(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["basis"]["cloud_main_sha"], "78a4106aaa7a4cbbe3b6c78525bf7991d05a83a7")
        self.assertEqual(receipt["basis"]["hygiene_pr"], 53)
        self.assertEqual(receipt["basis"]["hygiene_postmerge_ci_run"], 34068890016)
        self.assertEqual(receipt["repository_hygiene"]["historical_snapshot_branch_count"], 68)
        self.assertEqual(receipt["repository_hygiene"]["live_remote_branch_count"], 69)
        self.assertEqual(receipt["repository_hygiene"]["branch_deletions"], 0)
        self.assertEqual(len(receipt["g2b_pr21"]["fresh_hosted_reruns"]), 3)
        self.assertEqual(receipt["cross_repo"]["mcf_main_sha"], "0825bbcfa1c9e8a07c08d9ff7d9ecbcc51186b22")
        self.assertFalse(receipt["boundaries"]["destructive_history_remediation_authorized"])
        self.assertFalse(receipt["boundaries"]["branch_deletion_authorized"])

    def test_cross_repo_capsule_matches_current_cloud_contract(self):
        capsule_path = Path(".mcf/project-capsule.yaml")
        self.assertTrue(capsule_path.is_file())
        capsule = yaml.safe_load(capsule_path.read_text(encoding="utf-8"))
        self.assertEqual(capsule["schema_version"], 1)
        self.assertEqual(capsule["project_id"], "cloud-infrastructure")
        self.assertEqual(capsule["sources"]["current_state"], "state/current.yaml")
        self.assertEqual(capsule["snapshot"]["current_workstream"], "final-transversal-audit-closeout")
        self.assertIn("PR #21", " ".join(capsule["snapshot"]["blockers"]))
        self.assertIn("repository-history", capsule["snapshot"]["next_action"])

    def test_readme_does_not_regress_to_hygiene_as_next_work(self):
        readme = Path("README.md").read_text(encoding="utf-8")
        self.assertNotIn("O próximo trabalho operacional é a higiene canônica de PRs/branches", readme)
        self.assertIn("FINAL_TRANSVERSAL_AUDIT_EXECUTED", readme)

if __name__ == "__main__":
    unittest.main()
