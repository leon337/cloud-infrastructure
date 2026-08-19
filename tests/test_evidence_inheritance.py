from __future__ import annotations

import importlib.util
import pathlib
import stat
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "evidence_inheritance", ROOT / "scripts" / "classify_evidence_inheritance.py"
)
assert SPEC and SPEC.loader
EVIDENCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVIDENCE)


class GitRepoFixture:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self.run("git", "init", "-q")
        self.run("git", "config", "user.name", "Evidence Test")
        self.run("git", "config", "user.email", "evidence@example.invalid")

    def run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=self.root,
            check=check,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def write(self, path: str, content: str, mode: int | None = None) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if mode is not None:
            target.chmod(mode)

    def commit(self, message: str) -> str:
        self.run("git", "add", "-A")
        self.run("git", "commit", "-q", "-m", message)
        return self.run("git", "rev-parse", "HEAD").stdout.strip()


class EvidenceTestCase(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = pathlib.Path(temp.name)
        return GitRepoFixture(root), root

    def classify(self, root: pathlib.Path, anchor: str, candidate: str):
        return EVIDENCE.classify_repository_delta(root, anchor, candidate)


class EvidenceInheritancePathTests(EvidenceTestCase):
    def seed(self, repo: GitRepoFixture) -> str:
        repo.write("README.md", "baseline\n")
        repo.write("history/SESSION.md", "baseline\n")
        repo.write("scripts/example.sh", "#!/bin/sh\nexit 0\n", 0o755)
        return repo.commit("baseline")

    def test_history_only_delta_is_candidate_non_material(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("history/SESSION-2.md", "evidence\n")
        candidate = repo.commit("history")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "PASS")

    def test_checkpoint_modify_is_candidate_non_material(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("CHECKPOINT.md", "checkpoint\n")
        candidate = repo.commit("checkpoint")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "PASS")

    def test_script_change_is_refused_material_delta(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("scripts/example.sh", "#!/bin/sh\necho changed\n", 0o755)
        candidate = repo.commit("script")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["decision"], "REFUSED")
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_workflow_change_is_refused_material_delta(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write(".github/workflows/new.yml", "name: unsafe\n")
        candidate = repo.commit("workflow")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_unknown_path_is_refused_unknown_path(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.write("mystery/value.txt", "unknown\n")
        candidate = repo.commit("unknown")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_UNKNOWN_PATH")

    def test_deleted_document_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        (root / "README.md").unlink()
        candidate = repo.commit("delete")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_rename_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        (root / "README.md").rename(root / "CONTEXT.md")
        candidate = repo.commit("rename")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_executable_bit_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        readme = root / "README.md"
        readme.chmod(readme.stat().st_mode | stat.S_IXUSR)
        candidate = repo.commit("mode")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_MATERIAL_DELTA")

    def test_non_ancestor_candidate_is_refused_invalid_anchor(self):
        repo, root = self.make_repo()
        anchor = self.seed(repo)
        repo.run("git", "checkout", "-q", "--orphan", "other")
        repo.run("git", "rm", "-q", "-rf", ".")
        repo.write("history/other.md", "other\n")
        candidate = repo.commit("other")
        result = self.classify(root, anchor, candidate)
        self.assertEqual(result["reason"], "REFUSED_INVALID_ANCHOR")


class EvidenceInheritanceStateTests(EvidenceTestCase):
    def current_yaml(
        self,
        *,
        production_authorized: str = "false",
        production_gate: str = "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
        credential_rotation: str = "DEFERRED_BY_HUMAN_DECISION",
        working_branch: str = "codex/mission-001-f1-2c-network-enforcement",
        last_ci_run_id: int = 1,
        extra_status: str = "",
    ) -> str:
        return f"""documentation_state: BASE
project:
  credential_rotation: {credential_rotation}
  phases:
    future_platform_implementation: BASE
  next_exact_step: BASE
status_layer:
  last_material_checkpoint: BASE
  last_relevant_commit: 0000000000000000000000000000000000000000
  last_ci_run_id: {last_ci_run_id}
{extra_status}platform_discovery:
  production_promotion_authorized: {production_authorized}
authorization:
  credential_rotation: {credential_rotation}
  production_promotion: {production_gate}
  next_step: BASE
codex_execution:
  mission: docs/CODEX-EXECUTION-MISSION-001.md
  working_branch: {working_branch}
  active_slice: BASE
  repo_only_preparations:
    network_enforcement_f1_2c:
      status: BASE
      disposable_integration: BASE
      node_01_services_desired_state: BASE
"""

    def platform_discovery_yaml(self) -> str:
        return """phase: BASE
production_promotion_authorized: false
credential_rotation: DEFERRED_BY_HUMAN_DECISION
execution_mission: docs/CODEX-EXECUTION-MISSION-001.md
implementation:
  current_slice_status: BASE
  next_step: BASE
  f1_2c_repo_only:
    status: BASE
    disposable_integration: BASE
    node_01_services_desired_state: BASE
  production_promotion: NOT_AUTHORIZED
  credential_rotation: DEFERRED_BY_HUMAN_DECISION
"""

    def components_yaml(self) -> str:
        return """platform_components:
  network_enforcement:
    lifecycle: BASE
    validation:
      disposable_integration: BASE
      node_01_services_desired_state: BASE
production:
  deployment_authorized: false
  promotion_gate: LEANDRO
credential_rotation:
  status: DEFERRED_BY_HUMAN_DECISION
"""

    def seed_state(self, repo: GitRepoFixture) -> str:
        repo.write("state/current.yaml", self.current_yaml())
        repo.write("state/platform-discovery.yaml", self.platform_discovery_yaml())
        repo.write("state/components.yaml", self.components_yaml())
        return repo.commit("state baseline")

    def test_allowed_f1_2c_progress_state_change_passes(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", self.current_yaml(last_ci_run_id=2))
        candidate = repo.commit("progress")
        self.assertEqual(self.classify(root, anchor, candidate)["decision"], "PASS")

    def test_production_authorization_true_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", self.current_yaml(production_authorized="true"))
        candidate = repo.commit("production")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )

    def test_production_gate_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", self.current_yaml(production_gate="AUTHORIZED"))
        candidate = repo.commit("gate")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )

    def test_credential_rotation_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", self.current_yaml(credential_rotation="AUTHORIZED"))
        candidate = repo.commit("rotation")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )

    def test_working_branch_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", self.current_yaml(working_branch="main"))
        candidate = repo.commit("branch")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )

    def test_unlisted_state_key_change_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write(
            "state/current.yaml",
            self.current_yaml(extra_status="  vps_resident_components: ONE\n"),
        )
        candidate = repo.commit("unlisted")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )

    def test_invalid_yaml_is_refused(self):
        repo, root = self.make_repo()
        anchor = self.seed_state(repo)
        repo.write("state/current.yaml", "platform_discovery: [\n")
        candidate = repo.commit("invalid yaml")
        self.assertEqual(
            self.classify(root, anchor, candidate)["reason"],
            "REFUSED_PROTECTED_STATE_CHANGE",
        )


if __name__ == "__main__":
    unittest.main()
