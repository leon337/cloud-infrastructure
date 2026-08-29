import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OP = ROOT / "automation/mission-001/operations/recover-network-convergence"
KVM = ROOT / "scripts/test_network_convergence_recovery_vm.sh"
OVERLAY = ROOT / "config/vps/60-cloud-infrastructure-network-convergence.yaml"
RUNNER = ROOT / "scripts/run_network_convergence_kvm_lab.sh"
WORKFLOW = ROOT / ".github/workflows/network-convergence-p2-kvm.yml"
STATIC_WORKFLOW = ROOT / ".github/workflows/network-convergence-p2-validation.yml"


class NetworkConvergenceRecoveryContractTests(unittest.TestCase):
    def test_operation_is_explicit_and_fail_closed(self):
        self.assertTrue(OP.is_file(), "network convergence recovery must exist")
        text = OP.read_text(encoding="utf-8")
        for token in (
            "set -Eeuo pipefail",
            "precheck",
            "apply",
            "check",
            "rollback",
            "NETWORK_CONVERGENCE_PRECHECK=PASS",
            "NETWORK_CONVERGENCE_APPLY=PASS",
            "NETWORK_CONVERGENCE_CHECK=PASS",
            "NETWORK_CONVERGENCE_ROLLBACK=PASS",
            "NETWORK_CONVERGENCE_HUMAN_GATE_REQUIRED",
        ):
            self.assertIn(token, text)

    def test_operation_preserves_provider_routing_contract(self):
        text = OP.read_text(encoding="utf-8")
        overlay = OVERLAY.read_text(encoding="utf-8")
        for token in (
            "/etc/netplan/50-cloud-init.yaml",
            "/run/systemd/network/10-netplan-eth0.network",
            "/etc/cron.d/staticroute",
            "9ad2689b534bdb090060a51b3a1c0785384c65c2bd1bf3e42b9bbfdc76685790",
            "0f25043db9ffc67594a6d723a69550105fa8fb8d5ae2040905b1aff964042858",
            "4a0ab05ddb6ef718acc644f656d865b1129f0ec4996e1bf2725156042a913163",
            "169.58.171.192/17",
            "169.58.128.1",
        ):
            self.assertIn(token, text)
        self.assertIn("scope: link", overlay)
        self.assertIn("to: 169.58.128.1/32", overlay)
        self.assertNotIn("169.58.128.0/17 scope link", text)
        self.assertNotIn("netplan apply", text)

    def test_apply_uses_generate_and_single_host_route(self):
        text = OP.read_text(encoding="utf-8")
        self.assertIn("netplan generate", text)
        self.assertIn('ip route replace "$GATEWAY/32" dev "$INTERFACE" scope link', text)
        self.assertIn("systemd-networkd-wait-online", text)

    def test_kvm_harness_covers_break_recover_and_rollback(self):
        self.assertTrue(KVM.is_file(), "network convergence KVM harness must exist")
        text = KVM.read_text(encoding="utf-8")
        for token in (
            "NETWORK_CONVERGENCE_VM_PASS",
            "recover-network-convergence",
            "169.58.128.1/32",
            "WAIT_BROKEN_RC=124",
            "WAIT_RECOVERED_RC=0",
            "WAIT_ROLLBACK_RC=124",
            "ADMIN_STATE=configuring",
            "ADMIN_STATE=configured",
            "pre_netplan_hash",
            "pre_generated_hash",
            "pre_staticroute_hash",
            "checkpoint_hashes_match",
        ):
            self.assertIn(token, text)

    def test_hosted_kvm_gate_is_exact_head(self):
        self.assertTrue(RUNNER.is_file(), "dedicated KVM runner must exist")
        self.assertTrue(WORKFLOW.is_file(), "hosted KVM workflow must exist")
        runner = RUNNER.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("test_network_convergence_recovery_vm.sh", runner)
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertIn("github.event.pull_request.head.sha", workflow)
        self.assertIn("/dev/kvm", workflow)
        self.assertIn("run_network_convergence_kvm_lab.sh", workflow)
        self.assertIn("fix/f1-2c-systemd-runtime-lock", workflow)
        self.assertIn("fix/network-convergence-p2-generated-metadata-20260829", workflow)
        self.assertIn("fix/network-convergence-p2-postboot-route-contract-20260829", workflow)
        self.assertNotIn("self-hosted", workflow)
        self.assertNotIn("node-01", workflow)

    def test_hosted_static_gate_requires_shellcheck_and_exact_head(self):
        self.assertTrue(STATIC_WORKFLOW.is_file(), "hosted static workflow must exist")
        text = STATIC_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("github.event.pull_request.head.sha", text)
        self.assertIn("fix/network-convergence-p2-generated-metadata-20260829", text)
        self.assertIn("fix/network-convergence-p2-postboot-route-contract-20260829", text)
        for token in (
            "tests.test_network_convergence_recovery_contract",
            "scripts/check_markdown_links.py",
            "scripts/validate_yaml.py",
            "scripts/validate_manifests.py",
            "scripts/validate_state.py",
            "scripts/generate_project_status.py --check-readme",
            "defaultTestLoader.discover",
            "shellcheck",
        ):
            self.assertIn(token, text)
        self.assertNotIn("scripts/test.sh", text)
        self.assertNotIn("self-hosted", text)
        self.assertNotIn("node-01", text)

    def test_operation_has_no_duplicate_function_definitions(self):
        text = OP.read_text(encoding="utf-8")
        for name in ("require_commands", "recovered_state_valid"):
            self.assertEqual(text.count(f"{name}() {{"), 1, name)
        self.assertIn("checkpoint_hashes_valid", text)
        self.assertIn("NETWORK_CONVERGENCE_TEST_CONFIRM", text)

