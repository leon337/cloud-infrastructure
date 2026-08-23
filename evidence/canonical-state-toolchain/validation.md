# Canonical State + Toolchain Reconciliation — Validation Evidence

Date: 2026-08-22
Branch: `team/canonical-state-toolchain-20260822`
Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`
PR: #22 (draft / do not merge)

## Executed candidate 55cbbf0b

Run `32609819790`, job `97120890824`:

```text
EXACT_SHA_CHECKOUT=PASS
UNPRIVILEGED_BOUNDARY=PASS
PINNED_SHELLCHECK_PROVISION=PASS
WORKSPACE_CLEAN=PASS
CANONICAL_SUITE=FAIL
GIT_DIFF_CHECK=FAIL_FOUR_TRAILING_WHITESPACE_FINDINGS
```

Those four findings were owned by this front and were corrected.

## Canonicity hardening

Audit against the proven F1.1 lineage restored:

- reachable-history secret scanning;
- local Markdown links;
- strict YAML duplicate-key rejection;
- the GitHub-hosted `ubuntu-24.04` integration executor;
- Python 3.12 + locked neutral PyYAML dependency.

`validate_manifests.py` stays excluded as F1.1 implementation-coupled.

## Execution model

Canonical required CI:

```text
WORKFLOW=.github/workflows/canonical-validation.yml
RUNNER=ubuntu-24.04
PYTHON=3.12
LOCK=requirements-dev.lock
```

Maintenance proof:

```text
WORKFLOW=.github/workflows/canonical-validation-maintenance-proof.yml
RUNNER=NODE01_SELF_HOSTED_UNPRIVILEGED
SCOPE=team/canonical-state-toolchain-* OR manual dispatch
```

The maintenance proof does not replace the hosted CI path and must not preempt G2-B work occupying NODE-01.

## Current gate

Fresh exact-head execution is required. Interpret outcomes as follows:

- extraction-owned failure -> fix and rerun;
- historical `SECRET_POLICY_FAIL` -> Repository Hygiene blocker;
- hosted pre-step failure -> external execution blocker;
- NODE-01 proof queued behind G2-B -> wait for executor availability without interference.

Current state: `VALIDATION_IN_PROGRESS`.
