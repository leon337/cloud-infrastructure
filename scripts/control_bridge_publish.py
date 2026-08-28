#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import pathlib
import urllib.error
import urllib.request


def markdown(result: dict) -> str:
    lines = [
        "## MCF VPS Control Bridge — Probe Result",
        "",
        f"- request_id: `{result.get('request_id', 'UNKNOWN')}`",
        f"- status: `{result.get('status', 'UNKNOWN')}`",
        f"- generated_at: `{result.get('generated_at', 'UNKNOWN')}`",
        "",
    ]
    if result.get("error"):
        lines.extend(["### Error", "", f"`{result['error']}`", ""])
    for probe in result.get("probes", []):
        name = html.escape(str(probe.get("name", "probe")))
        exit_code = probe.get("exit_code")
        stdout = html.escape(str(probe.get("stdout", "")))
        stderr = html.escape(str(probe.get("stderr", "")))
        lines.extend(
            [
                f"<details><summary>{name} — exit {exit_code}</summary>",
                "",
                "<pre>",
                stdout,
                stderr,
                "</pre>",
                "</details>",
                "",
            ]
        )
    body = "\n".join(lines)
    return body[:60000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-file", type=pathlib.Path, required=True)
    args = parser.parse_args()

    result = json.loads(args.result_file.read_text(encoding="utf-8"))
    issue_number = result.get("issue_number")
    if not isinstance(issue_number, int) or issue_number <= 0:
        print("CONTROL_BRIDGE_PUBLISH_SKIP reason=no_issue_number")
        return 0

    token = os.environ.get("GITHUB_TOKEN")
    repository = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repository:
        raise SystemExit("missing GITHUB_TOKEN or GITHUB_REPOSITORY")

    url = f"https://api.github.com/repos/{repository}/issues/{issue_number}/comments"
    payload = json.dumps({"body": markdown(result)}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "mcf-vps-control-bridge",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(f"CONTROL_BRIDGE_PUBLISH_PASS status={response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"publish failed HTTP {exc.code}: {detail}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
