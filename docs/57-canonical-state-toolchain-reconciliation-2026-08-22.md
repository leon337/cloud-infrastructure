# Canonical State + Toolchain Reconciliation — 2026-08-22

Status: **REQUIRES_HUMAN_DECISION**  
Conclusion class: **C — the current integration model is inconsistent and needs a governance/integration decision before state/toolchain promotion**

## Mission boundary

This report answers two questions without changing G2-B, F1.2c, protected branches, NODE-01 privileged state, or production:

1. What is the real canonical project state supported by current evidence?
2. What validation toolchain is proven canonical, and can it be restored to the main integration path without importing unrelated active implementation?

Base examined for this isolated mission: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.

## Executive decision

The **real current state is identifiable as an evidence set**, but it is not safely represented by either existing `state/current.yaml` snapshot:

- `main/state/current.yaml` is dated 2026-08-18 and predates the merged 2026-08-22 reconciliation;
- `codex/control-bridge-g2b/state/current.yaml` is newer but still records Task 8 as an earlier `BLOCKED_EXTERNAL` snapshot;
- merged `main/README.md` records the later observation: G2-B Tasks 1–7 complete, Task 8 `FAILED_ATTEMPT_3`, Tasks 9–10 not started, F1.2c partial with `cloud-platform-network-services.service` failed, and main in `DOCUMENTATION_AND_INTEGRATION_DRIFT`.

Therefore **neither structured state file may be copied as current truth**.

The validation entrypoint **`scripts/test.sh` is proven canonical**. It first appears in the verified F1.1 implementation commit `edd2497d657cc9bc35952f5dfc71090a18dade53`, where `.github/workflows/foundation-ci.yml` invokes it as the required repository validation command. However, that first executable package is coupled to F1.1 implementation/state artifacts, and later versions accumulate F1.2c, G1 and G2-B-specific checks. No already-existing mainline-neutral extraction was found.

Accordingly, copying only `scripts/test.sh` would create a broken toolchain, while importing its whole later lineage would cross this mission boundary. That is a governance/integration conflict, not a hygiene failure.

## State source of truth reconstructed

The state rewrite must be derived from current evidence, not from a desired future state. The following facts are supported by the live repository topology and the 2026-08-22 merged reconciliation:

| Fact | Current evidence | Reconciliation result |
|---|---|---|
| Main integration base | `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b` | canonical main base for this mission |
| Main structured state | `state/current.yaml`, updated 2026-08-18 | stale; must not be treated as current |
| Main executive reconciliation | `README.md` merged by PR #18 on 2026-08-22 | newest integrated current-state account |
| G2-B live branch | `codex/control-bridge-g2b@fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`, PR #11 draft | active work, not integrated |
| G2-B Tasks 1–7 | complete | current evidence supports COMPLETE |
| G2-B Task 8 | attempt 3 ended `apply_g2b exit=2`; acceptance markers not proven | FAILED_ATTEMPT_3 / NOT_ACCEPTED |
| G2-B Tasks 9–10 | not started | NOT_STARTED |
| F1.2c | implementation/worktree remains separate; current NODE-01 network-services unit failed | PARTIAL; do not advance |
| Production | no current authorization | NOT_AUTHORIZED_HUMAN_GATE_REQUIRED |
| Repository integration | later lineages are not fully on main | DOCUMENTATION_AND_INTEGRATION_DRIFT |
| Repository hygiene | PR #19 draft remains blocked | blocked until state + tests are legitimate |

### Required serialization rule for `state/current.yaml`

A future rewrite of `state/current.yaml` must encode the facts above and preserve uncertainty explicitly. It must not:

- promote G2-B Task 8 to PASS/COMPLETE;
- claim F1.2c accepted;
- claim production authorization;
- claim the G2-B branch-local continuity state is already integrated into main;
- treat a historical NODE-01 observation as a fresh observation;
- invent a single active mission model where integration governance has not selected one.

For this reason, this branch does **not** modify `state/current.yaml`. The fail-closed checkpoint is persisted separately in `state/canonical-state-toolchain-reconciliation.yaml`.

## Toolchain lineage

### 1. First verified canonical validation entrypoint

