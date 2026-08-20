# AI / Project Startup & Recovery Protocol

Protocol: `CLOUD_INFRA_AI_STARTUP_RECOVERY_V1`  
Status: **ACTIVE / REQUIRED**  
Effective: 2026-08-21  
Repository: `leon337/cloud-infrastructure`

## Purpose

Any ChatGPT, Codex, other authorized AI, or human operator recovering project context must reconstruct the current project state before implementation. Prior chat context, the default branch, an old checkpoint, or a remembered mission must never be treated as sufficient by themselves.

The mandatory rule is:

```text
NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS
```

This protocol defines the recovery procedure. Automated enforcement and drift tooling belong to R6.

## Recovery modes

### LOCAL_ACCESS

Use when the executor can inspect the relevant local repository/worktree. Local Git state is part of the required evidence.

### REMOTE_ONLY

Use when the executor can inspect GitHub but not the workstation filesystem. Repository/GitHub context may be reconstructed, reviewed and planned, but local state must be reported as `UNVERIFIED`. A code/state mutation that could conflict with an unknown local writer is blocked until reconciliation.

Remote-only context recovery never opens a HUMAN_GATE and never authorizes NODE-01 or production mutation.

## Mandatory sequence

### S1 — Repository identity

Confirm:

- repository is `leon337/cloud-infrastructure`;
- remote/repository identity is not inferred from folder name alone;
- default branch is recorded, but is not assumed to be the active mission branch.

Mismatch => `BLOCKED_RECONCILIATION`.

### S2 — Active mission and branch topology

Read `state/active-mission.yaml` first, then confirm live Git/GitHub state for:

- active mission ID;
- active branch;
- base branch;
- open PR, if declared;
- live remote HEAD SHA;
- branch ownership and parallel branches that must not be touched.

The mission branch may differ from `main`. A mainline next step is not authorization for a transversal mission.

### S3 — Local Git/worktree state, when available

Before editing, collect non-destructive evidence for:

```text
repository root
worktree path
current branch
HEAD
upstream
local/remote ahead-behind
staged changes
unstaged changes
untracked files
other worktrees
```

Suggested diagnostic commands may include:

```bash
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch
git worktree list --porcelain
git remote -v
git branch -vv
```

Fetch remote metadata when appropriate before comparing refs. Do not use `reset`, `checkout`, `switch`, `stash`, `clean`, `rebase`, force push or deletion as part of recovery unless a later reconciled action explicitly authorizes it.

If local access does not exist, report:

```text
LOCAL_STATE=UNVERIFIED
```

Do not silently convert `UNVERIFIED` into `CLEAN`.

### S4 — Canonical state read

Read, at minimum:

1. `state/active-mission.yaml`;
2. `CONTEXT.md`;
3. `CHECKPOINT.md`;
4. `state/current.yaml`;
5. mission/capability-specific state referenced by the active mission;
6. active mission document;
7. recovery checkpoint referenced by state;
8. relevant approved spec/plan when implementation is in scope.

### S5 — Live GitHub reconciliation

Verify the live objects referenced by canonical state:

- active branch and remote HEAD;
- active PR state, base/head and draft/merge state;
- active issue/mission tracker;
- applicable commits and changed-file inventory when material;
- applicable workflow runs/checks;
- evidence source that supports any `PASS` claim.

A historical green run does not certify a newer operational HEAD unless evidence inheritance is explicitly valid and documented.

### S6 — Work-state reconstruction

The recovery report must distinguish:

```text
COMPLETE
IN_PROGRESS
PARTIAL
BLOCKED
BLOCKED_EXTERNAL
WAITING_HUMAN_GATE
REVIEW_REQUIRED
PASS
FAILED
NOT_STARTED
NOT_EXECUTED
UNVERIFIED
```

A WIP checkpoint preserves work; it does not imply acceptance. Missing validation is not equivalent to failure, and absence of logs is not proof of a content defect.

### S7 — Ownership, isolation and prohibited surfaces

Identify every relevant branch/workstream and state explicitly:

