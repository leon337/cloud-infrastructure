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
F1_2B_DESIRED_STATE_COMMIT = (
    "7015c80759a797bcb141773b79cd9b95f6fbecf1"
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
    "current_state_independent_validation_report",
)

F1_1_CURRENT_STATUS_PATHS = (
    "CHECKPOINT.md",
    "CONTEXT.md",
    "docs/05-roadmap.md",
    "docs/39-platform-discovery-checkpoint-028.md",
    "docs/40-mission-acceptance-recovery-report.md",
    "docs/44-infrastructure-blueprint-v1.md",
    "docs/45-revised-implementation-roadmap.md",
    "docs/46-technology-mapping-v1.md",
    "governance/CONTEXT-COVERAGE.md",
)

F1_1_STALE_DISPOSABLE_GATE_MARKERS = (
    "PARTIAL_PENDING_VM",
    "PENDING_REVALIDATION_IN_DISPOSABLE_GITHUB_VM_AFTER_REVIEW_DELTA",
    "SLICE_001_REVALIDATE_IN_DISPOSABLE_GITHUB_VM_AFTER_SAFETY_REMEDIATION",
    "PARTIAL_AWAITING_DISPOSABLE_VM_REVALIDATION",
    "integração descartável e apply real explicitamente pendentes",
    "prova dinâmica aguarda VM descartável",
    "rollback dinâmico e rebuild ainda aguardam fixture nova",
    "resultado histórico não vale após o delta e precisa de rerun",
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


def stale_f1_1_gate_errors(
    current: dict[str, Any],
    canonical_texts: dict[str, str] | None = None,
) -> list[str]:
    """Reject current-state prose that reopens an already passed disposable gate."""
    validation = current["codex_execution"]["current_slice"]["validation"]
    disposable_keys = (
        "disposable_ubuntu_check_mode",
        "disposable_ubuntu_first_apply",
        "disposable_ubuntu_second_apply",
        "disposable_ubuntu_rollback",
    )
    if not all(str(validation[key]).startswith("PASS_") for key in disposable_keys):
        return []

    if canonical_texts is None:
        canonical_texts = {
            relative_path: (ROOT / relative_path).read_text(encoding="utf-8")
            for relative_path in F1_1_CURRENT_STATUS_PATHS
        }

    errors: list[str] = []
    for relative_path, text in canonical_texts.items():
        for marker in F1_1_STALE_DISPOSABLE_GATE_MARKERS:
            if marker in text:
                errors.append(
                    f"{relative_path} reopens passed F1.1 disposable gate: {marker}"
                )
    return errors


def f1_2b_gate_errors(
    current: dict[str, Any],
    discovery: dict[str, Any],
    components: dict[str, Any],
    docker_baseline: dict[str, Any],
) -> list[str]:
    """Keep local, disposable-CI and real-node F1.2b claims distinct."""
    errors: list[str] = []
    current_state = current["codex_execution"]["repo_only_preparations"][
        "docker_runtime_f1_2b"
    ]
    discovery_state = discovery["implementation"]["f1_2b_repo_only"]
    component_state = components["platform_components"]["container_runtime"][
        "validation"
    ]
    evidence_validation = docker_baseline["validation"]

    commit_values = {
        "current": current_state["desired_state_commit"],
        "discovery": discovery_state["commit"],
        "components": component_state["desired_state_commit"],
        "evidence": docker_baseline["git"]["desired_state_commit"],
    }
    for location, value in commit_values.items():
        if value != F1_2B_DESIRED_STATE_COMMIT:
            errors.append(f"F1.2b desired-state commit differs at {location}")

    local_values = {
        "current": current_state["local_validation"],
        "discovery": discovery_state["local_validation"],
        "components": component_state["local_static"],
        "evidence": evidence_validation["local_static_suite"],
    }
    for location, value in local_values.items():
        if not str(value).startswith("PASS_"):
            errors.append(f"F1.2b local validation is no longer PASS at {location}")

    pending_values = {
        "current.github_actions": current_state["github_actions"],
        "current.disposable_vm_lifecycle": current_state[
            "disposable_vm_lifecycle"
        ],
        "discovery.github_actions": discovery_state["github_actions"],
        "components.ci": component_state["ci"],
        "components.disposable_vm": component_state["disposable_vm"],
        "evidence.github_actions": evidence_validation["github_actions"],
        "evidence.disposable_vm_check_mode": evidence_validation[
            "disposable_vm_check_mode"
        ],
        "evidence.disposable_vm_apply": evidence_validation[
            "disposable_vm_apply"
        ],
        "evidence.disposable_vm_idempotence": evidence_validation[
            "disposable_vm_idempotence"
        ],
        "evidence.disposable_vm_security": evidence_validation[
            "disposable_vm_security"
        ],
        "evidence.disposable_vm_restart": evidence_validation[
            "disposable_vm_restart"
        ],
        "evidence.disposable_vm_negative_cases": evidence_validation[
            "disposable_vm_negative_cases"
        ],
        "evidence.disposable_vm_rollback": evidence_validation[
            "disposable_vm_rollback"
        ],
    }
    for location, value in pending_values.items():
        if not str(value).startswith("PENDING"):
            errors.append(f"F1.2b disposable CI was overclaimed at {location}")

    not_executed_values = {
        "components.real_vps_check_mode": component_state[
            "real_vps_check_mode"
        ],
        "components.real_vps_apply": component_state["real_vps_apply"],
        "evidence.real_vps_check_mode": evidence_validation[
            "real_vps_check_mode"
        ],
        "evidence.real_vps_apply": evidence_validation["real_vps_apply"],
        "evidence.real_vps_idempotence": evidence_validation[
            "real_vps_idempotence"
        ],
        "evidence.real_vps_post_apply_invariance": evidence_validation[
            "real_vps_post_apply_invariance"
        ],
    }
    for location, value in not_executed_values.items():
        if value != "NOT_EXECUTED":
            errors.append(f"F1.2b real-node execution was overclaimed at {location}")
    for key in ("real_vps_check_mode", "real_vps_apply"):
        if current_state[key] != "NOT_EXECUTED_BLOCKED_BY_F1_1":
            errors.append(f"F1.2b real-node gate changed at current.{key}")

    workload_values = {
        "current": current_state["first_workload"],
        "discovery": discovery_state["first_workload"],
        "components": component_state["first_workload"],
        "evidence": docker_baseline["dependency"]["first_workload_gate"],
    }
    for location, value in workload_values.items():
        if "BLOCKED" not in str(value) or "F1_2C" not in str(value):
            errors.append(f"F1.2b first-workload gate changed at {location}")

    if docker_baseline["production"]["deployment_authorized"] is not False:
        errors.append("F1.2b evidence authorized production")
    if docker_baseline["credential_rotation"]["status"] != DEFERRED_ROTATION:
        errors.append("F1.2b evidence no longer defers credential rotation")

    return errors


def crosscheck_errors(
    current: dict[str, Any],
    discovery: dict[str, Any],
    components: dict[str, Any],
    baseline: dict[str, Any],
    docker_baseline: dict[str, Any],
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
    errors.extend(stale_f1_1_gate_errors(current))
    errors.extend(f1_2b_gate_errors(current, discovery, components, docker_baseline))
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
        docker_baseline = load_yaml(
            ROOT / "evidence" / "SLICE-002B" / "baseline.yaml"
        )
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
            docker_baseline,
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
        "STATE_CROSSCHECK_PASS decisions=Q1-Q40-exact "
        f"artifacts={len(CANONICAL_PATH_KEYS)} gates=F1.1+F1.2b-preserved "
        "real_apply=NOT_EXECUTED timestamps=aligned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
