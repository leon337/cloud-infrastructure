from __future__ import annotations

import hashlib
import importlib.util
import pathlib
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

    def test_secret_bearing_paths_are_detected(self):
        self.assertTrue(MODULE.path_is_forbidden("local/.env"))
        self.assertTrue(MODULE.path_is_forbidden("keys/id_ed25519"))

    def test_env_example_and_public_pem_paths_are_allowed(self):
        self.assertFalse(MODULE.path_is_forbidden("examples/.env.example"))
        self.assertFalse(MODULE.path_is_forbidden("certificates/public-chain.pem"))


CONTENT_RULES = MODULE.CONTENT_RULES
FORBIDDEN_PATH_PATTERNS = MODULE.FORBIDDEN_PATH_PATTERNS


if __name__ == "__main__":
    unittest.main()
