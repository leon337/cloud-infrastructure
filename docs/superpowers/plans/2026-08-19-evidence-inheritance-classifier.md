# Evidence Inheritance Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove a fail-closed F1.2c evidence-inheritance classifier without adding executable code to the F1.2c candidate being certified.

**Architecture:** Implement the classifier and its tests only on isolated branch `validation/evidence-inheritance-tool-20260819`. The classifier compares explicit Git commits using Git metadata plus semantic YAML comparison. It is F1.2c-specific and deny-by-default: only the exact documentation/evidence/state projection surfaces needed by the current lineage are eligible. A self-hosted unprivileged workflow runs the classifier against frozen candidate `c9f909945b544d22dbabc619252456f7190f7ae9`, while fresh static validation runs from a detached worktree of that exact candidate. Evidence is recorded in the validation PR/run, not committed back into the candidate before the gate decision.

**Tech Stack:** Python 3.12 standard library, PyYAML 6.x already present in the repository validation environment, Git CLI, GitHub Actions self-hosted runner `node-01 / mcf-control`, `unittest`, ShellCheck v0.11.0 pinned by SHA256.

**Spec:** `docs/superpowers/specs/2026-08-19-evidence-inheritance-non-executable-delta-design.md`

## Global Constraints

- Candidate under evaluation is frozen at `c9f909945b544d22dbabc619252456f7190f7ae9` until the inheritance decision is complete.
- Full disposable integration anchor is `f771cfd09f1824562ddfdaea507fb3cb0781f6ac`, with material lifecycle evidence recorded at run `32131461110` and companion foundation evidence already present in the checkpoint.
- No classifier code, tests or workflow may be committed to `codex/mission-001-f1-2c-network-enforcement` during this bootstrap.
- Unknown paths, deletions, renames/copies, file-mode/type changes, executable/operational paths, protected state changes, missing static evidence, invalid ancestry or parse errors must fail closed.
- The self-hosted runner must retain `no passwordless sudo` and `no read-write Docker socket` boundaries.
- No destructive integration test may run on NODE-01.
- No NODE-01 network-services apply is authorized by this plan; this plan only closes the evidence-inheritance gate.
- Production remains not authorized and credential rotation remains `DEFERRED_BY_HUMAN_DECISION`.

---

### Task 1: Add fail-closed path and Git-delta classification tests

**Files:**
- Create: `tests/test_evidence_inheritance.py`
- Create: `scripts/classify_evidence_inheritance.py`

**Interfaces:**
- Produces: `classify_repository_delta(repo: pathlib.Path, anchor: str, candidate: str) -> dict[str, object]`
- Produces: JSON result with `decision`, `reason`, `anchor`, `candidate`, `changed_paths`, `state_changes`, and `static_evidence` fields.
- Exit code `0` only for `PASS`; refusal exits `2`; invocation/internal validation errors exit `64`.

- [ ] **Step 1: Write failing tests for allowed and refused path classes**

Create tests using a temporary Git repository with deterministic commits. Cover at minimum:

```python
def test_history_only_delta_is_candidate_non_material(): ...
def test_checkpoint_modify_is_candidate_non_material(): ...
def test_script_change_is_refused_material_delta(): ...
def test_workflow_change_is_refused_material_delta(): ...
def test_unknown_path_is_refused_unknown_path(): ...
def test_deleted_document_is_refused(): ...
def test_rename_is_refused(): ...
def test_executable_bit_change_is_refused(): ...
def test_non_ancestor_candidate_is_refused_invalid_anchor(): ...
```

Allowed path surface for this F1.2c bootstrap is intentionally narrow:

```python
ALLOWED_DOC_EXACT = {
    "CHECKPOINT.md",
    "CONTEXT.md",
    "README.md",
    "docs/45-revised-implementation-roadmap.md",
    "docs/46-technology-mapping-v1.md",
    "docs/superpowers/specs/2026-08-19-evidence-inheritance-non-executable-delta-design.md",
}
ALLOWED_PREFIXES = ("history/", "evidence/SLICE-002C/")
STATE_FILES = {
    "state/current.yaml",
    "state/components.yaml",
    "state/platform-discovery.yaml",
}
```

Everything else is refused unless later approved in a new design revision.

