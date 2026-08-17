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
F1_2B_TESTED_COMMIT = "fa66f1049bac5540a5b12219186a421cc39dcbc0"
F1_2B_CI_RUN_ID = 31996516019
F1_2B_REAL_CHECK_MODE = "PASS_AT_2026_08_17T08_37_46Z_NO_MUTATION"
F1_2C_CONTRACT_COMMIT = "b4cbeb066605754d538ff5abe2d294f0759d6f59"
F1_2C_CONTRACT_PATH = "platform/network/f1-2c-contract.yaml"
F1_1_REAL_CHECK_MODE_CURRENT = (
    "PASS_AT_2026_08_17T05_48_16Z_CHANGED_SIMULATED_4_"
    "FAILED_0_UNREACHABLE_0_NO_MUTATION"
)
F1_1_REAL_CHECK_MODE_SHORT = "PASS_AT_2026_08_17T05_48_16Z_NO_MUTATION"
F1_1_REAL_CHECK_MODE_EVIDENCE = (
    "PASS_REAL_VPS_CHECK_MODE_FAILED_0_UNREACHABLE_0_"
    "MANAGED_SURFACE_INVARIANT"
)
F1_1_REAL_APPLY_CURRENT = (
    "PASS_AT_2026_08_17T06_48_33Z_CHANGED_7_FAILED_0_UNREACHABLE_0"
)
F1_1_REAL_IDEMPOTENCE_CURRENT = (
    "PASS_AT_2026_08_17T06_57_50Z_CHANGED_0_FAILED_0_UNREACHABLE_0"
)
F1_1_REAL_INVARIANCE_CURRENT = "PASS_AT_2026_08_17T06_58_43Z"
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

    ci_values = {
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
    for location, value in ci_values.items():
        if not str(value).startswith("PASS"):
            errors.append(f"F1.2b disposable CI lost PASS evidence at {location}")
    if docker_baseline["git"].get("tested_commit") != F1_2B_TESTED_COMMIT:
        errors.append("F1.2b tested commit differs from the green CI run")
    if docker_baseline["git"].get("ci_run_id") != F1_2B_CI_RUN_ID:
        errors.append("F1.2b CI run id differs from the recorded green run")
    if docker_baseline["git"].get("ci_conclusion") != "PASS":
        errors.append("F1.2b CI conclusion is no longer PASS")

    check_mode_values = {
        "current.real_vps_check_mode": current_state["real_vps_check_mode"],
        "components.real_vps_check_mode": component_state["real_vps_check_mode"],
        "evidence.real_vps_check_mode": evidence_validation["real_vps_check_mode"],
    }
    for location, value in check_mode_values.items():
        if value != F1_2B_REAL_CHECK_MODE:
            errors.append(f"F1.2b real check-mode evidence differs at {location}")

    not_executed_values = {
        "components.real_vps_apply": component_state["real_vps_apply"],
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
    expected_current_real_state = {
        "real_vps_check_mode": F1_2B_REAL_CHECK_MODE,
        "real_vps_apply": "NOT_EXECUTED_READY_AFTER_CHECK_MODE_RECONCILIATION",
    }
    for key, expected in expected_current_real_state.items():
        if current_state[key] != expected:
            errors.append(f"F1.2b real-node gate changed at current.{key}")
    if discovery_state["real_gate"] != "CHECK_MODE_PASS_READY_FOR_REVIEWED_APPLY_HUMAN_SUDO":
        errors.append("F1.2b discovery gate does not reflect passed real check mode")
    expected_foundation_dependency = {
        "f1_1_real_vps_status": "DONE",
        "f1_1_privileged_check_mode": "PASS_NO_MUTATION",
        "f1_1_apply": "PASS_CHANGED_7",
        "f1_1_idempotence": "PASS_CHANGED_0",
        "f1_1_post_apply_invariance": "PASS",
        "f1_2b_real_vps_gate": "CHECK_MODE_PASS_READY_FOR_REVIEWED_APPLY",
    }
    for key, expected in expected_foundation_dependency.items():
        if docker_baseline["dependency"][key] != expected:
            errors.append(f"F1.2b F1.1 dependency evidence differs at {key}")

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


def f1_2c_gate_errors(
    current: dict[str, Any],
    discovery: dict[str, Any],
    components: dict[str, Any],
    network_baseline: dict[str, Any],
    network_contract: dict[str, Any],
) -> list[str]:
    """Reject claims beyond the repo-only F1.2c contract checkpoint."""
    errors: list[str] = []
    current_state = current["codex_execution"]["repo_only_preparations"][
        "network_enforcement_f1_2c"
    ]
    discovery_state = discovery["implementation"]["f1_2c_repo_only"]
    component_state = components["platform_components"]["network_enforcement"]

    commit_values = {
        "current": current_state["contract_commit"],
        "discovery": discovery_state["contract_commit"],
        "components": component_state["contract"]["commit"],
        "evidence": network_baseline["git"]["contract_commit"],
    }
    for location, value in commit_values.items():
        if value != F1_2C_CONTRACT_COMMIT:
            errors.append(f"F1.2c contract commit differs at {location}")

    path_values = {
        "current": current_state["contract_path"],
        "discovery": discovery_state["contract_path"],
        "components": component_state["contract"]["path"],
        "evidence": network_baseline["contract"]["path"],
    }
    for location, value in path_values.items():
        if value != F1_2C_CONTRACT_PATH:
            errors.append(f"F1.2c contract path differs at {location}")
    if not (ROOT / F1_2C_CONTRACT_PATH).is_file():
        errors.append("F1.2c contract file is missing")

    metadata = network_contract["metadata"]
    if metadata["status"] != "REPO_CONTRACT_ONLY":
        errors.append("F1.2c contract no longer identifies as repo-only")
    if metadata["operational_state"] != "NOT_APPLIED":
        errors.append("F1.2c contract overclaims operational state")
    if metadata["technology_selection"] != "UNRESOLVED":
        errors.append("F1.2c technology was selected without an ADR checkpoint")
    if network_baseline["contract"]["executable_rules_present"] is not False:
        errors.append("F1.2c evidence claims executable rules")

    local_values = {
        "current": current_state["local_validation"],
        "discovery": discovery_state["local_validation"],
        "components": component_state["contract"]["local_tests"],
        "evidence": network_baseline["validation"]["local_contract_tests"],
    }
    for location, value in local_values.items():
        if not str(value).startswith("PASS_"):
            errors.append(f"F1.2c local contract validation changed at {location}")

    pending_values = {
        "current.technology_adr": current_state["technology_adr"],
        "current.disposable_integration": current_state[
            "disposable_integration"
        ],
        "discovery.technology_adr": discovery_state["technology_adr"],
        "discovery.disposable_integration": discovery_state[
            "disposable_integration"
        ],
        "components.technology_adr": component_state["validation"][
            "technology_adr"
        ],
        "components.disposable_integration": component_state["validation"][
            "disposable_integration"
        ],
        "evidence.technology_adr": network_baseline["validation"][
            "technology_adr"
        ],
        "evidence.disposable_integration": network_baseline["validation"][
            "disposable_integration"
        ],
        "contract.technology_adr": network_contract["gates"]["technology_adr"],
        "contract.disposable_integration": network_contract["gates"][
            "disposable_integration"
        ],
    }
    for location, value in pending_values.items():
        if not str(value).startswith("PENDING"):
            errors.append(f"F1.2c pending gate was overclaimed at {location}")

    not_executed_values = {
        "current.real_vps_check_mode": current_state["real_vps_check_mode"],
        "current.real_vps_apply": current_state["real_vps_apply"],
        "discovery.real_vps": discovery_state["real_vps"],
        "components.real_vps_check_mode": component_state["validation"][
            "real_vps_check_mode"
        ],
        "components.real_vps_apply": component_state["validation"][
            "real_vps_apply"
        ],
        "evidence.real_vps_check_mode": network_baseline["validation"][
            "real_vps_check_mode"
        ],
        "evidence.real_vps_apply": network_baseline["validation"][
            "real_vps_apply"
        ],
    }
    for location, value in not_executed_values.items():
        if value != "NOT_EXECUTED":
            errors.append(f"F1.2c real-node execution was overclaimed at {location}")

    workload_values = {
        "current": current_state["first_workload"],
        "discovery": discovery_state["first_workload"],
        "components": component_state["validation"]["first_workload"],
        "evidence": network_baseline["dependencies"]["first_workload"],
        "contract": network_contract["gates"]["first_workload"],
    }
    for location, value in workload_values.items():
        if "BLOCKED" not in str(value):
            errors.append(f"F1.2c first-workload gate changed at {location}")

    if network_baseline["production"]["deployment_authorized"] is not False:
        errors.append("F1.2c evidence authorized production")
    if network_contract["gates"]["production"] != "NOT_AUTHORIZED":
        errors.append("F1.2c contract authorized production")
    if network_baseline["credential_rotation"]["status"] != DEFERRED_ROTATION:
        errors.append("F1.2c evidence no longer defers credential rotation")

    return errors


def crosscheck_errors(
    current: dict[str, Any],
    discovery: dict[str, Any],
    components: dict[str, Any],
    baseline: dict[str, Any],
    docker_baseline: dict[str, Any],
    network_baseline: dict[str, Any],
    network_contract: dict[str, Any],
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
    errors.extend(
        f1_2c_gate_errors(
            current,
            discovery,
            components,
            network_baseline,
            network_contract,
        )
    )
    real_check_mode_values = {
        "current": current_validation["real_vps_privileged_check_mode"],
        "discovery": discovery["implementation"]["real_vps_privileged_check_mode"],
        "components": components["platform_components"]["foundation"][
            "ci_validation"
        ]["real_vps_privileged_check_mode"],
        "evidence": baseline["apply"]["privileged_check_mode"],
    }
    expected_real_check_mode_values = {
        "current": F1_1_REAL_CHECK_MODE_CURRENT,
        "discovery": F1_1_REAL_CHECK_MODE_SHORT,
        "components": F1_1_REAL_CHECK_MODE_SHORT,
        "evidence": F1_1_REAL_CHECK_MODE_EVIDENCE,
    }
    for location, expected in expected_real_check_mode_values.items():
        if real_check_mode_values[location] != expected:
            errors.append(f"F1.1 real check-mode evidence differs at {location}")

    check_evidence = baseline["apply"]["privileged_check_mode_evidence"]
    if check_evidence["remote_mutation"] is not False:
        errors.append("F1.1 real check mode claims a remote mutation")
    if check_evidence["password_or_private_key_persisted"] is not False:
        errors.append("F1.1 real check mode persisted secret material")
    node_recap = check_evidence["node_01_recap"]
    if node_recap["failed"] != 0 or node_recap["unreachable"] != 0:
        errors.append("F1.1 real check mode recap is not clean")
    if check_evidence["post_preview_foundation_objects_account_group_and_lock"] != (
        "ALL_ABSENT"
    ):
        errors.append("F1.1 post-preview managed surface is not invariant")

    real_f1_1_values = {
        "current.apply": current_validation["real_vps_apply"],
        "current.idempotence": current_validation["real_vps_idempotence"],
        "current.invariance": current_validation["real_vps_post_apply_invariance"],
        "discovery.apply": discovery["implementation"]["real_vps_apply"],
        "discovery.idempotence": discovery["implementation"]["real_vps_idempotence"],
        "discovery.invariance": discovery["implementation"][
            "real_vps_post_apply_invariance"
        ],
        "components.apply": components["platform_components"]["foundation"][
            "ci_validation"
        ]["real_vps_apply"],
        "components.idempotence": components["platform_components"]["foundation"][
            "ci_validation"
        ]["real_vps_idempotence"],
        "components.invariance": components["platform_components"]["foundation"][
            "ci_validation"
        ]["real_vps_post_apply_invariance"],
        "evidence.apply": baseline["apply"]["privileged_apply"],
        "evidence.idempotence": baseline["apply"]["idempotence_reconcile"],
        "evidence.invariance": baseline["apply"]["post_apply_invariance"],
    }
    expected_real_f1_1_values = {
        "current.apply": F1_1_REAL_APPLY_CURRENT,
        "current.idempotence": F1_1_REAL_IDEMPOTENCE_CURRENT,
        "current.invariance": F1_1_REAL_INVARIANCE_CURRENT,
        "discovery.apply": "PASS_AT_2026_08_17T06_48_33Z_CHANGED_7",
        "discovery.idempotence": "PASS_AT_2026_08_17T06_57_50Z_CHANGED_0",
        "discovery.invariance": F1_1_REAL_INVARIANCE_CURRENT,
        "components.apply": "PASS_AT_2026_08_17T06_48_33Z_CHANGED_7",
        "components.idempotence": "PASS_AT_2026_08_17T06_57_50Z_CHANGED_0",
        "components.invariance": F1_1_REAL_INVARIANCE_CURRENT,
        "evidence.apply": "PASS_REAL_VPS_CHANGED_7_FAILED_0_UNREACHABLE_0",
        "evidence.idempotence": "PASS_REAL_VPS_CHANGED_0_FAILED_0_UNREACHABLE_0",
        "evidence.invariance": "PASS_REAL_VPS_AT_2026_08_17T06_58_43Z",
    }
    for location, expected in expected_real_f1_1_values.items():
        if real_f1_1_values[location] != expected:
            errors.append(f"F1.1 real completion evidence differs at {location}")

    apply_recap = baseline["apply"]["privileged_apply_evidence"]["node_01_recap"]
    idempotence_recap = baseline["apply"]["idempotence_evidence"]["node_01_recap"]
    if apply_recap["changed"] != 7 or apply_recap["failed"] != 0:
        errors.append("F1.1 real apply recap is not the reviewed changed=7 success")
    if idempotence_recap["changed"] != 0 or idempotence_recap["failed"] != 0:
        errors.append("F1.1 real idempotence recap is not changed=0 success")
    if baseline["apply"]["pre_apply_backup"]["remote_mutation"] is not False:
        errors.append("F1.1 pre-apply backup validation claims remote mutation")

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
        network_baseline = load_yaml(
            ROOT / "evidence" / "SLICE-002C" / "baseline.yaml"
        )
        network_contract = load_yaml(ROOT / F1_2C_CONTRACT_PATH)
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
            network_baseline,
            network_contract,
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
        f"artifacts={len(CANONICAL_PATH_KEYS)} "
        "gates=F1.1+F1.2b+F1.2c-preserved "
        "f1_1_real_apply=PASS f1_2b_real_apply=NOT_EXECUTED timestamps=aligned"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
