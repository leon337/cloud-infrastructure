from __future__ import annotations

import copy
import json
import pathlib
import unittest

import jsonschema
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
CAPSULE = ROOT / ".mcf/project-capsule.yaml"
CAPSULE_SCHEMA = ROOT / "platform/schemas/mcf-project-capsule.schema.json"
CONTEXT = ROOT / "context/mcf-cloud-context.yaml"
CONTEXT_SCHEMA = ROOT / "platform/schemas/mcf-cloud-context.schema.json"
PROJECT_MANIFEST = ROOT / "platform/manifests/g2a-smoke.yaml"
G2A_STATE = ROOT / "state/control-bridge-g2a.yaml"

MARKERS = [
    "G2B_DISPOSABLE_IDENTITY_PASS",
    "G2B_TRANSPORT_DIRECT_WRITE_REFUSED",
    "G2B_GRANT_24H_PASS",
    "G2B_WRITE_PASS",
    "G2B_REPLAY_PASS",
    "G2B_REQUEST_ID_CONFLICT_PASS",
    "G2B_CONCURRENCY_PASS",
    "G2B_AUDIT_PASS",
    "G2B_ROLLBACK_PASS",
    "G2B_FINAL_STATE_PASS",
    "G2B_REVOKE_PASS",
    "G2B_POST_REVOKE_REFUSAL_PASS",
    "G2B_BOUNDED_CLEANUP_PASS",
]


class StrictSafeLoader(yaml.SafeLoader):
    pass


def _construct_unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


StrictSafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(path: pathlib.Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=StrictSafeLoader)


