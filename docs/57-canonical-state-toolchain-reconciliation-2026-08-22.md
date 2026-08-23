# Canonical State + Toolchain Reconciliation — 2026-08-22

Status: **VALIDATION_IN_PROGRESS**

Investigation conclusion: **C — governance/integration decision required**.
Human gate: **RESOLVED — LEANDRO authorized a mainline-neutral extraction**.

## Mission boundary

This isolated front reconciles canonical state and validation without changing functional G2-B or F1.2c implementation, protected lineages, privileged NODE-01 state, branch hygiene operations, or production.

Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
Branch: `team/canonical-state-toolchain-20260822`.
PR: `#22`, draft, no final merge authorized.

## State decision

`state/current.yaml` was reconciled from evidence rather than copied from either stale structured snapshot. It records durable facts and labels volatile branch work as live/diagnostic rather than promoting it to integrated main state.

Core nonpromotion facts are F1.2c `REQUIRES_REVIEW`, G2-B historical Task-8 attempt `FAILED_ATTEMPT_3_NOT_ACCEPTED` with root cause `NOT_VERIFIED`, Tasks 9–10 `NOT_STARTED`, production closed, and Repository Hygiene still blocked.

## Toolchain lineage and extraction

`scripts/test.sh` is the proven canonical entrypoint. Its first verified origin is `edd2497d657cc9bc35952f5dfc71090a18dade53` on `codex/mission-001-foundations-f1-1` / PR #2, where `.github/workflows/foundation-ci.yml` invokes it as the repository validation command.

The F1.1 state/manifests/Ansible implementation package is not separable as a whole. The authorized extraction therefore retains only generic contracts that are valid independently of F1.1/G2-B/F1.2c functional code.

### Preserved generic contracts

- `git diff --check`;
- original-style repository secret policy across current files and reachable Git history;
- local Markdown link checking;
- strict YAML parse with duplicate-key rejection;
- an adapted mainline-neutral `state/current.yaml` validator;
- cross-document consistency;
- unit tests, Python/shell syntax and ShellCheck.

### Explicitly excluded coupled contract

`validate_manifests.py` is not imported because it requires F1.1 platform schemas/manifests and implementation semantics.

The first extraction mistakenly narrowed the secret gate to the current tree. Emily's canonicity audit rejected that weakening. The hardened candidate restores the reachable-history contract even though it may reveal a real Repository Hygiene blocker. A green result will not be manufactured by hiding historical findings.

## Continuity artifacts

`state/active-mission.yaml` remains **NOT_ADOPTED**. It was introduced at `5717defcf59e6a4cb664119f74227d7f5dee812a` in the post-recovery G2-B continuity lineage and models one active mission, while current mainline work has multiple isolated parallel fronts.

`ROADMAP-CHECKLIST.md` remains **NOT_ADOPTED**. It was introduced at `48146d3ed6a7d28215b9d34f3954673054738d0a` as a G2-B Task-8 checkpoint surface.

## Executed validation evidence

Candidate `55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6`, run `32609819790`, job `97120890824`:

- exact checkout: PASS;
- nonprivileged runner boundary: PASS;
- pinned ShellCheck provision: PASS;
- workspace clean: PASS;
- suite: FAIL at `git diff --check` on four trailing-whitespace defects in this front's Markdown.

Those four defects were corrected. Before the next candidate could be accepted, the canonicity audit restored the stronger generic secret/Markdown/YAML contracts described above. The hardened candidate therefore requires a fresh exact-head run from the beginning.

## Boundary evidence

GitHub compare against main contains state/toolchain/tests/docs/workflow changes only. No functional G2-B/F1.2c implementation path is imported. No protected ref was rewritten, no branch was deleted, no privileged NODE-01 action occurred, and production remains untouched.

## Acceptance interpretation

If the hardened suite reaches a repository-history `SECRET_POLICY_FAIL`, that is evidence that the canonical toolchain is functioning and that Repository Hygiene has a real remaining blocker. This front must report it rather than weaken the scanner.

If a failure is caused by this extraction itself, this front remains blocked until corrected and revalidated.

No final merge is authorized by this report.