- [ ] **Step 2: Run the new tests and verify RED**

Run:

```bash
python3 -m unittest -v tests.test_evidence_inheritance
```

Expected: FAIL because `scripts/classify_evidence_inheritance.py` does not yet implement the interfaces.

- [ ] **Step 3: Implement minimal Git-delta parser**

Implement SHA validation (`^[0-9a-f]{40}$`), ancestry check via `git merge-base --is-ancestor`, and raw delta inspection via Git so status and modes are available. Refuse `D`, `R`, `C`, mode/type changes and any path outside the exact allowlist. Do not use shell interpolation; invoke Git with `subprocess.run([...], check=False, text=False)` argument arrays.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run the same unittest command. Expected: path/ancestry tests PASS; state-specific tests are added next.

- [ ] **Step 5: Commit Task 1 on the validation branch**

```bash
git add tests/test_evidence_inheritance.py scripts/classify_evidence_inheritance.py
git commit -m "test(f1.2c): add fail-closed evidence delta classifier"
```

### Task 2: Add semantic state protection and exact F1.2c progress allowlists

**Files:**
- Modify: `tests/test_evidence_inheritance.py`
- Modify: `scripts/classify_evidence_inheritance.py`

**Interfaces:**
- Produces: `diff_yaml_paths(before: object, after: object) -> list[str]`
- Produces: `validate_state_delta(repo, anchor, candidate, changed_state_files) -> dict[str, object]`

- [ ] **Step 1: Write failing tests for protected and allowed state changes**

Tests must prove that a harmless F1.2c progress projection passes but each protected safety change refuses independently:

```python
def test_allowed_f1_2c_progress_state_change_passes(): ...
def test_production_authorization_true_is_refused(): ...
def test_production_gate_change_is_refused(): ...
def test_credential_rotation_change_is_refused(): ...
def test_working_branch_change_is_refused(): ...
def test_unlisted_state_key_change_is_refused(): ...
def test_invalid_yaml_is_refused(): ...
```

- [ ] **Step 2: Run state tests and verify RED**

Expected: FAIL because semantic YAML comparison is not implemented.

- [ ] **Step 3: Implement recursive YAML path diff and exact allowlists**

Use `yaml.safe_load` on `git show <sha>:<path>` content. The only state keys eligible to differ are:

```python
ALLOWED_STATE_PATHS = {
    "state/current.yaml": {
        "documentation_state",
        "project.phases.future_platform_implementation",
        "project.next_exact_step",
        "status_layer.last_material_checkpoint",
        "status_layer.last_relevant_commit",
        "status_layer.last_ci_run_id",
        "authorization.next_step",
        "codex_execution.active_slice",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.status",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.disposable_integration",
        "codex_execution.repo_only_preparations.network_enforcement_f1_2c.node_01_services_desired_state",
    },
    "state/components.yaml": {
        "platform_components.network_enforcement.lifecycle",
        "platform_components.network_enforcement.validation.disposable_integration",
        "platform_components.network_enforcement.validation.node_01_services_desired_state",
    },
    "state/platform-discovery.yaml": {
        "phase",
        "implementation.current_slice_status",
        "implementation.next_step",
        "implementation.f1_2c_repo_only.status",
        "implementation.f1_2c_repo_only.disposable_integration",
        "implementation.f1_2c_repo_only.node_01_services_desired_state",
    },
}
```

Additionally assert candidate protected values exactly:

```python
PROTECTED_EXPECTED = {
    ("state/current.yaml", "platform_discovery.production_promotion_authorized"): False,
    ("state/current.yaml", "authorization.production_promotion"): "NOT_AUTHORIZED_HUMAN_GATE_REQUIRED",
    ("state/current.yaml", "project.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/current.yaml", "authorization.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/current.yaml", "codex_execution.working_branch"): "codex/mission-001-f1-2c-network-enforcement",
    ("state/current.yaml", "codex_execution.mission"): "docs/CODEX-EXECUTION-MISSION-001.md",
    ("state/platform-discovery.yaml", "production_promotion_authorized"): False,
    ("state/platform-discovery.yaml", "credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/platform-discovery.yaml", "execution_mission"): "docs/CODEX-EXECUTION-MISSION-001.md",
    ("state/platform-discovery.yaml", "implementation.production_promotion"): "NOT_AUTHORIZED",
    ("state/platform-discovery.yaml", "implementation.credential_rotation"): "DEFERRED_BY_HUMAN_DECISION",
    ("state/components.yaml", "production.deployment_authorized"): False,
    ("state/components.yaml", "production.promotion_gate"): "LEANDRO",
    ("state/components.yaml", "credential_rotation.status"): "DEFERRED_BY_HUMAN_DECISION",
}
```

