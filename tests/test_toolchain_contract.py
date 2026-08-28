from pathlib import Path
import os
import unittest


class ToolchainContractTests(unittest.TestCase):
    def test_canonical_entrypoint_is_executable(self):
        path = Path("scripts/test.sh")
        self.assertTrue(path.is_file())
        self.assertTrue(os.access(path, os.X_OK), "scripts/test.sh must be executable")
        self.assertTrue(path.read_text(encoding="utf-8").startswith("#!/usr/bin/env bash\n"))

    def test_document_authority_hierarchy_is_explicit(self):
        self.assertFalse(Path("state/active-mission.yaml").exists())
        readme = Path("README.md").read_text(encoding="utf-8")
        roadmap_path = Path("ROADMAP-CHECKLIST.md")
        self.assertTrue(roadmap_path.is_file())
        roadmap = roadmap_path.read_text(encoding="utf-8")
        self.assertIn("CANONICAL_EXECUTIVE_PANEL_IMPLEMENTACAO_DA_VPS", readme)
        self.assertIn("IMPLEMENTACAO_DA_VPS_OPERATIONAL_CHECKLIST", roadmap)
        self.assertIn("subordinado ao `README.md`", roadmap)
        self.assertNotIn("<!-- CANONICAL_OPERATIONAL_CHECKLIST -->", roadmap)

    def test_canonical_ci_preserves_hosted_integration_boundary(self):
        workflow = Path(".github/workflows/canonical-validation.yml").read_text(encoding="utf-8")
        self.assertIn("runs-on: ubuntu-24.04", workflow)
        self.assertIn("actions/setup-python@", workflow)
        self.assertIn("requirements-dev.lock", workflow)
        self.assertIn("./scripts/test.sh", workflow)
        self.assertIn("contents: read", workflow)

    def test_maintenance_proof_is_scoped_and_unprivileged(self):
        workflow = Path(
            ".github/workflows/canonical-validation-maintenance-proof.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("team/canonical-state-toolchain-", workflow)
        self.assertIn("self-hosted", workflow)
        self.assertIn("sudo -n true", workflow)
        self.assertIn("writable_docker_socket", workflow)
        self.assertIn("./scripts/test.sh", workflow)

    def test_neutral_dependency_lock(self):
        lock = Path("requirements-dev.lock").read_text(encoding="utf-8")
        requirements = [
            line for line in lock.splitlines() if line and not line.startswith("#")
        ]
        self.assertEqual(requirements, ["PyYAML==6.0.3"])

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
