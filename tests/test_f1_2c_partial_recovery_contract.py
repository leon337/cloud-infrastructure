import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / "automation/mission-001/operations/recover-network-services-partial"
KVM_RUNNER = ROOT / "scripts/run_f1_2c_kvm_lab.sh"
KVM_RECOVERY = ROOT / "scripts/test_node_network_services_partial_recovery_vm.sh"
CI_WORKFLOW = ROOT / ".github/workflows/f1-2c-rollout-recovery-validation.yml"
KVM_WORKFLOW = ROOT / ".github/workflows/f1-2c-rollout-recovery-kvm.yml"


class F12CPartialRecoveryContractTests(unittest.TestCase):
    def test_recovery_entrypoint_is_fail_closed_and_exact(self):
        self.assertTrue(RECOVERY.is_file(), "partial recovery entrypoint must exist")
        text = RECOVERY.read_text(encoding="utf-8")
        for token in (
            "set -Eeuo pipefail",
            "80a1579bf6525029be8085fa1d1cbdec602ddfbd",
            "c9f909945b544d22dbabc619252456f7190f7ae9",
            "06d0f016809a2e8d9cf0be5a258766563cc686fe40b21ec3578a99c731421060",
            "dfe10b0e0046242695fe5ba03215f49aa938cf94b733bba3b1a2ba9cfad7e6d1",
            "b69f41cd1c66000da239f39c09a46681afd5098a311065adf76b3c7aae35b9a3",
            "c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b",
            "RECOVERY_PRECHECK=PASS",
            "RECOVERY_APPLY=PASS",
            "RECOVERY_CHECK=PASS",
            "RECOVERY_ROLLBACK=PASS",
            "RECOVERY_HUMAN_GATE_REQUIRED",
            "checkpoint",
            "cloud-platform-network-services",
        ):
            self.assertIn(token, text)
        self.assertNotIn("rm -rf /", text)
        self.assertNotIn("ReadWritePaths=/run/lock\n", text)

    def test_recovery_has_explicit_operations_and_no_implicit_live_mode(self):
        text = RECOVERY.read_text(encoding="utf-8")
        for op in ("precheck", "apply", "check", "rollback"):
            self.assertIn(op, text)
        self.assertIn("vmi3506102", text)
        self.assertIn("MCF_F1_2C_KVM_LAB_V1", text)
        self.assertIn("F1_2C_RECOVERY_DISPOSABLE_KVM_ONLY", text)
        self.assertIn("root:root", text)

    def test_kvm_runner_executes_partial_recovery_harness(self):
        self.assertTrue(KVM_RECOVERY.is_file(), "partial recovery KVM harness must exist")
        runner = KVM_RUNNER.read_text(encoding="utf-8")
        self.assertIn("scripts/test_node_network_services_partial_recovery_vm.sh", runner)
        harness = KVM_RECOVERY.read_text(encoding="utf-8")
        self.assertIn("NODE_NETWORK_SERVICES_PARTIAL_RECOVERY_VM_PASS", harness)
        self.assertIn("recover-network-services-partial", harness)
        self.assertIn("c9f909945b544d22dbabc619252456f7190f7ae9", harness)

    def test_partial_recovery_harness_removes_prior_lab_runtime_residue(self):
        harness = KVM_RECOVERY.read_text(encoding="utf-8")
        cleanup = "sudo rmdir /run/cloud-platform-network-services"
        self.assertIn(cleanup, harness)
        self.assertLess(harness.index(cleanup), harness.index("fail private_runtime_preexists"))

    def test_recovery_ci_is_hosted_and_exact_head(self):
        self.assertTrue(CI_WORKFLOW.is_file(), "recovery validation workflow must exist")
        text = CI_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("github.event.pull_request.head.sha", text)
        self.assertIn("fix/f1-2c-node01-rollout-recovery-20260828", text)
        self.assertIn("tests.test_f1_2c_partial_recovery_contract", text)
        self.assertNotIn("runs-on: [self-hosted", text)
        self.assertNotIn("cache: pip", text)
        self.assertIn("requirements-dev.lock", text)

    def test_recovery_kvm_ci_is_hosted_exact_head_and_collects_evidence(self):
        self.assertTrue(KVM_WORKFLOW.is_file(), "hosted KVM recovery workflow must exist")
        text = KVM_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertIn("github.event.pull_request.head.sha", text)
        self.assertIn("scripts/run_f1_2c_kvm_lab.sh", text)
        self.assertIn("/dev/kvm", text)
        self.assertIn("actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02", text)
        self.assertNotIn("self-hosted", text)
        self.assertNotIn("node-01", text)
        self.assertIn("$RUNNER_TEMP/kvm-evidence", text)
        self.assertNotIn("$GITHUB_WORKSPACE/kvm-evidence", text)


if __name__ == "__main__":
    unittest.main()
