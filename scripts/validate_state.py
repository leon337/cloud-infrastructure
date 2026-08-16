#!/usr/bin/env python3
"""Cross-check continuity state, binding decisions and implementation gates."""

from __future__ import annotations

import pathlib
import sys
from typing import Any

import yaml

from yaml_strict import load_strict


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFERRED_ROTATION = "DEFERRED_BY_HUMAN_DECISION"
EXPECTED_MACHINE_ID_SHA256 = (
    "27cff9587c434cf9024bd88468a8997778a64ce9ca5c3dc8dbcb68e0aee8f107"
)
EXPECTED_DECISIONS = {
    f"q{number}": "D" if number in {5, 11, 28, 40} else "C"
    for number in range(1, 41)
}
CANONICAL_PATH_KEYS = (
    "canonical_entrypoint",
    "checkpoint",
    "platform_discovery_state",
    "codex_execution_mission",
    "mission_acceptance_report",
    "consolidated_requirements",
    "target_architecture",
    "threat_model",
    "infrastructure_blueprint",
    "revised_roadmap",
    "technology_mapping",
    "component_inventory",
)


def load_yaml(path: pathlib.Path) -> dict[str, Any]:
    loaded = load_strict(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError(f"{path.relative_to(ROOT)} must contain a mapping")
    return loaded


def path_errors(current: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in CANONICAL_PATH_KEYS:
        raw_path = current["continuity"][key]
        if not isinstance(raw_path, str) or not raw_path:
            errors.append(f"canonical artifact {key} has an invalid path")
            continue
        path = (ROOT / raw_path).resolve()
        if path != ROOT and ROOT not in path.parents:
            errors.append(f"canonical artifact {key} escapes repository root")
        elif not path.is_file():
            errors.append(f"missing canonical artifact for {key}: {raw_path}")
    return errors


def crosscheck_errors(
    current: dict[str, Any],
    discovery: dict[str, Any],
    components: dict[str, Any],
    baseline: dict[str, Any],
    inventory_hosts: dict[str, Any],
    inventory_vars: dict[str, Any],
) -> list[str]:
    errors = path_errors(current)

    if discovery["decisions"] != EXPECTED_DECISIONS:
        missing = sorted(set(EXPECTED_DECISIONS) - set(discovery["decisions"]))
        extra = sorted(set(discovery["decisions"]) - set(EXPECTED_DECISIONS))
        invalid = sorted(
            key
            for key in set(EXPECTED_DECISIONS).intersection(discovery["decisions"])
            if discovery["decisions"][key] != EXPECTED_DECISIONS[key]
        )
        errors.append(
            f"Platform Discovery differs from binding Q1-Q40: "
            f"missing={missing} extra={extra} invalid={invalid}"
        )

    if current["platform_discovery"]["q40"]["choice"] != "D":
        errors.append("state/current.yaml no longer records Q40-D")
    if discovery["decisions"].get("q40") != "D":
        errors.append("state/platform-discovery.yaml no longer records Q40-D")
    if current["platform_discovery"]["implementation_authorized"] is not True:
        errors.append("DEV/lab implementation authorization is missing")
    if discovery["implementation_authorized"] is not True:
        errors.append("Platform Discovery implementation authorization is missing")

    production_values = {
        "current.platform_discovery": current["platform_discovery"][
            "production_promotion_authorized"
        ],
        "discovery.top": discovery["production_promotion_authorized"],
        "components": components["production"]["deployment_authorized"],
    }
    for location, value in production_values.items():
        if value is not False:
            errors.append(f"production became authorized at {location}")
    if current["authorization"]["production_promotion"] != (
        "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED"
    ):
        errors.append("current authorization no longer requires production HUMAN_GATE")
    if discovery["implementation"]["production_promotion"] != "NOT_AUTHORIZED":
        errors.append("discovery implementation no longer blocks production")

    rotation_values = {
        "current.project": current["project"]["credential_rotation"],
        "current.authorization": current["authorization"]["credential_rotation"],
        "discovery.top": discovery["credential_rotation"],
        "discovery.implementation": discovery["implementation"]["credential_rotation"],
        "components": components["credential_rotation"]["status"],
    }
    for location, value in rotation_values.items():
        if value != DEFERRED_ROTATION:
            errors.append(f"credential rotation is no longer deferred at {location}")

    current_validation = current["codex_execution"]["current_slice"]["validation"]
    for key in (
        "real_vps_privileged_check_mode",
        "real_vps_apply",
        "real_vps_idempotence",
        "real_vps_post_apply_invariance",
    ):
        if current_validation[key] != "NOT_EXECUTED":
            errors.append(f"{key} changed without pre-apply evidence reconciliation")

    for key in (
        "privileged_check_mode",
        "privileged_apply",
        "idempotence_reconcile",
        "post_apply_invariance",
    ):
        if baseline["apply"][key] != "NOT_EXECUTED":
            errors.append(f"baseline apply.{key} changed before real VPS evidence exists")

    snapshot = current["remote_vps"]["snapshot_at_utc"]
    if components["observed_at_utc"] != snapshot:
        errors.append("component inventory timestamp differs from current VPS snapshot")
    if baseline["vps"]["observed_at_utc"] != snapshot:
        errors.append("evidence baseline timestamp differs from current VPS snapshot")
    if current["remote_vps"]["machine_id_sha256"] != baseline["vps"][
        "machine_id_sha256"
    ]:
        errors.append("sanitized machine-id hash differs from baseline evidence")
    if current["remote_vps"]["machine_id_sha256"] != EXPECTED_MACHINE_ID_SHA256:
        errors.append("sanitized machine-id hash differs from the accepted VPS identity")
    if current["remote_vps"]["machine_id_hash_input"] != baseline["vps"][
        "machine_id_hash_input"
    ]:
        errors.append("machine-id hash input normalization differs from baseline")
    if baseline["vps"]["machine_id_raw_persisted"] is not False:
        errors.append("baseline claims raw machine-id persistence")
    if current["remote_vps"]["machine_id_sha256_classification"] != (
        "HASH_SANITIZED_RAW_NOT_PERSISTED"
    ):
        errors.append("machine-id hash lost its sanitized classification")
    if current["remote_vps"]["machine_id_sha256_observed_at_utc"] != snapshot:
        errors.append("machine-id observation timestamp differs from VPS snapshot")

    inventory_nodes = inventory_hosts["all"]["children"]["platform_nodes"]["hosts"]
    if set(inventory_nodes) != {"node-01"}:
        errors.append("DEV inventory target set differs from the single accepted node-01")
    inventory_node = inventory_nodes["node-01"]
    identity_values = {
        "inventory ansible_host": (
            inventory_node["ansible_host"],
            current["remote_vps"]["ipv4"],
        ),
        "inventory expected ansible_host": (
            inventory_vars["platform_expected_ansible_host"],
            current["remote_vps"]["ipv4"],
        ),
        "inventory expected hostname": (
            inventory_vars["platform_expected_hostname"],
            current["remote_vps"]["hostname"],
        ),
        "baseline hostname": (
            baseline["vps"]["hostname"],
            current["remote_vps"]["hostname"],
        ),
        "component hostname": (
            components["observed"]["host"]["hostname"],
            current["remote_vps"]["hostname"],
        ),
        "inventory node id": (
            inventory_vars["platform_node_id"],
            components["node"],
        ),
        "inventory environment": (
            inventory_vars["platform_environment"],
            "dev",
        ),
        "inventory expected machine-id hash": (
            inventory_vars["platform_expected_machine_id_sha256"],
            EXPECTED_MACHINE_ID_SHA256,
        ),
        "inventory controller key fingerprint": (
            inventory_vars["platform_expected_controller_key_fingerprint"],
            current["remote_vps"]["accounts"]["ubuntu"]["authorized_keys"][
                "validated_key"
            ]["fingerprint"],
        ),
        "inventory SSH user": (inventory_node["ansible_user"], "ubuntu"),
        "inventory private-key reference": (
            inventory_node["ansible_ssh_private_key_file"],
            "{{ lookup('env', 'PLATFORM_SSH_KEY_FILE') }}",
        ),
    }
    for location, (actual, expected) in identity_values.items():
        if actual != expected:
            errors.append(f"{location} differs from the accepted VPS identity")

    expected_ssh_options = (
        "-o",
        "IdentitiesOnly=yes",
        "-o",
        "PreferredAuthentications=publickey",
        "-o",
        "PubkeyAuthentication=yes",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
        "-o",
        "StrictHostKeyChecking=yes",
    )
    ssh_options = tuple(inventory_node["ansible_ssh_common_args"].split())
    if ssh_options != expected_ssh_options:
        errors.append("DEV inventory SSH arguments differ from the strict profile")
    if current["codex_execution"]["base_sha"] != baseline["git"]["canonical_sha"]:
        errors.append("slice base SHA differs from recovered canonical evidence SHA")
    if current["codex_execution"]["working_branch"] != baseline["git"]["working_branch"]:
        errors.append("slice working branch differs from baseline evidence")

    required_secret_categories = {
        "passwords",
        "passphrases",
        "private_ssh_keys",
        "tokens",
        "api_keys",
        "two_factor_codes",
        "real_connection_strings",
        "provider_credentials",
    }
    recorded_secret_categories = set(current["secrets_policy"]["never_version"])
    missing_secret_categories = sorted(
        required_secret_categories - recorded_secret_categories
    )
    if missing_secret_categories:
        errors.append(
            "state/current.yaml lost secret prohibition categories: "
            f"{missing_secret_categories}"
        )

    return errors


def main() -> int:
    try:
        current = load_yaml(ROOT / "state" / "current.yaml")
        discovery = load_yaml(ROOT / "state" / "platform-discovery.yaml")
        components = load_yaml(ROOT / "state" / "components.yaml")
        baseline = load_yaml(ROOT / "evidence" / "SLICE-001" / "baseline.yaml")
        inventory_hosts = load_yaml(
            ROOT / "automation" / "ansible" / "inventory" / "dev" / "hosts.yml"
        )
        inventory_vars = load_yaml(
            ROOT
            / "automation"
            / "ansible"
            / "inventory"
            / "dev"
            / "group_vars"
            / "all.yml"
        )
        errors = crosscheck_errors(
            current,
            discovery,
            components,
            baseline,
            inventory_hosts,
            inventory_vars,
        )
    except (KeyError, OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        errors = [f"cannot validate structured state: {exc}"]

    if errors:
        for message in errors:
            print(f"STATE_CROSSCHECK_FAIL {message}", file=sys.stderr)
        return 1

    print(
        "STATE_CROSSCHECK_PASS decisions=Q1-Q40-exact artifacts=12 "
        "gates=preserved real_apply=NOT_EXECUTED timestamps=aligned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
