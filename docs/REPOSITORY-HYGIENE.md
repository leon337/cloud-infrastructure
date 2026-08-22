# Repository Hygiene Policy

Status: proposed repository governance for `leon337/cloud-infrastructure`.

## Branch lifecycle classes

Every branch must have one of four lifecycle classes:

- **CANONICAL** — long-lived integration/source-of-truth ref, normally `main`.
- **ACTIVE** — current implementation, incident, validation or mission work with an identifiable owner.
- **TEMPORARY** — bounded operational/test/validation ref created for a disposable purpose.
- **HISTORICAL** — intentionally retained milestone or evidence ref that is no longer active.

A branch is never deleted merely because its name looks temporary.

## Required metadata for TEMPORARY branches

At creation time, the PR/issue/commit message must make these three facts recoverable:

1. **owner** — person/agent/front responsible;
2. **purpose** — the one bounded reason the branch exists;
3. **removal condition** — objective evidence that permits closure/deletion.

Recommended wording:

```text
Lifecycle: TEMPORARY
Owner: <owner>
Purpose: <bounded purpose>
Remove when: <objective condition>
Preservation target: <main/active branch/tag/issue/evidence>
```

If removal condition or preservation target is missing, classify `UNKNOWN_REQUIRES_REVIEW` rather than guessing.

## Naming

- `codex/*`, `mcf/*`, or another agent prefix: implementation/mission ownership; lifecycle is determined by metadata, not prefix alone.
- `ops/*`: short operational intervention. Default `TEMPORARY` unless explicitly promoted.
- `validation/*`: bounded validation lab. Default `TEMPORARY` or `ACTIVE` while an associated review remains open.
- `test/*`: disposable test branch. Default `TEMPORARY`.
- `fix/*`: active correction until integrated or formally superseded.
- `sanitization/*`: repository-hygiene work. Delete after its integrated result and evidence are preserved.

Use date suffixes for one-off operational branches when useful, e.g. `ops/<purpose>-YYYYMMDD`.

## Creation rules

Create a branch when work needs isolation, independent review, rollback or a different lifecycle from the parent. Do not create a branch only to wait for an external condition.

For active high-risk work, prefer a dedicated PR/issue anchor so ownership, gates and evidence are visible remotely.

## Removal rules

A branch is `SAFE_TO_DELETE` only when all are true:

1. its HEAD and merge-base are recorded;
2. commits exclusive to the branch are enumerated;
3. every relevant exclusive commit is proven preserved elsewhere **or** explicitly classified disposable with evidence;
4. associated PR/issue/evidence has reached a terminal state or no longer needs the ref;
5. it is not protected/canonical/active;
6. integration tests applicable to the cleanup have passed.

If exclusive commits exist and their value is uncertain, use `ARCHIVE_BEFORE_DELETE` or `UNKNOWN_REQUIRES_REVIEW`.

## Archiving and historical preservation

Preserve history in the cheapest adequate durable form:

- integrated commit ancestry when the branch is fully contained in a protected/active descendant;
- merged/squashed PR plus evidence when content has been intentionally consolidated;
- a retained `HISTORICAL` branch when the branch itself is a useful milestone;
- a tag or explicit evidence record before deletion when unique commits must remain addressable.

Never force-push a protected/canonical branch as a hygiene operation.

## PR lifecycle

Temporary PRs must state `DO NOT MERGE` when they are only a validation vehicle. Close them as soon as their bounded purpose is complete **after** preservation is established. Closing a PR does not automatically make its branch safe to delete.

Stale implementation PRs with unique commits are `REQUIRES_HUMAN_REVIEW` unless a successor lineage is proven to preserve the work.

## Workflow lifecycle

Temporary workflows must have a removal condition and should be removed from the canonical branch immediately after their bounded proof is complete.

Permanent rule:

> **SELF-HOSTED RUNNER IS NOT A WAIT/POLLING MECHANISM.**

- self-hosted NODE-01 jobs are short, bounded request/probe executions;
- long-running work runs as a detached process/service on the VPS or in a disposable hosted environment;
- status probes are independent bounded jobs;
- do not occupy the only self-hosted runner with `sleep`, polling loops or waiting for human/external state.

## Periodic hygiene

At mission close or material integration checkpoint:

1. list branches, open PRs/issues and tracked workflows;
2. classify newly created temporary refs;
3. close completed temporary PRs/issues when safe;
4. remove obsolete temporary workflows;
5. prove commit preservation before ref deletion;
6. keep `UNKNOWN_REQUIRES_REVIEW` intact;
7. record before/after evidence for bulk cleanup.

## Protected branches

Current protected-by-process refs for the 2026-08-22 sanitization are:

- `main`;
- `mcf/mission-001-control-bridge-g1`;
- `codex/control-bridge-g2b`.

Future changes to the protected set must be explicit; this document does not silently grant permission to rewrite any branch.
