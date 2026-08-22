# Continuity Consistency & Drift Controls

Status: **ACTIVE_REQUIRED**  
Protocol: `CLOUD_INFRA_CONTINUITY_DRIFT_CONTROLS_V1`  
Scope: repository continuity and recovery state

## Purpose

Prevent the repository from silently presenting contradictory startup state to a new human, ChatGPT, Codex or other authorized agent.

These controls do not decide technical implementation policy. They verify that the repository's continuity surfaces agree on the mission that is already authorized and on the boundaries that remain closed.

## Core rule

```text
NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT
```

A drift failure must not be fixed by choosing the most convenient source. The executor must reconcile the sources according to `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`.

## Automated checks

The repository check `scripts/check_continuity_drift.py` is executed by `scripts/test.sh` and therefore by Foundation CI.

It verifies at minimum:

1. **Mission identity** — active mission, issue, branch and PR agree across structured sources.
2. **Roadmap coherence** — R1–R8 use allowed lifecycle states and cannot regress from `COMPLETE` to an earlier state.
3. **Single next exact step** — the active mission has a non-empty `next_exact_step` and canonical entrypoints expose the same value.
4. **G2-B preservation** — Tasks 1–6 remain complete/materially reviewed, Task 7 may advance only with recorded evidence, and Tasks 8–10 cannot silently advance ahead of their approved sequence.
5. **HUMAN_GATE fail-closed state** — NODE-01 bootstrap, real grant, real bounded write, production and merge cannot become authorized through documentation drift.
6. **Parallel ownership** — `fix/f1-2c-systemd-runtime-lock` remains isolated and must not be claimed by the active continuity mission.
7. **Institutional memory** — the memory contract and indexed first incident memo must exist.
8. **Checkpoint/state agreement** — `README.md`, `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml`, `state/active-mission.yaml` and the G2-B state must not advertise conflicting continuity stage/next action.
9. **PASS semantics** — a continuity validation may claim `PASS` only when its evidence record explicitly lists the checks that passed; WIP or persistence never imply acceptance.
10. **Cold-start evidence** — R7 may be `COMPLETE` only when `state/cold-start-validation.yaml` and its report exist and record a passing reconstruction.

## Failure classes

```text
STALE_ACTIVE_MISSION_REFERENCE
MISSION_BRANCH_OR_PR_MISMATCH
ROADMAP_STATE_REGRESSION_OR_INVALID_TRANSITION
MISSING_NEXT_EXACT_STEP
ENTRYPOINT_NEXT_STEP_DRIFT
G2B_TASK_STATE_DRIFT
HUMAN_GATE_BYPASS_OR_AMBIGUITY
PARALLEL_OWNERSHIP_DRIFT
INSTITUTIONAL_MEMORY_MISSING
CURRENT_STATE_DRIFT
PASS_WITHOUT_EVIDENCE
COLD_START_EVIDENCE_MISSING
```

Any failure is blocking for continuity advancement until reconciled.

## What this control does not prove

A passing static drift check does **not** prove:

- that GitHub Actions infrastructure is healthy;
- that the local workstation is clean or synchronized;
- that NODE-01 current runtime state matches historical observations;
- that any closed HUMAN_GATE is open;
- that G2-B Task 8 disposable lifecycle is complete;
- that a real write, rollback or revocation is safe to execute.

Those claims require their own current evidence and applicable gates.

## Integration

- normative contract: this document;
- machine-readable contract: `state/continuity-drift-controls.yaml`;
- executable check: `scripts/check_continuity_drift.py`;
- unit/contract coverage: `tests/test_continuity_drift_controls.py`;
- startup/recovery protocol remains authoritative for reconciliation behavior.
