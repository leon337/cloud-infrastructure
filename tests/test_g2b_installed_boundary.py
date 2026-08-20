from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "platform/control-bridge/mcf-control-g2b"
SUDOERS = ROOT / "platform/sudoers/mcf-control-g2b"
TMPFILES = ROOT / "platform/tmpfiles.d/mcf-control-bridge-g2b.conf"
MAX_STDIN_BYTES = 131_072


def load_entrypoint():
    loader = importlib.machinery.SourceFileLoader("mcf_control_g2b_entrypoint", str(ENTRYPOINT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("entrypoint loader unavailable")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def request(operation: str = "workspace.write") -> dict[str, object]:
    arguments: dict[str, object]
    if operation == "workspace.write":
        arguments = {
            "path": "G2B-PILOT.txt",
            "content": "bounded\n",
            "precondition": {"state": "ABSENT"},
        }
    else:
        arguments = {}
    return {
        "protocol": "MCF_WORKSPACE_MUTATION_V1",
        "request_id": "G2B-INSTALLED-0001",
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": operation,
        "arguments": arguments,
    }


def envelope(operation: str = "workspace.write") -> dict[str, object]:
    return {
        "transport_principal": {"login": "leon337", "actor_id": 25_374_535},
        "request": request(operation),
    }


class _BinaryInput:
    def __init__(self, value: bytes) -> None:
        self.buffer = io.BytesIO(value)


class G2BInstalledBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_entrypoint()

    def invoke(
        self,
        argv: list[str],
        stdin: bytes,
        *,
        account_uid: int = 4242,
        effective_uid: int = 4242,
        account_error: Exception | None = None,
        executor=None,
        loader_error: BaseException | None = None,
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        if executor is None:
            executor = lambda request_value, **kwargs: {
                "status": "PASS",
                "operation": request_value["operation"],
            }
        account_result = SimpleNamespace(pw_uid=account_uid)
        account_lookup = account_error if account_error is not None else account_result
        if loader_error is None:
            loader_patch = patch.object(
                self.module,
                "_load_execute_request",
                return_value=(
                    executor,
                    lambda *, login, actor_id: SimpleNamespace(login=login, actor_id=actor_id),
                ),
            )
        else:
            loader_patch = patch.object(
                self.module,
                "_load_execute_request",
                side_effect=loader_error,
            )
        with (
            patch.object(self.module.sys, "argv", argv),
            patch.object(self.module.sys, "stdin", _BinaryInput(stdin)),
            patch.object(self.module.sys, "stdout", stdout),
            patch.object(self.module.sys, "stderr", stderr),
            patch.object(
                self.module.pwd,
                "getpwnam",
                side_effect=account_lookup if isinstance(account_lookup, Exception) else None,
                return_value=None if isinstance(account_lookup, Exception) else account_lookup,
            ) as lookup,
            patch.object(self.module.os, "geteuid", return_value=effective_uid),
            loader_patch,
            patch.dict(self.module.os.environ, {"HOSTILE": "request-content-must-not-leak"}, clear=True),
        ):
            code = self.module.main()
        self.account_lookup_calls = list(lookup.call_args_list)
        return code, stdout.getvalue(), stderr.getvalue()

    def assert_boundary_failure(self, code: int, stdout: str, stderr: str) -> dict[str, object]:
        self.assertEqual(code, 2)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout.count("\n"), 1)
        value = json.loads(stdout)
        self.assertIsInstance(value, dict)
        self.assertLessEqual(len(stdout.encode("utf-8")), 8192)
        self.assertNotIn("request-content-must-not-leak", stdout)
        return value

    def stage_installed_bundle(
        self,
        root: Path,
        *,
        assert_isolated_path: bool,
        legacy_scripts: bool = False,
    ) -> tuple[Path, Path]:
        installed = root / "installed"
        shutil.copytree(
            ROOT / "control_plane",
            installed / "control_plane",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        if legacy_scripts:
            scripts = installed / "scripts"
            scripts.mkdir()
            (scripts / "__init__.py").write_text("", encoding="utf-8")
            shutil.copy2(ROOT / "scripts/check_repository_secrets.py", scripts)

        marker = installed / "control_plane/__init__.py"
        marker_text = marker.read_text(encoding="utf-8")
        marker_text += (
            "\nimport sys\n"
            'print("installed-import-stdout")\n'
            'print("installed-import-stderr", file=sys.stderr)\n'
        )
        if assert_isolated_path:
            marker_text += (
                f"assert sys.path[0] == {str(installed)!r}\n"
                "assert not any('site-packages' in value or 'dist-packages' in value "
                "for value in sys.path[1:])\n"
            )
        marker.write_text(marker_text, encoding="utf-8")

        entrypoint = root / "mcf-control-g2b"
        source = ENTRYPOINT.read_text(encoding="utf-8")
        source = source.replace("/usr/local/lib/mcf-control-bridge", str(installed))
        source = source.replace(
            "expected_uid = _resolve_service_uid()",
            "expected_uid = max(os.geteuid(), 1)",
        )
        for original, replacement in (
            ("/etc/mcf-control-bridge/g2b-grant.json", root / "g2b-grant.json"),
            ("/var/lib/mcf-control-bridge/workspaces", root / "workspaces"),
            ("/var/lib/mcf-control-bridge/state/g2b", root / "state"),
            ("/run/lock/mcf-control-bridge-g2b.lock", root / "g2b.lock"),
        ):
            source = source.replace(original, str(replacement))
        entrypoint.write_text(source, encoding="utf-8")
        entrypoint.chmod(0o755)
        self.assertEqual(source.splitlines()[0], "#!/usr/bin/python3 -I")

        (root / "workspaces").mkdir(mode=0o700)
        (root / "state").mkdir(mode=0o700)
        (root / "g2b.lock").touch(mode=0o600)
        (root / "g2b.lock").chmod(0o600)

        ambient = root / "ambient"
        (ambient / "control_plane/g2b").mkdir(parents=True)
        (ambient / "control_plane/__init__.py").write_text(
            'print("ambient-control-plane-stdout")\n', encoding="utf-8"
        )
        (ambient / "control_plane/g2b/__init__.py").write_text("", encoding="utf-8")
        (ambient / "control_plane/g2b/executor.py").write_text(
            'raise SystemExit("ambient-executor-loaded")\n', encoding="utf-8"
        )
        return entrypoint, ambient

    def run_staged_entrypoint(self, entrypoint: Path, ambient: Path) -> subprocess.CompletedProcess:
        child_environment = dict(os.environ)
        child_environment["PYTHONPATH"] = str(ambient)
        child_environment["PYTHONINSPECT"] = "1"
        return subprocess.run(
            [str(entrypoint), "status"],
            cwd=ambient,
            env=child_environment,
            input=json.dumps(envelope("status")).encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=10,
        )

    def test_entrypoint_has_isolated_system_python_shebang_and_fixed_paths(self) -> None:
        text = ENTRYPOINT.read_text(encoding="utf-8")
        lines = text.splitlines()

        self.assertEqual(lines[0], "#!/usr/bin/python3 -I")
        self.assertIn("/usr/local/lib/mcf-control-bridge", text)
        self.assertIn("/etc/mcf-control-bridge/g2b-grant.json", text)
        self.assertIn("/var/lib/mcf-control-bridge/workspaces", text)
        self.assertIn("/var/lib/mcf-control-bridge/state/g2b", text)
        self.assertIn("/run/lock/mcf-control-bridge-g2b.lock", text)

    def test_exact_account_uid_and_fixed_dependencies_reach_executor(self) -> None:
        observed: dict[str, object] = {}

        def executor(request_value, **kwargs):
            observed["request"] = request_value
            observed["environment"] = dict(os.environ)
            observed.update(kwargs)
            return {"status": "PASS", "operation": request_value["operation"]}

        payload = json.dumps(envelope()).encode("utf-8")
        code, stdout, stderr = self.invoke(
            [str(ENTRYPOINT), "execute"], payload, executor=executor
        )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(len(self.account_lookup_calls), 1)
        self.assertEqual(self.account_lookup_calls[0].args, ("mcf-workspace",))
        self.assertEqual(stdout, '{"operation":"workspace.write","status":"PASS"}\n')
        self.assertEqual(json.loads(stdout), {"operation": "workspace.write", "status": "PASS"})
        self.assertEqual(observed["request"], request())
        self.assertEqual(observed["transport_principal"].login, "leon337")
        self.assertEqual(observed["transport_principal"].actor_id, 25_374_535)
        self.assertEqual(observed["grant_path"], Path("/etc/mcf-control-bridge/g2b-grant.json"))
        self.assertEqual(observed["installed_root"], Path("/usr/local/lib/mcf-control-bridge"))
        self.assertEqual(observed["workspace_root"], Path("/var/lib/mcf-control-bridge/workspaces"))
        self.assertEqual(observed["state_root"], Path("/var/lib/mcf-control-bridge/state/g2b"))
        self.assertEqual(observed["lock_path"], Path("/run/lock/mcf-control-bridge-g2b.lock"))
        self.assertEqual(observed["expected_uid"], 4242)
        self.assertEqual(observed["environment"], {})

    def test_missing_service_account_is_a_bootstrap_failure(self) -> None:
        code, stdout, stderr = self.invoke(
            [str(ENTRYPOINT), "status"],
            json.dumps(envelope("status")).encode(),
            account_error=KeyError("mcf-workspace"),
        )

        value = self.assert_boundary_failure(code, stdout, stderr)
        self.assertEqual(value["error"], "service_account_missing")

    def test_root_service_account_and_root_execution_are_refused(self) -> None:
        for account_uid, effective_uid in ((0, 0), (4242, 0)):
            with self.subTest(account_uid=account_uid, effective_uid=effective_uid):
                code, stdout, stderr = self.invoke(
                    [str(ENTRYPOINT), "status"],
                    json.dumps(envelope("status")).encode(),
                    account_uid=account_uid,
                    effective_uid=effective_uid,
                )
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], "root_execution_refused")

    def test_non_service_account_uid_is_refused(self) -> None:
        code, stdout, stderr = self.invoke(
            [str(ENTRYPOINT), "status"],
            json.dumps(envelope("status")).encode(),
            account_uid=4242,
            effective_uid=4243,
        )

        value = self.assert_boundary_failure(code, stdout, stderr)
        self.assertEqual(value["error"], "execution_uid_mismatch")

    def test_only_one_exact_command_argument_is_accepted(self) -> None:
        for argv in (
            [str(ENTRYPOINT)],
            [str(ENTRYPOINT), "execute", "extra"],
            [str(ENTRYPOINT), "workspace.write"],
            [str(ENTRYPOINT), "shell"],
        ):
            with self.subTest(argv=argv):
                code, stdout, stderr = self.invoke(argv, b"{}")
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], "invalid_invocation")

    def test_command_must_match_request_operation(self) -> None:
        for command, operation in (
            ("execute", "rollback"),
            ("rollback", "status"),
            ("status", "revoke"),
            ("revoke", "workspace.write"),
        ):
            with self.subTest(command=command, operation=operation):
                code, stdout, stderr = self.invoke(
                    [str(ENTRYPOINT), command], json.dumps(envelope(operation)).encode()
                )
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], "operation_mismatch")
                self.assertNotIn("bounded", stdout)
                self.assertNotIn("bounded", stderr)

    def test_oversized_and_trailing_stdin_are_rejected(self) -> None:
        valid = json.dumps(envelope("status")).encode()
        for payload, error in (
            (b" " * (MAX_STDIN_BYTES + 1), "stdin_too_large"),
            (valid + b"{}", "invalid_json"),
        ):
            with self.subTest(error=error):
                code, stdout, stderr = self.invoke([str(ENTRYPOINT), "status"], payload)
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], error)

    def test_malformed_or_non_object_json_is_rejected(self) -> None:
        for payload, error in (
            (b'{"request":', "invalid_json"),
            (b"[]", "input_must_be_object"),
            (b'{"request":{}}', "invalid_input_envelope"),
        ):
            with self.subTest(payload=payload):
                code, stdout, stderr = self.invoke([str(ENTRYPOINT), "status"], payload)
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], error)

    def test_output_is_one_compact_bounded_json_object_on_stdout_only(self) -> None:
        result = {"status": "PASS", "value": "x" * 9000}
        code, stdout, stderr = self.invoke(
            [str(ENTRYPOINT), "status"],
            json.dumps(envelope("status")).encode(),
            executor=lambda request_value, **kwargs: result,
        )

        value = self.assert_boundary_failure(code, stdout, stderr)
        self.assertEqual(value["error"], "result_too_large")
        self.assertNotIn(" ", stdout)

    def test_isolated_subprocess_uses_only_staged_application_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            entrypoint, ambient = self.stage_installed_bundle(
                Path(temporary), assert_isolated_path=True
            )

            completed = self.run_staged_entrypoint(entrypoint, ambient)

        self.assertEqual(completed.returncode, 0, completed)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout.count(b"\n"), 1)
        result = json.loads(completed.stdout)
        self.assertIn(result["error"], {"grant_missing", "root_execution_refused"})
        self.assertNotIn(b"installed-import", completed.stdout)
        self.assertNotIn(b"ambient-", completed.stdout)

    def test_application_module_symlink_escape_is_bootstrap_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entrypoint, ambient = self.stage_installed_bundle(
                root,
                assert_isolated_path=False,
                legacy_scripts=True,
            )
            escaped = root / "outside-secret-policy.py"
            escaped.write_text(
                "def content_findings(content, **kwargs):\n    return iter(())\n",
                encoding="utf-8",
            )
            installed_policy = root / "installed/control_plane/g2b/secret_policy.py"
            installed_policy.unlink(missing_ok=True)
            installed_policy.symlink_to(escaped)

            completed = self.run_staged_entrypoint(entrypoint, ambient)

        self.assertEqual(completed.returncode, 2, completed)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(
            json.loads(completed.stdout),
            {"error": "bootstrap_failure", "status": "REFUSED"},
        )
        self.assertNotIn(b"outside-secret-policy", completed.stdout)

    def test_import_and_core_baseexceptions_are_normalized_without_raw_text(self) -> None:
        cases = (
            ("import", SystemExit("raw-import-request-content"), None),
            ("core", None, KeyboardInterrupt("raw-core-request-content")),
            (
                "core-boundary-type",
                None,
                self.module._BoundaryError("raw-core-boundary-request-content"),
            ),
        )
        for source, loader_error, core_error in cases:
            with self.subTest(source=source):
                def executor(request_value, **kwargs):
                    raise core_error  # type: ignore[misc]

                try:
                    code, stdout, stderr = self.invoke(
                        [str(ENTRYPOINT), "status"],
                        json.dumps(envelope("status")).encode("utf-8"),
                        executor=executor,
                        loader_error=loader_error,
                    )
                except BaseException as escaped:
                    self.fail(f"boundary escaped {type(escaped).__name__}")
                value = self.assert_boundary_failure(code, stdout, stderr)
                self.assertEqual(value["error"], "bootstrap_failure")
                self.assertNotIn("raw-", stdout)

    def test_environment_clear_baseexception_is_normalized(self) -> None:
        class ExplodingEnvironment(dict):
            def clear(self) -> None:
                raise SystemExit("raw-environment-request-content")

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            patch.object(self.module.sys, "stdout", stdout),
            patch.object(self.module.sys, "stderr", stderr),
            patch.object(self.module.os, "environ", ExplodingEnvironment()),
        ):
            try:
                code = self.module.main()
            except BaseException as escaped:
                self.fail(f"environment clear escaped {type(escaped).__name__}")

        value = self.assert_boundary_failure(code, stdout.getvalue(), stderr.getvalue())
        self.assertEqual(value["error"], "bootstrap_failure")
        self.assertNotIn("raw-environment", stdout.getvalue())

    def test_sudoers_allows_only_four_exact_non_root_commands(self) -> None:
        text = SUDOERS.read_text(encoding="utf-8")
        logical = text.replace("\\\n", " ")
        commands = [
            "/usr/local/libexec/mcf-control-g2b execute",
            "/usr/local/libexec/mcf-control-g2b rollback",
            "/usr/local/libexec/mcf-control-g2b status",
            "/usr/local/libexec/mcf-control-g2b revoke",
        ]
        logical_lines = logical.splitlines()
        self.assertEqual(len(logical_lines), 2)
        alias_name, alias_body = logical_lines[0].split("=", 1)

        self.assertEqual(alias_name.strip(), "Cmnd_Alias MCF_G2B")
        self.assertEqual([item.strip() for item in alias_body.split(",")], commands)
        self.assertEqual(logical_lines[1], "ubuntu ALL=(mcf-workspace) NOPASSWD: MCF_G2B")
        self.assertNotIn("*", text)
        self.assertNotRegex(text, r"/(?:bin/)?(?:ba|z|c|k)?sh(?:\s|,|$)")
        self.assertNotRegex(text, r"(?:^|/)(?:python(?:3)?|vi|vim|nano|emacs)(?:\s|,|$)")
        self.assertNotRegex(alias_body, r"(?:^|\s)[A-Za-z_][A-Za-z0-9_]*=")
        self.assertNotIn("/usr/bin/env", alias_body)
        self.assertNotRegex(text, r"ALL=\((?:root|ALL)(?::ALL)?\)")

    def test_tmpfiles_creates_only_exact_private_service_lock(self) -> None:
        lines = [
            line.strip()
            for line in TMPFILES.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        self.assertEqual(
            lines,
            ["f /run/lock/mcf-control-bridge-g2b.lock 0600 mcf-workspace mcf-workspace -"],
        )


if __name__ == "__main__":
    unittest.main()
