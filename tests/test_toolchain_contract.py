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


if __name__ == "__main__":
    unittest.main()
