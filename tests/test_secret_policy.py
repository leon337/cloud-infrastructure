from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_repository_secrets", ROOT / "scripts" / "check_repository_secrets.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SecretPolicyTests(unittest.TestCase):
    def test_private_key_material_is_detected(self):
        synthetic = b"-----BEGIN " + b"PRIVATE KEY-----"
        self.assertIsNotNone(CONTENT_RULES["private-key-material"].search(synthetic))

    def test_github_token_is_detected_without_storing_one(self):
        synthetic = b"gh" + b"p_" + (b"A" * 24)
        self.assertIsNotNone(CONTENT_RULES["github-token"].search(synthetic))

    def test_encrypted_private_key_material_is_detected(self):
        synthetic = b"-----BEGIN " + b"ENCRYPTED PRIVATE KEY-----"
        self.assertIsNotNone(CONTENT_RULES["private-key-material"].search(synthetic))

    def test_github_fine_grained_token_is_detected(self):
        synthetic = b"github_" + b"pat_" + (b"A" * 30)
        self.assertIsNotNone(
            CONTENT_RULES["github-fine-grained-token"].search(synthetic)
        )

    def test_jwt_is_detected(self):
        synthetic = b"eyJ" + (b"A" * 16) + b"." + (b"B" * 16) + b"." + (b"C" * 16)
        self.assertIsNotNone(CONTENT_RULES["jwt"].search(synthetic))

    def test_literal_secret_assignment_is_detected(self):
        synthetic = b"DB_CLIENT_" + b"SECRET=ordinary-but-real-value"
        self.assertIsNotNone(CONTENT_RULES["secret-like-assignment"].search(synthetic))

    def test_symbolic_secret_assignment_is_allowed(self):
        synthetic = b"client_" + b"secret=${CLIENT_SECRET}"
        self.assertIsNone(CONTENT_RULES["secret-like-assignment"].search(synthetic))

    def test_disabled_password_status_is_allowed(self):
        synthetic = b"root_" + b"password: DISABLED_AND_NOT_USED_AFTER_BOOTSTRAP"
        self.assertIsNone(CONTENT_RULES["secret-like-assignment"].search(synthetic))

    def test_symbolic_runtime_credential_in_uri_is_allowed(self):
        synthetic = b"https://x-access-token:${RUNTIME_TOKEN}@github.com/example/repository.git"
        self.assertNotIn("credential-in-uri", set(MODULE.content_findings(synthetic)))

    def test_literal_credential_in_uri_remains_blocked(self):
        synthetic = (
            b"https://service-user:"
            + b"literal-password-1234"
            + b"@example.invalid/repository.git"
        )
        self.assertIn("credential-in-uri", set(MODULE.content_findings(synthetic)))

    def test_known_historical_diagnostic_assignment_is_exactly_allowlisted(self):
        synthetic = b'password = match.group("password").lower()'
        findings = set(
            MODULE.content_findings(
                synthetic,
                allowed_assignment_line_hashes=frozenset(
                    MODULE.HISTORICAL_NON_SECRET_ASSIGNMENT_LINE_SHA256
                ),
            )
        )
        self.assertNotIn("secret-like-assignment", findings)

    def test_only_an_explicit_line_hash_can_allowlist_historical_status(self):
        synthetic = b"root_" + b"password: reviewed-historical-status"
        line_hash = hashlib.sha256(synthetic).hexdigest()
        self.assertEqual(
            list(
                MODULE.content_findings(
                    synthetic,
                    allowed_assignment_line_hashes=frozenset({line_hash}),
                )
            ),
            [],
        )
        self.assertEqual(list(MODULE.content_findings(synthetic)), ["secret-like-assignment"])

    def test_secret_fixture_sources_do_not_embed_scannable_secret_shapes(self):
        for relative in (
            "tests/test_control_bridge_g2a_adapter.py",
            "tests/test_g2a_protected_reader.py",
        ):
            with self.subTest(relative=relative):
                findings = list(MODULE.content_findings((ROOT / relative).read_bytes()))
                self.assertEqual(findings, [])

    def test_reviewed_historical_synthetic_fixture_exceptions_are_exact(self):
        expected = {
            "1a4107d50e291c3f3230c237c990f5724da4fc1e": frozenset(
                {"github-token", "secret-like-assignment"}
            ),
            "a37f59b70d74e0d072751b6a6047a274f78346c3": frozenset(
                {"private-key-material", "aws-access-key", "credential-in-uri"}
            ),
        }
        self.assertEqual(
            getattr(MODULE, "HISTORICAL_SYNTHETIC_TEST_BLOB_RULES", None),
            expected,
        )
        helper = getattr(MODULE, "historical_content_findings", None)
        self.assertIsNotNone(helper)
        if helper is None:
            return
        for object_id in expected:
            content = subprocess.run(
                ["git", "cat-file", "blob", object_id],
                cwd=ROOT, check=True, capture_output=True,
            ).stdout
            self.assertEqual(list(helper(object_id, content)), [])
            injected = content + b"\n" + b"sk-" + (b"A" * 24) + b"\n"
            self.assertIn("openai-token", set(helper(object_id, injected)))

    def test_secret_bearing_paths_are_detected(self):
        self.assertTrue(MODULE.path_is_forbidden("local/.env"))
        self.assertTrue(MODULE.path_is_forbidden("keys/id_ed25519"))

    def test_env_example_and_public_pem_paths_are_allowed(self):
        self.assertFalse(MODULE.path_is_forbidden("examples/.env.example"))
        self.assertFalse(MODULE.path_is_forbidden("certificates/public-chain.pem"))

    def test_history_modes_cover_merge_ancestry_unrelated_refs_and_worktree(self):
        with tempfile.TemporaryDirectory() as temporary:
            repository = pathlib.Path(temporary) / "repository"
            self._git(repository.parent, "init", "-b", "main", repository.name)
            self._git(repository, "config", "user.name", "Secret Policy Test")
            self._git(repository, "config", "user.email", "test@example.invalid")

            (repository / "root.txt").write_text("root\n", encoding="utf-8")
            self._git(repository, "add", "root.txt")
            self._git(repository, "commit", "-m", "root")
            root_revision = self._git(repository, "rev-parse", "HEAD").strip()

            self._git(repository, "switch", "-c", "merged-side")
            (repository / "merged.txt").write_text("merged\n", encoding="utf-8")
            self._git(repository, "add", "merged.txt")
            self._git(repository, "commit", "-m", "merged side")
            merged_blob = self._git(repository, "hash-object", "merged.txt").strip()

            self._git(repository, "switch", "main")
            (repository / "main.txt").write_text("main\n", encoding="utf-8")
            self._git(repository, "add", "main.txt")
            self._git(repository, "commit", "-m", "main")
            self._git(repository, "merge", "--no-ff", "merged-side", "-m", "merge")

            self._git(repository, "switch", "-c", "unrelated", root_revision)
            unrelated_secret = b"DB_CLIENT_" + b"SECRET=ordinary-but-real-value\n"
            (repository / "unrelated.txt").write_bytes(unrelated_secret)
            self._git(repository, "add", "unrelated.txt")
            self._git(repository, "commit", "-m", "unrelated")
            unrelated_blob = self._git(
                repository, "hash-object", "unrelated.txt"
            ).strip()
            self._git(repository, "switch", "main")

            current_secret = b"CURRENT_CLIENT_" + b"SECRET=ordinary-but-real-value\n"
            (repository / "current.txt").write_bytes(current_secret)

            candidate_blobs = {
                object_id
                for object_id, _ in MODULE.reachable_history_blobs(
                    repository_root=repository,
                    revision="HEAD",
                )
            }
            all_ref_blobs = {
                object_id
                for object_id, _ in MODULE.reachable_history_blobs(
                    repository_root=repository,
                    all_refs=True,
                )
            }
            self.assertIn(merged_blob, candidate_blobs)
            self.assertNotIn(unrelated_blob, candidate_blobs)
            self.assertIn(unrelated_blob, all_ref_blobs)

            candidate_findings = MODULE.scan(
                repository_root=repository,
                revision="HEAD",
            )
            all_ref_findings = MODULE.scan(
                repository_root=repository,
                all_refs=True,
            )
            self.assertIn(("current.txt", "secret-like-assignment"), candidate_findings)
            unrelated_finding = (
                f"<git-history-blob:{unrelated_blob[:12]}>",
                "secret-like-assignment",
            )
            self.assertNotIn(unrelated_finding, candidate_findings)
            self.assertIn(unrelated_finding, all_ref_findings)
            with self.assertRaisesRegex(ValueError, "exactly one history scope"):
                list(MODULE.reachable_history_blobs(repository_root=repository))

    def test_repository_gate_declares_candidate_head_scope(self):
        gate = (ROOT / "scripts/test.sh").read_text(encoding="utf-8")
        self.assertIn(
            '"$PYTHON" scripts/check_repository_secrets.py --revision HEAD',
            gate,
        )
        self.assertNotIn("check_repository_secrets.py --all-refs", gate)

    @staticmethod
    def _git(repository: pathlib.Path, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return completed.stdout


CONTENT_RULES = MODULE.CONTENT_RULES
FORBIDDEN_PATH_PATTERNS = MODULE.FORBIDDEN_PATH_PATTERNS


if __name__ == "__main__":
    unittest.main()
