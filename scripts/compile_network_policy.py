#!/usr/bin/env python3
"""Compile a strict F1.2c policy plan into owned iptables restore fragments."""

from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import pathlib
import re
import sys
from typing import Any

import yaml


INTERFACE_RE = re.compile(r"^cp[0-9a-f]{8}$")
IDENTITY_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{2,127}$")
PROFILES = {"none", "restricted", "development-default"}
TOP_KEYS = {
    "api_version",
    "kind",
    "metadata",
    "addressing",
    "sandboxes",
    "shared_service_grants",
    "service_records",
    "egress_destinations",
}
METADATA_KEYS = {"environment", "evaluation_time_utc", "status"}
ADDRESSING_KEYS = {"ipv4_pool", "protected_ipv4", "protected_ipv6"}
SANDBOX_KEYS = {
    "identity",
    "interface",
    "subnet_ipv4",
    "gateway_ipv4",
    "dns_ipv4",
    "proxy_ipv4",
    "egress_profile",
}
GRANT_KEYS = {
    "grant_id",
    "source_interface",
    "destination_interface",
    "destination_ipv4",
    "protocol",
    "destination_port",
    "valid_until_utc",
}
SERVICE_RECORD_KEYS = {"record_id", "name", "ipv4", "visible_to_interfaces"}
EGRESS_DESTINATION_KEYS = {"destination_id", "hostname", "ports", "profiles"}
DNS_NAME_RE = re.compile(
    r"^(?=.{1,253}\.?$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.?$"
)


class PolicyError(ValueError):
    pass


