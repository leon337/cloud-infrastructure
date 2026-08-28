#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import urllib.error
import urllib.request
from typing import Any


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("json_must_be_object")
    return value


def issue_number(envelope: dict[str, Any]) -> int | None:
    transport = envelope.get("transport")
    if not isinstance(transport, dict):
        return None
    value = transport.get("issue_number")
    return value if isinstance(value, int) and value > 0 else None


def markdown(
    envelope: dict[str, Any],
    result: dict[str, Any],
    *,
    attachment_present: bool,
) -> str:
    project = result.get("project")
    if not isinstance(project, dict):
        project = {}
    project_key = "/".join(
        html.escape(str(project.get(key, "UNKNOWN")))
        for key in ("tenant", "name", "environment")
    )
    error = result.get("error")
    error_code = error.get("code") if isinstance(error, dict) else None
    lines = [
        "## MCF VPS Control Bridge — G2-A Result",
        "",
        f"- request_id: `{html.escape(str(result.get('request_id', 'UNKNOWN')))}`",
        f"- operation: `{html.escape(str(result.get('operation', 'UNKNOWN')))}`",
        f"- project: `{project_key}`",
        f"- status: `{html.escape(str(result.get('status', 'UNKNOWN')))}`",
        f"- finished_at: `{html.escape(str(result.get('finished_at', 'UNKNOWN')))}`",
    ]
    if error_code:
        lines.append(f"- error: `{html.escape(str(error_code))}`")
    lines.append(f"- artifact: `{'present' if attachment_present else 'none'}`")
    lines.extend(
        [
            "",
            "> Resultado compacto. Conteúdo de arquivo/diff e bytes de Artifact não são reproduzidos neste comentário.",
        ]
    )
    return "\n".join(lines)[:60000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--envelope-file", type=pathlib.Path, required=True)
    parser.add_argument("--result-file", type=pathlib.Path, required=True)
    parser.add_argument("--attachment-file", type=pathlib.Path, required=True)
    parser.add_argument("--summary-file", type=pathlib.Path)
    args = parser.parse_args()

    envelope = load_json(args.envelope_file)
    result = load_json(args.result_file)
    body = markdown(envelope, result, attachment_present=args.attachment_file.is_file())

    if args.summary_file is not None:
        with args.summary_file.open("a", encoding="utf-8") as handle:
            handle.write(body + "\n")

    number = issue_number(envelope)
    if number is None:
        print("CONTROL_BRIDGE_G2A_PUBLISH_SKIP reason=no_issue_number")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        raise SystemExit("missing GITHUB_TOKEN or GITHUB_REPOSITORY")

    url = f"https://api.github.com/repos/{repository}/issues/{number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "mcf-vps-control-bridge-g2a",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"CONTROL_BRIDGE_G2A_PUBLISH_PASS status={response.status}")
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"publish failed HTTP {exc.code}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
