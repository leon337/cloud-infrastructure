from __future__ import annotations

import copy
import json
import pathlib
import unittest

import jsonschema
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]


class ManifestNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (ROOT / "platform" / "schemas" / "project.schema.json").read_text(
                encoding="utf-8"
            )
        )
        cls.example = yaml.safe_load(
            (
                ROOT
                / "platform"
                / "manifests"
                / "examples"
                / "project.example.yaml"
            ).read_text(encoding="utf-8")
        )

    def assert_invalid(self, manifest):
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.validate(manifest, self.schema)

    def test_inline_password_field_is_rejected(self):
        manifest = copy.deepcopy(self.example)
        manifest["spec"]["password"] = "not-a-real-secret"
        self.assert_invalid(manifest)

    def test_production_authorization_is_rejected(self):
        manifest = copy.deepcopy(self.example)
        manifest["spec"]["production"]["promotionAuthorized"] = True
        self.assert_invalid(manifest)

    def test_real_secret_value_instead_of_reference_is_rejected(self):
        manifest = copy.deepcopy(self.example)
        manifest["spec"]["secretRefs"] = ["literal-value"]
        self.assert_invalid(manifest)

    def test_public_ingress_is_not_a_valid_manifest_value(self):
        manifest = copy.deepcopy(self.example)
        manifest["spec"]["sandbox"]["network"]["ingress"] = "public"
        self.assert_invalid(manifest)


if __name__ == "__main__":
    unittest.main()
