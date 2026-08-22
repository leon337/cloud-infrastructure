# Documentation Hygiene Audit

## Material drift found

`README.md` was reconciled on 2026-08-22 and records G2-B Tasks 1–7 complete, Task 8 `FAILED_ATTEMPT_3`, Tasks 9–10 not started, plus an open F1.2c incident.

Before hygiene:

- `CONTEXT.md` still described the temporary LEANDRO manual-execution contingency from 2026-08-18 and named `MISSION ACCEPTANCE + RECOVERY REPORT` as the exact point;
- `CHECKPOINT.md` still described the same obsolete state and next step;
- both were linked from current README as canonical recovery material.

This was a current-vs-historical contradiction, not an architectural disagreement.

## Corrections integrated

- `CONTEXT.md` now routes recovery through live GitHub and distinguishes canonical, active-branch and historical evidence.
- `CHECKPOINT.md` now reflects the 22/08 reconciled state already supported by README.

The patch does not edit `state/**`, G2-B code/design, architecture, production, NODE-01, or historical files under `history/**`.

## Remaining risk

`state/current.yaml` on `main` remains stale and is intentionally not rewritten from an older protected-branch snapshot. That unresolved structured-state drift is an Integrator blocker.

`DOCUMENTATION_HYGIENE=PATCH_INTEGRATED_PENDING_STATE_RECONCILIATION`