Any changed YAML path outside the allowlist returns `REFUSED_PROTECTED_STATE_CHANGE`; missing protected values also refuse.

- [ ] **Step 4: Run focused tests and full static repository suite**

Run:

```bash
python3 -m unittest -v tests.test_evidence_inheritance
REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=0 scripts/test.sh
```

Expected: all classifier tests PASS; repository unit suite remains green.

- [ ] **Step 5: Commit Task 2**

```bash
git add tests/test_evidence_inheritance.py scripts/classify_evidence_inheritance.py
git commit -m "feat(f1.2c): protect inherited evidence state semantics"
```

### Task 3: Add CLI evidence record and real frozen-candidate regression test

**Files:**
- Modify: `tests/test_evidence_inheritance.py`
- Modify: `scripts/classify_evidence_inheritance.py`

**Interfaces:**
- CLI: `python3 scripts/classify_evidence_inheritance.py --anchor SHA --candidate SHA --static-run-id ID --static-conclusion PASS [--output PATH]`
- JSON result must be deterministic (`sort_keys=True`) and contain no secrets or file contents.

- [ ] **Step 1: Write failing CLI and real-lineage tests**

Add tests that invoke the CLI and verify exit codes/JSON. Add repository regression test:

```python
ANCHOR = "f771cfd09f1824562ddfdaea507fb3cb0781f6ac"
CANDIDATE = "c9f909945b544d22dbabc619252456f7190f7ae9"

def test_real_f1_2c_candidate_is_non_material_and_guard_safe():
    result = classify_repository_delta(REPOSITORY_ROOT, ANCHOR, CANDIDATE)
    assert result["decision"] == "PASS"
```

Also prove `--static-conclusion FAIL` and missing static evidence return `REFUSED_STATIC_EVIDENCE_MISSING`.

- [ ] **Step 2: Run and verify RED**

Expected: CLI/static-evidence assertions fail before implementation.

- [ ] **Step 3: Implement CLI and deterministic JSON record**

The record must include:

```json
{
  "schema_version": 1,
  "policy": "F1_2C_NON_EXECUTABLE_EVIDENCE_INHERITANCE_V1",
  "decision": "PASS",
  "reason": "NON_EXECUTABLE_DELTA_GUARDS_UNCHANGED_STATIC_PASS",
  "anchor": "...",
  "candidate": "...",
  "changed_paths": [],
  "state_changes": {},
  "protected_state": "PASS",
  "static_evidence": {"run_id": "...", "conclusion": "PASS"}
}
```

No timestamps are generated by the classifier itself; GitHub run metadata supplies time externally, keeping output deterministic for identical inputs.

- [ ] **Step 4: Run focused and repository tests**

Expected: real frozen candidate returns PASS; all negative cases refuse.

- [ ] **Step 5: Commit Task 3**

```bash
git add tests/test_evidence_inheritance.py scripts/classify_evidence_inheritance.py
git commit -m "feat(f1.2c): emit deterministic inheritance evidence"
```

### Task 4: Prove the classifier and frozen candidate on the free self-hosted runner

**Files:**
- Create: `.github/workflows/evidence-inheritance-lab.yml`

**Interfaces:**
- Self-hosted runner labels: `[self-hosted, linux, x64, node-01, mcf-control]`
- Candidate: `c9f909945b544d22dbabc619252456f7190f7ae9`
- Anchor: `f771cfd09f1824562ddfdaea507fb3cb0781f6ac`

- [ ] **Step 1: Add a self-hosted-only workflow**

Workflow requirements:

```yaml
permissions:
  contents: read
jobs:
  validate-inheritance:
    runs-on: [self-hosted, linux, x64, node-01, mcf-control]
    timeout-minutes: 10
```

Checkout must use pinned `actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`, `fetch-depth: 0`, `persist-credentials: false`.