class NetworkConvergenceSelfReviewTests(unittest.TestCase):
    def test_route_probe_and_checkpoint_are_unambiguous(self):
        text = OP.read_text(encoding="utf-8")
        self.assertIn("show default |", text)
        self.assertNotIn("show default dev", text)
        for token in (
            "netplan_sha256=$NETPLAN_SHA256",
            "generated_sha256=$GENERATED_SHA256",
            "staticroute_sha256=$STATICROUTE_SHA256",
        ):
            self.assertIn(token, text)

    def test_generated_network_metadata_matches_netplan_runtime_contract(self):
        text = OP.read_text(encoding="utf-8")
        harness = KVM.read_text(encoding="utf-8")
        self.assertIn("generated_file_exact", text)
        self.assertIn("root:systemd-network:640:1", text)
        self.assertIn("0f25043db9ffc67594a6d723a69550105fa8fb8d5ae2040905b1aff964042858", text)
        self.assertNotIn('file_exact "$GENERATED" 644', text)
        self.assertIn("generated_metadata_match=PASS", harness)

    def test_postboot_provider_subnet_route_is_safe_but_direct_connected_route_is_not(self):
        text = OP.read_text(encoding="utf-8")
        harness = KVM.read_text(encoding="utf-8")
        for token in (
            "subnet_route_absent",
            "direct_connected_route_absent",
            "provider_subnet_route_safe",
            'scope link',
            '-v gateway="$GATEWAY"',
            '$2 == "via"',
        ):
            self.assertIn(token, text)
        self.assertIn('ip -o -4 route show "$SUBNET" table main dev "$INTERFACE"', text)
        self.assertNotIn('ip -o -4 route show "$SUBNET" table main | awk', text)
        self.assertIn("PROVIDER_POSTBOOT_ROUTE=PASS", harness)
        self.assertIn("POSTBOOT_P2_CHECK=PASS", harness)
        self.assertIn('ip route replace 169.58.128.0/17 via 169.58.128.1 dev eth0', harness)

    def test_successor_check_accepts_exact_live_applied_checkpoint_without_relaxing_mutators(self):
        text = OP.read_text(encoding="utf-8")
        harness = KVM.read_text(encoding="utf-8")
        applied = "682c3e55d835ebea4bcc2edd297a8b819b2df434"
        for token in (
            f"LIVE_APPLIED_CANDIDATE_SHA={applied}",
            "checkpoint_candidate_valid_exact",
            "checkpoint_candidate_valid_for_check",
            "recovered_state_valid_for_check",
        ):
            self.assertIn(token, text)
        self.assertIn("recovered_state_valid_for_check || refuse recovered_state_invalid", text)
        self.assertIn("SUCCESSOR_CHECK=PASS", harness)
        self.assertIn(applied, harness)

    def test_new_checkpoint_lineage_branch_runs_hosted_gates(self):
        branch = "fix/network-convergence-p2-check-lineage-20260829"
        self.assertIn(branch, WORKFLOW.read_text(encoding="utf-8"))
        self.assertIn(branch, STATIC_WORKFLOW.read_text(encoding="utf-8"))

    def test_live_rollback_restores_persistence_without_forcing_runtime_reconfigure(self):
        text = OP.read_text(encoding="utf-8")
        self.assertIn("runtime_reconfigure=NOT_FORCED", text)
        self.assertNotIn("rollback_admin_state_unexpected", text)
        self.assertNotIn("rollback_wait_online_unexpected", text)
        harness = KVM.read_text(encoding="utf-8")
        self.assertIn("ROLLBACK_RUNTIME_REEVALUATED", harness)


if __name__ == "__main__":
    unittest.main()
