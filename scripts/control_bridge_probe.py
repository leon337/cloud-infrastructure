#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import subprocess
import sys
from typing import Any

PROTOCOL = "MCF_CONTROL_BRIDGE_PROBE_V1"
RESULT_PROTOCOL = "MCF_CONTROL_BRIDGE_PROBE_RESULT_V1"


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("request_must_be_object")
    return value


def load_request(event_name: str, event_path: pathlib.Path, request_file: pathlib.Path) -> dict[str, Any]:
    if event_name == "issues":
        event = load_json(event_path)
        issue = event.get("issue")
        if not isinstance(issue, dict):
            raise ValueError("issue_event_missing_issue")
        if not str(issue.get("title", "")).startswith("[VPS-CMD] PROBE"):
            raise ValueError("issue_title_not_probe")
        body = issue.get("body")
        if not isinstance(body, str):
            raise ValueError("issue_body_missing")
        request = json.loads(body)
        if not isinstance(request, dict):
            raise ValueError("issue_body_request_must_be_object")
        request.setdefault("issue_number", issue.get("number"))
        return request
    if event_name == "push":
        return load_json(request_file)
    raise ValueError("unsupported_event")


def validate(request: dict[str, Any]) -> tuple[str, int]:
    if request.get("protocol") != PROTOCOL:
        raise ValueError("invalid_protocol")
    request_id = request.get("request_id")
    if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
        raise ValueError("invalid_request_id")
    issue_number = request.get("issue_number")
    if not isinstance(issue_number, int) or issue_number <= 0:
        raise ValueError("invalid_issue_number")
    return request_id, issue_number


def run_probe(name: str, argv: list[str], timeout: int = 15) -> dict[str, Any]:
    started = now()
    try:
        result = subprocess.run(
            argv,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
        return {
            "name": name,
            "argv": argv,
            "exit_code": result.returncode,
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-4000:],
            "started_at": started,
            "finished_at": now(),
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "name": name,
            "argv": argv,
            "exit_code": 124 if isinstance(exc, subprocess.TimeoutExpired) else 127,
            "stdout": "",
            "stderr": str(exc),
            "started_at": started,
            "finished_at": now(),
        }


def build_result(request_id: str, issue_number: int) -> dict[str, Any]:
    probes = [
        run_probe("hostname", ["hostname"]),
        run_probe("identity", ["id"]),
        run_probe("kernel", ["uname", "-a"]),
        run_probe("python", ["python3", "--version"]),
        run_probe("disk", ["df", "-h", "/"]),
        run_probe("memory", ["free", "-h"]),
        run_probe("ssh", ["systemctl", "is-active", "ssh"]),
        run_probe("ufw", ["systemctl", "is-active", "ufw"]),
        run_probe("docker", ["systemctl", "is-active", "docker"]),
        run_probe("containerd", ["systemctl", "is-active", "containerd"]),
        run_probe(
            "python_ensurepip",
            ["python3", "-c", "import ensurepip; print(ensurepip.version())"],
        ),
        run_probe(
            "python_g2a_imports",
            ["python3", "-c", "import jsonschema, yaml; print('g2a-imports-ok')"],
        ),
        run_probe("python_pip", ["python3", "-m", "pip", "--version"]),
    ]
    runner_path = pathlib.Path("/usr/local/sbin/codex-mission-001-runner")
    if runner_path.is_file():
        probes.append(
            run_probe(
                "mission001_runner_status",
                ["sudo", "-n", str(runner_path), "status"],
            )
        )
    all_core_ok = all(item["exit_code"] == 0 for item in probes[:6])
    return {
        "protocol": RESULT_PROTOCOL,
        "request_id": request_id,
        "issue_number": issue_number,
        "status": "PASS" if all_core_ok else "PARTIAL",
        "generated_at": now(),
        "probes": probes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-name", required=True)
    parser.add_argument("--event-path", type=pathlib.Path, required=True)
    parser.add_argument("--request-file", type=pathlib.Path, required=True)
    parser.add_argument("--result-file", type=pathlib.Path, required=True)
    args = parser.parse_args()

    try:
        request = load_request(args.event_name, args.event_path, args.request_file)
        request_id, issue_number = validate(request)
        result = build_result(request_id, issue_number)
    except (ValueError, json.JSONDecodeError) as exc:
        result = {
            "protocol": RESULT_PROTOCOL,
            "request_id": "UNKNOWN",
            "issue_number": None,
            "status": "REFUSED",
            "generated_at": now(),
            "error": str(exc),
            "probes": [],
        }

    args.result_file.parent.mkdir(parents=True, exist_ok=True)
    args.result_file.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"request_id": result["request_id"], "status": result["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
