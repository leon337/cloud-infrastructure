from __future__ import annotations

import hashlib
import pathlib
import unittest

import yaml

from scripts.compile_network_policy import PolicyError, load_and_validate
from scripts.generate_network_services import generate_coredns, generate_hosts, generate_squid


ROOT = pathlib.Path(__file__).resolve().parents[1]
POLICY = ROOT / "platform/network/f1-2c-policy.node-01.yaml"
PAYLOAD = ROOT / "platform/network/cloud-platform-network-services"
COMPOSE = ROOT / "platform/network/node-01/compose.yaml"
UNIT = ROOT / "platform/systemd/cloud-platform-network-services.service"
SYSCTL = ROOT / "platform/sysctl/90-cloud-platform-network-forwarding.conf"
APPLY = ROOT / "automation/mission-001/operations/apply"
ROLLBACK = ROOT / "automation/mission-001/operations/rollback"


class NodeNetworkServicesTests(unittest.TestCase):
    def test_operational_policy_requires_an_explicit_node_status(self):
        with self.assertRaisesRegex(PolicyError, "status is not accepted"):
            load_and_validate(POLICY)
        plan = load_and_validate(POLICY, allowed_statuses={"NODE_01_DESIRED_STATE"})
        self.assertEqual(plan["metadata"]["environment"], "DEV_LAB")
        self.assertEqual(plan["shared_service_grants"], [])
        self.assertEqual(plan["service_records"], [])
        self.assertEqual(
            {item["egress_profile"] for item in plan["sandboxes"]},
            {"none", "restricted", "development-default"},
        )

    def test_installed_configs_are_exact_deterministic_projections(self):
        plan = load_and_validate(POLICY, allowed_statuses={"NODE_01_DESIRED_STATE"})
        for interface in ("cp00000002", "cp00000003"):
            directory = ROOT / "platform/network/node-01" / interface
            self.assertEqual((directory / "Corefile").read_text(), generate_coredns(plan, interface))
            self.assertEqual((directory / "squid.conf").read_text(), generate_squid(plan, interface))
            self.assertEqual(generate_hosts(plan, interface), "")
            self.assertIn("No shared service is authorized", (directory / "records.hosts").read_text())

    def test_compose_has_only_four_pinned_private_platform_services(self):
        compose = yaml.safe_load(COMPOSE.read_text())
        self.assertEqual(
            set(compose["services"]),
            {"dns-dev", "dns-restricted", "proxy-dev", "proxy-restricted"},
        )
        for name, service in compose["services"].items():
            with self.subTest(service=name):
                self.assertRegex(service["image"], r"@sha256:[0-9a-f]{64}$")
                self.assertTrue(service["read_only"])
                self.assertEqual(service["restart"], "no")
                self.assertNotIn("ports", service)
                self.assertNotIn("privileged", service)
                self.assertNotIn("network_mode", service)
                self.assertEqual(service["cgroup_parent"], "cloud-platform.slice")
                self.assertIn("no-new-privileges:true", service["security_opt"])
                self.assertEqual(
                    service["labels"]["cloud.platform.managed"],
                    "mission-001-f1-2c-services",
                )
        self.assertEqual(set(compose["networks"]), {"scope-dev", "scope-restricted", "egress"})
        self.assertTrue(all(item["external"] for item in compose["networks"].values()))

    def test_runtime_owns_only_exact_chains_networks_and_containers(self):
        script = PAYLOAD.read_text()
        self.assertIn("CLOUD-PLATFORM-SVC", script)
        self.assertIn("CLOUD-PLATFORM-EGRESS", script)
        self.assertIn("10.240.254.2/31", script)
        self.assertIn("10.240.254.4/31", script)
        self.assertIn("--dports 80,443", script)
        self.assertIn("-i cpeg0001 -j DROP", script)
        self.assertIn("-o cpeg0001 -j DROP", script)
        self.assertIn("net.ipv6.conf.all.forwarding", script)
        self.assertIn("unexpected_container_set", script)
        self.assertIn("unexpected_network_set", script)
        self.assertNotIn("rm -rf", script)
        self.assertNotIn("eval ", script)
        self.assertNotRegex(script, r"(?m)^\s*ufw\s")

    def test_forwarding_is_persistent_only_with_owned_fail_closed_chains(self):
        sysctl = SYSCTL.read_text()
        runtime = PAYLOAD.read_text()
        self.assertIn("net.ipv4.ip_forward = 1", sysctl)
        self.assertIn("net.ipv6.conf.all.forwarding = 0", sysctl)
        self.assertLess(runtime.index("apply_firewall\n"), runtime.index("create_scope_network cloud-scope"))
        self.assertLess(runtime.index("create_egress_network\n"), runtime.index("sysctl -q -w net.ipv4.ip_forward=1"))

    def test_systemd_reconciles_after_docker_without_auto_restarting_containers(self):
        unit = UNIT.read_text()
        self.assertIn("After=docker.service cloud-platform-network-enforcement.service", unit)
        self.assertIn("PartOf=docker.service", unit)
        self.assertIn("ExecStart=/usr/local/libexec/cloud-platform-network-services apply", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertNotIn("/bin/sh", unit)

    def test_systemd_strict_protection_has_private_writable_runtime_lock(self):
        unit = UNIT.read_text()
        runtime = PAYLOAD.read_text()
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("RuntimeDirectory=cloud-platform-network-services", unit)
        self.assertIn("RuntimeDirectoryMode=0700", unit)
        self.assertIn(
            "readonly LOCK=/run/cloud-platform-network-services/lock",
            runtime,
        )
        self.assertNotIn("/run/lock/cloud-platform-network-services.lock", runtime)
        self.assertNotIn("ReadWritePaths=/run/lock", unit)

    def test_apply_hash_inventory_matches_every_installed_source(self):
        operation = APPLY.read_text()
        sources = (
            PAYLOAD,
            COMPOSE,
            ROOT / "platform/network/node-01/cp00000002/Corefile",
            ROOT / "platform/network/node-01/cp00000002/records.hosts",
            ROOT / "platform/network/node-01/cp00000002/squid.conf",
            ROOT / "platform/network/node-01/cp00000003/Corefile",
            ROOT / "platform/network/node-01/cp00000003/records.hosts",
            ROOT / "platform/network/node-01/cp00000003/squid.conf",
            UNIT,
            SYSCTL,
        )
        for source in sources:
            with self.subTest(source=source.relative_to(ROOT)):
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                self.assertIn(digest, operation)

    def test_rollback_removes_services_before_base_and_never_recurses(self):
        rollback = ROLLBACK.read_text()
        self.assertLess(rollback.index("$SERVICE_HELPER\" rollback"), rollback.index("$BASE_HELPER\" rollback"))
        self.assertIn("base_preserved=true", rollback)
        self.assertNotIn("rm -rf", rollback)
        self.assertIn('unlink -- "$SERVICE_MARKER"', rollback)


if __name__ == "__main__":
    unittest.main()
