from __future__ import annotations

import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
HARNESS = ROOT / "scripts/test_node_network_services_vm.sh"


class JournalEvidencePipefailTests(unittest.TestCase):
    def test_journal_evidence_checks_consume_full_stream(self):
        text = HARNESS.read_text()

        unsafe = "grep -q 'NETWORK_SERVICES_APPLY=PASS changed=1'"
        safe = "grep -F 'NETWORK_SERVICES_APPLY=PASS changed=1' >/dev/null"

        self.assertNotIn(unsafe, text)
        self.assertEqual(text.count(safe), 2)


if __name__ == "__main__":
    unittest.main()