Commit `edd2497d657cc9bc35952f5dfc71090a18dade53` (`feat: establish mission baseline and foundation slice`) is the first verified commit in the investigated implementation lineage that adds both:

- `.github/workflows/foundation-ci.yml`;
- `scripts/test.sh`.

The workflow installs locked Python dependencies and ShellCheck, sets `REQUIRE_ANSIBLE=1` and `REQUIRE_SHELLCHECK=1`, and executes `scripts/test.sh`. This establishes `scripts/test.sh` as the repository validation entrypoint, not merely a convenience script.

This change is represented by draft PR #2, `Mission 001: baseline and Foundations F1.1`, based on `main@987c5359ea948d1903355e98177ae1eb2f1849d5`.

### 2. Why the F1.1 package is not separable by copying one file

The F1.1 `scripts/test.sh` calls repository validators including state validation, schema/manifests checks, unit tests, Python compilation, shell syntax, Ansible syntax and ShellCheck.

Its `scripts/validate_state.py` directly requires F1.1-specific repository objects, including:

- `state/components.yaml`;
- `evidence/SLICE-001/baseline.yaml`;
- DEV Ansible inventory and group vars;
- exact Q1–Q40 decisions;
- F1.1 real-VPS gate fields and evidence semantics;
- accepted VPS identity and implementation-base relationships.

Therefore `scripts/test.sh` without its package dependencies is not executable on current main. Importing the whole F1.1 commit solely for hygiene would also import Foundation implementation, desired-state and automation artifacts outside this mission.

### 3. Successor mutations of the toolchain

| Lineage | `scripts/test.sh` role/change | Boundary consequence |
|---|---|---|
| `codex/mission-001-foundations-f1-1` | establishes canonical entrypoint and F1.1 static suite | coupled to F1.1 implementation/state |
| `codex/mission-001-f1-2c-network-enforcement` | retains entrypoint and adds generated project-status consistency | carries F1.2c implementation dependencies |
| `mcf/mission-001-control-bridge-g1` | retains entrypoint and expands compilation/coverage for `control_plane` | carries G1/G2-A implementation |
| `codex/control-bridge-g2b` | retains entrypoint and adds `scripts/check_continuity_drift.py` | carries G2-B and branch-local continuity model |

The branch `validation/evidence-inheritance-tool-20260819` was also inspected. It diverges from main at `987c5359...` and contains a large F1.1/F1.2b/F1.2c implementation stack; it is not a neutral toolchain extraction.

## `state/active-mission.yaml` lineage and decision

`state/active-mission.yaml` is absent from:

- current `main`;
- `codex/mission-001-foundations-f1-1`;
- `codex/mission-001-f1-2c-network-enforcement`;
- `mcf/mission-001-control-bridge-g1`;
- recovered G2-B checkpoint `7205a647f918580d09c87ed44f38b0a433552a51`.

The exact introduction point is commit `5717defcf59e6a4cb664119f74227d7f5dee812a` (`docs(continuity): add canonical active mission state`), whose direct parent is the recovered G2-B checkpoint `7205a647f918580d09c87ed44f38b0a433552a51`. The file is therefore proven to originate in the post-recovery G2-B continuity lineage, not in F1.1/F1.2c/G1 or current main.

By continuity checkpoint `5db49d76dd530038aaf032aeba055b61eaab653a`, it describes `REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING`, references G2-B PR #11, isolates F1.2c, and is used by continuity/drift controls that are later wired into `scripts/test.sh`.

The later G2-B branch changes that same file to make `CONTROL_BRIDGE_G2B` the active mission. Its current contents are also stale relative to the merged 2026-08-22 attempt-3 reconciliation.

Decision: **the active-mission model is a real continuity artifact, but it is not yet proven to be a mainline-neutral, integrated canonical model. Do not copy it to main without selecting the governance/integration package that owns it.**

## `ROADMAP-CHECKLIST.md` lineage and decision

`ROADMAP-CHECKLIST.md` is absent from current main, F1.2c, G1, the recovered G2-B checkpoint `7205a647...`, continuity R7 checkpoint `5db49d76...`, and remains absent through commit `8e696288cb8f02b79ee130ac7cc5eca42ab6c961`.

