from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/test_control_bridge_g2a_protected_vm.sh"
WORKFLOW = ROOT / ".github/workflows/control-bridge-g2a-protected-ci.yml"

MARKERS = [
    "G2A_PROTECTED_G2B_BASELINE_PASS",
    "G2A_PROTECTED_APPLY_PASS",
    "G2A_PROTECTED_IDEMPOTENCE_PASS",
    "G2A_PROTECTED_DIRECT_READ_REFUSED",
    "G2A_PROTECTED_ABSENT_PASS",
    "G2A_PROTECTED_CROSS_READ_PASS",
    "G2A_PROTECTED_G2B_ROLLBACK_PASS",
    "G2A_PROTECTED_FINAL_ABSENT_PASS",
    "G2A_PROTECTED_CLEANUP_PASS",
]


class G2AProtectedDisposableIntegrationTests(unittest.TestCase):
    def test_harness_exists_and_emits_markers_once_in_order(self) -> None:
        self.assertTrue(HARNESS.is_file(), "missing protected-reader disposable harness")
        text = HARNESS.read_text(encoding="utf-8")
        positions = [text.index(marker) for marker in MARKERS]
        self.assertEqual(positions, sorted(positions))
        for marker in MARKERS:
            self.assertEqual(text.count(marker), 1, marker)

    def test_harness_is_disposable_only_commit_bound_and_networkless(self) -> None:
        self.assertTrue(HARNESS.is_file(), "missing protected-reader disposable harness")
        text = HARNESS.read_text(encoding="utf-8")
        self.assertIn("G2A_PROTECTED_TEST_PRIVILEGED_CONFIRM", text)
        self.assertIn("DISPOSABLE_UBUNTU_24_04_ONLY", text)
        self.assertIn("G2A_PROTECTED_CANDIDATE_SHA", text)
        self.assertRegex(text, r"G2A_PROTECTED_CANDIDATE_SHA.*\^\[0-9a-f\]\{40\}\$")
        self.assertIn("node-01", text)
        self.assertIn("vmi3506102", text)
        self.assertIn("--privileged", text)
        self.assertIn("--cgroupns private", text)
        self.assertIn("--network none", text)
        self.assertIn("trap cleanup EXIT", text)
        self.assertNotIn("TARGET_HOST", text)
        self.assertNotIn("set -x", text)

    def test_harness_uses_explicit_allowlist_and_exact_cross_lifecycle(self) -> None:
        self.assertTrue(HARNESS.is_file(), "missing protected-reader disposable harness")
        text = HARNESS.read_text(encoding="utf-8")
        for required in (
            "apply-control-bridge-g2b.yml",
            "apply-control-bridge-g2a-protected-read.yml",
            "issue-control-bridge-g2b-grant.yml",
            "rollback-control-bridge-g2a-protected-read.yml",
            "G2B-PILOT.txt",
            "workspace.read",
            "path_not_found",
            "ROLLED_BACK",
            "after.sha256",
            "ALLOWLIST",
        ):
            self.assertIn(required, text)
        self.assertNotIn("cp -a .", text)
        self.assertNotIn("rsync .", text)

    def test_workflow_is_github_hosted_pinned_and_commit_bound(self) -> None:
        self.assertTrue(WORKFLOW.is_file(), "missing protected-reader CI workflow")
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("permissions:\n  contents: read", text)
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertNotIn("self-hosted", text)
        self.assertIn(
            "G2A_PROTECTED_TEST_PRIVILEGED_CONFIRM: DISPOSABLE_UBUNTU_24_04_ONLY",
            text,
        )
        self.assertIn("G2A_PROTECTED_CANDIDATE_SHA: ${{ github.sha }}", text)
        self.assertIn("scripts/test_control_bridge_g2a_protected_vm.sh", text)
        refs = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", text)
        self.assertTrue(refs)
        for ref in refs:
            self.assertRegex(ref, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
