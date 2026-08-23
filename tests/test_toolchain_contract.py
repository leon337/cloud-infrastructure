from pathlib import Path
import os
import unittest


class ToolchainContractTests(unittest.TestCase):
    def test_canonical_entrypoint_is_executable(self):
        path = Path("scripts/test.sh")
        self.assertTrue(path.is_file())
        self.assertTrue(os.access(path, os.X_OK), "scripts/test.sh must be executable")
        self.assertTrue(path.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash\n"))

    def test_mainline_neutral_continuity_decisions(self):
        self.assertFalse(Path("state/active-mission.yaml").exists())
        self.assertFalse(Path("ROADMAP-CHECKLIST.md").exists())

    def test_workflow_invokes_canonical_entrypoint(self):
        workflow = Path(".github/workflows/canonical-validation.yml").read_text(encoding="utf-8")
        self.assertIn("./scripts/test.sh", workflow)
        self.assertIn("contents: read", workflow)

    def test_secret_gate_preserves_reachable_history_scan(self):
        scanner = Path("scripts/check_repository_secrets.py").read_text(encoding="utf-8")
        self.assertIn('"rev-list", "--objects", "--all", "--no-object-names"', scanner)
        self.assertIn("reachable_history_blobs", scanner)

    def test_yaml_validation_rejects_duplicate_keys(self):
        validator = Path("scripts/validate_yaml.py").read_text(encoding="utf-8")
        loader = Path("scripts/yaml_strict.py").read_text(encoding="utf-8")
        self.assertIn("load_all_strict", validator)
        self.assertIn("found duplicate key", loader)

    def test_platform_manifest_validator_is_not_imported(self):
        entrypoint = Path("scripts/test.sh").read_text(encoding="utf-8")
        self.assertNotIn("validate_manifests.py", entrypoint)


if __name__ == "__main__":
    unittest.main()
