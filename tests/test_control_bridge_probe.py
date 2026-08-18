from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "control_bridge_probe.py"
SPEC = importlib.util.spec_from_file_location("control_bridge_probe", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ControlBridgeProbeTests(unittest.TestCase):
    def test_validate_accepts_probe_request(self):
        request_id, issue_number = MODULE.validate(
            {
                "protocol": MODULE.PROTOCOL,
                "request_id": "CB-PROBE-001",
                "issue_number": 12,
            }
        )
        self.assertEqual(request_id, "CB-PROBE-001")
        self.assertEqual(issue_number, 12)

    def test_validate_rejects_wrong_protocol(self):
        with self.assertRaisesRegex(ValueError, "invalid_protocol"):
            MODULE.validate(
                {"protocol": "WRONG", "request_id": "CB-PROBE-001", "issue_number": 12}
            )

    def test_validate_rejects_missing_issue(self):
        with self.assertRaisesRegex(ValueError, "invalid_issue_number"):
            MODULE.validate(
                {"protocol": MODULE.PROTOCOL, "request_id": "CB-PROBE-001"}
            )

    def test_push_request_loads_from_fixed_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            request_file = root / "probe.json"
            event_file = root / "event.json"
            request_file.write_text(
                json.dumps(
                    {
                        "protocol": MODULE.PROTOCOL,
                        "request_id": "CB-PROBE-002",
                        "issue_number": 99,
                    }
                ),
                encoding="utf-8",
            )
            event_file.write_text("{}", encoding="utf-8")
            loaded = MODULE.load_request("push", event_file, request_file)
            self.assertEqual(loaded["request_id"], "CB-PROBE-002")

    def test_issue_request_requires_probe_title(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            event_file = root / "event.json"
            request_file = root / "unused.json"
            event_file.write_text(
                json.dumps(
                    {
                        "issue": {
                            "number": 7,
                            "title": "ordinary issue",
                            "body": json.dumps(
                                {
                                    "protocol": MODULE.PROTOCOL,
                                    "request_id": "CB-PROBE-003",
                                }
                            ),
                        }
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "issue_title_not_probe"):
                MODULE.load_request("issues", event_file, request_file)

    def test_run_probe_does_not_use_shell(self):
        result = MODULE.run_probe("python", ["python3", "--version"])
        self.assertEqual(result["exit_code"], 0)
        self.assertIn("Python", result["stdout"] or result["stderr"])


if __name__ == "__main__":
    unittest.main()
