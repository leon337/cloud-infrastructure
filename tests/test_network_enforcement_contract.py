from __future__ import annotations

import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class NetworkEnforcementContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "platform" / "network" / "f1-2c-contract.yaml"
        cls.contract = yaml.safe_load(cls.path.read_text(encoding="utf-8"))

    def test_contract_records_node_desired_state_and_keeps_real_apply_gated(self):
        metadata = self.contract["metadata"]
        gates = self.contract["gates"]

        self.assertEqual(metadata["slice"], "F1.2c")
        self.assertEqual(metadata["environment"], "DEV_LAB")
        self.assertEqual(
            metadata["status"],
            "NODE_01_NETWORK_SERVICES_DESIRED_STATE_PREPARED",
        )
        self.assertEqual(
            metadata["operational_state"],
            "BASE_APPLIED_NODE_01_SERVICES_LOCAL_STATIC_PASS_CI_AND_REAL_APPLY_PENDING",
        )
        self.assertEqual(
            metadata["technology_selection"],
            "DOCKER_IPTABLES_NFT_DOCKER_USER_INTERNAL_BRIDGES_PROXY_EGRESS",
        )
        self.assertEqual(gates["technology_adr"], "ACCEPTED_DEC_008")
        self.assertTrue(gates["disposable_integration"].startswith("PASS_RUN_"))
        self.assertEqual(
            gates["node_01_execution"],
            "BASE_ONLY_APPLIED_SERVICES_DESIRED_STATE_NOT_APPLIED",
        )
        self.assertEqual(gates["production"], "NOT_AUTHORIZED")
        self.assertEqual(
            gates["credential_rotation"],
            "DEFERRED_BY_HUMAN_DECISION",
        )

    def test_both_address_families_and_all_protected_zones_are_mandatory(self):
        scope = self.contract["scope"]

        self.assertEqual(set(scope["address_families"]), {"ipv4", "ipv6"})
        self.assertEqual(
            set(scope["protected_zones"]),
            {"host", "management", "metadata", "control"},
        )
        self.assertEqual(
            set(scope["workload_scopes"]),
            {"tenant", "project", "mission", "sandbox"},
        )
        selected = scope["selected_mechanisms"]
        self.assertEqual(selected["docker_firewall_backend"], "iptables")
        self.assertEqual(selected["host_frontend"], "iptables-nft")
        self.assertEqual(selected["policy_entry_chain"], "DOCKER-USER")
        self.assertEqual(selected["owned_chain"], "CLOUD-PLATFORM-FWD")
        self.assertEqual(selected["workload_network_mode"], "internal")
        self.assertFalse(selected["inter_container_communication"])
        self.assertEqual(
            selected["host_ip_forwarding"],
            "enabled_only_with_default_drop_and_explicit_grants",
        )
        self.assertEqual(selected["egress"], "explicit_http_connect_proxy")
        self.assertTrue(scope["address_pools"]["collision_check_required"])

    def test_default_policy_is_fail_closed_and_sharing_is_explicit(self):
        policy = self.contract["default_policy"]
        sharing = self.contract["sharing"]
        discovery = self.contract["service_discovery"]

        exact_denies = {
            "ingress",
            "published_ports",
            "host_access",
            "management_access",
            "metadata_access",
            "control_plane_access",
            "cross_tenant",
            "cross_project",
            "cross_mission",
            "cross_sandbox",
            "private_destination_access",
            "unknown_identity",
            "policy_unavailable",
        }
        self.assertTrue(all(policy[key] == "DENY" for key in exact_denies))
        self.assertEqual(
            policy["shared_service_access"],
            "DENY_WITHOUT_EXPLICIT_IDENTITY_GRANT",
        )
        self.assertEqual(
            policy["internet_egress"],
            "DENY_WITHOUT_EXPLICIT_PROFILE",
        )
        self.assertEqual(sharing["implicit_shared_networks"], "FORBIDDEN")
        self.assertEqual(sharing["missing_or_invalid_grant"], "DENY")
        self.assertTrue(discovery["identity_aware_authorization_required"])
        self.assertFalse(discovery["raw_ip_or_container_name_grants_authority"])

    def test_first_workload_requires_complete_disposable_evidence(self):
        required = set(self.contract["required_disposable_evidence"])
        expected = {
            "baseline_and_post_ruleset_ipv4",
            "baseline_and_post_ruleset_ipv6",
            "external_ingress_probe_ipv4",
            "external_ingress_probe_ipv6",
            "deny_host_management_metadata_control",
            "deny_cross_tenant_project_mission_sandbox",
            "allow_explicit_shared_service_grant",
            "deny_revoked_or_expired_shared_service_grant",
            "egress_profile_none",
            "egress_profile_restricted",
            "egress_profile_development_default",
            "controlled_dns_and_identity_aware_discovery",
            "policy_dependency_failure_denies",
            "restart_and_idempotence",
            "rollback_and_cleanup",
        }

        self.assertEqual(required, expected)
        self.assertEqual(
            set(self.contract["egress_profiles"]["required_names"]),
            {"none", "restricted", "development-default"},
        )
        self.assertEqual(
            self.contract["gates"]["first_workload"],
            "BLOCKED_BY_NODE_01_NETWORK_SERVICES_CI_REAL_APPLY_AND_REMAINING_GATES",
        )


if __name__ == "__main__":
    unittest.main()
