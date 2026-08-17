from __future__ import annotations

import copy
import pathlib
import unittest

import yaml

from scripts.compile_network_policy import PolicyError, compile_ipv4, compile_ipv6, load_and_validate


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "platform" / "network" / "f1-2c-policy.example.yaml"


class NetworkPolicyCompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))

    def validate_copy(self, tmp_path: pathlib.Path, raw: dict):
        tmp_path.write_text(yaml.safe_dump(raw, sort_keys=False), encoding="utf-8")
        return load_and_validate(tmp_path)

    def test_example_compiles_owned_fail_closed_chains(self):
        plan = load_and_validate(EXAMPLE)
        ipv4 = compile_ipv4(plan)
        ipv6 = compile_ipv6(plan)
        self.assertIn(":CLOUD-PLATFORM-IN - [0:0]", ipv4)
        self.assertIn(":CLOUD-PLATFORM-FWD - [0:0]", ipv4)
        self.assertIn("-i cp00000001 -j DROP", ipv4)
        self.assertNotIn("-i cp00000001 -p udp --dport 53 -j ACCEPT", ipv4)
        self.assertIn("-i cp00000002 -d 10.240.2.1/32 -p udp --dport 53 -j ACCEPT", ipv4)
        self.assertIn("-d 10.240.3.10/32 -p tcp --dport 5000", ipv4)
        self.assertLess(
            ipv4.index("-d 10.240.3.10/32 -p tcp --dport 5000"),
            ipv4.index("-i cp00000002 -d 10.0.0.0/8 -j DROP"),
        )
        self.assertNotIn("-j ACCEPT\nCOMMIT", ipv4)
        self.assertIn("-i cp00000002 -j DROP", ipv6)
        self.assertNotIn("-j ACCEPT", ipv6)

    def test_unknown_field_is_refused(self):
        raw = copy.deepcopy(self.raw)
        raw["unsafe_override"] = True
        with self.subTest("unknown"):
            with self.assertRaisesRegex(PolicyError, "unknown"):
                exact = ROOT / ".network-policy-unknown.test.yaml"
                try:
                    self.validate_copy(exact, raw)
                finally:
                    exact.unlink(missing_ok=True)

    def test_overlap_and_expired_grant_are_refused(self):
        overlap = copy.deepcopy(self.raw)
        overlap["sandboxes"][1]["subnet_ipv4"] = "10.240.1.0/24"
        overlap["sandboxes"][1]["gateway_ipv4"] = "10.240.1.1"
        expired = copy.deepcopy(self.raw)
        expired["shared_service_grants"][0]["valid_until_utc"] = "2026-08-17T11:59:59Z"
        for name, raw, message in (
            ("overlap", overlap, "overlap"),
            ("expired", expired, "expired"),
        ):
            path = ROOT / f".network-policy-{name}.test.yaml"
            try:
                with self.assertRaisesRegex(PolicyError, message):
                    self.validate_copy(path, raw)
            finally:
                path.unlink(missing_ok=True)

    def test_external_destination_and_invalid_interface_are_refused(self):
        destination = copy.deepcopy(self.raw)
        destination["shared_service_grants"][0]["destination_ipv4"] = "203.0.113.10"
        interface = copy.deepcopy(self.raw)
        interface["sandboxes"][0]["interface"] = "eth0"
        for name, raw, message in (
            ("destination", destination, "outside scope"),
            ("interface", interface, "interface is invalid"),
        ):
            path = ROOT / f".network-policy-{name}.test.yaml"
            try:
                with self.assertRaisesRegex(PolicyError, message):
                    self.validate_copy(path, raw)
            finally:
                path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
