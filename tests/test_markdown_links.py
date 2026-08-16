from __future__ import annotations

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_markdown_links", ROOT / "scripts" / "check_markdown_links.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MarkdownLinkTests(unittest.TestCase):
    def test_reference_style_links_are_discovered(self):
        self.assertEqual(
            list(MODULE.markdown_targets("[entry]: <CONTEXT.md>\n")),
            ["CONTEXT.md"],
        )

    def test_repository_escape_is_rejected(self):
        error = MODULE.local_target_error(ROOT / "README.md", "../../etc/passwd")
        self.assertEqual(error, "target escapes repository root")

    def test_existing_repository_link_is_accepted(self):
        self.assertIsNone(
            MODULE.local_target_error(ROOT / "README.md", "CONTEXT.md#protocolo")
        )


if __name__ == "__main__":
    unittest.main()
