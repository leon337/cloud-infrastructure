# Canonical State + Toolchain Reconciliation — Validation Evidence

Date: 2026-08-23
Branch: `team/canonical-state-toolchain-20260822`
Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`
PR: #22 (draft / do not merge)

## First executed neutral candidate

Run `32609819790`, job `97120890824`, candidate `55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6`:

```text
EXACT_SHA_CHECKOUT=PASS
UNPRIVILEGED_BOUNDARY=PASS
PINNED_SHELLCHECK_PROVISION=PASS
WORKSPACE_CLEAN=PASS
CANONICAL_SUITE=FAIL
GIT_DIFF_CHECK=FAIL_FOUR_TRAILING_WHITESPACE_FINDINGS
```

Those four extraction-owned findings were corrected.

## Canonicity hardening

Audit against the proven F1.1 lineage restored:

- reachable-history secret scanning;
- local Markdown links;
- strict YAML duplicate-key rejection;
- the GitHub-hosted `ubuntu-24.04` integration executor;
- Python 3.12 + locked neutral PyYAML dependency.

`validate_manifests.py` stays excluded as F1.1 implementation-coupled.

## Executed maintenance proof

Run `32610484209`, job `97122604465`, exact candidate `8d5353eb1d8550d849f81866b54266a4f5afc862` proved:

```text
EXACT_SHA_CHECKOUT=PASS
UNPRIVILEGED_BOUNDARY=PASS
NO_PASSWORDLESS_SUDO=PASS
NO_WRITABLE_DOCKER_SOCKET=PASS
PINNED_SHELLCHECK_PROVISION=PASS
GIT_DIFF_CHECK=PASS
CANONICAL_SUITE=FAIL_HISTORICAL_SECRET_POLICY
```

The canonical suite stopped at the reachable-history secret gate with exactly nine pre-existing `credential-in-uri` blobs. No secret value is reproduced here. The observed redacted blob prefixes were:

```text
0a5c72448f76
1463aa5966fc
26662227662e
43322571c9ce
54dcadd6c80d
5a8cf172a30d
9d45a9b256f4
b3cb6dcbce59
ed89ae930c82
```

Independent targeted evidence in the same job then proved:

```text
TARGETED_GIT_DIFF_CHECK_PASS
LOCAL_MARKDOWN_LINKS_PASS
YAML_PARSE_PASS count=5
CANONICAL_STATE_VALIDATION_PASS
CANONICAL_CONSISTENCY_PASS
UNIT_TESTS=12/12_PASS
TARGETED_PYTHON_SYNTAX_PASS count=8
TARGETED_SHELL_VALIDATION_PASS count=3
TARGETED_STATE_CONSISTENCY_PASS
```

The targeted diagnostic step generated Python bytecode cache directories, so the workflow-level clean-workspace assertion failed. `scripts/test.sh` already exported `PYTHONDONTWRITEBYTECODE=1`; the defect was isolated to the maintenance workflow and corrected in commit `84d1d23ff32ee1577958da9d754179eeb217ddb9` by applying that environment setting to the whole job.

## Hosted executor evidence

Hosted canonical runs repeatedly failed before executing repository steps. For head `e524ec4af8eb9b8fdf8220ee7b977a1158894c44`, run `32618609069` completed `failure` with `steps=null`; the job log endpoint returned external storage `BlobNotFound`. This is classified as an external hosted-executor blocker, not a repository-content verdict.

## Historical hygiene classification boundary

Repository Hygiene PR #19 independently recorded the same count of nine pre-existing historical `credential-in-uri` findings and classified them as historical security debt requiring separate review. The blobs are not present in the sampled current G2-B tree, the F1.1 founding snapshot, or sampled historical `main` snapshots.

That evidence is sufficient to prove the failures are not introduced by the State + Toolchain extraction. It is **not** sufficient to prove the historical values are synthetic or safe. Therefore:

- no credential finding is allowlisted;
- the reachable-history scan remains fail-closed;
- no history rewrite, force-push, credential rotation, or protected-line mutation is performed;
- the exact canonical suite remains red until the nine historical findings are classified/remediated under Repository Hygiene authority.

A temporary redacted diagnostic workflow was created only to collect provenance on the constrained self-hosted runner, but the job remained queued. It is removed from the final mission candidate rather than left as temporary repository surface.

## Final mission verdict

```text
STATE_RECONCILIATION=PASS_WITH_EXECUTABLE_TARGETED_EVIDENCE
TOOLCHAIN_CANONICITY=PASS
FUNCTIONAL_G2B_F1_2C_IMPORT_BOUNDARY=PASS
PRODUCTION_BOUNDARY=PASS
PROTECTED_LINE_MUTATION=PASS_NONE_PERFORMED
CANONICAL_FULL_SUITE=BLOCKED_PREEXISTING_HISTORICAL_SECURITY_DEBT
REPOSITORY_HYGIENE=BLOCKED_9_HISTORICAL_CREDENTIAL_URI_FINDINGS
HOSTED_EXECUTOR=EXTERNAL_PRE_STEP_FAILURE
PR22=DO_NOT_MERGE
```

Final classification: `CONCLUDED_WITH_VERIFIED_HISTORICAL_HYGIENE_BLOCKER`.
