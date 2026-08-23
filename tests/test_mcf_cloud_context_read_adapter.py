from __future__ import annotations

import ast
import copy
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import jsonschema

from control_plane.g2a import local_context_adapter as adapter


ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / adapter.ADAPTER_CLI_PATH
CONFIG = ROOT / adapter.CONFIG_PATH
CONFIG_SCHEMA = ROOT / adapter.CONFIG_SCHEMA_PATH
RESULT_SCHEMA = ROOT / adapter.RESULT_SCHEMA_PATH

VALID_REQUEST = {
    "protocol": adapter.REQUEST_PROTOCOL,
    "request_id": "MCF-LAB-CONTEXT-001",
    "project_id": adapter.PROJECT_ID,
    "operation": adapter.OPERATION,
    "arguments": {},
}


def load_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


class DisposableRepository:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = (
            pathlib.Path(self.temporary.name)
            / "workspaces"
            / "leon337"
            / "g2a-smoke"
            / "dev"
        )
        self.root.mkdir(parents=True)
        for relative in adapter.PROVENANCE_PATHS:
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in (
            "control_plane/__init__.py",
            "control_plane/g2a/__init__.py",
            "scripts/yaml_strict.py",
        ):
            source = ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def close(self):
        self.temporary.cleanup()


class McfCloudContextReadAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = DisposableRepository()
        self.schema = load_json(RESULT_SCHEMA)
        self.validator = jsonschema.Draft202012Validator(
            self.schema,
            format_checker=jsonschema.FormatChecker(),
        )

    def tearDown(self):
        self.fixture.close()

    def execute(self, request=None, *, enabled=True):
        return adapter.execute_local_context_read(
            request if request is not None else copy.deepcopy(VALID_REQUEST),
            repository_root=self.fixture.root,
            enabled=enabled,
        )

    def test_disabled_by_default_refuses_before_reading_sources(self):
        with mock.patch.object(
            adapter,
            "_read_confined_file",
            side_effect=AssertionError("disabled adapter read a source"),
        ):
            result = self.execute(enabled=False)
        self.validator.validate(result)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error"], {"code": "adapter_disabled"})
        self.assertEqual(result["provenance"]["sources"], [])
        self.assertEqual(result["freshness"]["workspace_observation"], "NOT_OBSERVED")
        self.assertFalse(adapter.enabled_from_environment({}))
        with self.assertRaisesRegex(adapter.AdapterError, "invalid_enable_value"):
            adapter.enabled_from_environment({adapter.ENABLE_ENVIRONMENT: "1"})

    def test_exact_context_get_returns_strict_read_only_projection(self):
        result = self.execute()
        self.validator.validate(result)
        self.assertEqual(result["status"], "PASS")
        self.assertIsNone(result["error"])
        self.assertEqual(
            result["result"]["mapping"]["cloud_project_key"],
            {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        )
        self.assertEqual(result["result"]["workspace"]["state"], "PRESENT")
        self.assertEqual(result["result"]["control_bridge"]["g2a"]["operational_freshness"], "LIVE_REQUIRED")
        self.assertEqual(result["result"]["control_bridge"]["g2b"]["lifecycle"], "LAB_VALIDATED_INACTIVE")
        self.assertEqual(
            result["result"]["adapter"],
            {
                "transport": "STDIO",
                "operation": "context.get",
                "enabled_by_default": False,
                "read_only": True,
                "network_access": False,
                "external_process": False,
                "arbitrary_path": False,
            },
        )
        self.assertEqual(
            {item["path"] for item in result["provenance"]["sources"]},
            set(adapter.PROVENANCE_PATHS),
        )

    def test_request_contract_rejects_extra_fields_paths_and_operations(self):
        cases = []
        extra = copy.deepcopy(VALID_REQUEST)
        extra["path"] = "/etc"
        cases.append((extra, "unexpected_request_field"))
        wrong_operation = copy.deepcopy(VALID_REQUEST)
        wrong_operation["operation"] = "workspace.read"
        cases.append((wrong_operation, "unknown_operation"))
        arguments = copy.deepcopy(VALID_REQUEST)
        arguments["arguments"] = {"path": "state/current.yaml"}
        cases.append((arguments, "invalid_arguments"))
        project = copy.deepcopy(VALID_REQUEST)
        project["project_id"] = "g2a-smoke"
        cases.append((project, "invalid_project_id"))

        for request, code in cases:
            with self.subTest(code=code):
                result = self.execute(request)
                self.validator.validate(result)
                self.assertEqual(result["status"], "REFUSED")
                self.assertEqual(result["error"], {"code": code})

    def test_input_is_bounded_utf8_unique_key_json(self):
        encoded = json.dumps(VALID_REQUEST, separators=(",", ":")).encode("utf-8")
        self.assertEqual(adapter.decode_request(encoded), VALID_REQUEST)
        for raw, code in (
            (b"{}\x00", "invalid_json"),
            (b'{"protocol":"a","protocol":"b"}', "invalid_json"),
            (b"[1]", "request_must_be_object"),
            (b"x" * (adapter.MAX_INPUT_BYTES + 1), "request_too_large"),
        ):
            with self.subTest(code=code):
                with self.assertRaisesRegex(adapter.AdapterError, code):
                    adapter.decode_request(raw)

    def test_wrong_layout_or_symlinked_source_fails_closed(self):
        wrong_layout = adapter.execute_local_context_read(
            copy.deepcopy(VALID_REQUEST),
            repository_root=ROOT,
            enabled=True,
        )
        self.validator.validate(wrong_layout)
        self.assertEqual(wrong_layout["error"], {"code": "repository_layout_refused"})

        source = self.fixture.root / "context/mcf-cloud-context.yaml"
        external = pathlib.Path(self.fixture.temporary.name) / "external.yaml"
        external.write_text("secret: must-not-appear\n", encoding="utf-8")
        source.unlink()
        source.symlink_to(external)
        refused = self.execute()
        self.validator.validate(refused)
        self.assertEqual(refused["error"], {"code": "source_boundary_refused"})
        self.assertNotIn("must-not-appear", json.dumps(refused))

    def test_tampered_contract_is_refused_without_echo(self):
        source = self.fixture.root / "context/mcf-cloud-context.yaml"
        text = source.read_text(encoding="utf-8")
        source.write_text(
            text.replace("lifecycle: LAB_VALIDATED_INACTIVE", "lifecycle: ACTIVE"),
            encoding="utf-8",
        )
        result = self.execute()
        self.validator.validate(result)
        self.assertEqual(result["error"], {"code": "source_contract_invalid"})
        self.assertNotIn("ACTIVE", json.dumps(result))

    def test_config_and_result_schemas_are_strict_draft_2020_12(self):
        config_schema = load_json(CONFIG_SCHEMA)
        result_schema = load_json(RESULT_SCHEMA)
        for schema in (config_schema, result_schema):
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            jsonschema.Draft202012Validator.check_schema(schema)
            self.assertFalse(schema["additionalProperties"])

        invalid = self.execute()
        invalid["unexpected"] = True
        self.assertTrue(list(self.validator.iter_errors(invalid)))

    def test_cli_is_one_line_stdio_with_no_arguments_or_default_activation(self):
        request = json.dumps(VALID_REQUEST, separators=(",", ":"))
        environment = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            adapter.ENABLE_ENVIRONMENT: adapter.ENABLE_VALUE,
        }
        completed = subprocess.run(
            [sys.executable, "-I", str(self.fixture.root / adapter.ADAPTER_CLI_PATH)],
            input=request,
            text=True,
            capture_output=True,
            cwd=self.fixture.root,
            env=environment,
            timeout=20,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        result = json.loads(completed.stdout)
        self.validator.validate(result)
        self.assertEqual(result["status"], "PASS")

        disabled = subprocess.run(
            [sys.executable, "-I", str(self.fixture.root / adapter.ADAPTER_CLI_PATH)],
            input=request,
            text=True,
            capture_output=True,
            cwd=self.fixture.root,
            env={"PATH": environment["PATH"]},
            timeout=20,
            check=False,
        )
        self.assertEqual(disabled.returncode, 2)
        self.assertEqual(json.loads(disabled.stdout)["error"], {"code": "adapter_disabled"})

    def test_adapter_has_no_network_subprocess_shell_or_write_surface(self):
        for path in (ROOT / adapter.ADAPTER_MODULE_PATH, CLI):
            text = path.read_text(encoding="utf-8")
            tree = ast.parse(text)
            imported = {
                alias.name.split(".")[0]
                for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom))
                for alias in node.names
            }
            calls = {
                node.func.attr
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            }
            self.assertTrue(
                imported.isdisjoint({"socket", "subprocess", "urllib", "http", "requests"}),
                (path, imported),
            )
            self.assertTrue(
                calls.isdisjoint(
                    {
                        "write_text",
                        "write_bytes",
                        "touch",
                        "unlink",
                        "remove",
                        "rename",
                        "mkdir",
                        "rmdir",
                        "chmod",
                        "chown",
                        "symlink_to",
                    }
                ),
                (path, calls),
            )
            for forbidden in (
                ".write_text(",
                ".write_bytes(",
                "os.system(",
                "shell=True",
                "ssh ",
                "curl ",
            ):
                self.assertNotIn(forbidden, text, (path, forbidden))

        cli_text = CLI.read_text(encoding="utf-8")
        self.assertIn("sys.dont_write_bytecode = True", cli_text)
        self.assertIn("sys.addaudithook(_read_only_audit_hook)", cli_text)
        self.assertIn('"subprocess.Popen"', cli_text)
        self.assertIn('"socket.connect"', cli_text)
        self.assertIn("_WRITE_OPEN_FLAGS", cli_text)


if __name__ == "__main__":
    unittest.main()
