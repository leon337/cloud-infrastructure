from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_repository_secrets as scanner


class SecretPolicyBehaviorTests(unittest.TestCase):
    def test_symbolic_runtime_credential_in_uri_is_not_a_secret(self):
        content = b"https://x-access-token:${RUNTIME_TOKEN}@github.com/example/repository.git"
        findings = set(scanner.content_findings(content))
        self.assertNotIn("credential-in-uri", findings)

    def test_literal_credential_in_uri_remains_blocked(self):
        content = (
            b"https://service-user:"
            + b"literal-password-1234"
            + b"@example.invalid/repository.git"
        )
        findings = set(scanner.content_findings(content))
        self.assertIn("credential-in-uri", findings)

    def test_known_historical_diagnostic_assignment_is_exactly_allowlisted(self):
        content = b'password = match.group("password").lower()'
        findings = set(
            scanner.content_findings(
                content,
                allowed_assignment_line_hashes=frozenset(
                    scanner.HISTORICAL_NON_SECRET_ASSIGNMENT_LINE_SHA256
                ),
            )
        )
        self.assertNotIn("secret-like-assignment", findings)


if __name__ == "__main__":
    unittest.main()
