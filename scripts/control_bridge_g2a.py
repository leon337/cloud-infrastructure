#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control_plane.g2a.core import execute


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("json_must_be_object")
    return value


def validate_envelope(value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(value, dict):
        raise ValueError("envelope_must_be_object")
    if set(value) - {"transport", "request"}:
        raise ValueError("unexpected_envelope_field")
    if set(value) != {"transport", "request"}:
        raise ValueError("invalid_envelope")

    transport = value.get("transport")
    request = value.get("request")
    if not isinstance(transport, dict):
        raise ValueError("transport_must_be_object")
    if set(transport) - {"issue_number"}:
        raise ValueError("unexpected_transport_field")
    issue = transport.get("issue_number")
    if issue is not None and (not isinstance(issue, int) or issue <= 0):
        raise ValueError("invalid_issue_number")
    if not isinstance(request, dict):
        raise ValueError("request_must_be_object")
    return dict(transport), dict(request)


def load_envelope(event_name: str, dispatch_file: pathlib.Path) -> dict[str, Any]:
    if event_name != "push":
        raise ValueError("unsupported_event")
    envelope = load_json(dispatch_file)
    validate_envelope(envelope)
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=pathlib.Path, required=True)
    parser.add_argument("--dispatch-file", type=pathlib.Path, required=True)
    parser.add_argument("--envelope-file", type=pathlib.Path, required=True)
    parser.add_argument("--result-file", type=pathlib.Path, required=True)
    parser.add_argument("--attachment-file", type=pathlib.Path, required=True)
    parser.add_argument("--manifest-root", type=pathlib.Path, default=ROOT / "platform" / "manifests")
    parser.add_argument("--workspace-root", type=pathlib.Path, default=pathlib.Path("/home/ubuntu/mcf-workspaces"))
    args = parser.parse_args()

    try:
        envelope = load_envelope(args.event_name, args.dispatch_file)
        transport, request = validate_envelope(envelope)
        execution = execute(
            request,
            manifest_root=args.manifest_root,
            workspace_root=args.workspace_root,
        )
        normalized_envelope = {"transport": transport, "request": request}
        result = execution.result
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSED", "error": str(exc)}, sort_keys=True))
        return 2

    args.envelope_file.parent.mkdir(parents=True, exist_ok=True)
    args.result_file.parent.mkdir(parents=True, exist_ok=True)
    args.envelope_file.write_text(
        json.dumps(normalized_envelope, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.result_file.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if execution.attachment is not None:
        args.attachment_file.parent.mkdir(parents=True, exist_ok=True)
        args.attachment_file.write_bytes(execution.attachment.content)

    print(
        json.dumps(
            {
                "request_id": result.get("request_id", "UNKNOWN"),
                "operation": result.get("operation"),
                "status": result.get("status", "UNKNOWN"),
                "attachment": execution.attachment is not None,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
