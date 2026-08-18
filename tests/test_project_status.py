import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "generate_project_status", ROOT / "scripts/generate_project_status.py"
)
STATUS = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(STATUS)


class ProjectStatusTests(unittest.TestCase):
    def test_canonical_state_normalizes_current_progress_and_gates(self):
        status = STATUS.normalized_status()
        self.assertEqual(status["current_slice"], "F1.2c")
        self.assertEqual(status["current_slice_status"], "PARTIAL")
        self.assertEqual(len(status["done"]), 3)
        self.assertEqual(len(status["human_gates"]), 4)

    def test_readme_projection_is_bounded_and_contains_no_secret_fields(self):
        block = STATUS.readme_block(STATUS.normalized_status())
        self.assertTrue(block.startswith(STATUS.START))
        self.assertTrue(block.endswith(STATUS.END))
        self.assertNotIn("password", block.lower())
        self.assertNotIn("token", block.lower())
        self.assertIn("NOT_AUTHORIZED_HUMAN_GATE_REQUIRED", block)

    def test_readme_update_is_idempotent_and_preserves_surrounding_text(self):
        block = STATUS.readme_block(STATUS.normalized_status())
        with tempfile.TemporaryDirectory() as directory:
            readme = pathlib.Path(directory) / "README.md"
            readme.write_text("# Test\n\nbefore\n", encoding="utf-8")
            with mock.patch.object(STATUS, "README", readme):
                STATUS.update_readme(block, check=False)
                first = readme.read_text(encoding="utf-8")
                STATUS.update_readme(block, check=False)
                second = readme.read_text(encoding="utf-8")
            self.assertEqual(first, second)
            self.assertIn("before", second)

    def test_check_mode_rejects_a_stale_projection(self):
        block = STATUS.readme_block(STATUS.normalized_status())
        with tempfile.TemporaryDirectory() as directory:
            readme = pathlib.Path(directory) / "README.md"
            readme.write_text("# Test\n", encoding="utf-8")
            with mock.patch.object(STATUS, "README", readme):
                with self.assertRaisesRegex(ValueError, "stale"):
                    STATUS.update_readme(block, check=True)

    def test_invalid_production_authorization_fails_closed(self):
        current = yaml.safe_load(STATUS.CURRENT.read_text(encoding="utf-8"))
        current["authorization"]["production_promotion"] = "AUTHORIZED"
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "current.yaml"
            path.write_text(yaml.safe_dump(current), encoding="utf-8")
            with mock.patch.object(STATUS, "CURRENT", path):
                with self.assertRaisesRegex(ValueError, "production"):
                    STATUS.normalized_status()

    def test_project_columns_are_only_the_five_visual_states(self):
        rows = STATUS.normalized_status()["slices"]
        allowed = {"TODO", "IN PROGRESS", "HUMAN GATE", "VALIDATING", "DONE"}
        self.assertTrue({row["project_column"] for row in rows} <= allowed)
        self.assertEqual(set(STATUS.PROJECT_COLUMNS.values()), allowed)


if __name__ == "__main__":
    unittest.main()
