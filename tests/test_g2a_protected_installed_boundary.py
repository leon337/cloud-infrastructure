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
ENTRYPOINT = ROOT / "platform/control-bridge/mcf-control-g2a-protected-read"
MAX_STDIN_BYTES = 131_072
MAX_RESULT_BYTES = 131_072
VALID_REQUEST = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-PROTECTED-INSTALLED-001",
    "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
    "operation": "workspace.read",
    "arguments": {"path": "G2B-PILOT.txt"},
}


def load_entrypoint():
    loader = importlib.machinery.SourceFileLoader("g2a_protected_entrypoint", str(ENTRYPOINT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    if spec is None:
        raise AssertionError("entrypoint loader unavailable")
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class _BinaryInput:
    def __init__(self, value: bytes) -> None:
        self.buffer = io.BytesIO(value)


class G2AProtectedInstalledBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_entrypoint()

    def invoke(
        self, argv, stdin, *, account_uid=4242, effective_uid=4242,
        account_error=None, executor=None, loader_error=None,
    ):
        stdout, stderr = io.StringIO(), io.StringIO()
        observed = {}
        if executor is None:
            def executor(value):
                observed["request"] = value
                observed["environment"] = dict(os.environ)
                return SimpleNamespace(result={"status": "PASS", "operation": value["operation"]})
        loader = (patch.object(self.module, "_load_execute_protected", side_effect=loader_error)
                  if loader_error is not None else
                  patch.object(self.module, "_load_execute_protected", return_value=executor))
        account = SimpleNamespace(pw_uid=account_uid)
        with (
            patch.object(self.module.sys, "argv", argv),
            patch.object(self.module.sys, "stdin", _BinaryInput(stdin)),
            patch.object(self.module.sys, "stdout", stdout),
            patch.object(self.module.sys, "stderr", stderr),
            patch.object(self.module.pwd, "getpwnam",
                         side_effect=account_error,
                         return_value=None if account_error else account) as lookup,
            patch.object(self.module.os, "geteuid", return_value=effective_uid),
            patch.dict(self.module.os.environ, {"PYTHONPATH": "/hostile", "SECRET": "must-not-leak"}, clear=True),
            loader,
        ):
            code = self.module.main()
        return code, stdout.getvalue(), stderr.getvalue(), observed, lookup.call_args_list

    def assert_one_json(self, code, stdout, stderr, *, expected_exit=None):
        if expected_exit is not None:
            self.assertEqual(code, expected_exit)
        self.assertEqual(stderr, "")
        self.assertEqual(stdout.count("\n"), 1)
        self.assertTrue(stdout.endswith("\n"))
        self.assertLessEqual(len(stdout.encode()), MAX_RESULT_BYTES)
        value = json.loads(stdout)
        self.assertIsInstance(value, dict)
        self.assertNotIn("must-not-leak", stdout)
        return value

    def assert_failure(self, result, code):
        self.assertEqual(result, {"status": "REFUSED", "error": {"code": code}})

    def test_isolated_shebang_fixed_root_and_zero_argument_contract(self):
        text = ENTRYPOINT.read_text(encoding="utf-8")
        self.assertEqual(text.splitlines()[0], "#!/usr/bin/python3 -I")
        self.assertIn("/usr/local/lib/mcf-control-bridge-g2a-protected", text)
        self.assertNotIn("/usr/local/lib/mcf-control-bridge\"", text)
        for argv in ([str(ENTRYPOINT), "extra"], [str(ENTRYPOINT), "workspace.read"]):
            code, out, err, _, _ = self.invoke(argv, json.dumps(VALID_REQUEST).encode())
            self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), "invalid_invocation")

    def test_exact_service_identity_and_hostile_environment_is_cleared(self):
        code, out, err, observed, calls = self.invoke(
            [str(ENTRYPOINT)], json.dumps(VALID_REQUEST).encode())
        self.assertEqual(self.assert_one_json(code, out, err, expected_exit=0)["status"], "PASS")
        self.assertEqual(calls[0].args, ("mcf-workspace",))
        self.assertEqual(observed["request"], VALID_REQUEST)
        self.assertEqual(observed["environment"], {})

    def test_missing_account_root_and_wrong_euid_fail_closed(self):
        cases = (
            ({"account_error": KeyError("missing")}, "service_account_missing"),
            ({"account_uid": 0, "effective_uid": 0}, "root_execution_refused"),
            ({"account_uid": 4242, "effective_uid": 0}, "root_execution_refused"),
            ({"account_uid": 4242, "effective_uid": 4243}, "execution_uid_mismatch"),
        )
        for kwargs, expected in cases:
            with self.subTest(expected=expected):
                code, out, err, _, _ = self.invoke([str(ENTRYPOINT)], b"{}", **kwargs)
                self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), expected)

    def test_oversized_trailing_malformed_and_non_object_stdin(self):
        valid = json.dumps(VALID_REQUEST).encode()
        cases = (
            (b" " * (MAX_STDIN_BYTES + 1), "stdin_too_large"),
            (valid + b"{}", "invalid_json"),
            (b'{"request":', "invalid_json"),
            (b"\xff", "invalid_json"),
            (b"[]", "input_must_be_object"),
            (b'"object"', "input_must_be_object"),
        )
        for payload, expected in cases:
            with self.subTest(expected=expected):
                code, out, err, _, _ = self.invoke([str(ENTRYPOINT)], payload)
                self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), expected)

    def test_invalid_or_oversized_result_is_one_bounded_failure(self):
        for result, expected in (
            ([], "invalid_result"),
            ({"value": object()}, "invalid_result"),
            ({"value": "x" * MAX_RESULT_BYTES}, "result_too_large"),
        ):
            def executor(_request, result=result):
                return SimpleNamespace(result=result)
            code, out, err, _, _ = self.invoke(
                [str(ENTRYPOINT)], json.dumps(VALID_REQUEST).encode(), executor=executor)
            self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), expected)

    def stage_bundle(self, root: Path, *, symlink=False, noisy=False, core_failure=False):
        installed = root / "installed"
        shutil.copytree(ROOT / "control_plane", installed / "control_plane",
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        marker = installed / "control_plane/__init__.py"
        marker.write_text(marker.read_text() + "\nimport os,sys\nprint('installed-noise')\n"
                          + ("os.write(1,b'fd-noise\\n');os.write(2,b'fd-noise\\n')\n" if noisy else ""))
        protected = installed / "control_plane/g2a/protected_reader.py"
        if core_failure:
            protected.write_text(protected.read_text() +
                "\n_original=execute_protected\ndef execute_protected(value):\n"
                " os.write(1,b'core-noise\\n');os.write(2,b'core-noise\\n')\n"
                " raise SystemExit('raw-core-secret')\n")
        if symlink:
            outside = root / "outside.py"
            outside.write_text("raise SystemExit('outside-loaded')\n")
            protected.unlink()
            protected.symlink_to(outside)
        source = ENTRYPOINT.read_text().replace(
            "/usr/local/lib/mcf-control-bridge-g2a-protected", str(installed))
        source = source.replace("expected_uid = _resolve_service_uid()",
                                "expected_uid = max(os.geteuid(), 1)")
        staged = root / "mcf-control-g2a-protected-read"
        staged.write_text(source)
        staged.chmod(0o755)
        ambient = root / "ambient"
        (ambient / "control_plane/g2a").mkdir(parents=True)
        (ambient / "control_plane/__init__.py").write_text("print('ambient-loaded')\n")
        (ambient / "control_plane/g2a/__init__.py").write_text("")
        (ambient / "control_plane/g2a/protected_reader.py").write_text(
            "raise SystemExit('ambient-reader-loaded')\n")
        return staged, ambient

    def run_staged(self, staged, ambient):
        env = dict(os.environ)
        env.update(PYTHONPATH=str(ambient), PYTHONINSPECT="1", SECRET="must-not-leak")
        return subprocess.run([str(staged)], cwd=ambient, env=env,
            input=json.dumps(VALID_REQUEST).encode(), capture_output=True,
            check=False, timeout=10)

    def test_ambient_injection_is_ignored_and_import_output_is_suppressed(self):
        with tempfile.TemporaryDirectory() as temporary:
            staged, ambient = self.stage_bundle(Path(temporary), noisy=True)
            completed = self.run_staged(staged, ambient)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout.count(b"\n"), 1)
        self.assertNotIn(b"ambient", completed.stdout)
        self.assertNotIn(b"noise", completed.stdout)
        self.assertNotIn(b"must-not-leak", completed.stdout)
        self.assertIsInstance(json.loads(completed.stdout), dict)

    def test_symlinked_installed_module_is_bootstrap_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            staged, ambient = self.stage_bundle(Path(temporary), symlink=True)
            completed = self.run_staged(staged, ambient)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, b"")
        self.assertEqual(completed.stdout.count(b"\n"), 1)
        self.assert_failure(json.loads(completed.stdout), "bootstrap_failure")
        self.assertNotIn(b"outside", completed.stdout)

    def test_import_and_core_baseexceptions_are_content_free(self):
        payload = json.dumps(VALID_REQUEST).encode()
        for failure in (SystemExit("raw-import-secret"), KeyboardInterrupt("raw-import-secret")):
            code, out, err, _, _ = self.invoke([str(ENTRYPOINT)], payload, loader_error=failure)
            self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), "bootstrap_failure")
            self.assertNotIn("raw-", out)
        for failure in (SystemExit("raw-core-secret"), KeyboardInterrupt("raw-core-secret")):
            def executor(_request, failure=failure):
                raise failure
            code, out, err, _, _ = self.invoke([str(ENTRYPOINT)], payload, executor=executor)
            self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), "bootstrap_failure")
            self.assertNotIn("raw-", out)

    def test_environment_clear_baseexception_is_normalized(self):
        class ExplodingEnvironment(dict):
            def clear(self):
                raise SystemExit("raw-environment-secret")
        stdout, stderr = io.StringIO(), io.StringIO()
        with (patch.object(self.module.sys, "stdout", stdout),
              patch.object(self.module.sys, "stderr", stderr),
              patch.object(self.module.os, "environ", ExplodingEnvironment())):
            code = self.module.main()
        self.assert_failure(self.assert_one_json(code, stdout.getvalue(), stderr.getvalue(), expected_exit=2),
                            "bootstrap_failure")

    def test_descriptor_cleanup_on_success_and_failure(self):
        fd_root = Path("/proc/self/fd")
        if not fd_root.is_dir():
            self.skipTest("descriptor accounting requires /proc/self/fd")
        before = set(fd_root.iterdir())
        payload = json.dumps(VALID_REQUEST).encode()
        for loader_error in (None, SystemExit("raw-loader-secret")):
            code, out, err, _, _ = self.invoke(
                [str(ENTRYPOINT)], payload, loader_error=loader_error)
            self.assert_one_json(code, out, err)
        self.assertEqual(set(fd_root.iterdir()), before)

    def test_descriptor_faults_fail_closed_without_leaks_or_noise(self):
        original_open, original_close = os.open, os.close
        boundary_fd = None
        failed = False
        def tracked_open(path, flags, *args, **kwargs):
            nonlocal boundary_fd
            descriptor = original_open(path, flags, *args, **kwargs)
            if path == os.devnull:
                boundary_fd = descriptor
            return descriptor
        def fault_close(descriptor):
            nonlocal failed
            if descriptor == boundary_fd and not failed:
                failed = True
                raise OSError("raw-close-secret")
            return original_close(descriptor)
        before = set(Path("/proc/self/fd").iterdir()) if Path("/proc/self/fd").is_dir() else None
        with (patch.object(self.module.os, "open", side_effect=tracked_open),
              patch.object(self.module.os, "close", side_effect=fault_close)):
            code, out, err, _, _ = self.invoke([str(ENTRYPOINT)], json.dumps(VALID_REQUEST).encode())
        self.assert_failure(self.assert_one_json(code, out, err, expected_exit=2), "bootstrap_failure")
        self.assertNotIn("raw-", out)
        self.assertTrue(failed)
        if before is not None:
            self.assertEqual(set(Path("/proc/self/fd").iterdir()), before)


if __name__ == "__main__":
    unittest.main()
