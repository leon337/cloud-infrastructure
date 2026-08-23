# Canonical State + Toolchain Reconciliation — 2026-08-22

Status: **VALIDATION_IN_PROGRESS**

Investigation conclusion: **C — governance/integration decision required**.
Human gate: **RESOLVED — LEANDRO authorized a mainline-neutral extraction**.

## Mission boundary

This isolated front reconciles canonical state and validation without changing functional G2-B or F1.2c implementation, protected lineages, privileged NODE-01 state, branch hygiene operations, or production.

Base selected for integration work: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
Branch: `team/canonical-state-toolchain-20260822`.
PR: `#22`, draft, no final merge authorized.

## State source of truth

Neither historical structured snapshot is current truth:

- `main/state/current.yaml` was a 2026-08-18 snapshot;
- the G2-B branch-local `state/current.yaml` represented an earlier Task-8 state;
- the later read-only audit run `32577815107` and merged PR #18 establish the terminal attempt-3 observation for the historical G2-B candidate;
- live parallel PRs must still be read live because their heads and diagnostic progress can change independently.

The reconciled candidate `state/current.yaml` therefore records proven facts and explicitly labels volatile or unverified fields instead of copying a newer branch wholesale.

Current durable facts encoded by the candidate include:

| Area | Reconciled state |
|---|---|
| Main integration | `DOCUMENTATION_AND_INTEGRATION_DRIFT` |
| S0 / F1.1 / F1.2b | `COMPLETE` |
| F1.2c | `REQUIRES_REVIEW`, not accepted, NODE-01 reapply not authorized |
| G1 | `PASS_REAL_NODE_01_ROUNDTRIP` |
| G2-A | `PASS_REAL_NODE_01_READ_ONLY` |
| G2-B Tasks 1–7 | `COMPLETE` |
| G2-B Task 8 historical terminal attempt | `FAILED_ATTEMPT_3_NOT_ACCEPTED` |
| G2-B Task 8 current diagnostic | `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`; root cause remains `NOT_VERIFIED` |
| G2-B Tasks 9–10 | `NOT_STARTED` |
| Production | `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` |
| Repository Hygiene | `REPOSITORY_HYGIENE_BLOCKED` pending canonical green evidence |

## Canonical toolchain lineage

The canonical validation entrypoint is `scripts/test.sh`.

Its first verified origin is commit `edd2497d657cc9bc35952f5dfc71090a18dade53` on `codex/mission-001-foundations-f1-1`, represented by PR #2. The same commit adds `.github/workflows/foundation-ci.yml`, which invokes `scripts/test.sh` as the repository validation command.

The original F1.1 implementation is not copied because its validator package directly depends on F1.1 state, inventory, Ansible, evidence and implementation artifacts. Later versions add F1.2c, G1 and G2-B-specific checks. Copying a later whole lineage would violate this mission boundary.

### Neutral extraction authorized by LEANDRO

The authorized package preserves the stable entrypoint while implementing only contracts owned by the current mainline:

- `scripts/test.sh`;
- `scripts/check_current_tree_secrets.py`;
- `scripts/validate_yaml.py`;
- `scripts/validate_state.py`;
- `scripts/check_canonical_consistency.py`;
- unit tests for canonical state and toolchain contract;
- `.github/workflows/canonical-validation.yml`.

The suite validates `git diff --check`, current tracked-tree high-confidence secret patterns, YAML parseability, state invariants, cross-document consistency, Python syntax, shell syntax and ShellCheck.

## Continuity artifacts

### `state/active-mission.yaml`

Exact introduction: `5717defcf59e6a4cb664119f74227d7f5dee812a` (`docs(continuity): add canonical active mission state`), after recovered G2-B checkpoint `7205a647f918580d09c87ed44f38b0a433552a51`.

Decision: **NOT_ADOPTED** in the neutral package. The recovered artifact models one active mission, while current mainline governance has multiple isolated parallel fronts. Promoting it now would invent an unapproved single-active hierarchy.

### `ROADMAP-CHECKLIST.md`

Exact introduction: `48146d3ed6a7d28215b9d34f3954673054738d0a` (`checkpoint(g2b): record Task 8 external boundary blocker`), absent through parent `8e696288cb8f02b79ee130ac7cc5eca42ab6c961`.

Decision: **NOT_ADOPTED**. Its origin is a G2-B Task-8 checkpoint surface, not a mainline-neutral predecessor. `README.md` remains the executive projection.

## First exact-head validation attempt

Candidate SHA: `55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6`.
Workflow run: `32609819790`.
Job: `97120890824`.

Executed evidence:

- exact SHA checkout: PASS;
- unprivileged NODE-01 runner boundary: PASS;
- passwordless sudo refusal boundary: PASS;
- writable Docker socket refusal boundary: PASS;
- pinned ShellCheck download/hash: PASS;
- workspace cleanliness after execution: PASS;
- canonical suite: FAIL at the first `git diff --check` gate.

The failure was four trailing-whitespace findings in this mission's own report/evidence Markdown. This is a real content failure, not an infrastructure failure. No later validator in the suite was reached on that attempt.

This checkpoint removes those four whitespace defects and must be revalidated on its own exact SHA before PASS can be claimed.

## Explicitly avoided

- no G2-B Task 8 functional correction;
- no F1.2c functional correction or NODE-01 reapply;
- no protected-lineage rewrite or force push;
- no branch deletion;
- no privileged NODE-01 operation;
- no production promotion;
- no copying of branch-local G2-B/F1.2c state as main truth;
- no claim that queued, partial, or failed validation equals PASS.

## Acceptance gate

PASS requires a final exact-head run proving:

1. `git diff --check` PASS against the PR base;
2. `./scripts/test.sh` PASS;
3. state validation and consistency PASS;
4. unit tests, Python/shell syntax and ShellCheck PASS;
5. clean workspace;
6. GitHub compare contains no functional G2-B/F1.2c paths;
7. run/job/SHA evidence persisted in the PR checkpoint.

Until those conditions are all true, Repository Hygiene remains blocked.
