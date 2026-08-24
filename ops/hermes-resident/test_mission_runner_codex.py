import importlib.util
import json
import pathlib
import types
import unittest
from unittest.mock import patch

here = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('mission_runner_under_test', here / 'mission_runner.py')
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

class CodexBrainDiscoveryTest(unittest.TestCase):
    def test_runtime_resolver_can_recover_cli_session_without_logging_secret(self):
        runner = mod.Runner.__new__(mod.Runner)
        runner.discover_hermes_python = lambda: '/usr/bin/python3'
        logs = []
        runner.log = logs.append
        payload = {'usable': True, 'model': 'gpt-test-codex', 'models': ['gpt-test-codex'], 'source': 'hermes-auth-store', 'recovered_cli': True, 'error': None}
        cp = types.SimpleNamespace(returncode=0, stdout=json.dumps(payload) + '\n')
        with patch.object(mod.subprocess, 'run', return_value=cp) as run:
            selected = runner.discover_codex_brain()
        self.assertEqual(selected, 'gpt-test-codex')
        code = run.call_args.args[0][2]
        self.assertIn('resolve_codex_runtime_credentials', code)
        self.assertIn('_recover_codex_tokens_from_cli', code)
        joined = ''.join(logs)
        self.assertNotIn('access_token', joined)
        self.assertNotIn('api_key', joined)

if __name__ == '__main__':
    unittest.main()