- active ownership;
- parallel/out-of-scope ownership;
- files/branches/services that must not be touched;
- whether local uncommitted work has known ownership.

Unknown ownership of local changes => `BLOCKED_RECONCILIATION` for mutation.

### S8 — HUMAN_GATE reconstruction

List each current gate and its exact state. A gate is open only through explicit current human authorization from LEANDRO.

Commits, PRs, tests, issue text, prior approvals from another scope, or an AI's inference cannot open a HUMAN_GATE.

### S9 — Contradiction handling

Use this precedence when facts disagree:

```text
1. current explicit LEANDRO instruction
2. verified live infrastructure for host facts
3. live Git/GitHub for the applicable branch/PR/SHA
4. state/active-mission.yaml
5. state/current.yaml + capability state
6. CHECKPOINT.md
7. approved decisions/specifications
8. docs/runbooks/findings/evidence
9. history
10. prior chats/sessions
```

Do not silently choose a convenient source. Record the contradiction and stop mutation until reconciled.

## Fail-closed conditions

Any of the following blocks implementation:

- repository identity mismatch;
- active branch mismatch;
- unexplained local/remote divergence;
- uncommitted or untracked work with unknown ownership;
- contradiction between canonical sources;
- contradictory task state;
- `PASS` claim without evidence applicable to the claimed SHA/state;
- ambiguous or closed HUMAN_GATE for the requested action;
- missing/conflicting next exact step;
- active PR/head mismatch.

## Recovery verdicts

### `PASS`

Context is reconstructed and the requested scope is internally consistent. Repository mutation may proceed **only within the recovered scope**. Any separate HUMAN_GATE still applies.

### `PASS_READ_ONLY`

Context is sufficient for analysis/review/planning, but mutation prerequisites are not fully proven. No implementation or state mutation.

### `BLOCKED_RECONCILIATION`

Git, GitHub, local state, canonical state or evidence disagree. Reconcile before implementation.

### `WAITING_HUMAN_GATE`

Context is reconstructed, but the requested action requires a human authorization that is not open.

## Mandatory recovery report

Before implementation, the executor must be able to state:

```text
REPOSITORY=<owner/repo>
MODE=<LOCAL_ACCESS|REMOTE_ONLY>
ACTIVE_MISSION=<id>
ACTIVE_BRANCH=<branch>
BASE_BRANCH=<branch>
REMOTE_HEAD=<sha>
LOCAL_HEAD=<sha|UNVERIFIED>
LOCAL_REMOTE_DIVERGENCE=<state|UNVERIFIED>
WORKTREE_STATUS=<state|UNVERIFIED>
ACTIVE_PR=<number/state|NONE>
TASK_STATE=<summary>
TEST_STATE=<evidence-backed summary>
BLOCKERS=<summary|NONE>
PARALLEL_WORK_DO_NOT_TOUCH=<summary|NONE>
HUMAN_GATES=<summary>
NEXT_EXACT_STEP=<one exact action>
CONTRADICTIONS=<summary|NONE>
RECOVERY_VERDICT=<PASS|PASS_READ_ONLY|BLOCKED_RECONCILIATION|WAITING_HUMAN_GATE>
```

Implementation must not begin if this report cannot be produced without guessing.

## Current mission binding

For the continuity mission that created this protocol:

```text
MISSION=REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING
ISSUE=10
ACTIVE_BRANCH=codex/control-bridge-g2b
PR=11_DRAFT_DO_NOT_MERGE
R1=COMPLETE
R2=COMPLETE
R3=COMPLETE
R4=COMPLETE
PERSISTENCE_POLICY=governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md
NEXT=R5_CREATE_INSTITUTIONAL_PROJECT_MEMORY_AND_FIRST_INCIDENT_MEMO
```

The G2-B Task 7 technical RED remains deliberately deferred to R8. F1.2c remains a parallel isolated workstream for this mission. NODE-01 G2-B bootstrap, real grant issuance, real bounded write, production and merge remain unauthorized.
