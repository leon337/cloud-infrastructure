from __future__ import annotations

import importlib.util
import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_checker_module():
    path = ROOT / "scripts/check_continuity_drift.py"
    spec = importlib.util.spec_from_file_location("check_continuity_drift", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load continuity drift checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContinuityDriftControlsTests(unittest.TestCase):
    def test_contract_is_active_and_integrated(self):
        contract = yaml.safe_load((ROOT / "state/continuity-drift-controls.yaml").read_text())
        self.assertEqual(contract["status"], "ACTIVE_REQUIRED")
        self.assertEqual(
            contract["principle"],
            "NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT",
        )
        self.assertEqual(contract["executable_check"], "scripts/check_continuity_drift.py")
        self.assertEqual(contract["integrated_test_entrypoint"], "scripts/test.sh")
        required = {
            "mission_identity",
            "branch_and_pr_alignment",
            "roadmap_lifecycle",
            "next_exact_step",
            "entrypoint_next_step_alignment",
            "g2b_task_state_preservation",
            "human_gates_fail_closed",
            "parallel_ownership_isolation",
            "institutional_memory_presence",
            "current_state_alignment",
            "pass_requires_evidence",
            "cold_start_evidence_required_for_r7_complete",
        }
        self.assertTrue(required.issubset(contract["checks"]))

    def test_institutional_memory_contract_and_first_memo_exist(self):
        memory = yaml.safe_load((ROOT / "state/institutional-memory.yaml").read_text())
        self.assertEqual(memory["status"], "ACTIVE_REQUIRED")
        self.assertIn("NO_SILENT_RETROACTIVE_REWRITE", memory["principles"])
        memo = ROOT / memory["first_memo"]["path"]
        self.assertTrue(memo.is_file())
        text = memo.read_text()
        self.assertIn("2026-08-20", text)
        self.assertIn("6_PASS_1_FAIL", text)
        self.assertIn("append-oriented", text)

    def test_executable_checker_reports_no_canonical_drift(self):
        checker = load_checker_module()
        self.assertEqual(checker.collect_errors(), [])


if __name__ == "__main__":
    unittest.main()
