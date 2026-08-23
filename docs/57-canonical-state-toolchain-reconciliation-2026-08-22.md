# Canonical State + Toolchain Reconciliation — 2026-08-22

Status: **VALIDATION_IN_PROGRESS**

Investigation conclusion: **C — governance/integration decision required**.
Human gate: **RESOLVED — LEANDRO authorized a mainline-neutral extraction**.

## Mission boundary

Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
Branch: `team/canonical-state-toolchain-20260822`.
PR: `#22`, draft, no final merge authorized.

No functional G2-B/F1.2c code, privileged NODE-01 mutation, production promotion or branch cleanup belongs to this front.

## Canonical state

`state/current.yaml` is reconciled from evidence instead of copying stale main/G2-B snapshots. It preserves F1.2c as `REQUIRES_REVIEW`, historical G2-B Task 8 as `FAILED_ATTEMPT_3_NOT_ACCEPTED` with root cause `NOT_VERIFIED`, Tasks 9–10 `NOT_STARTED`, production closed and Repository Hygiene blocked until real validation/hygiene findings are resolved.

Volatile diagnostic heads are explicitly marked `READ_GITHUB_LIVE` rather than serialized as durable truth.

## Toolchain lineage

`scripts/test.sh` is the proven canonical entrypoint. Its first verified origin is `edd2497d657cc9bc35952f5dfc71090a18dade53` on F1.1 / PR #2.

The neutral extraction preserves generic, separable gates:

- `git diff --check`;
- current-tree + reachable-history secret policy;
- local Markdown links;
- strict YAML/duplicate-key rejection;
- neutral state and cross-document consistency;
- unit tests and Python/shell syntax;
- ShellCheck.

`validate_manifests.py` remains excluded because it is tied to F1.1 platform schemas/manifests.

## Canonical integration executor

The F1.1 workflow proves the intended CI boundary: `ubuntu-24.04`, Python 3.12, locked Python dependencies and ShellCheck. The extraction restores the same boundary in `.github/workflows/canonical-validation.yml`, with a minimal neutral `requirements-dev.lock` containing only `PyYAML==6.0.3`.

This is intentionally **not** moved onto NODE-01 merely because hosted Actions are currently unreliable.

## Maintenance proof executor

`.github/workflows/canonical-validation-maintenance-proof.yml` runs only for state/toolchain maintenance branches or manual dispatch. It executes the same `scripts/test.sh` on NODE-01 after proving no passwordless sudo and no writable Docker socket. It is evidence/fallback, not the required integration executor.

If the runner is occupied by G2-B, this front does not cancel or preempt that work.

## Continuity artifacts

`state/active-mission.yaml`: `NOT_ADOPTED`; introduced by `5717defcf59e6a4cb664119f74227d7f5dee812a` in G2-B continuity and based on a single-active-mission model not proven for current parallel fronts.

`ROADMAP-CHECKLIST.md`: `NOT_ADOPTED`; introduced by `48146d3ed6a7d28215b9d34f3954673054738d0a` as G2-B Task-8 checkpoint surface.

## Validation history

Candidate `55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6`, run `32609819790`, job `97120890824`, executed on NODE-01 and passed exact checkout/boundary/ShellCheck provisioning/workspace cleanliness, then failed `git diff --check` on four trailing spaces in this front's Markdown. Those defects are corrected.

The canonicity audit then restored the stronger generic secret/Markdown/YAML gates and the hosted CI boundary. Therefore the current candidate requires fresh execution.

Hosted runs that end before any step are classified as external execution blockers, not content failures. Maintenance-proof results are reported separately.

## Acceptance

This front will not weaken historical secret scanning to manufacture PASS. A reproduced historical `SECRET_POLICY_FAIL` is a real Repository Hygiene input. A failure in files introduced by this extraction remains owned by this front and must be corrected.

No final merge is authorized.
