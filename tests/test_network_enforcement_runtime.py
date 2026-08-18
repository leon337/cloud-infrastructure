import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "platform/network/cloud-platform-network-enforcement").read_text(
    encoding="utf-8"
)
UNIT = (ROOT / "platform/systemd/cloud-platform-network-enforcement.service").read_text(
    encoding="utf-8"
)
DROPIN = (
    ROOT / "platform/systemd/docker.service.network-enforcement.conf"
).read_text(encoding="utf-8")
HARNESS = (ROOT / "scripts/test_network_enforcement_vm.sh").read_text(encoding="utf-8")
SERVICES_HARNESS = (ROOT / "scripts/test_network_services_vm.sh").read_text(encoding="utf-8")


class NetworkEnforcementRuntimeTests(unittest.TestCase):
    def test_cli_is_fixed_and_has_no_arbitrary_command_path(self):
        self.assertIn("apply | check | rollback", SCRIPT)
        self.assertIn("exactly_one_operation_required", SCRIPT)
        self.assertNotIn("eval ", SCRIPT)
        self.assertNotIn("bash -c", SCRIPT)

    def test_ipv4_and_ipv6_owned_chains_fail_closed(self):
        self.assertGreaterEqual(SCRIPT.count(":CLOUD-PLATFORM-IN - [0:0]"), 2)
        self.assertGreaterEqual(SCRIPT.count(":CLOUD-PLATFORM-FWD - [0:0]"), 2)
        self.assertIn("-A CLOUD-PLATFORM-FWD -i cp+ -j DROP", SCRIPT)
        self.assertIn("-A CLOUD-PLATFORM-FWD -o cp+ -j DROP", SCRIPT)
        self.assertIn("-A CLOUD-PLATFORM-IN -i cp+ -j DROP", SCRIPT)

    def test_only_owned_chains_are_restored_without_flushing_host_rules(self):
        self.assertEqual(SCRIPT.count("iptables-restore -w 5 --noflush"), 1)
        self.assertEqual(SCRIPT.count("ip6tables-restore -w 5 --noflush"), 1)
        self.assertNotIn("iptables -F INPUT", SCRIPT)
        self.assertNotIn("iptables -F FORWARD", SCRIPT)
        self.assertNotIn("nft flush ruleset", SCRIPT)

    def test_protected_ipv4_ranges_precede_the_terminal_drop(self):
        for cidr in (
            "10.0.0.0/8",
            "100.64.0.0/10",
            "169.254.0.0/16",
            "172.16.0.0/12",
            "192.168.0.0/16",
        ):
            self.assertIn(f"-i cp+ -d {cidr} -j DROP", SCRIPT)

    def test_marker_provenance_and_collision_refusals_are_mandatory(self):
        self.assertIn("root:root:600:1", SCRIPT)
        self.assertIn("preexisting_owned_input_chain", SCRIPT)
        self.assertIn("preexisting_owned_forward_chain", SCRIPT)
        self.assertIn("marker_drift", SCRIPT)
        self.assertIn("previously_managed=true", SCRIPT)

    def test_rollback_is_bounded_and_refuses_live_managed_interfaces(self):
        self.assertIn("managed_interface_still_present", SCRIPT)
        self.assertIn('"$tool" -w 5 -X "$CHAIN_IN"', SCRIPT)
        self.assertIn('"$tool" -w 5 -X "$CHAIN_FWD"', SCRIPT)
        self.assertNotIn("rm -rf", SCRIPT)

    def test_systemd_reapplies_after_docker_without_shell(self):
        self.assertIn("After=docker.service", UNIT)
        self.assertIn("Type=oneshot", UNIT)
        self.assertIn(
            "ExecStart=/usr/local/libexec/cloud-platform-network-enforcement apply",
            UNIT,
        )
        self.assertNotIn("/bin/sh", UNIT)
        self.assertEqual(
            DROPIN,
            "[Service]\nExecStartPost=/usr/local/libexec/cloud-platform-network-enforcement apply\n",
        )

    def test_disposable_harness_covers_apply_restart_refusal_and_rollback(self):
        self.assertIn("GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY", HARNESS)
        self.assertIn("changed=1", HARNESS)
        self.assertIn("changed=0", HARNESS)
        self.assertIn("managed_interface_still_present", HARNESS)
        self.assertIn("systemctl restart docker.service", HARNESS)
        self.assertIn("NETWORK_ENFORCEMENT_VM_TEST_PASS", HARNESS)

    def test_network_services_are_github_only_pinned_and_fully_cleaned(self):
        self.assertIn("GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY", SERVICES_HARNESS)
        self.assertIn("case \"$(hostname --short)\" in node-01 | vmi3506102", SERVICES_HARNESS)
        self.assertEqual(SERVICES_HARNESS.count("@sha256:"), 3)
        self.assertIn("revoked_grant_remained_reachable", SERVICES_HARNESS)
        self.assertIn("hidden_dns_record_resolved", SERVICES_HARNESS)
        self.assertIn("workload_reached_direct_egress", SERVICES_HARNESS)
        self.assertIn("NETWORK_SERVICES_VM_TEST_PASS", SERVICES_HARNESS)

    def test_shared_service_probe_gets_only_one_exact_mediated_route(self):
        self.assertEqual(SERVICES_HARNESS.count("--cap-add NET_ADMIN"), 1)
        self.assertIn("--name cp-grant-probe", SERVICES_HARNESS)
        self.assertIn(
            "ip route add 10.240.3.10/32 via 10.240.2.1 dev eth0",
            SERVICES_HARNESS,
        )
        self.assertNotIn("ip route add default", SERVICES_HARNESS)


if __name__ == "__main__":
    unittest.main()
