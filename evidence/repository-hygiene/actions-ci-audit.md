# Actions / CI Hygiene Audit

## Permanent rule

**SELF-HOSTED RUNNER IS NOT A WAIT/POLLING MECHANISM.**

Self-hosted NODE-01 jobs must be bounded, short and request-driven. Long-running work belongs to a detached VPS process with later bounded probes. Disposable integration may run longer only on disposable/hosted runners.

## Current findings

Current `main` has no persistent temporary wait/terminal workflow remaining after the bounded proofs were removed on 2026-08-22.

On the active protected Control Bridge line:

| WORKFLOW | RUNNER | TIMEOUT | FINDING |
|---|---|---:|---|
| `control-bridge-g1.yml` | self-hosted NODE-01 | 10m | bounded probe; no wait loop observed |
| `control-bridge-g2a-bootstrap.yml` | self-hosted NODE-01 | 10m | bounded bootstrap; no polling observed |
| `control-bridge-g2a.yml` | self-hosted NODE-01 | 10m | bounded read-only request; no polling observed |
| `control-bridge-g2b.yml` | self-hosted NODE-01 | 10m | bounded executor request; no polling observed |
| `control-bridge-g2b-ci.yml` | GitHub-hosted Ubuntu | 15m / 35m | long disposable lifecycle is not on NODE-01 |
| `docker-boundary-ci.yml` | GitHub-hosted Ubuntu | 10–35m | disposable integration |
| `foundation-ci.yml` | GitHub-hosted Ubuntu | 10–20m | validation/disposable integration |

No active inspected self-hosted workflow uses `sleep`/poll-until-done as a runner occupancy mechanism.

Temporary operational refs with exclusive commits remain branch-hygiene work and are not safe to delete based on naming alone.

## Decision

`ACTIONS_HYGIENE=PASS_WITH_NO_PATCH_REQUIRED`

No workflow, documentation or `state/**` file was modified by Agent C.
