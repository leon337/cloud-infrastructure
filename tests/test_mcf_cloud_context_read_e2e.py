from __future__ import annotations

import pathlib
import unittest

from scripts import run_mcf_cloud_context_read_e2e as e2e


ROOT = pathlib.Path(__file__).resolve().parents[1]


class McfCloudContextReadE2ETests(unittest.TestCase):
    def test_fixture_client_uses_exact_one_line_contract(self):
        client = e2e._load_client()
        self.assertEqual(
            client.REQUEST_LINE,
            '{"protocol":"MCF_CLOUD_CONTEXT_READ_V1",'
            '"request_id":"MCF-CLOUD-G2A-E2E-20260823",'
            '"project_id":"cloud-infrastructure",'
            '"operation":"context.get","arguments":{}}\n',
        )
        self.assertEqual(
            tuple(client.ADAPTER_COMMAND[1:]),
            ("-I", "platform/control-bridge/mcf-cloud-context-read"),
        )

    def test_harness_is_disposable_and_has_complete_ordered_markers(self):
        text = (ROOT / "scripts/run_mcf_cloud_context_read_e2e.py").read_text(
            encoding="utf-8"
        )
        positions = [text.index(marker) for marker in e2e.MARKERS]
        self.assertEqual(positions, sorted(positions))
        self.assertIn('tempfile.mkdtemp(prefix="mcf-cloud-context-e2e-")', text)
        self.assertIn('temporary_root / "workspaces/leon337/g2a-smoke/dev"', text)
        self.assertIn("shutil.rmtree(temporary_root)", text)
        self.assertNotIn("node-01", text.lower())
        self.assertNotIn("vmi3506102", text.lower())

    def test_disposable_mcf_client_to_local_cloud_adapter_e2e(self):
        markers, result = e2e.run_e2e()
        self.assertEqual(markers, list(e2e.MARKERS))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(
            result["result"]["mapping"]["canonical_cloud_key"],
            "leon337/g2a-smoke/dev",
        )
        self.assertEqual(
            result["freshness"]["workspace_observation"],
            "LIVE_LOCAL_DISPOSABLE",
        )
        self.assertEqual(len(result["provenance"]["sources"]), 13)


if __name__ == "__main__":
    unittest.main()
