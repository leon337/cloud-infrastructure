# PR / Issue Hygiene Audit

Snapshot: 2026-08-22.

## Pull requests

| PR | HEAD | STATE | CLASSIFICATION | ACTION |
|---|---|---|---|---|
| #11 G2-B Task 8 | `codex/control-bridge-g2b` | OPEN DRAFT | ACTIVE | KEEP OPEN. Explicitly protected by this hygiene mission. |
| #9 F1.2c runtime-lock fix | `fix/f1-2c-systemd-runtime-lock` | OPEN DRAFT | ACTIVE | KEEP OPEN. Parallel F1.2c work. |
| #8 evidence-inheritance validator | `validation/evidence-inheritance-tool-20260819` | OPEN DRAFT | REQUIRES_HUMAN_REVIEW | KEEP OPEN. Validation purpose is not proven obsolete. |
| #7 temporary exact-state CI validation | `mcf/f1-2c-exact-head-ci-20260819` | OPEN DRAFT | TEMPORARY / STALE | Candidate SAFE_TO_CLOSE only after its branch-only commits are archived or explicitly declared disposable. |
| #3 G1 Control Bridge | protected G1 | OPEN DRAFT | ACTIVE / HISTORICAL | KEEP OPEN while G1/G2-A lineage remains parent of active G2-B. |
| #2 Mission 001 / F1.1 | F1.1 | OPEN DRAFT | STALE / HISTORICAL | REQUIRES_HUMAN_REVIEW. Historical checkpoint. |
| #1 initial Mission 001 baseline | `codex/mission-001` | OPEN DRAFT | STALE | REQUIRES_HUMAN_REVIEW. Head retains unique commits not proven preserved elsewhere. |
| #18 consolidated state/roadmap | merged head | CLOSED / MERGED | HISTORICAL | KEEP CLOSED. Squash `f2e01dfa` is on main. |
| #14 terminal proof via main | terminal branch | CLOSED UNMERGED | TEMPORARY | KEEP CLOSED. |
| #13 bounded terminal proof | terminal branch | CLOSED UNMERGED | TEMPORARY | KEEP CLOSED. |
| #12 R8 Task 7 candidate | candidate branch | CLOSED UNMERGED | TEMPORARY / SUPERSEDED | KEEP CLOSED. Candidate branch still requires archival review before deletion. |
| #6 older F1.2c exact-head validation | F1.2c | CLOSED UNMERGED | HISTORICAL / SUPERSEDED | KEEP CLOSED. |

## Issues

| ISSUE | STATE | CLASSIFICATION | ACTION |
|---|---|---|---|
| #4 G1 first handshake | OPEN | ACTIVE / HISTORICAL EVIDENCE SINK | KEEP OPEN. |
| #5 G2-A read-only roundtrip | OPEN | ACTIVE / HISTORICAL EVIDENCE SINK | KEEP OPEN. Last activity 2026-08-22. |
| #10 Repository Continuity & Context Recovery Hardening | CLOSED COMPLETED | HISTORICAL | KEEP CLOSED. |
| #15 temporary terminal trigger | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. |
| #16 persistent Hello World | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. |
| #17 persistence verification | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. |

## Findings

1. No currently open issue is proven `SAFE_TO_CLOSE` without potentially removing an evidence sink still referenced by active lineage.
2. PR #7 is temporary/stale, but its branch contains exclusive commits; PR closure and branch deletion must remain separate decisions.
3. PRs #1 and #2 are old draft checkpoints and should not be auto-closed without review.
4. PR #11 remains untouched.

No PR or issue was closed by Agent B.
