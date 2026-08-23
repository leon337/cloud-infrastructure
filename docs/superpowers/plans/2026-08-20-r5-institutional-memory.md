# R5 Lean Institutional Project Memory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a token-efficient institutional memory layer that preserves only material events, supports material timeline reconstruction, and keeps current-state startup reads small.

**Architecture:** Keep current state, session archive, and institutional memory strictly separate. Add a compact YAML memo index plus short append-oriented memo files; the active mission references only relevant memo IDs, and agents load memo bodies only on demand.

**Tech Stack:** Markdown, YAML, Python `unittest` + PyYAML, Git/GitHub.

**Spec:** `docs/superpowers/specs/2026-08-20-r5-institutional-memory-design.md`

## Global Constraints

- `CURRENT_STATE_MUST_BE_CHEAP_TO_READ`.
- `HISTORY_MUST_BE_CHEAP_TO_SEARCH`.
- `DETAIL_MUST_BE_LOADED_ONLY_ON_DEMAND`.
- `MEMOS_ONLY_FOR_MATERIAL_EVENTS`.
- Memo target size: 300–600 words; soft maximum: 800 words.
- `TIMELINE_MATERIAL=RECONSTRUCTABLE`; exhaustive timeline is not required.
- `history/SESSION-*.md` remains archival and is not startup-required.
- Memo bodies must not duplicate current state, long logs, full diffs, or long commit lists.
- Material factual reinterpretation uses a later addendum/new memo; editorial corrections may edit the same memo.
- Remote-only execution must keep local workstation state `UNVERIFIED`.
- G2-B Task 7 remains `PARTIAL`; Tasks 8–10 remain `NOT_STARTED`; F1.2c remains isolated; NODE-01, production, merge, real grant and real write gates remain closed.

---

### Task 1: Create the lean institutional-memory store and first material memo

**Files:**
- Create: `history/memos/README.md`
- Create: `history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md`
- Create: `state/institutional-memory.yaml`
- Modify: `history/README.md`

**Interfaces:**
- Consumes: approved R5 spec, Issue #10, PR #11, checkpoint `7205a647f918580d09c87ed44f38b0a433552a51`, `docs/54-control-bridge-g2b-recovery-checkpoint.md`, R3 protocol, R4 persistence policy.
- Produces: compact memo index keyed by `MEMO-2026-08-20-001`; human-readable material memo discoverable by path without startup-wide loading.

- [ ] **Step 1: Create the memo rules document**

`history/memos/README.md` must define:

```text
MEMO PURPOSE = material institutional memory, not current state or task tracking
ALLOWED TYPES = INCIDENT | OBJECTIVE_CHANGE | MATERIAL_DECISION | DISCOVERY | RECOVERY_EVENT | RISK_CHANGE
REQUIRED INDEX FIELDS = id, occurred_at, recorded_at, type, scope, summary, related_evidence, caused_or_resulted_in, path
STARTUP RULE = do not read all memo bodies
EDITORIAL CORRECTION = same memo allowed
MATERIAL REINTERPRETATION = addendum/new memo required
```

It must also contain the anti-bureaucracy rules from the approved spec.

- [ ] **Step 2: Create the first memo**

Create `history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md` with 300–600 words covering only evidence-backed facts:

```text
ID=MEMO-2026-08-20-001
TYPE=INCIDENT
SCOPE=CONTROL_BRIDGE_G2B_CONTINUITY
OCCURRED_AT=2026-08-20
RECORDED_AT=2026-08-21
```

Required content sections:

```text
What happened
Why it mattered
Confirmed facts / unknowns
Recovery
Resulting controls
Evidence references
```

Confirmed facts must include: multi-hour G2-B work existed locally; unexpected notebook reboot terminated temporary subagent/session context; local Git work survived; Task 7 was reconstructed as `PARTIAL` with `6 PASS / 1 FAIL`; remote publication was initially blocked because local OAuth lacked GitHub `workflow` scope; authentication was repaired and branch publication succeeded; R1–R4 were created as corrective/preventive continuity controls. Do not claim an unproven hardware, OS, Git, or Codex root cause.

- [ ] **Step 3: Create the compact machine-readable index**

Create `state/institutional-memory.yaml` with this exact top-level shape:

```yaml
protocol_version: CLOUD_INFRA_INSTITUTIONAL_MEMORY_V1
updated_at: 2026-08-21
status: ACTIVE
startup_policy: INDEX_ON_DEMAND_MEMO_BODIES_NOT_GLOBAL_STARTUP
session_archive:
  path_glob: history/SESSION-*.md
  role: ARCHIVAL_DETAILED_HISTORY
  startup_required: false
memo_store:
  directory: history/memos
  materiality_required: true
  target_words: 300_600
  soft_max_words: 800
  exhaustive_timeline_required: false
memos:
  - id: MEMO-2026-08-20-001
    occurred_at: 2026-08-20
    recorded_at: 2026-08-21
    type: INCIDENT
    scope: CONTROL_BRIDGE_G2B_CONTINUITY
    summary: Local-only G2-B work survived reboot but exposed a continuity and remote-persistence gap.
    related_evidence:
      issue: 10
      pull_request: 11
      recovery_checkpoint_sha: 7205a647f918580d09c87ed44f38b0a433552a51
      recovery_checkpoint_doc: docs/54-control-bridge-g2b-recovery-checkpoint.md
    caused_or_resulted_in:
      - R1_REMOTE_RECOVERY_PUBLICATION
      - R2_CANONICAL_RECONCILIATION
      - R3_STARTUP_RECOVERY_PROTOCOL
      - R4_LONG_RUNNING_PERSISTENCE_POLICY
    path: history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md
```

- [ ] **Step 4: Clarify the legacy session archive**

Update `history/README.md` so that it explicitly states:

```text
SESSION-* = detailed archival history, not startup-required, not canonical current state
memos/ = material institutional memory, discovered through state/institutional-memory.yaml
history never overrides verified live/current canonical state
```

- [ ] **Step 5: Verify Task 1 remotely and checkpoint**

Verify all four paths exist on `codex/control-bridge-g2b`; inspect the index and memo contents; verify PR #11 head moved to the new commits. Commit messages must keep the work clearly R5-scoped.

---

### Task 2: Bind only relevant memory into the active mission and current-state entrypoints

**Files:**
- Modify: `state/active-mission.yaml`
- Modify: `state/current.yaml`
- Modify: `CONTEXT.md`
- Modify: `README.md`
- Modify: `CHECKPOINT.md`
- Modify: `docs/53-repository-continuity-context-recovery-mission.md`
- Modify: `state/control-bridge-g2b.yaml`

**Interfaces:**
- Consumes: `state/institutional-memory.yaml` from Task 1.
- Produces: minimal canonical references; only the active mission lists `relevant_memos`, avoiding memo inventory duplication.

- [ ] **Step 1: Bind relevant memo IDs only in active mission state**

Add to `state/active-mission.yaml`:

```yaml
institutional_memory:
  status: ACTIVE
  index: state/institutional-memory.yaml
  startup_read_policy: INDEX_ONLY_UNLESS_RELEVANT_MEMO_REQUIRED
  relevant_memos:
    - MEMO-2026-08-20-001
```

Advance roadmap only after Task 1 is verified:

```yaml
continuity_roadmap:
  R1: COMPLETE
  R2: COMPLETE
  R3: COMPLETE
  R4: COMPLETE
  R5: COMPLETE
  R6: NEXT
  R7: NOT_STARTED
  R8: NOT_STARTED
next_exact_step: R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS
```

- [ ] **Step 2: Add only compact current-state references**

In `state/current.yaml`, add only:

```yaml
institutional_memory_index: state/institutional-memory.yaml
institutional_memory_startup_policy: INDEX_ON_DEMAND_MEMO_BODIES_NOT_GLOBAL_STARTUP
active_roadmap_stage: R5_COMPLETE_R6_NEXT
next_exact_step: R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS
```

Do not duplicate memo entries or memo contents into `state/current.yaml`.

- [ ] **Step 3: Update human entrypoints minimally**

`CONTEXT.md`, `README.md`, and `CHECKPOINT.md` must each contain only a short pointer to `state/institutional-memory.yaml` and the rule that memo bodies are loaded only when relevant. They must not enumerate all memos.

Update current roadmap markers to:

```text
ROADMAP_R5=COMPLETE
ROADMAP_R6=NEXT
NEXT_EXACT_STEP=R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS
```

- [ ] **Step 4: Reconcile mission and G2-B continuity documents**

Update `docs/53-repository-continuity-context-recovery-mission.md` and `state/control-bridge-g2b.yaml` so R5 is complete, R6 is next, and the G2-B technical next step remains deferred to R8.

- [ ] **Step 5: Audit diffs for historical contamination**

For every large-file update, inspect the exact commit diff. Any unrelated historical evidence change must be reverted before Task 2 can be accepted.

---

### Task 3: Add structural tests for token-efficient institutional memory

**Files:**
- Modify: `tests/test_control_bridge_continuity.py`

**Interfaces:**
- Consumes: files from Tasks 1–2.
- Produces: regression assertions that R5 remains lean, indexed, timeline-capable, and non-duplicative.

- [ ] **Step 1: Extend the continuity test with R5 assertions**

