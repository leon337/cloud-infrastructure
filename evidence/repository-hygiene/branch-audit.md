# Branch Audit

Scope: 23 branches present before sanitization. `main`, `mcf/mission-001-control-bridge-g1`, and `codex/control-bridge-g2b` are protected.

Method: live GitHub branch inventory; compare each ref to `main`; compare temporary branches to their actual parent line where needed; inspect associated PR state and HEAD metadata. `UNIQUE COMMITS` below is against `main` unless the evidence column states a stronger parent-line comparison.

## Classification

| BRANCH | HEAD | UNIQUE COMMITS | STATUS | ACTION | EVIDENCE |
|---|---|---:|---|---|---|
| `main` | `f2e01dfa` | 0 | CANONICAL, active | KEEP_ACTIVE | HEAD 2026-08-22; PR #18 squash is current main |
| `codex/control-bridge-g2b` | `fbef3d40` | 303 | ACTIVE, protected, PR #11 draft | KEEP_ACTIVE | last HEAD activity 2026-08-22; G2-B Task 8 remains unaccepted |
| `mcf/mission-001-control-bridge-g1` | `3e34044c` | 207 | ACTIVE/HISTORICAL CONTROL BRIDGE, protected, PR #3 draft | KEEP_ACTIVE | base for G2-B and live Control Bridge lineage |
| `codex/mission-001-f1-2c-network-enforcement` | `c9f90994` | 104 | ACTIVE parallel F1.2c | KEEP_ACTIVE | last HEAD activity 2026-08-19; parent of PR #9 line |
| `fix/f1-2c-systemd-runtime-lock` | `48be17cc` | 149 | ACTIVE parallel F1.2c, PR #9 draft | KEEP_ACTIVE | README inventory records local worktree ownership; do not sanitize away |
| `validation/evidence-inheritance-tool-20260819` | `22cd0d28` | 152 | ACTIVE validation, PR #8 draft | KEEP_ACTIVE | open PR and unresolved integration/validation purpose |
| `codex/mission-001-foundations-f1-1` | `e4503af1` | 4 | COMPLETED milestone, PR #2 still open | KEEP_HISTORICAL | exact ancestor of F1.2b preparation; milestone history is still useful |
| `codex/mission-001-foundations-f1-2b-preparation` | `6333efc7` | 35 | COMPLETED milestone | KEEP_HISTORICAL | exact ancestor of active F1.2c branch; zero exclusive commits relative to that descendant |
| `codex/mission-001` | `d9d6879f` | 43 | STALE draft PR #1, divergent experimental foundation | UNKNOWN_REQUIRES_REVIEW | HEAD 2026-08-16; not an ancestor of F1.1; 43 commits remain unique |
| `mcf/f1-2c-exact-head-ci-20260819` | `a871b5d1` | 105 | TEMPORARY validation, PR #7 draft | ARCHIVE_BEFORE_DELETE | 4 commits remain exclusive relative to `fix/f1-2c-systemd-runtime-lock`; cannot delete directly |
| `codex/r8-task7-candidate-20260822` | `604e6d0e` | 297 | TEMPORARY validation, PR #12 closed | ARCHIVE_BEFORE_DELETE | relative to G2-B: 3 candidate-only commits remain; accepted result was later published separately |
| `mcf/terminal-hell-word-main-test` | `486cd847` | 2 | TEMPORARY, PR #14 closed | ARCHIVE_BEFORE_DELETE | temporary self-hosted terminal proof; branch still has exclusive commits |
| `mcf/terminal-hell-word-test` | `d2f37533` | 196 | TEMPORARY, PR #13 closed | ARCHIVE_BEFORE_DELETE | relative to current G1: 1 branch-only commit remains; evidence mission completed |
| `ops/g2b-cancel-long-waiters-20260822` | `20d5510d` | 315 | TEMPORARY OPS | ARCHIVE_BEFORE_DELETE | relative to current G2-B: 21 branch-only commits; name alone is insufficient for deletion |
| `ops/g2b-status-output-20260822` | `bba4fc2f` | 11 | TEMPORARY/OPS, divergent | UNKNOWN_REQUIRES_REVIEW | merge-base with main `9cc71f2f`; 11 commits not preserved by main proven in this audit |
| `ops/open-browser-vps-20260822` | `e76f4468` | 2 | TEMPORARY OPS | ARCHIVE_BEFORE_DELETE | temporary browser/terminal line; 2 commits remain exclusive to branch relative to main |
| `ops/r8-task7-syntax-selfhosted-20260822` | `a15e1d8a` | 314 | TEMPORARY validation | ARCHIVE_BEFORE_DELETE | relative to current G2-B: 20 branch-only commits; not safe to drop |
| `test/caixa-de-pandora` | `30b4ae24` | 295 | TEMPORARY test | ARCHIVE_BEFORE_DELETE | relative to current G2-B: 1 branch-only commit remains |
| `ops/vps-sync-bootstrap-20260821` | `5db49d76` | 294 | SUPERSEDED checkpoint | SAFE_TO_DELETE | exact ancestor of current G2-B; zero exclusive commits relative to protected G2-B; HEAD 2026-08-21 |
| `continuity-protocol-v1` | `1984fe73` | 0 | MERGED/SUPERSEDED | SAFE_TO_DELETE | HEAD is exact ancestor of main; main is 132 commits ahead; HEAD 2026-08-14 |
| `continuity-protocol-v1-final` | `f1ecfeec` | 0 | MERGED/SUPERSEDED | SAFE_TO_DELETE | HEAD is exact ancestor of main; main is 135 commits ahead; HEAD 2026-08-14 |
| `continuity-protocol-v1-review` | `f1ecfeec` | 0 | DUPLICATE REF, merged/superseded | SAFE_TO_DELETE | same HEAD as `-final`; exact ancestor of main |
| `continuity-protocol-v1-staging` | `f1ecfeec` | 0 | DUPLICATE REF, merged/superseded | SAFE_TO_DELETE | same HEAD as `-final`; exact ancestor of main |

## Ahead/behind and merge-base notes

- The main implementation families (`G2-B`, `G1`, F1.2c) diverge from `main` at the historical implementation base `987c5359...`; this is expected and is not hygiene evidence for deletion.
- `codex/mission-001-foundations-f1-1` is an ancestor of `codex/mission-001-foundations-f1-2b-preparation`, which is an ancestor of `codex/mission-001-f1-2c-network-enforcement`.
- `ops/vps-sync-bootstrap-20260821@5db49d76` is an exact ancestor of `codex/control-bridge-g2b` and therefore has explicit preservation proof.
- Temporary G2-B branches with names suggesting disposability were deliberately *not* classified SAFE_TO_DELETE when parent-line comparison found exclusive commits.

## Final removable set from Agent A

Only these refs satisfy branch-level `SAFE_TO_DELETE` evidence at this stage:

- `continuity-protocol-v1`
- `continuity-protocol-v1-final`
- `continuity-protocol-v1-review`
- `continuity-protocol-v1-staging`
- `ops/vps-sync-bootstrap-20260821`

Deletion still depends on the Integrator proving final preservation and tests. No branch was deleted by Agent A.
