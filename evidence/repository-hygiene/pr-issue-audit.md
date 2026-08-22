# PR / Issue Hygiene Audit

Snapshot: 2026-08-22.

## Pull requests

| PR | HEAD | STATE | CLASSIFICATION | ACTION |
|---|---|---|---|---|
| #11 `G2-B — Task 8...` | `codex/control-bridge-g2b` | OPEN DRAFT | ACTIVE | KEEP OPEN. Explicitly protected by this hygiene mission. |
| #9 `F1.2c — fix private systemd runtime lock` | `fix/f1-2c-systemd-runtime-lock` | OPEN DRAFT | ACTIVE | KEEP OPEN. Parallel F1.2c work. |
| #8 `F1.2c — evidence inheritance validator lab` | `validation/evidence-inheritance-tool-20260819` | OPEN DRAFT | REQUIRES_HUMAN_REVIEW | KEEP OPEN. Validation purpose is not proven obsolete. |
| #7 `F1.2c — temporary exact-state CI validation` | `mcf/f1-2c-exact-head-ci-20260819` | OPEN DRAFT | TEMPORARY / STALE | Candidate SAFE_TO_CLOSE only after its 4 branch-only commits are archived or explicitly declared disposable. |
| #3 `G1 — MCF VPS Control Bridge bootstrap` | protected G1 | OPEN DRAFT | ACTIVE / HISTORICAL | KEEP OPEN while G1/G2-A lineage remains the parent of active G2-B. |
| #2 `Mission 001: baseline and Foundations F1.1` | F1.1 | OPEN DRAFT | STALE / HISTORICAL | REQUIRES_HUMAN_REVIEW. F1.1 is preserved in later implementation lineage but the PR is still an explicit checkpoint. |
| #1 `mission: establish CODEX execution foundation baseline` | `codex/mission-001` | OPEN DRAFT | STALE | REQUIRES_HUMAN_REVIEW. Head retains 43 commits not proven preserved by a descendant. |
| #18 `docs: consolidar estado atual da VPS e roadmap` | deleted merged head | CLOSED / MERGED | HISTORICAL | KEEP CLOSED. Squash `f2e01dfa` is on main. |
| #14 terminal proof via main | terminal branch | CLOSED UNMERGED | TEMPORARY | KEEP CLOSED. Branch handled by branch audit. |
| #13 bounded terminal proof | terminal branch | CLOSED UNMERGED | TEMPORARY | KEEP CLOSED. Branch handled by branch audit. |
| #12 R8 Task 7 candidate validation | candidate branch | CLOSED UNMERGED | TEMPORARY / SUPERSEDED | KEEP CLOSED. Accepted result was later published to G2-B; candidate branch still has 3 unique commits and must be archived before deletion. |
| #6 F1.2c exact-head validation | F1.2c | CLOSED UNMERGED | HISTORICAL / SUPERSEDED | KEEP CLOSED. |

## Issues

| ISSUE | STATE | CLASSIFICATION | ACTION |
|---|---|---|---|
| #4 G1 first handshake | OPEN | ACTIVE / HISTORICAL EVIDENCE SINK | KEEP OPEN. Control Bridge lineage still exists and issue is evidence. |
| #5 G2-A read-only roundtrip | OPEN | ACTIVE / HISTORICAL EVIDENCE SINK | KEEP OPEN. Last activity 2026-08-22; G2-A evidence remains referenced by G2-B. |
| #10 Repository Continuity & Context Recovery Hardening | CLOSED COMPLETED | HISTORICAL | KEEP CLOSED. Mission completed and preserved. |
| #15 temporary `hell word` trigger | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. No further action. |
| #16 Mission2 persistent Hello World | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. No further action. |
| #17 Mission2 persistence verification | CLOSED COMPLETED | TEMPORARY | KEEP CLOSED. No further action. |

## Findings

1. No currently open issue is proven `SAFE_TO_CLOSE` without potentially removing an evidence sink still referenced by an active lineage.
2. PR #7 is operationally temporary and stale, but its branch contains exclusive commits. Closing the PR can be safe *after* preservation is explicit; branch deletion is a separate decision.
3. PRs #1 and #2 are old drafts. Their functional work may be superseded, but the open PRs are historical checkpoints and should not be closed automatically during the same pass without a human policy decision.
4. PR #11 must remain untouched.

No PR or issue was closed by Agent B.