- [ ] **Step 2: Enforce runner boundary before tests**

Fail if `sudo -n true` succeeds or if `/var/run/docker.sock` is read-write for the runner. Print only sanitized boundary status.

- [ ] **Step 3: Run lab classifier tests**

Run `python3 -m unittest -v tests.test_evidence_inheritance`.

- [ ] **Step 4: Create detached worktree for the exact F1.2c candidate and run fresh static validation**

Create `${RUNNER_TEMP}/f1-2c-candidate`, detached at exact candidate SHA. Provision ShellCheck v0.11.0 in runner temp with SHA256 `8c3be12b05d5c177a04c29e3c78ce89ac86f1595681cab149b65b97c4e227198`. From the candidate worktree run:

```bash
PYTHON=python3 REQUIRE_ANSIBLE=0 REQUIRE_SHELLCHECK=1 scripts/test.sh
```

The worktree must remain clean and be removed in an `always()` cleanup step.

- [ ] **Step 5: Run classifier after static validation**

Run from the lab checkout:

```bash
python3 scripts/classify_evidence_inheritance.py \
  --anchor f771cfd09f1824562ddfdaea507fb3cb0781f6ac \
  --candidate c9f909945b544d22dbabc619252456f7190f7ae9 \
  --static-run-id "${GITHUB_RUN_ID}" \
  --static-conclusion PASS \
  --output "${RUNNER_TEMP}/evidence-inheritance.json"
cat "${RUNNER_TEMP}/evidence-inheritance.json"
```

Expected decision: `PASS`.

- [ ] **Step 6: Commit workflow and open a draft validation PR to the frozen F1.2c branch**

The PR body must explicitly state that the validator branch is not to be merged before a future full disposable test of the classifier implementation itself.

### Task 5: Record the gate result externally and hand back to F1.2c execution

**Files:**
- No candidate-branch file changes in this task.
- Record result in validation PR conversation and, if useful, PR #7 conversation.

**Interfaces:**
- Evidence source: successful self-hosted run/job logs.
- Required record: anchor SHA, candidate SHA, changed paths, state-path decision, protected-state PASS, static suite counts, runner privilege boundary and classifier decision.

- [ ] **Step 1: Verify workflow completion and logs**

Require all workflow steps to be `success`, including candidate static validation and classifier PASS. Do not treat queued/in-progress as evidence.

- [ ] **Step 2: Review the exact changed-path list against GitHub compare output**

Expected current delta contains only `CHECKPOINT.md`, `CONTEXT.md`, `README.md`, docs 45/46/spec, `evidence/SLICE-002C/**`, `history/**`, and the three state files. Any new path blocks the gate.

- [ ] **Step 3: Add sanitized PR evidence comment**

Record the machine-readable result and human summary. Do not modify the candidate branch, so `c9f909...` remains exactly the SHA certified by the classifier/static run.

- [ ] **Step 4: Declare evidence-inheritance gate satisfied only if all conditions pass**

Use wording equivalent to:

`F1_2C_EVIDENCE_INHERITANCE_PASS — integration inherited from f771cfd/run 32131461110; static evidence fresh on c9f909; current HEAD did not itself run destructive integration.`

- [ ] **Step 5: Continue to the existing next operational gate**

Return to `SLICE_002C_VERIFY_RUNNER_AND_APPLY_NODE_01_NETWORK_SERVICES`: recheck the temporary privileged runner/status path. If the signed privileged runner is expired/absent and cannot be reactivated without personal sudo/SSH signing, stop only that path at the existing HUMAN_GATE and provide the single minimal human action from the runbook. No apply occurs before that gate is satisfied.

## Self-review

- Spec coverage: path classification, protected state, fresh static validation, unprivileged boundary, deterministic evidence record, real lineage regression and fail-closed behavior are all mapped to Tasks 1–5.
- Bootstrap paradox resolved: executable classifier/workflow code lives only on the isolated validation branch and is not part of candidate `c9f909...`.
- Candidate evidence is external to the candidate branch until the operational gate completes, preventing an evidence-record commit from changing the SHA being certified.
- No placeholders or unspecified error-handling steps remain.
- Production, credential rotation, Docker socket, unrestricted sudo and destructive NODE-01 testing remain prohibited.
