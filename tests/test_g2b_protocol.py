from __future__ import annotations

import unittest

from control_plane.g2b.errors import RefusedError
from control_plane.g2b.protocol import (
    MAX_CONTENT_BYTES,
    MUTATION_PROTOCOL,
    OPERATIONS,
    MutationRequest,
    Precondition,
    ProjectKey,
    parse_request,
)


def valid_request() -> dict[str, object]:
    return {
        "protocol": MUTATION_PROTOCOL,
        "request_id": "G2B-TEST-0001",
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": "workspace.write",
        "arguments": {
            "path": "G2B-PILOT.txt",
            "content": "pilot\n",
            "precondition": {"state": "ABSENT"},
        },
    }


class G2BProtocolTests(unittest.TestCase):
    def test_valid_write_normalizes_utf8_content_and_precondition(self):
        request = parse_request(valid_request())

        self.assertIsInstance(request, MutationRequest)
        self.assertEqual(request.protocol, "MCF_WORKSPACE_MUTATION_V1")
        self.assertEqual(request.project, ProjectKey("leon337", "g2a-smoke", "dev"))
        self.assertEqual(request.content, b"pilot\n")
        self.assertEqual(request.precondition, Precondition(state="ABSENT"))
        self.assertIsNone(request.original_request_id)

    def test_only_approved_operations_are_accepted(self):
        self.assertEqual(
            OPERATIONS,
            frozenset({"workspace.write", "rollback", "status", "revoke"}),
        )
        for operation, arguments, original_request_id in (
            ("rollback", {"original_request_id": "G2B-TEST-0001"}, "G2B-TEST-0001"),
            ("status", {}, None),
            ("revoke", {}, None),
        ):
            with self.subTest(operation=operation):
                value = valid_request()
                value["operation"] = operation
                value["arguments"] = arguments
                request = parse_request(value)
                self.assertEqual(request.original_request_id, original_request_id)
                self.assertIsNone(request.path)
                self.assertIsNone(request.content)
                self.assertIsNone(request.precondition)

    def test_request_identity_and_project_are_fixed_and_well_formed(self):
        invalid_values = (
            ("request_id", "g2b-lowercase"),
            ("request_id", "-G2B"),
            ("request_id", "A" * 129),
            ("mission_id", "OTHER"),
            ("declared_actor", "OTHER"),
        )
        for field, value in invalid_values:
            with self.subTest(field=field, value=value):
                candidate = valid_request()
                candidate[field] = value
                self._assert_refused(candidate)

        for project in (
            {"tenant": "A", "name": "g2a-smoke", "environment": "dev"},
            {"tenant": "leon337", "name": "g2a-smoke-", "environment": "dev"},
            {"tenant": "leon337", "name": "g2a-smoke", "environment": "production"},
        ):
            with self.subTest(project=project):
                candidate = valid_request()
                candidate["project"] = project
                self._assert_refused(candidate)

    def test_write_requires_exact_safe_arguments_and_size_limit(self):
        invalid_arguments = (
            {"path": "G2B-PILOT.txt", "content": b"bytes", "precondition": {"state": "ABSENT"}},
            {"path": "G2B-PILOT.txt", "content": "x", "precondition": {"state": "present"}},
            {"path": "G2B-PILOT.txt", "content": "x", "precondition": {"sha256": "A" * 64}},
            {"path": "G2B-PILOT.txt", "content": "x", "precondition": {"state": "ABSENT", "sha256": "a" * 64}},
            {"path": "G2B-PILOT.txt", "content": "x", "precondition": {}},
            {"path": "G2B-PILOT.txt", "content": "x" * (MAX_CONTENT_BYTES + 1), "precondition": {"state": "ABSENT"}},
        )
        for arguments in invalid_arguments:
            with self.subTest(arguments=arguments):
                candidate = valid_request()
                candidate["arguments"] = arguments
                self._assert_refused(candidate)

        sha_request = valid_request()
        sha_request["arguments"] = {
            "path": "G2B-PILOT.txt",
            "content": "next\n",
            "precondition": {"sha256": "a" * 64},
        }
        self.assertEqual(parse_request(sha_request).precondition, Precondition(sha256="a" * 64))

    def test_execution_escape_fields_and_unknown_fields_are_refused(self):
        for forbidden in ("cwd", "argv", "environment", "shell", "command", "sudo_flags"):
            with self.subTest(forbidden=forbidden):
                candidate = valid_request()
                candidate[forbidden] = "untrusted"
                self._assert_refused(candidate, "unexpected_request_field")

        candidate = valid_request()
        arguments = dict(candidate["arguments"])
        arguments["cwd"] = "/"
        candidate["arguments"] = arguments
        self._assert_refused(candidate, "unexpected_arguments_field")

    def _assert_refused(self, value: dict[str, object], code: str | None = None) -> None:
        with self.assertRaises(RefusedError) as caught:
            parse_request(value)
        if code is not None:
            self.assertEqual(caught.exception.code, code)
        self.assertNotIn("pilot", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
