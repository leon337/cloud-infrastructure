from __future__ import annotations

import hashlib
import pathlib
import subprocess
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "platform/network/cloud-platform-network-services"
UNIT = ROOT / "platform/systemd/cloud-platform-network-services.service"
COMPOSE = ROOT / "platform/network/node-01/compose.yaml"
SYSCTL = ROOT / "platform/sysctl/90-cloud-platform-network-forwarding.conf"
VM_HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"
APPLY = ROOT / "automation/mission-001/operations/apply"
ROLLBACK = ROOT / "automation/mission-001/operations/rollback"


class NodeNetworkServicesTests(unittest.TestCase):
    def test_compose_has_only_four_pinned_private_platform_services(self):
        data = yaml.safe_load(COMPOSE.read_text())
        services = data["services"]
        self.assertEqual(
            set(services),
            {"dns-cp00000002", "proxy-cp00000002", "dns-cp00000003", "proxy-cp00000003"},
        )
        for service in services.values():
            self.assertRegex(service["image"], r"^[^:]+@sha256:[0-9a-f]{64}$")
            self.assertEqual(service["restart"], "no")
            self.assertEqual(service["read_only"], True)
            self.assertIn("ALL", service["cap_drop"])
            self.assertEqual(service["security_opt"], ["no-new-privileges:true"])
            self.assertNotIn("ports", service)
            self.assertNotIn("network_mode", service)
            self.assertNotIn("privileged", service)

    def test_runtime_owns_only_exact_chains_networks_and_containers(self):
        runtime = PAYLOAD.read_text()
        for token in (
            "CLOUD-SVC-IN",
            "CLOUD-SVC-OUT",
            "CLOUD-SVC-EGRESS",
            "cloud-scope-cp00000002",
            "cloud-scope-cp00000003",
            "cloud-egress-dev",
            "cp-dns-dev",
            "cp-proxy-dev",
            "cp-dns-test",
            "cp-proxy-test",
        ):
            self.assertIn(token, runtime)
        self.assertNotIn("iptables -F", runtime)
        self.assertNotIn("ip6tables -F", runtime)
        self.assertNotIn("docker system prune", runtime)

    def test_installed_configs_are_exact_deterministic_projections(self):
        runtime = PAYLOAD.read_text()
        self.assertIn("sha256sum", runtime)
        self.assertIn("assert_config_file", runtime)
        self.assertIn("assert_managed_file", runtime)
        self.assertIn("/etc/cloud-platform/network-services", runtime)

    def test_forwarding_is_persistent_only_with_owned_fail_closed_chains(self):
        runtime = PAYLOAD.read_text()
        sysctl = SYSCTL.read_text()
        self.assertIn("net.ipv4.ip_forward = 1", sysctl)
        self.assertIn("net.ipv6.conf.all.forwarding = 0", sysctl)
        self.assertIn("-A CLOUD-SVC-EGRESS -j DROP", runtime)
        self.assertIn("ip6tables", runtime)
        self.assertLess(runtime.index("apply_firewall\n"), runtime.index("create_scope_network cloud-scope"))
        self.assertLess(runtime.index("create_egress_network\n"), runtime.index("sysctl -q -w net.ipv4.ip_forward=1"))

    def test_operational_policy_requires_an_explicit_node_status(self):
        runtime = PAYLOAD.read_text()
        self.assertIn("NETWORK_SERVICES_CHECK=PASS", runtime)
        self.assertIn("NETWORK_SERVICES_APPLY=PASS", runtime)
        self.assertIn("NETWORK_SERVICES_ROLLBACK=PASS", runtime)

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
        self.assertIn(
            "ReadWritePaths=/run/lock/cloud-platform-network-enforcement.lock",
            unit,
        )
        self.assertNotIn("\nReadWritePaths=/run/lock\n", unit)

    def test_disposable_vm_harness_exercises_the_exact_systemd_service(self):
        harness = VM_HARNESS.read_text()
        self.assertIn(
            "platform/systemd/cloud-platform-network-services.service",
            harness,
        )
        self.assertIn(
            "systemctl enable --now cloud-platform-network-services.service",
            harness,
        )
        self.assertIn(
            "systemctl is-active --quiet cloud-platform-network-services.service",
            harness,
        )
        self.assertIn(
            "systemctl disable --now cloud-platform-network-services.service",
            harness,
        )
        self.assertIn("journalctl -u cloud-platform-network-services.service", harness)

    def test_disposable_vm_harness_dumps_root_cause_when_systemd_service_is_inactive(self):
        harness = VM_HARNESS.read_text()
        self.assertIn("diagnose_network_services_failure()", harness)
        self.assertIn(
            "systemctl status cloud-platform-network-services.service --no-pager --full",
            harness,
        )
        self.assertIn(
            "journalctl -u cloud-platform-network-services.service -n 160 --no-pager",
            harness,
        )
        self.assertIn("docker compose version", harness)
        self.assertIn(
            "if ! sudo systemctl is-active --quiet cloud-platform-network-services.service; then",
            harness,
        )
        self.assertGreaterEqual(harness.count("diagnose_network_services_failure"), 3)

    def test_disposable_identities_share_one_full_privileged_lifecycle(self):
        harness = VM_HARNESS.read_text()
        github_gate = harness.index("GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY")
        local_gate = harness.index("MCF_LOCAL_KVM_UBUNTU_24_04_DISPOSABLE_VM_ONLY")
        lifecycle = harness.index("sudo install -d -o root -g root -m 0755 /usr/local/libexec")
        self.assertLess(github_gate, lifecycle)
        self.assertLess(local_gate, lifecycle)
        for marker in (
            "systemctl enable --now cloud-platform-network-services.service",
            "probe nslookup api.github.com",
            "direct_egress_allowed",
            "development_proxy_failed",
            "systemctl restart docker.service",
            "NETWORK_SERVICES_ROLLBACK=PASS",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, harness)
        self.assertEqual(harness.count("NODE_NETWORK_SERVICES_VM_PASS"), 1)

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