def load_schema(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


class McfCloudContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capsule = load_yaml(CAPSULE)
        cls.capsule_schema = load_schema(CAPSULE_SCHEMA)
        cls.context = load_yaml(CONTEXT)
        cls.context_schema = load_schema(CONTEXT_SCHEMA)
        cls.manifest = load_yaml(PROJECT_MANIFEST)
        cls.g2a_state = load_yaml(G2A_STATE)

    def test_schemas_are_draft_2020_12_and_artifacts_validate(self):
        checker = jsonschema.FormatChecker()
        for schema, value in (
            (self.capsule_schema, self.capsule),
            (self.context_schema, self.context),
        ):
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
            )
            jsonschema.Draft202012Validator.check_schema(schema)
            jsonschema.Draft202012Validator(
                schema,
                format_checker=checker,
            ).validate(value)

    def test_capsule_points_to_the_context_contract(self):
        self.assertEqual(self.capsule["project_id"], "cloud-infrastructure")
        self.assertEqual(
            self.capsule["sources"]["current_state"],
            "context/mcf-cloud-context.yaml",
        )
        self.assertTrue((ROOT / self.capsule["sources"]["current_state"]).is_file())
        self.assertIn(
            "G2B_TASK8_LAB_VALIDATED_INACTIVE",
            self.capsule["snapshot"]["current_status"],
        )

    def test_context_project_id_maps_exactly_to_cloud_manifest_key(self):
        mapping = self.context["mapping"]
        metadata = self.manifest["metadata"]
        expected = {
            "tenant": metadata["tenant"],
            "name": metadata["name"],
            "environment": metadata["environment"],
        }
        self.assertEqual(mapping["from"]["context_project_id"], self.capsule["project_id"])
        self.assertEqual(mapping["to"], expected)
        self.assertEqual(
            mapping["canonical_cloud_key"],
            "/".join((metadata["tenant"], metadata["name"], metadata["environment"])),
        )
        self.assertEqual(mapping["identity_authority"], "CLOUD_PROJECT_MANIFEST")
        self.assertFalse(mapping["duplicate_registry"])

    def test_g2a_is_read_only_historic_and_live_required(self):
        g2a = self.context["capabilities"]["g2a"]
        self.assertEqual(g2a["lifecycle"], "HISTORIC_READ_ONLY_LIVE_REQUIRED")
        self.assertEqual(g2a["operational_freshness"], "LIVE_REQUIRED")
        self.assertTrue(g2a["read_only"])
        self.assertFalse(g2a["mutation"])
        self.assertEqual(g2a["operations"], self.g2a_state["capabilities"])
        local = g2a["local_context_adapter"]
        self.assertEqual(
            local["lifecycle"],
            "LAB_E2E_WITH_MCF_FIXTURE_VERIFIED_DISABLED_BY_DEFAULT",
        )
        self.assertEqual(local["e2e"], "PASS_13_OF_13")
        self.assertEqual(local["e2e_client"], "DISPOSABLE_MCF_FIXTURE")
        self.assertEqual(
            local["repository_fingerprint"],
            "PASS_GIT_AND_FILESYSTEM_UNCHANGED",
        )
        self.assertEqual(local["vps_freshness"], "NOT_OBSERVED_LIVE_REQUIRED")
        self.assertFalse(local["enabled_by_default"])
        self.assertEqual(local["activation"], "NOT_AUTHORIZED")

    def test_g2b_is_lab_validated_but_inactive_and_fail_closed(self):
        g2b = self.context["capabilities"]["g2b"]
        self.assertEqual(g2b["lifecycle"], "LAB_VALIDATED_INACTIVE")
        self.assertEqual(g2b["state"], "TASK_8_LAB_PASS_TASKS_9_10_NOT_STARTED")
        self.assertEqual(g2b["task_8"]["acceptance_markers"], MARKERS)
        self.assertEqual(g2b["task_8"]["marker_count"], len(MARKERS))
        self.assertEqual(g2b["task_8"]["boundary"], "DISPOSABLE_NOTEBOOK_DOCKER")
        self.assertEqual(g2b["task_8"]["network"], "NONE")
        self.assertEqual(g2b["tasks_9_10"], "NOT_STARTED")
        self.assertEqual(g2b["activation"], "NOT_AUTHORIZED")
        self.assertEqual(g2b["transport_from_context"], "NOT_IMPLEMENTED")
        self.assertFalse(g2b["production_authorized"])
        self.assertTrue(all(value is False for value in g2b["real_evidence"].values()))

    def test_publication_and_lineage_are_explicit_and_local_only(self):
        publication = self.context["publication"]
        self.assertEqual(
            publication["safe_pull_request_target"],
            self.context["lineage"]["mature_base_branch"],
        )
        self.assertFalse(publication["push_executed"])
        self.assertIsNone(publication["pull_request"])
        self.assertFalse(publication["merge_authorized"])

    def test_shared_git_object_database_recovery_is_attributed_to_parallel_mission(self):
        gate = self.context["validation"]["aggregate_gate"]
        self.assertEqual(gate["result"], "PASS")
        self.assertFalse(gate["candidate_failure"])
        self.assertEqual(
            gate["shared_git_object_database"],
            "PASS_FSCK_FULL_NO_DANGLING",
        )
        self.assertEqual(
            gate["resolution_origin"],
            "PARALLEL_MISSION_NOT_THIS_WORKSTREAM",
        )
        self.assertEqual(
            gate["history_secret_scope"],
            "HEAD_REACHABLE_CANDIDATE_ANCESTRY",
        )
        self.assertEqual(
            gate["unrelated_ref_findings"],
            "OUT_OF_SCOPE_REQUIRES_SEPARATE_SECURITY_REVIEW",
        )

    def test_schema_rejects_capability_promotion_or_real_evidence(self):
        validator = jsonschema.Draft202012Validator(self.context_schema)

        promoted = copy.deepcopy(self.context)
        promoted["capabilities"]["g2b"]["lifecycle"] = "ACTIVE"
        self.assertTrue(list(validator.iter_errors(promoted)))

        overclaimed = copy.deepcopy(self.context)
        overclaimed["capabilities"]["g2b"]["real_evidence"]["write"] = True
        self.assertTrue(list(validator.iter_errors(overclaimed)))

        mutated_identity = copy.deepcopy(self.context)
        mutated_identity["mapping"]["from"]["context_project_id"] = "g2a-smoke"
        self.assertTrue(list(validator.iter_errors(mutated_identity)))

    def test_strict_yaml_loader_rejects_duplicate_keys(self):
        with self.assertRaises(yaml.constructor.ConstructorError):
            yaml.load("schema_version: 1\nschema_version: 2\n", Loader=StrictSafeLoader)


if __name__ == "__main__":
    unittest.main()
