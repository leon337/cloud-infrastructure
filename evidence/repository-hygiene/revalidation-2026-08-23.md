# Repository Hygiene Revalidation — 2026-08-23

This document records the Repository Hygiene revalidation procedure. Earlier reports under `evidence/repository-hygiene/` remain preserved as dated 2026-08-22 snapshots and are not rewritten as if their original observations had never occurred.

Because this evidence file and its supersession addenda are themselves committed to PR #19, this file records the **pre-evidence content head** used for the first synthetic validation. The exact post-publication PR #19 head and its final synthetic revalidation SHA are recorded in the live PR #19 metadata after publication and final rerun.

## Inputs

- Repository: `leon337/cloud-infrastructure`
- PR #19 pre-evidence content head: `5b0864762e2c3054da4e449feb1e47abc584963f`
- Canonical State + Toolchain head: `f39464daf4a4c5508d891e61f4ddd6394afd08fd` (PR #22)
- Common base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`
- First local synthetic merge candidate: `da4cba0ccb768e01afeb445678478fb3f39d30b0`
- Synthetic parents: PR #22 head first, PR #19 pre-evidence content head second.

The synthetic candidate was local-only and was never pushed or merged.

## Conflict resolution

Combining PR #19 with the newer canonical State + Toolchain produced exactly two text conflicts:

- `CHECKPOINT.md`
- `CONTEXT.md`

Resolution policy followed repository truth precedence: the newer PR #22 canonical State + Toolchain versions win for those two canonical entry files. The older PR #19 edits to those same files are therefore `SUPERSEDED_BY_CANONICAL_STATE_TOOLCHAIN`, not silently promoted.

The remaining Repository Hygiene files integrated without conflict and were preserved in the synthetic candidate.

## Security-policy revalidation

PR #22 resolved the historical secret-policy blocker through a full private mirror audit without printing credential values:

- historical `credential-in-uri` blobs previously reported: 9;
- classified as GitHub workflow symbolic runtime authentication references: 9/9;
- literal historical credential URI findings: 0;
- no blob-specific allowlist added for those nine;
- literal credential URIs remain fail-closed.

A separate historical `secret-like-assignment` match created by PR #22's temporary diagnostic workflow was proven to be analyzer code assigning `match.group(...)` to a local variable, not a credential value. Only the SHA-256 of that exact normalized non-secret line was added to the pre-existing historical-line allowlist mechanism.

No history rewrite, force-push, credential rotation, protected-line mutation, or production action was required.

## First executable revalidation

The first local synthetic candidate was committed only to obtain a deterministic local SHA and validated from a clean worktree.

```text
SYNTHETIC_SHA=da4cba0ccb768e01afeb445678478fb3f39d30b0
WORKTREE_BEFORE_TEST=0
GIT_DIFF_CHECK_PASS
SECRET_POLICY_PASS
LOCAL_MARKDOWN_LINKS_PASS
YAML_PARSE_PASS count=5
CANONICAL_STATE_VALIDATION_PASS
CANONICAL_CONSISTENCY_PASS
UNIT_TESTS=15/15_PASS
PYTHON_SYNTAX_PASS count=9
SHELL_SYNTAX_PASS count=3
CANONICAL_VALIDATION_PASS
WORKTREE_AFTER_TEST=0
EXACT_SYNTHETIC_REVALIDATION=PASS
```

ShellCheck was not installed on the connected local host and therefore followed the documented non-CI skip path. PR #19 adds no shell script and the PR #22 maintenance proof had already passed pinned ShellCheck for the canonical shell surface.

## Superseded blockers

The following 2026-08-22 statements are historical and no longer current blockers:

- canonical structured state cannot be reconciled;
- `scripts/test.sh` is absent from the usable integration toolchain;
- the nine historical `credential-in-uri` findings are unclassified;
- Repository Hygiene revalidation is blocked by those causes.

They remain visible in older evidence solely as provenance of the earlier state.

## Revalidation verdict

```text
REPOSITORY_HYGIENE_REVALIDATION=PASS_AGAINST_PR22_CANONICAL_TOOLCHAIN
PR19_CONTENT_COMPATIBILITY=PASS_WITH_TWO_SUPERSEDED_CANONICAL_DOC_CONFLICTS
SECRET_POLICY_BLOCKER=RESOLVED
PROTECTED_REF_MUTATION=NONE
PRODUCTION_ACTION=NONE
BRANCH_DELETION=NONE
MERGE_AUTHORIZATION=NOT_GRANTED
```

The live PR #19 metadata is the source for the exact published head and final post-publication rerun. PR #19 must remain draft / `DO NOT MERGE` until a separate human merge gate is explicitly opened. Branch cleanup is also a separate operation and is not authorized by this revalidation.
