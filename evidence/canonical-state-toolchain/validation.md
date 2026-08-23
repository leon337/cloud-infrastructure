# Canonical State + Toolchain Reconciliation — Validation Evidence

Date: 2026-08-22
Branch: `team/canonical-state-toolchain-20260822`
Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`
PR: #22 (draft / do not merge)

## First neutral candidate

```text
SHA=55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6
WORKFLOW_RUN=32609819790
JOB=97120890824
```

Executed results:

```text
EXACT_SHA_CHECKOUT=PASS
UNPRIVILEGED_BOUNDARY=PASS
PINNED_SHELLCHECK_PROVISION=PASS
WORKSPACE_CLEAN=PASS
CANONICAL_SUITE=FAIL
GIT_DIFF_CHECK=FAIL_FOUR_TRAILING_WHITESPACE_FINDINGS
```

The four findings belonged to this mission's own report/evidence Markdown. Later suite stages were not executed because the entrypoint fails fast.

## Canonicity audit after the first run

Review against the proven F1.1 contract found that the first extracted secret scanner was weaker than the canonical generic gate: it scanned only current tracked files, while the original scanner also inspects reachable Git-history blobs and forbidden secret-bearing paths.

Generic contracts additionally proven separable:

- `scripts/check_repository_secrets.py`: current repository + reachable Git history;
- `scripts/check_markdown_links.py`: local Markdown targets;
- `scripts/yaml_strict.py` + `scripts/validate_yaml.py`: duplicate-key rejection.

`validate_manifests.py` is intentionally excluded because it depends on F1.1 platform schemas/manifests.

Audit verdict:

`HARDEN_TOOLCHAIN_BEFORE_ACCEPTANCE`.

## Hardened candidate rule

The next exact-head run must use the hardened neutral package. Repository-history findings are not to be allowlisted, skipped or converted to PASS merely to unblock hygiene. If a historical secret-policy finding is reproduced, it becomes explicit input to Repository Hygiene.

## Boundary verification

GitHub compare against `main` contains only state/toolchain/workflow/tests/docs/evidence surfaces. Functional G2-B/F1.2c implementation paths are outside the diff.

Current status:

```text
CANONICAL_ENTRYPOINT=RESTORED_EXECUTABLE
GENERIC_SECRET_HISTORY_GATE=PRESERVED
MARKDOWN_LINK_GATE=PRESERVED
STRICT_YAML_GATE=PRESERVED
F1_1_MANIFEST_VALIDATOR=EXCLUDED_AS_COUPLED
FINAL_EXACT_HEAD_EXECUTION=REQUIRED
OVERALL=VALIDATION_IN_PROGRESS
```
