from __future__ import annotations

import copy
import pathlib
import unittest

import yaml

from scripts.compile_network_policy import PolicyError, load_and_validate
from scripts.generate_network_services import generate_coredns, generate_hosts, generate_squid


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "platform/network/f1-2c-policy.example.yaml"
IMAGES = ROOT / "platform/network/f1-2c-service-images.yaml"


class NetworkServicesGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = load_and_validate(EXAMPLE)
        cls.raw = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))

    def validate_copy(self, name: str, raw: dict):
        path = ROOT / f".network-services-{name}.test.yaml"
        try:
            path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
            return load_and_validate(path)
        finally:
            path.unlink(missing_ok=True)

    def test_coredns_is_generated_per_scope_and_separates_hosts_views(self):
        config = generate_coredns(self.plan, "cp00000002")
        self.assertIn("bind 0.0.0.0", config)
        self.assertEqual(config.count("forward . 1.1.1.1 1.0.0.1"), 1)
        self.assertEqual(
            generate_hosts(self.plan, "cp00000002"),
            "10.240.3.10 registry.shared.dev.internal\n",
        )
        self.assertIn(
            "10.240.3.11 admin.registry.shared.dev.internal",
            generate_hosts(self.plan, "cp00000003"),
        )
        self.assertNotIn("fallthrough", config.split(".:53", maxsplit=1)[0])

    def test_squid_is_exact_destination_proxy_and_ends_in_deny_all(self):
        config = generate_squid(self.plan, "cp00000002")
        self.assertIn("http_port 0.0.0.0:3128", config)
        self.assertIn("acl scope_source src 10.240.2.0/24", config)
        self.assertIn("acl protected_dst dst 10.0.0.0/8", config)
        self.assertIn("dns_nameservers 1.1.1.1 1.0.0.1", config)
        self.assertIn("acl destination_github_api dstdomain api.github.com", config)
        self.assertNotIn(
            "scope_source destination_not_declared",
            config,
        )
        self.assertIn(
            "scope_source destination_github_api destination_ports_github_api",
            config,
        )
        self.assertLess(config.index("http_access deny protected_dst"), config.index("http_access allow"))
        self.assertEqual(config.splitlines()[-2], "http_access deny all")

        restricted = generate_squid(self.plan, "cp00000003")
        self.assertNotIn("scope_source destination_github_api", restricted)
        self.assertIn("scope_source destination_github_container_registry", restricted)

    def test_none_profile_has_no_service_configuration(self):
        with self.assertRaisesRegex(PolicyError, "none profile"):
            generate_coredns(self.plan, "cp00000001")
        with self.assertRaisesRegex(PolicyError, "none profile"):
            generate_squid(self.plan, "cp00000001")

    def test_service_images_are_pinned_and_node_start_remains_ci_gated(self):
        images = yaml.safe_load(IMAGES.read_text(encoding="utf-8"))
        self.assertFalse(images["metadata"]["production"])
        self.assertEqual(images["metadata"]["status"], "NODE_01_DESIRED_STATE_PREPARED_CI_PENDING")
        for name, image in images["images"].items():
            with self.subTest(image=name):
                self.assertRegex(image["reference"], r"@sha256:[0-9a-f]{64}$")
                self.assertEqual(image["platform"], "linux/amd64")
        self.assertEqual(images["gates"]["node_01_pull"], "AUTHORIZED_AFTER_COMMIT_BOUND_CI_PASS")
        self.assertEqual(images["gates"]["first_user_workload"], "NOT_AUTHORIZED")

    def test_wildcard_private_and_none_profile_destinations_are_refused(self):
        cases = []
        wildcard = copy.deepcopy(self.raw)
        wildcard["egress_destinations"][0]["hostname"] = "*.github.com"
        cases.append(("wildcard", wildcard, "exact public DNS name"))
        internal = copy.deepcopy(self.raw)
        internal["egress_destinations"][0]["hostname"] = "service.dev.internal"
        cases.append(("internal", internal, "exact public DNS name"))
        none = copy.deepcopy(self.raw)
        none["egress_destinations"][0]["profiles"] = ["none"]
        cases.append(("none", none, "profiles is invalid"))
        for name, raw, message in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(PolicyError, message):
                    self.validate_copy(name, raw)

    def test_service_record_requires_internal_name_managed_ip_and_known_view(self):
        cases = []
        public_name = copy.deepcopy(self.raw)
        public_name["service_records"][0]["name"] = "registry.example.com"
        cases.append(("public", public_name, "DEV internal DNS name"))
        external_ip = copy.deepcopy(self.raw)
        external_ip["service_records"][0]["ipv4"] = "203.0.113.10"
        cases.append(("external", external_ip, "outside managed scopes"))
        unknown_view = copy.deepcopy(self.raw)
        unknown_view["service_records"][0]["visible_to_interfaces"] = ["cpdeadbeef"]
        cases.append(("view", unknown_view, "visible_to_interfaces is invalid"))
        for name, raw, message in cases:
            with self.subTest(name=name):
                with self.assertRaisesRegex(PolicyError, message):
                    self.validate_copy(name, raw)


if __name__ == "__main__":
    unittest.main()
