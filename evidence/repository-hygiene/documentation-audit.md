# Documentation Hygiene Audit

## Scope

Audited canonical entrypoints and their relation to current live GitHub evidence, with special attention to `README.md`, `CONTEXT.md`, `CHECKPOINT.md`, `docs/**`, `runbooks/**`, `decisions/**`, `history/**` and `evidence/**`.

## Material drift found

`README.md` was reconciled on 2026-08-22 and records G2-B Tasks 1–7 complete, Task 8 `FAILED_ATTEMPT_3`, Tasks 9–10 not started, plus an open F1.2c incident.

Before this hygiene patch:

- `CONTEXT.md` still described the temporary LEANDRO manual-execution contingency from 2026-08-18 and named `MISSION ACCEPTANCE + RECOVERY REPORT` as the exact point;
- `CHECKPOINT.md` still described the same 2026-08-18 contingency and the same obsolete next step;
- both were linked from current `README.md` as canonical recovery material.

This was a direct current-vs-historical contradiction, not an architectural disagreement.

## Corrections applied on this branch

- `CONTEXT.md`: rewritten as a compact recovery entrypoint that explicitly distinguishes `main` state, active branch state, historical evidence and live GitHub state.
- `CHECKPOINT.md`: replaced the obsolete 18/08 checkpoint with the 22/08 reconciled state already supported by `README.md`.

The patch does **not**:

- edit `state/**`;
- edit G2-B code/design;
- claim Task 8 passed;
- authorize Tasks 9–10;
- reopen Q1–Q40;
- modify production or NODE-01;
- rewrite historical files under `history/**`.

## Historical material

Historical documents, decisions and evidence were left in place. The cleanup rule is: history may be stale as *current state*, but it is not wrong merely because it is historical. Current entrypoints must label/route history correctly rather than deleting it.

## Remaining documentation risks

- Current `main` remains an integration/documentation line that does not contain every active implementation artifact; startup must therefore consult the owning active branch before acting.
- `state/current.yaml` on `main` was also stale before this mission. That is Agent E's surface and was not modified here.
- G2-B's protected branch contains branch-local continuity state that may itself lag the later attempt-3 README reconciliation; this audit records the mismatch but does not alter the protected branch.

`DOCUMENTATION_HYGIENE=PATCH_PREPARED`