The exact introduction point is the next commit, `48146d3ed6a7d28215b9d34f3954673054738d0a` (`checkpoint(g2b): record Task 8 external boundary blocker`). The first version explicitly names the G2-B branch and PR #11 and projects machine-readable state from `state/current.yaml` plus `state/control-bridge-g2b.yaml`. This proves that the checklist was introduced as a G2-B Task-8 checkpoint surface, not as a neutral predecessor artifact.

The current G2-B copy still advertises the earlier Task-8 external-block/QEMU-install step, while merged main `README.md` records Task-8 attempt 3 already failed. Therefore the file is not a safe source for current main state.

Decision: **do not restore/copy `ROADMAP-CHECKLIST.md` in this mission**. The merged main README is the fresher integrated roadmap/state projection until a neutral continuity package is explicitly selected and reconciled.

## PR and integration intent

- PR #2 demonstrates the origin and intended CI role of `scripts/test.sh`, but remains draft/unmerged and carries F1.1 implementation.
- PR #11 is the active G2-B draft and is explicitly not merge-eligible yet.
- PR #18 merged the current 2026-08-22 state/roadmap reconciliation into main via README.
- PR #19 is the hygiene integration checkpoint and explicitly blocks on canonical state and missing `scripts/test.sh`.

No inspected PR provides a ready, neutral extraction containing only current-state governance plus the canonical validation runner.

## Result classification

### A — separate recovery/integration

**Not proven.** Individual file copying is unsafe because the executable validation package has lineage dependencies, and the continuity files are branch-local/stale.

### B — wait for one active lineage to integrate

**Not selected.** Waiting for G2-B would unnecessarily bind repository hygiene to unfinished G2-B work. Waiting for F1.2c likewise crosses a boundary. PR #2 includes implementation rather than a neutral validation package.

### C — governance/integration decision required

**Selected.** The project has a proven canonical validation entrypoint but no proven neutral mainline package; the continuity model that introduces active-mission/drift controls is intertwined with G2-B state. A deliberate extraction/integration strategy is required before those artifacts can be made canonical on main.

## Safe integration choices for LEANDRO / MESTRE CENTRAL

1. **Authorize a mainline-neutral extraction**: factor only the generic validation/continuity contracts needed by current main, preserve `scripts/test.sh` as the canonical entrypoint, define a state validator for the selected main schema, and explicitly exclude F1.2c/G2-B functional code. This is the technically shortest route, but it is a governance change and must be explicitly selected.
2. **Wait for an explicit predecessor governance integration** that already contains a reviewed neutral state/validation package, then reconcile main against that package. Do not use “newest branch” as the selection rule.

Forbidden shortcut: cherry-pick/copy the latest G2-B/F1.2c versions of the four named files merely to satisfy hygiene.

## Proposed changes after the gate

If option 1 is authorized, the next isolated implementation should:

1. define the minimal mainline schema/continuity surfaces that `state/current.yaml` must validate;
2. extract/adapt only validators that are generic to that schema;
3. restore `scripts/test.sh` as the stable entrypoint and a CI workflow that invokes it;
4. reconcile `state/current.yaml` from current evidence, preserving `UNVERIFIED`/historical boundaries;
5. add `state/active-mission.yaml` only if the selected governance model requires it;
6. add/reconcile `ROADMAP-CHECKLIST.md` only if it remains a required independent surface rather than duplicating README;
7. run `git diff --check`, `./scripts/test.sh`, targeted state tests and continuity consistency checks;
8. verify no G2-B/F1.2c functional paths entered the diff;
9. hand the green SHA back to Repository Hygiene.

## Explicitly avoided

- no Task 8 G2-B correction;
- no F1.2c service correction;
- no protected branch modification;
- no branch deletion;
- no privileged NODE-01 action;
- no production promotion;
- no copy of stale branch-local state;
- no claim that missing validation equals PASS;
- no full-lineage import to manufacture a runnable test command.

## Checkpoint

Machine-readable checkpoint: `state/canonical-state-toolchain-reconciliation.yaml`.

Final mission state at this checkpoint: **REQUIRES_HUMAN_DECISION**.
