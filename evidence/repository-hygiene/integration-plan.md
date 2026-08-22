# Repository Sanitization — Integration Plan

## Integrated compatible patches

The integrator consolidated only:

- current-context documentation corrections (`CONTEXT.md`, `CHECKPOINT.md`);
- repository hygiene governance (`docs/REPOSITORY-HYGIENE.md`);
- A–H audit/evidence reports.

It did not integrate G2-B code, F1.2c code, active state files, temporary operational branches, or any privileged NODE-01 action.

## Conflicts / blockers

### Canonical structured state

`state/current.yaml` on main is older than current README. Protected G2-B state is also older than the later attempt-3 README reconciliation. Copying either would create false canonical state. Resolution is blocked until the correct implementation integration source and its state validation toolchain are selected.

### Mandatory repository tests

`scripts/test.sh` is absent from `main` and therefore absent from this main-based integration branch. `ROADMAP-CHECKLIST.md` and `state/active-mission.yaml` are also absent. They exist in later implementation lineage, but importing them as part of repository hygiene would cross the active-work boundary.

## Candidate removable refs — preservation proof

Deletion is deferred until integration tests can be completed.

| BRANCH | HEAD SHA | LAST COMMIT | REASON | PRESERVATION PROOF |
|---|---|---|---|---|
| `continuity-protocol-v1` | `1984fe73a4eaa50a34990e0d9fca1a721b544de2` | `docs: add formal continuity validation gate` | merged/superseded historical ref | HEAD is exact ancestor of protected `main@f2e01dfa`; main is 132 commits ahead |
| `continuity-protocol-v1-final` | `f1ecfeec9810cf07135233dcb0cc47e39cf01419` | `config: pin Contabo VPS SSH endpoint in sanitized example` | merged/superseded | HEAD exact ancestor of `main@f2e01dfa`; main 135 commits ahead |
| `continuity-protocol-v1-review` | `f1ecfeec9810cf07135233dcb0cc47e39cf01419` | same as above | duplicate historical ref | same HEAD already preserved by main ancestry |
| `continuity-protocol-v1-staging` | `f1ecfeec9810cf07135233dcb0cc47e39cf01419` | same as above | duplicate historical ref | same HEAD already preserved by main ancestry |
| `ops/vps-sync-bootstrap-20260821` | `5db49d76dd530038aaf032aeba055b61eaab653a` | `docs(continuity): complete R7 and set R8 as next stage` | superseded checkpoint | exact ancestor of protected `codex/control-bridge-g2b@fbef3d40`; G2-B is 9 commits ahead and contains the commit |

No ref above will be deleted while the Wave-3 test requirement remains unsatisfied.

## Not removable

Branches with unpreserved exclusive commits remain `ARCHIVE_BEFORE_DELETE` or `UNKNOWN_REQUIRES_REVIEW`. In particular, temporary G2-B/F1.2c/terminal/test refs are not deleted based on naming.

## PR / issue actions

- PR #11: no action; protected active G2-B.
- PR #7: do not auto-close until its branch-only commits are preserved/classified.
- Issues #4/#5: remain evidence sinks.
- No PR/issue closure is required to establish the current blocked hygiene verdict.

## Execution rule

When a valid canonical integration base containing the active validation toolchain is available:

1. reconcile structured state without promoting G2-B beyond evidence;
2. run `git diff --check`;
3. run `./scripts/test.sh` and relevant targeted tests;
4. rerun independent verification;
5. only then delete the five proven removable refs;
6. record final branch/PR/workflow before/after counts and preservation evidence.
