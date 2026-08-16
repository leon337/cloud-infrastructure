from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "validate_state", ROOT / "scripts" / "validate_state.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StateCrosscheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = MODULE.load_yaml(ROOT / "state" / "current.yaml")
        cls.discovery = MODULE.load_yaml(ROOT / "state" / "platform-discovery.yaml")
        cls.components = MODULE.load_yaml(ROOT / "state" / "components.yaml")
        cls.baseline = MODULE.load_yaml(ROOT / "evidence" / "SLICE-001" / "baseline.yaml")
        cls.inventory_hosts = MODULE.load_yaml(
            ROOT / "automation" / "ansible" / "inventory" / "dev" / "hosts.yml"
        )
        cls.inventory_vars = MODULE.load_yaml(
            ROOT
            / "automation"
            / "ansible"
            / "inventory"
            / "dev"
            / "group_vars"
            / "all.yml"
        )

    def errors_for(
        self,
        *,
        current=None,
        discovery=None,
        components=None,
        baseline=None,
        inventory_hosts=None,
        inventory_vars=None,
    ):
        return MODULE.crosscheck_errors(
            copy.deepcopy(self.current) if current is None else current,
            copy.deepcopy(self.discovery) if discovery is None else discovery,
            copy.deepcopy(self.components) if components is None else components,
            copy.deepcopy(self.baseline) if baseline is None else baseline,
            (
                copy.deepcopy(self.inventory_hosts)
                if inventory_hosts is None
                else inventory_hosts
            ),
            (
                copy.deepcopy(self.inventory_vars)
                if inventory_vars is None
                else inventory_vars
            ),
        )

    def test_current_documents_pass_crosscheck(self):
        self.assertEqual(self.errors_for(), [])

    def test_replacing_q1_with_q41_is_rejected(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["decisions"].pop("q1")
        discovery["decisions"]["q41"] = "C"
        self.assertTrue(
            any("binding Q1-Q40" in error for error in self.errors_for(discovery=discovery))
        )

    def test_invalid_choice_is_rejected(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["decisions"]["q1"] = "Z"
        self.assertTrue(
            any("binding Q1-Q40" in error for error in self.errors_for(discovery=discovery))
        )

    def test_production_authorization_drift_is_rejected(self):
        discovery = copy.deepcopy(self.discovery)
        discovery["production_promotion_authorized"] = True
        self.assertTrue(
            any("production became authorized" in error for error in self.errors_for(discovery=discovery))
        )

    def test_rotation_drift_is_rejected(self):
        components = copy.deepcopy(self.components)
        components["credential_rotation"]["status"] = "AUTHORIZED"
        self.assertTrue(
            any("credential rotation" in error for error in self.errors_for(components=components))
        )

    def test_machine_identity_drift_is_rejected(self):
        current = copy.deepcopy(self.current)
        current["remote_vps"]["machine_id_sha256"] = "0" * 64
        self.assertTrue(
            any("machine-id hash differs" in error for error in self.errors_for(current=current))
        )

    def test_inventory_identity_and_ssh_drift_are_rejected(self):
        cases = []

        inventory_vars = copy.deepcopy(self.inventory_vars)
        inventory_vars["platform_expected_machine_id_sha256"] = "0" * 64
        cases.append(("machine-id", {"inventory_vars": inventory_vars}))

        inventory_hosts = copy.deepcopy(self.inventory_hosts)
        node = inventory_hosts["all"]["children"]["platform_nodes"]["hosts"][
            "node-01"
        ]
        node["ansible_host"] = "192.0.2.1"
        cases.append(("ansible_host", {"inventory_hosts": inventory_hosts}))

        inventory_hosts = copy.deepcopy(self.inventory_hosts)
        node = inventory_hosts["all"]["children"]["platform_nodes"]["hosts"][
            "node-01"
        ]
        node["ansible_ssh_common_args"] = "-o StrictHostKeyChecking=no"
        cases.append(("SSH", {"inventory_hosts": inventory_hosts}))

        inventory_hosts = copy.deepcopy(self.inventory_hosts)
        hosts = inventory_hosts["all"]["children"]["platform_nodes"]["hosts"]
        hosts["unexpected-production-node"] = copy.deepcopy(hosts["node-01"])
        cases.append(("target-set", {"inventory_hosts": inventory_hosts}))

        for label, arguments in cases:
            with self.subTest(label=label):
                self.assertTrue(self.errors_for(**arguments))

    def test_removing_secret_prohibition_is_rejected(self):
        current = copy.deepcopy(self.current)
        current["secrets_policy"]["never_version"].remove("tokens")
        self.assertTrue(
            any("lost secret prohibition" in error for error in self.errors_for(current=current))
        )

    def test_adding_secret_prohibition_is_allowed(self):
        current = copy.deepcopy(self.current)
        current["secrets_policy"]["never_version"].append("session_cookies")
        self.assertFalse(
            any("secret prohibition" in error for error in self.errors_for(current=current))
        )

    def test_stale_disposable_gate_is_rejected_after_ci_pass(self):
        errors = MODULE.stale_f1_1_gate_errors(
            copy.deepcopy(self.current),
            {"docs/example.md": "status: PARTIAL_PENDING_VM"},
        )
        self.assertTrue(
            any("reopens passed F1.1 disposable gate" in error for error in errors)
        )


if __name__ == "__main__":
    unittest.main()
