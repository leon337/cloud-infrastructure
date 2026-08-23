# R5 — Lean Institutional Project Memory Design

Date: 2026-08-20
Status: APPROVED DESIGN — IMPLEMENTATION NOT YET STARTED
Mission: Repository Continuity & Context Recovery Hardening
Issue: #10
Branch: `codex/control-bridge-g2b`
PR: #11 — DRAFT / DO NOT MERGE
Authority: LEANDRO
Orchestrator: MESTRE / MCF

## Objective

Add durable institutional memory without turning project recovery into a high-token historical read. Current state must remain cheap to read; history must remain cheap to search; detail is loaded only on demand.

Core principles:

```text
CURRENT_STATE_MUST_BE_CHEAP_TO_READ
HISTORY_MUST_BE_CHEAP_TO_SEARCH
DETAIL_MUST_BE_LOADED_ONLY_ON_DEMAND
MEMOS_ONLY_FOR_MATERIAL_EVENTS
```

## Separation of responsibilities

- `state/*.yaml` and `CHECKPOINT.md`: where the project is now.
- `history/SESSION-*.md`: detailed session archive; not startup-required and not canonical current state.
- `history/memos/MEMO-*.md`: durable material events and causal project memory.
- `state/institutional-memory.yaml`: compact machine-readable index used to discover relevant memos without loading them all.

Memos must never become a duplicate task tracker or a copy of current state.

## Files

```text
history/
├── README.md
├── SESSION-*.md
└── memos/
    ├── README.md
    └── MEMO-YYYY-MM-DD-NNN-<slug>.md

state/
└── institutional-memory.yaml
```

No separate memo template file is required. The compact schema belongs in `history/memos/README.md` to reduce sources that can drift.

## Materiality gate

Create a memo only when an event materially changes at least one of:

- project objective or direction;
- architecture or security boundary;
- permanent work process;
- significant risk;
- material recovery/incident state;
- important technical understanding whose loss would cause substantial repeated work.

Normal test failures, routine commits, ordinary review rounds, reversible decisions, routine task transitions and ordinary sessions do not generate memos.

## Memo size and evidence discipline

Target size: 300–600 words. Soft maximum: 800 words.

Memos summarize only:

1. what happened;
2. why it matters;
3. what was learned or decided;
4. what changed as a consequence;
5. where supporting evidence lives.

Do not embed long logs, full diffs, long commit lists or copies of canonical state. Link to commits, PRs, issues, checkpoints and evidence instead.

## Timeline reconstruction

The compact index must support material timeline reconstruction without loading memo bodies. Each memo index entry contains at minimum:

```text
id
occurred_at
recorded_at
type
scope
summary
related_evidence
caused_or_resulted_in
path
```

`occurred_at` and `recorded_at` are distinct because an event may be documented later than it happened.

The target is:

```text
TIMELINE_MATERIAL=RECONSTRUCTABLE
TIMELINE_EXHAUSTIVE=NOT_REQUIRED
```

Detailed investigation can descend from the index into one memo, then into related sessions, commits, PRs, issues or evidence only when necessary.

## Memo types

Supported types:

- `INCIDENT`
- `OBJECTIVE_CHANGE`
- `MATERIAL_DECISION`
- `DISCOVERY`
- `RECOVERY_EVENT`
- `RISK_CHANGE`

## Startup/token policy

Institutional history is not globally loaded at startup.

Three read levels:

```text
LEVEL_0_NORMAL_STARTUP:
  do not read memo bodies

LEVEL_1_ACTIVE_MISSION_RELEVANCE:
  read only memo IDs explicitly listed in active mission `relevant_memos`

LEVEL_2_HISTORICAL_INVESTIGATION:
  inspect `state/institutional-memory.yaml`, select relevant entries, then open only required memo/session/evidence files
```

`state/active-mission.yaml` may contain only a small `relevant_memos` list. README and CHECKPOINT must not duplicate the memo inventory.

## Historical integrity

Memos are append-oriented historical records.

- Editorial corrections that do not change meaning may modify the same memo.
- Material factual reinterpretation must not silently rewrite history.
- A later correction/addendum must reference the earlier memo and explain the changed understanding.
- Historical memory never overrides verified live state or canonical current state.

## Anti-bureaucracy rules

```text
DO_NOT_SUMMARIZE_EVERY_SESSION
DO_NOT_CREATE_MEMO_PER_TASK
DO_NOT_COPY_CURRENT_STATE_INTO_MEMOS
DO_NOT_READ_ALL_MEMOS_AT_STARTUP
DO_NOT_DUPLICATE_EVIDENCE
DO_NOT_EMBED_LONG_LOGS
DO_NOT_CREATE_ADDENDUM_FOR_EDITORIAL_FIXES
DO_NOT_USE_MEMO_AS_TASK_TRACKER
```

## First memo

Create:

`history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md`

It records the material continuity incident around G2-B local-only work, unexpected notebook reboot, loss of temporary subagent/session context, survival of local Git work, reconstruction of Task 7 state, initial remote publication blocker caused by missing GitHub OAuth `workflow` scope, successful publication, and the resulting continuity controls R1–R4.

The memo must distinguish confirmed facts from unknowns and must not claim unproven root causes.

Primary references should include Issue #10, PR #11, recovery checkpoint `7205a647f918580d09c87ed44f38b0a433552a51`, `docs/54-control-bridge-g2b-recovery-checkpoint.md`, the R3 startup protocol and the R4 persistence policy.

## Current mission integration

R5 implementation will add the compact index and first memo, update only the minimal canonical references required, and then advance the continuity roadmap to:

```text
R5=COMPLETE
R6=NEXT
NEXT_EXACT_STEP=R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS
```

The G2-B technical Task 7 remains `PARTIAL`; Tasks 8–10 remain not started; F1.2c remains isolated; NODE-01, production and merge HUMAN_GATEs remain closed.

## Remote-only constraint

This design is being persisted from a remote-only executor. Local workstation state remains `UNVERIFIED` and must not be represented as synchronized or clean until reconciled through the R3 protocol.