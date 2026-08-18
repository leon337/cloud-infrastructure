from __future__ import annotations

import unittest

from control_plane.g2a.errors import RefusedError
from control_plane.g2a.protocol import (
    CORE_PROTOCOL,
    OPERATIONS,
    CoreRequest,
    ProjectKey,
    parse_request,
)


VALID = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-000001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "git.status",
    "arguments": {},
}


class G2AProtocolTests(unittest.TestCase):
    def test_valid_request_parses_without_transport_metadata(self):
        request = parse_request(VALID)
        self.assertEqual(request.protocol, CORE_PROTOCOL)
        self.assertEqual(request.request_id, "G2A-000001")
        self.assertEqual(request.project, ProjectKey("tenant-a", "project-a", "dev"))
        self.assertEqual(request.operation, "git.status")
        self.assertEqual(request.arguments, {})
        self.assertIsInstance(request, CoreRequest)

    def test_operation_allowlist_is_exactly_the_approved_nine(self):
        self.assertEqual(
            OPERATIONS,
            frozenset(
                {
                    "project.list",
                    "project.get",
                    "workspace.stat",
                    "workspace.list",
                    "workspace.read",
                    "git.status",
                    "git.branch",
                    "git.head",
                    "git.diff",
                }
            ),
        )

    def test_transport_or_execution_fields_are_refused(self):
        for forbidden in ("issue_number", "cwd", "argv", "command", "workspace"):
            with self.subTest(forbidden=forbidden):
                candidate = dict(VALID)
                candidate[forbidden] = 1
                with self.assertRaises(RefusedError) as caught:
                    parse_request(candidate)
                self.assertEqual(caught.exception.code, "unexpected_request_field")
                self.assertEqual(caught.exception.status, "REFUSED")

    def test_unknown_operation_is_refused(self):
        candidate = dict(VALID)
        candidate["operation"] = "shell.run"
        with self.assertRaises(RefusedError) as caught:
            parse_request(candidate)
        self.assertEqual(caught.exception.code, "unknown_operation")

    def test_request_id_must_be_nonempty_and_at_most_128_chars(self):
        for request_id in ("", "x" * 129, 123):
            with self.subTest(request_id=request_id):
                candidate = dict(VALID)
                candidate["request_id"] = request_id
                with self.assertRaises(RefusedError) as caught:
                    parse_request(candidate)
                self.assertEqual(caught.exception.code, "invalid_request_id")

    def test_project_fields_are_exact_and_environment_is_bounded(self):
        extra = dict(VALID)
        extra["project"] = dict(VALID["project"], repository="x")
        with self.assertRaises(RefusedError) as caught_extra:
            parse_request(extra)
        self.assertEqual(caught_extra.exception.code, "unexpected_project_field")

        invalid_environment = dict(VALID)
        invalid_environment["project"] = dict(VALID["project"], environment="production")
        with self.assertRaises(RefusedError) as caught_environment:
            parse_request(invalid_environment)
        self.assertEqual(caught_environment.exception.code, "invalid_environment")

    def test_missing_project_identity_or_non_object_arguments_are_refused(self):
        missing = dict(VALID)
        missing["project"] = {"tenant": "tenant-a", "name": "project-a"}
        with self.assertRaises(RefusedError) as caught_missing:
            parse_request(missing)
        self.assertEqual(caught_missing.exception.code, "invalid_project")

        arguments = dict(VALID)
        arguments["arguments"] = []
        with self.assertRaises(RefusedError) as caught_arguments:
            parse_request(arguments)
        self.assertEqual(caught_arguments.exception.code, "invalid_arguments")


if __name__ == "__main__":
    unittest.main()
