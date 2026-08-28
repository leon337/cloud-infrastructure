# Long-Running Mission Persistence Policy

Policy: `CLOUD_INFRA_LONG_RUNNING_MISSION_PERSISTENCE_V1`  
Status: **ACTIVE / REQUIRED**  
Effective: 2026-08-21  
Repository: `leon337/cloud-infrastructure`

## Purpose

Long-running work must remain recoverable when a workstation reboots, an AI session ends, a rate limit is reached, a subagent disappears, or execution moves to another authorized agent.

The central rules are:

```text
NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS
MAX_MATERIAL_WORK_WITHOUT_REMOTE_CHECKPOINT=30_MINUTES
WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE
SESSION_STATE_IS_NOT_DURABLE_STATE
```

This policy governs durability of current work. Historical incident/decision memory belongs to R5 and is not replaced by checkpoints.

## Scope

Applies to ChatGPT, Codex, subagents and other authorized executors working on `leon337/cloud-infrastructure`, including documentation-only missions when their state is material to project continuity.

It does not open HUMAN_GATEs, authorize NODE-01/production mutation, or change task acceptance criteria.

## Definitions

### Material work

Work is material when losing it would require meaningful reconstruction, reimplementation or re-review. Examples include:

- executable or infrastructure changes;
- tests or fixtures that encode new behavior;
- approved specifications/plans;
- task implementation or review results;
- corrective rounds after review findings;
- mission/ownership/gate changes;
- evidence needed to support a status claim;
- significant uncommitted WIP that another agent would need to resume.

### Durable local checkpoint

A Git commit on the correct mission branch/worktree that preserves the recoverable work locally. It is better than session-only state but is **not** sufficient for a long-running mission when remote persistence is available.

### Recoverable remote checkpoint

A pushed commit/branch plus enough canonical state to identify what the checkpoint means. It may be explicitly WIP/PARTIAL. It must not contain secrets.

### Acceptance

A separate evidence-backed decision that a task/slice has met its completion criteria. Commit, push, PR, checkpoint or remote preservation do not imply acceptance.

## P1 — Preflight durability gate

Before starting a long-running implementation/review cycle, the controlling agent must execute the R3 startup/recovery protocol and additionally verify:

1. the correct mission branch/worktree is known;
2. a remote checkpoint target exists or the absence is explicitly recorded;
3. push/authentication capability is known before hours of work accumulate;
4. if the mission can modify `.github/workflows/`, the local Git credential must be capable of publishing workflow changes before depending on that path;
5. the controlling agent knows which canonical ledger/state must be updated with the task;
6. secrets or private credentials are not part of the persistence payload.

If remote publication cannot be proven, the mission may perform only the minimum work needed to preserve/reconcile the current state. It must not knowingly accumulate hours of new material work behind an unresolved persistence blocker.

## P2 — Mandatory checkpoint triggers

A recoverable checkpoint is required at the earliest of the following:

- completion of a Task/slice or meaningful subtask;
- completion of a review round that changes acceptance status;
- completion of a corrective round for material findings;
- transition to `BLOCKED`, `WAITING_HUMAN_GATE`, `REVIEW_REQUIRED`, `PARTIAL`, `PASS` or `FAILED`;
- before a planned pause, reboot, environment switch or executor handoff;
- before an action that may invalidate the current environment/session;
- when rate-limit/session exhaustion becomes reasonably foreseeable;
- **30 minutes after the last recoverable remote checkpoint while material work is accumulating**.

The 30-minute boundary is a maximum, not a target. Task/gate events take precedence and may require earlier persistence.

## P3 — Remote persistence rule

When remote publication is available and safe:

1. commit bounded work on the correct branch;
2. push the branch/checkpoint;
3. update the canonical ledger/state in the same persistence cycle when task/status meaning changed;
4. record blockers/tests/gates and `NEXT_EXACT_STEP`;
5. verify the remote SHA/ref after publication when the checkpoint is material.

A WIP commit should use language such as `wip`, `partial`, `checkpoint` or equivalent when acceptance has not been established.

A draft PR is a valid continuity surface but does not replace canonical state and does not mean merge readiness.

## P4 — When remote persistence is blocked

If push or remote write fails:

1. stop accumulating unrelated new material work;
2. create a durable local checkpoint immediately when safe;
3. preserve untracked/staged work explicitly without destructive Git commands;
4. record the exact blocker and last known local HEAD;
5. resolve authentication/network/permission/remote conflict or obtain human intervention as required;
6. publish the checkpoint once the blocker is cleared;
7. verify remote state before resuming normal long-running execution.

Do not use force push, reset, clean, rebase, stash, checkout/switch or deletion as an improvised recovery mechanism unless separately reconciled and authorized.

## P5 — Ledger/state synchronization

Git and the project ledger must not silently describe different task realities.

