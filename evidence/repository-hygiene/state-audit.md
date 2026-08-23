# State / Continuity Hygiene Audit

## Verdict

`STATE_HYGIENE=DRIFT_CONFIRMED_NOT_AUTOMATICALLY_PROMOTED`

## `main` drift

`state/current.yaml` on `main` is dated 2026-08-18 and still declares the manual-execution contingency and `MISSION_ACCEPTANCE_AND_RECOVERY_REPORT` as the next step. Those claims conflict with `README.md` reconciled on 2026-08-22.

## Active G2-B branch state

Protected `codex/control-bridge-g2b` has a newer state snapshot, but it still represents an earlier Task-8 state than the later attempt-3 reconciliation recorded on main. It therefore cannot be copied into main as if it were current truth.

## ROADMAP / active mission comparison

`ROADMAP-CHECKLIST.md` and `state/active-mission.yaml` exist in later active implementation lineage but are absent from the current main baseline. Their absence is part of documented integration drift, not authorization to recreate them from memory.

No evidence supports promoting G2-B Task 8 to `PASS` or `COMPLETE`; Tasks 9–10 remain `NOT_STARTED`.

## Action

No `state/**` file was modified.

Reason: a correct structured-state rewrite requires an agreed integration source and validation against the active state schema/tests. Under the mission rule, unresolved values are **NÃO VERIFICADO**, not guessed.

The Integrator must not claim hygiene PASS while canonical structured state contradicts current README, and must not solve that contradiction by copying an older G2-B snapshot.
