from __future__ import annotations

import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class DockerBoundaryArtifactTests(unittest.TestCase):
    def test_dedicated_workflow_is_pinned_and_runs_only_on_a_disposable_vm(self):
        workflow_path = ROOT / ".github" / "workflows" / "docker-boundary-ci.yml"
        workflow = workflow_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(workflow)

        jobs = parsed["jobs"]
        self.assertEqual(jobs["disposable-integration"]["runs-on"], "ubuntu-24.04")
        self.assertEqual(jobs["disposable-integration"]["needs"], "validate")
        self.assertEqual(parsed["permissions"], {"contents": "read"})
        self.assertNotIn("pull-requests: write", workflow)
        self.assertIn(
            "actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09",
            workflow,
        )
        self.assertIn(
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
            workflow,
        )
        self.assertIn(
            "GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY",
            workflow,
        )

    def test_harness_gate_precedes_every_privileged_or_destructive_operation(self):
        harness = (ROOT / "scripts" / "test_docker_boundary_vm.sh").read_text(
            encoding="utf-8"
        )
        accepted = harness.index("DOCKER_BOUNDARY_VM_GATE_ACCEPTED")
        for required in (
            "RUNNER_ENVIRONMENT",
            "ImageOS",
            "GITHUB_REPOSITORY",
            "GITHUB_WORKSPACE",
            "systemd-detect-virt --quiet --vm",
            "node-01 | vmi3506102",
        ):
            self.assertIn(required, harness[:accepted])
        self.assertNotIn("apt-get", harness[:accepted])
        self.assertNotIn("rm -rf", harness[:accepted])
        self.assertNotIn("systemctl stop", harness[:accepted])
        self.assertNotIn("sudo -n true", harness[accepted:])

    def test_bundle_contract_names_exact_docker_apt_preference_file(self):
        # This exact source/destination pair prevents the historical `.pref`
        # suffix mismatch from making the APT pin silently ineffective.
        expected_source = "platform/docker/cloud-platform-docker.pref"
        expected_destination = "/etc/apt/preferences.d/cloud-platform-docker.pref"
        self.assertIn(expected_source, self._all_boundary_sources())
        self.assertIn(expected_destination, self._all_boundary_sources())

    @staticmethod
    def _all_boundary_sources() -> str:
        paths = [
            ROOT / "scripts" / "test_docker_boundary_vm.sh",
            ROOT / "tests" / "fixtures" / "docker-boundary" / "provision-foundation.sh",
        ]
        role_root = ROOT / "automation" / "ansible" / "roles" / "docker_runtime"
        paths.extend(path for path in role_root.rglob("*") if path.is_file())
        return "\n".join(path.read_text(encoding="utf-8") for path in paths)


if __name__ == "__main__":
    unittest.main()
