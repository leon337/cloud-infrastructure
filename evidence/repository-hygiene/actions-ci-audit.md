# Actions / CI Hygiene Audit

## Permanent rule

**SELF-HOSTED RUNNER IS NOT A WAIT/POLLING MECHANISM.**

Self-hosted NODE-01 jobs must be bounded, short and request-driven. Long-running work belongs to a detached VPS process with later bounded probes. Disposable integration may run longer only on disposable/hosted runners.

## Current findings

### `main`

No persistent workflow remained visible on current `main` after the temporary terminal/probe workflows were removed on 2026-08-22. Therefore there is no workflow patch to apply to `main` from this branch.

### Active protected Control Bridge line

| WORKFLOW | RUNNER | TIMEOUT | FINDING |
|---|---|---:|---|
| `control-bridge-g1.yml` | self-hosted NODE-01 | 10m | bounded probe; no wait loop observed |
| `control-bridge-g2a-bootstrap.yml` | self-hosted NODE-01 | 10m | bounded bootstrap; no polling observed |
| `control-bridge-g2a.yml` | self-hosted NODE-01 | 10m | bounded read-only request; no polling observed |
| `control-bridge-g2b.yml` | self-hosted NODE-01 | 10m | bounded executor request; no polling observed |
| `control-bridge-g2b-ci.yml` | GitHub-hosted Ubuntu | 15m / 35m | repository validation + disposable lifecycle; long lifecycle is not on self-hosted runner |
| `docker-boundary-ci.yml` | GitHub-hosted Ubuntu | 10–35m | disposable integration; no NODE-01 waiting mechanism |
| `foundation-ci.yml` | GitHub-hosted Ubuntu | 10–20m | validation/disposable integration; no NODE-01 waiting mechanism |

No `sleep`/poll-until-done behavior was observed in the inspected active Control Bridge workflows.

## Temporary residues

Temporary workflow history is associated with dedicated branches and completed PR/issues, notably the terminal proof lines. Current `main` already removed those workflow files. The correct cleanup is therefore branch/ref hygiene, not resurrecting or editing those workflows.

Branches `ops/g2b-cancel-long-waiters-20260822` and `ops/r8-task7-syntax-selfhosted-20260822` are **not** safe to delete merely because their purpose was operational: parent-line comparison found 21 and 20 branch-only commits respectively. They require archival/review before any ref cleanup.

## Decision

`ACTIONS_HYGIENE=PASS_WITH_NO_PATCH_REQUIRED`

No documentation or `state/**` file was modified by this agent. No active protected workflow was modified.