Whenever a persistence event changes any of the following, the same checkpoint cycle must update the applicable canonical state:

- active task/slice;
- task lifecycle state;
- review status;
- test/evidence status;
- blocker;
- HUMAN_GATE status;
- ownership/parallel-work boundary;
- exact next action.

A commit sequence may be technically valid while the ledger is stale; that condition is `BLOCKED_RECONCILIATION`, not permission to continue silently.

## P6 — Lifecycle vocabulary

Use these states where applicable:

- `NOT_STARTED` — no implementation started;
- `IN_PROGRESS` — active work, no completion claim;
- `PARTIAL` — bounded useful work preserved, known work remains;
- `BLOCKED` — cannot continue until a technical/project condition changes;
- `BLOCKED_EXTERNAL` — external service/account/environment condition blocks progress;
- `WAITING_HUMAN_GATE` — explicit human authorization is required;
- `REVIEW_REQUIRED` — implementation exists but required review/acceptance is pending;
- `PASS` — acceptance criteria are evidenced for the applicable commit/scope;
- `FAILED` — applicable verification/operation has a proven failure.

A checkpoint may preserve any of these states. `PASS` requires applicable evidence and must never be inferred from persistence alone.

## P7 — Subagent durability

The controlling agent owns durability even when subagents perform implementation or review.

Subagent output is not durable merely because it exists in a subagent transcript. Material subagent results must be integrated into the controlling branch/ledger/checkpoint at the required event/time boundary.

Before dispatching dependent work, the controlling agent must ensure the predecessor result needed by that dependency is recoverable. Temporary subagent loss must not erase the authoritative state of completed review/implementation rounds.

## P8 — Restart, rate-limit and session-loss recovery

After a reboot, context compaction, rate limit, chat loss or executor handoff:

1. do not resume from memory alone;
2. execute `CLOUD_INFRA_AI_STARTUP_RECOVERY_V1`;
3. identify the latest verified remote checkpoint;
4. if local access exists, compare local worktree/HEAD/untracked work against that checkpoint;
5. reconcile any newer local-only work before new implementation;
6. resume only from an evidence-backed `NEXT_EXACT_STEP`.

Recovery target: interruption should normally cost minutes of reconstruction rather than hours of forensic recovery.

## P9 — Minimum checkpoint payload

A material remote checkpoint must make the following reconstructable either directly or through canonical references:

```text
MISSION
TASK_OR_SLICE
BRANCH
REMOTE_HEAD
LIFECYCLE_STATE
TEST_OR_EVIDENCE_STATE
KNOWN_BLOCKERS
WIP_SCOPE
PARALLEL_WORK_DO_NOT_TOUCH
HUMAN_GATES
NEXT_EXACT_STEP
ACCEPTANCE_STATUS
```

For `PARTIAL`/`FAILED`, include the known failing condition when safe. Never include secret values.

## P10 — Fail-closed conditions

Normal long-running implementation must stop for reconciliation when any of these are true:

- more than 30 minutes of material work accumulated without a recoverable remote checkpoint while remote persistence should be available;
- remote push/write is known broken and new unrelated material work would continue accumulating;
- branch/worktree ownership is uncertain;
- Git advanced materially but ledger/state meaning is stale;
- material uncommitted/untracked work has unknown ownership;
- checkpoint state is being mistaken for acceptance;
- a required HUMAN_GATE is closed or ambiguous;
- the controlling agent cannot identify the latest recoverable checkpoint.

## P11 — Checkpoint versus institutional memory

Persistence checkpoint:

> Where are we now and exactly how do we resume?

Institutional memo (R5):

> What happened, why did it matter, what did we learn, and what changed because of it?

Do not rewrite old memos to make history look consistent with the present. Do not overload current checkpoints with the full historical narrative.

## Required handoff report

Before an executor intentionally stops a long-running mission, it must leave a handoff containing:

```text
MISSION=<id>
TASK=<task/slice>
STATE=<lifecycle state>
BRANCH=<branch>
REMOTE_HEAD=<sha or UNPUBLISHED_BLOCKED>
LOCAL_DELTA=<clean/ahead/uncommitted/unverified>
TESTS=<summary>
BLOCKERS=<summary>
HUMAN_GATES=<summary>
PARALLEL_WORK=<do-not-touch summary>
NEXT_EXACT_STEP=<one evidence-backed action>
ACCEPTANCE=<accepted/not accepted/review required>
```

## Relationship to other controls

- R3 (`CLOUD_INFRA_AI_STARTUP_RECOVERY_V1`) determines whether an agent has reconstructed enough state to work.
- R4 determines how active work remains durable while the mission runs.
- R5 preserves institutional historical memory.
- R6 will add automated consistency/drift enforcement around these contracts.

No policy in R4 overrides an explicit HUMAN_GATE or production boundary.