Add assertions equivalent to:

```python
def test_institutional_memory_is_lean_and_timeline_reconstructable(self):
    memory = yaml.safe_load((ROOT / "state/institutional-memory.yaml").read_text())
    self.assertEqual(memory["status"], "ACTIVE")
    self.assertFalse(memory["session_archive"]["startup_required"])
    self.assertFalse(memory["memo_store"]["exhaustive_timeline_required"])
    self.assertEqual(len(memory["memos"]), 1)
    memo = memory["memos"][0]
    self.assertEqual(memo["id"], "MEMO-2026-08-20-001")
    self.assertEqual(memo["occurred_at"], "2026-08-20")
    self.assertEqual(memo["recorded_at"], "2026-08-21")
    self.assertEqual(memo["type"], "INCIDENT")
    self.assertIn("R3_STARTUP_RECOVERY_PROTOCOL", memo["caused_or_resulted_in"])
    self.assertIn("R4_LONG_RUNNING_PERSISTENCE_POLICY", memo["caused_or_resulted_in"])
    self.assertTrue((ROOT / memo["path"]).is_file())


def test_active_mission_loads_only_relevant_memo_ids(self):
    mission = yaml.safe_load((ROOT / "state/active-mission.yaml").read_text())
    memory = mission["institutional_memory"]
    self.assertEqual(memory["index"], "state/institutional-memory.yaml")
    self.assertEqual(memory["relevant_memos"], ["MEMO-2026-08-20-001"])
    self.assertEqual(mission["continuity_roadmap"]["R5"], "COMPLETE")
    self.assertEqual(mission["continuity_roadmap"]["R6"], "NEXT")
    self.assertEqual(mission["next_exact_step"], "R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS")
```

Because PyYAML may parse unquoted ISO dates as `date` objects, the implementation may quote `occurred_at` and `recorded_at` in YAML so these exact string assertions remain stable.

- [ ] **Step 2: Add anti-duplication assertions**

Add a test that verifies `README.md` and `CHECKPOINT.md` reference `state/institutional-memory.yaml` but do not contain the memo path `history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md`.

- [ ] **Step 3: Run the focused continuity test in an approved execution environment**

Run:

```bash
python3 -m unittest tests.test_control_bridge_continuity -v
```

Expected: all continuity tests pass. If the current executor cannot run repository code, record test execution as `UNVERIFIED_REMOTE_ONLY`; do not claim PASS from static inspection.

- [ ] **Step 4: Inspect CI without overclaiming**

Check workflow runs bound to the final R5 HEAD. If validate jobs again fail before exposing steps/logs, record them as `INCONCLUSIVE`, not as R5 content failure and not as PASS.

---

### Task 4: Close R5 remotely and preserve a clean handoff to R6

**Files / remote objects:**
- Update: PR #11 body
- Update: Issue #10 comment/tracker
- Verify: remote branch `codex/control-bridge-g2b`

**Interfaces:**
- Consumes: verified Tasks 1–3.
- Produces: remotely recoverable R5 completion checkpoint and exact R6 next action.

- [ ] **Step 1: Verify final remote inventory**

Confirm the remote branch contains:

```text
history/memos/README.md
history/memos/MEMO-2026-08-20-001-g2b-local-work-recovery.md
state/institutional-memory.yaml
docs/superpowers/specs/2026-08-20-r5-institutional-memory-design.md
docs/superpowers/plans/2026-08-20-r5-institutional-memory.md
```

Confirm canonical state reports `R5=COMPLETE`, `R6=NEXT`, and `NEXT_EXACT_STEP=R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS`.

- [ ] **Step 2: Search for stale R5-next markers**

Search active operational files for:

```text
R5_CREATE_INSTITUTIONAL_PROJECT_MEMORY_AND_FIRST_INCIDENT_MEMO
R5: NEXT
ROADMAP_R5=NEXT
```

Historical/spec/plan references that intentionally describe pre-R5 state may remain; operational current-state sources must not.

- [ ] **Step 3: Update PR #11**

Keep PR #11 `DRAFT / DO NOT MERGE`. Add R5 summary, lean token policy, first memo ID, current test/CI evidence state, and `R6_ADD_CONSISTENCY_AND_DRIFT_CONTROLS` as next exact action.

- [ ] **Step 4: Update Issue #10**

Record R5 completion evidence, final remote HEAD, first memo/index paths, test evidence state, unchanged G2-B Task 7 status, closed HUMAN_GATEs, and R6 as the next roadmap item.

- [ ] **Step 5: Stop before R6**

Do not begin R6 automatically. Report the final R5 state and wait for LEANDRO's approval of the next roadmap item.
