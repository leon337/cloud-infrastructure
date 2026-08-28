from pathlib import Path
import socket
import subprocess
import tempfile
import unittest


class RunnerIsolationContractTests(unittest.TestCase):
    def test_runner_isolation_checker_exists(self):
        self.assertTrue(Path("scripts/check_runner_isolation.py").is_file())

    def test_checker_rejects_runner_tracking_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / ".github/workflows/bad.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("run: |\n  unset RUNNER_TRACKING_ID\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", "scripts/check_runner_isolation.py", "--root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RUNNER_ISOLATION_POLICY_FAIL", result.stdout + result.stderr)

    def test_canonical_suite_invokes_runner_isolation_checker(self):
        entrypoint = Path("scripts/test.sh").read_text(encoding="utf-8")
        self.assertIn("check_runner_isolation.py", entrypoint)

    def test_host_runner_isolation_guard_exists(self):
        guard = Path("config/runner/cloud-infrastructure-runner-isolation-guard")
        self.assertTrue(guard.is_file())

    def test_host_guard_removes_legacy_socket_residue(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtime"
            home = root / "home"
            runtime.mkdir()
            home.mkdir()
            sock_path = runtime / "mcf-mission2-terminal.sock"
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(sock_path))
            sock.close()
            result = subprocess.run(
                ["bash", "config/runner/cloud-infrastructure-runner-isolation-guard"],
                check=False,
                capture_output=True,
                text=True,
                env={**__import__("os").environ, "RUNNER_ISOLATION_RUNTIME_DIR": str(runtime), "RUNNER_ISOLATION_HOME": str(home)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(sock_path.exists())
            self.assertIn("RUNNER_ISOLATION_GUARD_PASS", result.stdout)

    def test_checker_rejects_self_hosted_workflow_without_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / ".github/workflows/unguarded.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "jobs:\n  proof:\n    runs-on: [self-hosted, linux, x64]\n    steps:\n      - run: echo ok\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", "scripts/check_runner_isolation.py", "--root", str(root)],
                check=False, capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("self-hosted-workflow-missing-isolation-guard", result.stdout + result.stderr)

    def test_self_hosted_maintenance_proof_enforces_runner_guard(self):
        workflow = Path(".github/workflows/canonical-validation-maintenance-proof.yml").read_text(encoding="utf-8")
        self.assertIn("runner/isolation-", workflow)
        self.assertGreaterEqual(workflow.count("cloud-infrastructure-runner-isolation-guard"), 2)

    def test_cross_job_proof_is_bounded_and_does_not_bypass_tracking(self):
        proof = Path(".github/workflows/runner-isolation-proof.yml")
        self.assertTrue(proof.is_file())
        text = proof.read_text(encoding="utf-8")
        self.assertIn("runner-isolation-probe", text)
        self.assertIn("needs: seed", text)
        self.assertGreaterEqual(text.count("cloud-infrastructure-runner-isolation-guard"), 2)
        self.assertNotIn("RUNNER_TRACKING_ID", text)

    def test_runner_guard_activation_is_documented(self):
        doc = Path("config/runner/README.md")
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("ACTIONS_RUNNER_HOOK_JOB_STARTED", text)
        self.assertIn("ACTIONS_RUNNER_HOOK_JOB_COMPLETED", text)
        self.assertIn("restart", text.lower())


if __name__ == "__main__":
    unittest.main()
