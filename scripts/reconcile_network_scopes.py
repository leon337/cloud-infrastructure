#!/usr/bin/env python3
"""Reconcile empty, internal Docker networks for the F1.2c disposable proof."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import pathlib
import subprocess
import socket
import sys

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.compile_network_policy import PolicyError, load_and_validate


CONFIRMATION = "GITHUB_HOSTED_UBUNTU_24_04_DISPOSABLE_VM_ONLY"
MANAGED_LABEL = "cloud.platform.managed=mission-001-f1-2c"


class ReconcileError(RuntimeError):
    pass


def run(*args: str) -> str:
    result = subprocess.run(args, check=False, text=True, capture_output=True)
    if result.returncode:
        raise ReconcileError(f"command_failed={args[0]} rc={result.returncode}")
    return result.stdout


def expected_networks(policy: pathlib.Path) -> tuple[list[dict[str, str]], str]:
    plan = load_and_validate(policy, allowed_statuses={"DISPOSABLE_TEST_ONLY"})
    digest = hashlib.sha256(policy.read_bytes()).hexdigest()
    expected = []
    for sandbox in plan["_validated"]["sandboxes"]:
        expected.append(
            {
                "name": f"cloud-scope-{sandbox['interface']}",
                "interface": sandbox["interface"],
                "identity": sandbox["identity"],
                "subnet": sandbox["subnet_ipv4"],
                "gateway": sandbox["gateway_ipv4"],
                "profile": sandbox["egress_profile"],
            }
        )
    return expected, digest


def inspect_network(name: str) -> dict:
    raw = run("docker", "network", "inspect", name)
    parsed = json.loads(raw)
    if not isinstance(parsed, list) or len(parsed) != 1:
        raise ReconcileError(f"invalid_inspect={name}")
    return parsed[0]


def verify(item: dict[str, str], digest: str, *, require_empty: bool = True) -> None:
    data = inspect_network(item["name"])
    labels = data.get("Labels") or {}
    options = data.get("Options") or {}
    configs = (data.get("IPAM") or {}).get("Config") or []
    expected_labels = {
        "cloud.platform.managed": "mission-001-f1-2c",
        "cloud.platform.policy-sha256": digest,
        "cloud.platform.identity": item["identity"],
        "cloud.platform.egress-profile": item["profile"],
    }
    if data.get("Driver") != "bridge" or data.get("Internal") is not True:
        raise ReconcileError(f"network_not_internal_bridge={item['name']}")
    if labels != expected_labels:
        raise ReconcileError(f"network_label_drift={item['name']}")
    if options != {
        "com.docker.network.bridge.enable_icc": "false",
        "com.docker.network.bridge.host_binding_ipv4": "127.0.0.1",
        "com.docker.network.bridge.name": item["interface"],
    }:
        raise ReconcileError(f"network_option_drift={item['name']}")
    if configs != [{"Subnet": item["subnet"], "Gateway": item["gateway"]}]:
        raise ReconcileError(f"network_address_drift={item['name']}")
    if require_empty and data.get("Containers"):
        raise ReconcileError(f"network_has_attachments={item['name']}")


def existing_custom_names() -> set[str]:
    output = run(
        "docker", "network", "ls", "--filter", "type=custom", "--format", "{{.Name}}"
    )
    return {line for line in output.splitlines() if line}


def refuse_route_collisions(expected: list[dict[str, str]]) -> None:
    try:
        routes = json.loads(run("ip", "-j", "-4", "route", "show", "table", "all"))
    except json.JSONDecodeError as exc:
        raise ReconcileError("route_inventory_invalid") from exc
    for item in expected:
        subnet = ipaddress.ip_network(item["subnet"], strict=True)
        for route in routes:
            destination = route.get("dst")
            if not destination or destination == "default":
                continue
            try:
                routed = ipaddress.ip_network(destination, strict=False)
            except ValueError:
                continue
            if subnet.overlaps(routed) and route.get("dev") != item["interface"]:
                raise ReconcileError(
                    f"route_collision={item['subnet']} dev={route.get('dev', 'unknown')}"
                )


def apply(expected: list[dict[str, str]], digest: str) -> int:
    expected_names = {item["name"] for item in expected}
    unexpected = existing_custom_names() - expected_names
    if unexpected:
        raise ReconcileError("unexpected_custom_networks=" + ",".join(sorted(unexpected)))
    refuse_route_collisions(expected)
    changed = 0
    for item in expected:
        if item["name"] in existing_custom_names():
            verify(item, digest)
            continue
        run(
            "docker", "network", "create",
            "--driver", "bridge", "--internal",
            "--subnet", item["subnet"], "--gateway", item["gateway"],
            "--opt", f"com.docker.network.bridge.name={item['interface']}",
            "--opt", "com.docker.network.bridge.enable_icc=false",
            "--opt", "com.docker.network.bridge.host_binding_ipv4=127.0.0.1",
            "--label", MANAGED_LABEL,
            "--label", f"cloud.platform.policy-sha256={digest}",
            "--label", f"cloud.platform.identity={item['identity']}",
            "--label", f"cloud.platform.egress-profile={item['profile']}",
            item["name"],
        )
        verify(item, digest)
        changed += 1
    return changed


def check(expected: list[dict[str, str]], digest: str) -> None:
    if existing_custom_names() != {item["name"] for item in expected}:
        raise ReconcileError("network_set_drift")
    for item in expected:
        verify(item, digest)


def rollback(expected: list[dict[str, str]], digest: str) -> int:
    expected_names = {item["name"] for item in expected}
    unexpected = existing_custom_names() - expected_names
    if unexpected:
        raise ReconcileError("unexpected_custom_networks=" + ",".join(sorted(unexpected)))
    for item in expected:
        if item["name"] in existing_custom_names():
            verify(item, digest)
    changed = 0
    for item in reversed(expected):
        if item["name"] in existing_custom_names():
            run("docker", "network", "rm", item["name"])
            changed += 1
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("apply", "check", "rollback"))
    parser.add_argument("policy", type=pathlib.Path)
    args = parser.parse_args()
    try:
        if os.geteuid() != 0:
            raise ReconcileError("root_required")
        if os.environ.get("F1_2C_NETWORK_SCOPE_CONFIRM") != CONFIRMATION:
            raise ReconcileError("disposable_confirmation_missing")
        if os.environ.get("GITHUB_ACTIONS") != "true" or os.environ.get("RUNNER_ENVIRONMENT") != "github-hosted":
            raise ReconcileError("github_hosted_runner_required")
        if os.environ.get("ImageOS") != "ubuntu24":
            raise ReconcileError("ubuntu_24_runner_required")
        if socket.gethostname().split(".", maxsplit=1)[0] in {"node-01", "vmi3506102"}:
            raise ReconcileError("real_dev_node_refused")
        run("systemd-detect-virt", "--quiet", "--vm")
        expected, digest = expected_networks(args.policy)
        if args.operation == "apply":
            changed = apply(expected, digest)
        elif args.operation == "check":
            check(expected, digest)
            changed = 0
        else:
            changed = rollback(expected, digest)
        print(f"NETWORK_SCOPES_{args.operation.upper()}=PASS changed={changed}")
        return 0
    except (PolicyError, ReconcileError, OSError, json.JSONDecodeError) as exc:
        print(f"NETWORK_SCOPES_REFUSED reason={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
