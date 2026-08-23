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

## Prior mission verdict before historical-hygiene resolution

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

Final classification at that point: `CONCLUDED_WITH_VERIFIED_HISTORICAL_HYGIENE_BLOCKER`.


## Historical-hygiene resolution follow-up

A full `--mirror` clone was created on the connected local host so the audit could see repository refs that the earlier Actions checkout did not expose. No credential value was printed or persisted in evidence.

The nine historical `credential-in-uri` blobs were mapped to historical operational GitHub Actions workflows. Redacted classification of all nine returned the same result:

```text
KNOWN_AUTH_MARKER / SYMBOLIC_RUNTIME_REFERENCE / GITHUB
```

Therefore the nine raw regex hits contained runtime credential references, not literal versioned passwords or tokens. The policy defect was that `credential-in-uri` treated a pure symbolic runtime reference as if it were literal credential material. The correction keeps literal credentials fail-closed and does not add a blob-specific allowlist for these nine objects.

The full mirror also exposed one additional historical `secret-like-assignment` blob, `af1ce6811000...`, from the temporary redacted diagnostic workflow created by this mission. Inspection of that historical source proved the matched assignment is analyzer code assigning `match.group(...)` to a local variable named `password`; it contains no credential value. That single normalized line is covered by an exact SHA-256 allowlist using the scanner's pre-existing non-secret historical-line mechanism.

TDD evidence:

```text
RED: symbolic runtime credential URI was rejected by the old policy
GREEN: symbolic runtime credential URI accepted
GREEN: literal credential URI remains rejected
RED: known non-secret historical diagnostic assignment rejected before exact hash allowlist
GREEN: exact diagnostic line allowlisted; all other assignment-shaped history remains scanned
```

Pre-publication full-history worktree validation then proved:

```text
GIT_DIFF_CHECK_PASS
SECRET_POLICY_PASS
LOCAL_MARKDOWN_LINKS_PASS
YAML_PARSE_PASS count=5
CANONICAL_STATE_VALIDATION_PASS
CANONICAL_CONSISTENCY_PASS
UNIT_TESTS=15/15_PASS
PYTHON_SYNTAX_PASS count=8
SHELL_SYNTAX_PASS count=3
CANONICAL_VALIDATION_PASS
```

ShellCheck was not installed on the connected local host, so `scripts/test.sh` used its documented non-CI skip path for that stage. The earlier constrained maintenance proof had already passed pinned ShellCheck, and this resolution changes no shell script. Exact-head CI remains a separate executor check.

No history rewrite, force-push, credential rotation, protected-line mutation, production action, G2-B functional change, or F1.2c functional change was required.

## Current resolution verdict

```text
STATE_RECONCILIATION=PASS_WITH_EXECUTABLE_FULL_SUITE_EVIDENCE
TOOLCHAIN_CANONICITY=PASS
SECRET_POLICY=PASS_LOCAL_FULL_HISTORY
HISTORICAL_CREDENTIAL_URI_LITERAL_FINDINGS=0
HISTORICAL_SYMBOLIC_RUNTIME_REFERENCES_CLASSIFIED=9
TEMP_DIAGNOSTIC_NON_SECRET_ASSIGNMENT=EXACT_LINE_HASH_ALLOWLISTED
FUNCTIONAL_G2B_F1_2C_IMPORT_BOUNDARY=PASS
PRODUCTION_BOUNDARY=PASS
PROTECTED_LINE_MUTATION=PASS_NONE_PERFORMED
REPOSITORY_HYGIENE_REVALIDATION=PASS_AGAINST_CANONICAL_TOOLCHAIN
HOSTED_EXECUTOR=EXTERNAL_PRE_STEP_FAILURE
PR22=DRAFT_DO_NOT_MERGE_PENDING_EXACT_HEAD_AND_HUMAN_REVIEW
```

Current classification: `CONCLUDED_STATE_TOOLCHAIN_VALIDATED_LOCAL_FULL_HISTORY`.
## Repository Hygiene revalidation handoff

PR #19 final published head `f34aec6c641fb577d620446df4a743df3ff3fa5d` was revalidated against this canonical toolchain head `f39464daf4a4c5508d891e61f4ddd6394afd08fd`. A local-only synthetic integration candidate `3a6b040c67334aeb7f0411f3d6b7c712ed52987b` resolved exactly `CHECKPOINT.md` and `CONTEXT.md` in favor of the newer canonical projections and passed `git diff --check`, secret policy, Markdown/YAML/state/consistency, 15/15 unit tests, Python/shell syntax, and the canonical validation suite with a clean worktree before and after.

Repository Hygiene is therefore `REPOSITORY_HYGIENE_REVALIDATED`. Branch cleanup remains a separate lifecycle operation and is not required for content integration.