def exact_keys(value: Any, expected: set[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyError(f"{location} must be a mapping")
    keys = set(value)
    if keys != expected:
        raise PolicyError(
            f"{location} keys differ: missing={sorted(expected - keys)} "
            f"unknown={sorted(keys - expected)}"
        )
    return value


def parse_utc(value: Any, location: str) -> dt.datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise PolicyError(f"{location} must be an RFC3339 UTC string")
    try:
        parsed = dt.datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise PolicyError(f"{location} is not a valid timestamp") from exc
    if parsed.tzinfo != dt.timezone.utc:
        raise PolicyError(f"{location} must use UTC")
    return parsed


def load_and_validate(
    path: pathlib.Path,
    *,
    allowed_statuses: set[str] | None = None,
) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PolicyError(f"unable to read strict YAML: {exc}") from exc

    plan = exact_keys(raw, TOP_KEYS, "plan")
    if plan["api_version"] != "cloud-platform/v1alpha1":
        raise PolicyError("unsupported api_version")
    if plan["kind"] != "NetworkPolicyPlan":
        raise PolicyError("kind must be NetworkPolicyPlan")

    metadata = exact_keys(plan["metadata"], METADATA_KEYS, "metadata")
    if metadata["environment"] != "DEV_LAB":
        raise PolicyError("only DEV_LAB is authorized")
    accepted_statuses = allowed_statuses or {"EXAMPLE_NOT_OPERATIONAL"}
    if metadata["status"] not in accepted_statuses:
        raise PolicyError("policy status is not accepted by this operation")
    evaluation_time = parse_utc(
        metadata["evaluation_time_utc"], "metadata.evaluation_time_utc"
    )

    addressing = exact_keys(plan["addressing"], ADDRESSING_KEYS, "addressing")
    try:
        pool = ipaddress.ip_network(addressing["ipv4_pool"], strict=True)
    except ValueError as exc:
        raise PolicyError("addressing.ipv4_pool is invalid") from exc
    if pool.version != 4 or pool != ipaddress.ip_network("10.240.0.0/16"):
        raise PolicyError("addressing.ipv4_pool must equal the reviewed candidate")

    protected_v4 = _networks(addressing["protected_ipv4"], 4, "protected_ipv4")
    protected_v6 = _networks(addressing["protected_ipv6"], 6, "protected_ipv6")
    required_v4 = {
        ipaddress.ip_network(value)
        for value in (
            "10.0.0.0/8",
            "100.64.0.0/10",
            "169.254.0.0/16",
            "172.16.0.0/12",
            "192.168.0.0/16",
        )
    }
    if not required_v4.issubset(set(protected_v4)):
        raise PolicyError("protected_ipv4 omits a mandatory private/metadata zone")

    sandboxes_raw = plan["sandboxes"]
    if not isinstance(sandboxes_raw, list) or not sandboxes_raw:
        raise PolicyError("sandboxes must be a non-empty list")
    sandboxes: list[dict[str, Any]] = []
    interfaces: set[str] = set()
    identities: set[str] = set()
    subnets: list[ipaddress.IPv4Network] = []
    for index, raw_sandbox in enumerate(sandboxes_raw):
        sandbox = exact_keys(raw_sandbox, SANDBOX_KEYS, f"sandboxes[{index}]")
        identity = sandbox["identity"]
        interface = sandbox["interface"]
        if not isinstance(identity, str) or not IDENTITY_RE.fullmatch(identity):
            raise PolicyError(f"sandboxes[{index}].identity is invalid")
        if not isinstance(interface, str) or not INTERFACE_RE.fullmatch(interface):
            raise PolicyError(f"sandboxes[{index}].interface is invalid")
        if identity in identities or interface in interfaces:
            raise PolicyError("sandbox identities and interfaces must be unique")
        identities.add(identity)
        interfaces.add(interface)
        try:
            subnet = ipaddress.ip_network(sandbox["subnet_ipv4"], strict=True)
            gateway = ipaddress.ip_address(sandbox["gateway_ipv4"])
        except ValueError as exc:
            raise PolicyError(f"sandboxes[{index}] has invalid IPv4 addressing") from exc
        if subnet.version != 4 or subnet.prefixlen != 24 or not subnet.subnet_of(pool):
            raise PolicyError(f"sandboxes[{index}].subnet_ipv4 must be a /24 in pool")
        if gateway != subnet.network_address + 1:
            raise PolicyError(f"sandboxes[{index}].gateway_ipv4 must be first host")
        if any(subnet.overlaps(existing) for existing in subnets):
            raise PolicyError("sandbox IPv4 subnets overlap")
        subnets.append(subnet)
        if sandbox["egress_profile"] not in PROFILES:
            raise PolicyError(f"sandboxes[{index}].egress_profile is invalid")
        if sandbox["egress_profile"] == "none":
            if sandbox["dns_ipv4"] is not None or sandbox["proxy_ipv4"] is not None:
                raise PolicyError(f"sandboxes[{index}] none profile cannot declare DNS/proxy IPs")
        else:
            try:
                dns_ip = ipaddress.ip_address(sandbox["dns_ipv4"])
                proxy_ip = ipaddress.ip_address(sandbox["proxy_ipv4"])
            except ValueError as exc:
                raise PolicyError(f"sandboxes[{index}] has invalid DNS/proxy IPv4") from exc
            if dns_ip != subnet.network_address + 2 or proxy_ip != subnet.network_address + 3:
                raise PolicyError(f"sandboxes[{index}] DNS/proxy IPs must be reserved hosts .2/.3")
        sandboxes.append(sandbox)

    grants_raw = plan["shared_service_grants"]
    if not isinstance(grants_raw, list):
        raise PolicyError("shared_service_grants must be a list")
    grants: list[dict[str, Any]] = []
    grant_ids: set[str] = set()
    by_interface = {item["interface"]: item for item in sandboxes}
    for index, raw_grant in enumerate(grants_raw):
        grant = exact_keys(raw_grant, GRANT_KEYS, f"shared_service_grants[{index}]")
        grant_id = grant["grant_id"]
        if not isinstance(grant_id, str) or not IDENTITY_RE.fullmatch(grant_id):
            raise PolicyError(f"shared_service_grants[{index}].grant_id is invalid")
        if grant_id in grant_ids:
            raise PolicyError("grant IDs must be unique")
        grant_ids.add(grant_id)
        source = grant["source_interface"]
        destination = grant["destination_interface"]
        if source not in by_interface or destination not in by_interface or source == destination:
            raise PolicyError(f"shared_service_grants[{index}] references invalid scopes")
        if grant["protocol"] not in {"tcp", "udp"}:
            raise PolicyError(f"shared_service_grants[{index}].protocol is invalid")
        port = grant["destination_port"]
        if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
            raise PolicyError(f"shared_service_grants[{index}].destination_port is invalid")
        try:
            destination_ip = ipaddress.ip_address(grant["destination_ipv4"])
            destination_subnet = ipaddress.ip_network(
                by_interface[destination]["subnet_ipv4"], strict=True
            )
        except ValueError as exc:
            raise PolicyError(f"shared_service_grants[{index}] has invalid destination") from exc
        if destination_ip.version != 4 or destination_ip not in destination_subnet:
            raise PolicyError(f"shared_service_grants[{index}] destination is outside scope")
        if parse_utc(grant["valid_until_utc"], f"grant[{index}].valid_until_utc") <= evaluation_time:
            raise PolicyError(f"shared_service_grants[{index}] is expired")
        grants.append(grant)

    records_raw = plan["service_records"]
    if not isinstance(records_raw, list) or not records_raw:
        raise PolicyError("service_records must be a non-empty list")
    records: list[dict[str, Any]] = []
    record_ids: set[str] = set()
    record_names: set[str] = set()
    for index, raw_record in enumerate(records_raw):
        record = exact_keys(raw_record, SERVICE_RECORD_KEYS, f"service_records[{index}]")
        record_id = record["record_id"]
        name = record["name"]
        if not isinstance(record_id, str) or not IDENTITY_RE.fullmatch(record_id):
            raise PolicyError(f"service_records[{index}].record_id is invalid")
        if record_id in record_ids:
            raise PolicyError("service record IDs must be unique")
        if not isinstance(name, str) or not DNS_NAME_RE.fullmatch(name) or not name.endswith(".dev.internal"):
            raise PolicyError(f"service_records[{index}].name must be an exact DEV internal DNS name")
        if name in record_names:
            raise PolicyError("service record names must be unique")
        try:
            record_ip = ipaddress.ip_address(record["ipv4"])
        except ValueError as exc:
            raise PolicyError(f"service_records[{index}].ipv4 is invalid") from exc
        if record_ip.version != 4 or not any(record_ip in subnet for subnet in subnets):
            raise PolicyError(f"service_records[{index}].ipv4 is outside managed scopes")
        visibility = record["visible_to_interfaces"]
        if (
            not isinstance(visibility, list)
            or not visibility
            or any(not isinstance(value, str) or value not in interfaces for value in visibility)
            or len(set(visibility)) != len(visibility)
        ):
            raise PolicyError(f"service_records[{index}].visible_to_interfaces is invalid")
        record_ids.add(record_id)
        record_names.add(name)
        records.append(record)

    destinations_raw = plan["egress_destinations"]
    if not isinstance(destinations_raw, list) or not destinations_raw:
        raise PolicyError("egress_destinations must be a non-empty list")
    destinations: list[dict[str, Any]] = []
    destination_ids: set[str] = set()
    destination_hosts: set[str] = set()
    for index, raw_destination in enumerate(destinations_raw):
        destination = exact_keys(
            raw_destination,
            EGRESS_DESTINATION_KEYS,
            f"egress_destinations[{index}]",
        )
        destination_id = destination["destination_id"]
        hostname = destination["hostname"]
        if not isinstance(destination_id, str) or not IDENTITY_RE.fullmatch(destination_id):
            raise PolicyError(f"egress_destinations[{index}].destination_id is invalid")
        if destination_id in destination_ids:
            raise PolicyError("egress destination IDs must be unique")
        if (
            not isinstance(hostname, str)
            or hostname != hostname.lower()
            or not DNS_NAME_RE.fullmatch(hostname)
            or hostname.endswith(".internal")
        ):
            raise PolicyError(f"egress_destinations[{index}].hostname must be an exact public DNS name")
        if hostname in destination_hosts:
            raise PolicyError("egress destination hostnames must be unique")
        ports = destination["ports"]
        if (
            not isinstance(ports, list)
            or not ports
            or any(isinstance(port, bool) or port not in {80, 443} for port in ports)
            or len(set(ports)) != len(ports)
        ):
            raise PolicyError(f"egress_destinations[{index}].ports must contain only unique 80/443 values")
        profiles = destination["profiles"]
        if (
            not isinstance(profiles, list)
            or not profiles
            or any(profile not in {"restricted", "development-default"} for profile in profiles)
            or len(set(profiles)) != len(profiles)
        ):
            raise PolicyError(f"egress_destinations[{index}].profiles is invalid")
        destination_ids.add(destination_id)
        destination_hosts.add(hostname)
        destinations.append(destination)

    plan["_validated"] = {
        "protected_v4": protected_v4,
        "protected_v6": protected_v6,
        "sandboxes": sandboxes,
        "grants": grants,
        "records": records,
        "destinations": destinations,
    }
    return plan


def _networks(values: Any, version: int, location: str) -> list[Any]:
    if not isinstance(values, list) or not values:
        raise PolicyError(f"addressing.{location} must be a non-empty list")
    result = []
    for value in values:
        try:
            network = ipaddress.ip_network(value, strict=True)
        except ValueError as exc:
            raise PolicyError(f"addressing.{location} contains invalid CIDR") from exc
        if network.version != version:
            raise PolicyError(f"addressing.{location} mixes address families")
        result.append(network)
    if len(set(result)) != len(result):
        raise PolicyError(f"addressing.{location} contains duplicates")
    return result


def compile_ipv4(plan: dict[str, Any]) -> str:
    validated = plan["_validated"]
    lines = [
        "*filter",
        ":CLOUD-PLATFORM-IN - [0:0]",
        ":CLOUD-PLATFORM-FWD - [0:0]",
        "-F CLOUD-PLATFORM-IN",
        "-F CLOUD-PLATFORM-FWD",
        "-A CLOUD-PLATFORM-IN -m conntrack --ctstate INVALID -j DROP",
        "-A CLOUD-PLATFORM-IN -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
    ]
    for sandbox in validated["sandboxes"]:
        interface = sandbox["interface"]
        lines.append(f"-A CLOUD-PLATFORM-IN -i {interface} -j DROP")
    lines.extend(
        [
            "-A CLOUD-PLATFORM-IN -j RETURN",
            "-A CLOUD-PLATFORM-FWD -m conntrack --ctstate INVALID -j DROP",
            "-A CLOUD-PLATFORM-FWD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT",
        ]
    )
    for sandbox in validated["sandboxes"]:
        if sandbox["egress_profile"] == "none":
            continue
        interface = sandbox["interface"]
        lines.extend(
            [
                f"-A CLOUD-PLATFORM-FWD -i {interface} -o {interface} -d {sandbox['dns_ipv4']}/32 -p udp --dport 53 -j ACCEPT",
                f"-A CLOUD-PLATFORM-FWD -i {interface} -o {interface} -d {sandbox['dns_ipv4']}/32 -p tcp --dport 53 -j ACCEPT",
                f"-A CLOUD-PLATFORM-FWD -i {interface} -o {interface} -d {sandbox['proxy_ipv4']}/32 -p tcp --dport 3128 -j ACCEPT",
            ]
        )
    for grant in validated["grants"]:
        lines.append(
            "-A CLOUD-PLATFORM-FWD "
            f"-i {grant['source_interface']} -o {grant['destination_interface']} "
            f"-d {grant['destination_ipv4']}/32 -p {grant['protocol']} "
            f"--dport {grant['destination_port']} -m conntrack --ctstate NEW -j ACCEPT"
        )
    for sandbox in validated["sandboxes"]:
        for network in validated["protected_v4"]:
            lines.append(
                f"-A CLOUD-PLATFORM-FWD -i {sandbox['interface']} -d {network} -j DROP"
            )
    for sandbox in validated["sandboxes"]:
        lines.append(f"-A CLOUD-PLATFORM-FWD -i {sandbox['interface']} -j DROP")
        lines.append(f"-A CLOUD-PLATFORM-FWD -o {sandbox['interface']} -j DROP")
    lines.extend(["-A CLOUD-PLATFORM-FWD -j RETURN", "COMMIT", ""])
    return "\n".join(lines)


def compile_ipv6(plan: dict[str, Any]) -> str:
    sandboxes = plan["_validated"]["sandboxes"]
    lines = [
        "*filter",
        ":CLOUD-PLATFORM-IN - [0:0]",
        ":CLOUD-PLATFORM-FWD - [0:0]",
        "-F CLOUD-PLATFORM-IN",
        "-F CLOUD-PLATFORM-FWD",
    ]
    for sandbox in sandboxes:
        lines.append(f"-A CLOUD-PLATFORM-IN -i {sandbox['interface']} -j DROP")
        lines.append(f"-A CLOUD-PLATFORM-FWD -i {sandbox['interface']} -j DROP")
        lines.append(f"-A CLOUD-PLATFORM-FWD -o {sandbox['interface']} -j DROP")
    lines.extend(
        [
            "-A CLOUD-PLATFORM-IN -j RETURN",
            "-A CLOUD-PLATFORM-FWD -j RETURN",
            "COMMIT",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("policy", type=pathlib.Path)
    parser.add_argument("--family", choices=("ipv4", "ipv6"), required=True)
    args = parser.parse_args()
    try:
        plan = load_and_validate(args.policy)
        output = compile_ipv4(plan) if args.family == "ipv4" else compile_ipv6(plan)
    except PolicyError as exc:
        print(f"NETWORK_POLICY_REFUSED: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
