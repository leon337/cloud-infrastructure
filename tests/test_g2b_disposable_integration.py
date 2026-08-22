from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "scripts/test_control_bridge_g2b_vm.sh"
WORKFLOW_PATH = ROOT / ".github/workflows/control-bridge-g2b-ci.yml"

MARKERS = [
    "G2B_DISPOSABLE_IDENTITY_PASS",
    "G2B_TRANSPORT_DIRECT_WRITE_REFUSED",
    "G2B_GRANT_24H_PASS",
    "G2B_WRITE_PASS",
    "G2B_REPLAY_PASS",
    "G2B_REQUEST_ID_CONFLICT_PASS",
    "G2B_CONCURRENCY_PASS",
    "G2B_AUDIT_PASS",
    "G2B_ROLLBACK_PASS",
    "G2B_FINAL_STATE_PASS",
    "G2B_REVOKE_PASS",
    "G2B_POST_REVOKE_REFUSAL_PASS",
    "G2B_BOUNDED_CLEANUP_PASS",
]


class G2BDisposableIntegrationTests(unittest.TestCase):
    def test_harness_exists_and_emits_required_markers_in_order(self) -> None:
        self.assertTrue(HARNESS_PATH.is_file(), "missing G2-B disposable harness")
        text = HARNESS_PATH.read_text(encoding="utf-8")
        positions = [text.index(marker) for marker in MARKERS]
        self.assertEqual(positions, sorted(positions))
        for marker in MARKERS:
            self.assertEqual(text.count(marker), 1, marker)

    def test_harness_is_disposable_only_and_refuses_real_node(self) -> None:
        text = HARNESS_PATH.read_text(encoding="utf-8")
        self.assertIn("DISPOSABLE_UBUNTU_24_04_ONLY", text)
        self.assertIn("node-01", text)
        self.assertIn("vmi3506102", text)
        self.assertIn("--privileged", text)
        self.assertIn("--cgroupns private", text)
        self.assertIn("/workspace/cloud-infrastructure", text)
        self.assertIn("systemctl is-system-running", text)
        self.assertIn("trap cleanup EXIT", text)
        self.assertNotIn("/etc/shadow", text)
        self.assertNotIn("env |", text)

    def test_harness_proves_exact_g2b_lifecycle_without_request_echo(self) -> None:
        text = HARNESS_PATH.read_text(encoding="utf-8")
        for expected in (
            "apply-control-bridge-g2b.yml",
            "issue-control-bridge-g2b-grant.yml",
            "rollback-control-bridge-g2b.yml",
            "request_id_conflict",
            "active_mutation_exists",
            "grant_revoked",
            "ROLLED_BACK",
            "REVOKED",
            "audit.jsonl",
            "mcf-workspace",
            "G2B-PILOT.txt",
        ):
            self.assertIn(expected, text)
        self.assertNotIn("cat /etc/mcf-control-bridge/g2b-grant.json", text)
        self.assertNotIn("set -x", text)
        self.assertIn('if ! docker exec "$CONTAINER" id -u ubuntu', text)

    def test_workflow_is_commit_bound_github_hosted_and_pinned(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file(), "missing G2-B CI workflow")
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-24.04", text)
        self.assertNotIn("runs-on: self-hosted", text)
        self.assertIn("G2B_TEST_PRIVILEGED_CONFIRM: DISPOSABLE_UBUNTU_24_04_ONLY", text)
        self.assertIn("G2B_CANDIDATE_SHA: ${{ github.sha }}", text)
        self.assertIn("python3 -m unittest tests.test_g2b_disposable_integration -v", text)
        self.assertIn("scripts/test_control_bridge_g2b_vm.sh", text)
        action_refs = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", text)
        self.assertTrue(action_refs)
        for ref in action_refs:
            self.assertRegex(ref, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
