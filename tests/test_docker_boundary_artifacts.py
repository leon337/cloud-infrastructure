from __future__ import annotations

import hashlib
import json
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
        self.assertIn("SHELLCHECK_VERSION: v0.11.0", workflow)
        self.assertIn(
            "8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198",
            workflow,
        )
        self.assertNotIn("apt-get install --yes", workflow)

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
            "unexpected_os_release_link",
            "unsafe_os_release_metadata",
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

    def test_all_managed_payload_hashes_match_the_immutable_role_inventory(self):
        variables = yaml.safe_load(
            (
                ROOT
                / "automation"
                / "ansible"
                / "roles"
                / "docker_runtime"
                / "vars"
                / "main.yml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(len(variables["platform_docker_managed_payloads"]), 7)
        for payload in variables["platform_docker_managed_payloads"]:
            source = ROOT / payload["source"]
            self.assertTrue(source.is_file(), payload["source"])
            self.assertEqual(
                hashlib.sha256(source.read_bytes()).hexdigest(),
                payload["sha256"],
                payload["source"],
            )

    def test_daemon_configuration_is_empty_root_only_and_has_no_tcp_api(self):
        daemon = json.loads(
            (ROOT / "platform" / "docker" / "daemon.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "bridge": "none",
            "cgroup-parent": "cloud-workloads.slice",
            "default-cgroupns-mode": "private",
            "firewall-backend": "iptables",
            "group": "root",
            "icc": False,
            "ip": "127.0.0.1",
            "ip-forward": False,
            "ip-masq": False,
            "ip6tables": True,
            "iptables": True,
            "ipv6": False,
            "live-restore": False,
            "no-new-privileges": True,
        }
        for key, value in expected.items():
            self.assertEqual(daemon[key], value, key)
        for forbidden in ("hosts", "metrics-addr", "tls", "tlsverify"):
            self.assertNotIn(forbidden, daemon)
        self.assertEqual(daemon["exec-opts"], ["native.cgroupdriver=systemd"])

    def test_apt_preferences_pin_each_exact_package_version(self):
        preference = (
            ROOT / "platform" / "docker" / "cloud-platform-docker.pref"
        ).read_text(encoding="utf-8")
        records = []
        for block in preference.strip().split("\n\n"):
            record = dict(line.split(": ", 1) for line in block.splitlines())
            records.append(record)
        actual = {
            record["Package"]: (record["Pin"], record["Pin-Priority"])
            for record in records
        }
        self.assertEqual(
            actual,
            {
                "docker-ce": (
                    "version 5:29.7.2-1~ubuntu.24.04~noble",
                    "1001",
                ),
                "docker-ce-cli": (
                    "version 5:29.7.2-1~ubuntu.24.04~noble",
                    "1001",
                ),
                "containerd.io": (
                    "version 2.3.3-1~ubuntu.24.04~noble",
                    "1001",
                ),
                "docker-buildx-plugin": (
                    "version 0.36.1-1~ubuntu.24.04~noble",
                    "1001",
                ),
                "docker-compose-plugin": (
                    "version 5.4.0-1~ubuntu.24.04~noble",
                    "1001",
                ),
            },
        )

    def test_apply_and_rollback_import_the_same_controller_preflight(self):
        playbook_root = ROOT / "automation" / "ansible" / "playbooks"
        apply = yaml.safe_load((playbook_root / "docker-runtime.yml").read_text())
        rollback = yaml.safe_load(
            (playbook_root / "rollback-docker-runtime.yml").read_text()
        )
        self.assertEqual(
            apply[0]["import_playbook"], "docker-runtime-controller-preflight.yml"
        )
        self.assertEqual(
            rollback[0]["import_playbook"],
            "docker-runtime-controller-preflight.yml",
        )
        self.assertEqual(apply[1]["hosts"], "platform_nodes")
        self.assertEqual(rollback[1]["hosts"], "platform_nodes")
        self.assertTrue(apply[1]["become"])
        self.assertTrue(rollback[1]["become"])

    def test_controller_preflight_uses_the_selected_inventory_source(self):
        preflight = (
            ROOT
            / "automation"
            / "ansible"
            / "playbooks"
            / "docker-runtime-controller-preflight.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("ansible_inventory_sources | length == 1", preflight)
        self.assertIn("ansible_inventory_sources | first", preflight)
        self.assertNotIn('{{ inventory_file }}', preflight)

    def test_reconcile_validates_index_digest_before_suppressed_install(self):
        reconcile = (
            ROOT
            / "automation"
            / "ansible"
            / "roles"
            / "docker_runtime"
            / "tasks"
            / "reconcile.yml"
        ).read_text(encoding="utf-8")
        digest_check = reconcile.index("SHA256: ")
        install = reconcile.index("Install only the five exact Docker packages")
        self.assertLess(digest_check, install)
        self.assertIn("policy_rc_d: 101", reconcile)
        self.assertIn("map('trim')", reconcile)
        self.assertIn("'Candidate: ' ~ item.item.version", reconcile)
        self.assertIn("Prove package scripts did not start the runtime", reconcile)
        self.assertIn("Prove package scripts did not initialize runtime state", reconcile)

    def test_package_preflight_distinguishes_installed_from_known_records(self):
        role = (
            ROOT
            / "automation"
            / "ansible"
            / "roles"
            / "docker_runtime"
            / "tasks"
            / "main.yml"
        ).read_text(encoding="utf-8")
        self.assertEqual(role.count("selectattr('stdout', 'match', '^ii ')"), 3)

    def test_rollback_is_manifest_bounded_and_relinquishes_marker_last(self):
        playbook_root = ROOT / "automation" / "ansible" / "playbooks"
        rollback = (playbook_root / "rollback-docker-runtime.yml").read_text(
            encoding="utf-8"
        )
        mutate = (
            playbook_root / "tasks" / "rollback-docker-runtime-mutate.yml"
        ).read_text(encoding="utf-8")
        combined = rollback + mutate
        self.assertIn("runtime_tree_guard.py prepare-removal", mutate)
        self.assertIn("runtime_tree_guard.py remove", mutate)
        self.assertIn("autoremove: false", mutate)
        self.assertNotIn("autoremove: true", combined)
        self.assertNotIn("rm -rf", combined)
        self.assertNotIn("state: touch", combined)
        marker = mutate.index("Remove the exact Docker management marker last")
        self.assertGreater(marker, mutate.index("daemon_reload: true"))
        self.assertGreater(marker, mutate.index("runtime-tree-baseline.json"))

    def test_harness_exercises_check_apply_idempotence_refusals_and_cleanup(self):
        harness = (ROOT / "scripts" / "test_docker_boundary_vm.sh").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("harness_implementation_not_yet_complete", harness)
        for required in (
            "DOCKER_BOUNDARY_CHECK_MODE_PASS",
            "second_reconcile_not_idempotent",
            "rollback_marker_drift",
            "rollback_group_member",
            "rollback_docker_object",
            "rollback_tree_drift",
            "rollback_check_mode_mutated_managed_surface",
            "DOCKER_BOUNDARY_VM_TEST_PASS",
        ):
            self.assertIn(required, harness)
        self.assertIn("residual-config (rc) records", harness)
        self.assertIn("stable, exact interface set", harness)
        self.assertIn("DOCKER_BOUNDARY_NETWORK_DIFF", harness)
        self.assertIn("preinstalled_docker0_is_not_a_bridge", harness)
        self.assertIn("ip link delete dev docker0 type bridge", harness)
        self.assertNotIn("rm -rf", harness)
        self.assertNotIn("apt-get autoremove", harness)

    @staticmethod
    def _all_boundary_sources() -> str:
        paths = [
            ROOT / "scripts" / "test_docker_boundary_vm.sh",
            ROOT / "tests" / "fixtures" / "docker-boundary" / "provision-foundation.sh",
        ]
        role_root = ROOT / "automation" / "ansible" / "roles" / "docker_runtime"
        paths.extend(
            path
            for path in role_root.rglob("*")
            if path.is_file() and "__pycache__" not in path.parts
        )
        return "\n".join(path.read_text(encoding="utf-8") for path in paths)


if __name__ == "__main__":
    unittest.main()
