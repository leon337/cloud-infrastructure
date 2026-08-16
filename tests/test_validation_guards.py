from __future__ import annotations

import importlib.util
import pathlib
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "yaml_strict", ROOT / "scripts" / "yaml_strict.py"
)
assert SPEC and SPEC.loader
YAML_STRICT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YAML_STRICT)


class StrictYamlTests(unittest.TestCase):
    def test_duplicate_mapping_key_is_rejected(self):
        document = "production: false\nproduction: true\n"
        with self.assertRaises(yaml.constructor.ConstructorError):
            YAML_STRICT.load_strict(document)

    def test_distinct_mapping_keys_are_accepted(self):
        self.assertEqual(
            YAML_STRICT.load_strict("production: false\nenvironment: dev\n"),
            {"production": False, "environment": "dev"},
        )


if __name__ == "__main__":
    unittest.main()
