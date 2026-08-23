# G2-B Task 8 — Finalization evidence — 2026-08-23

Status: PASS_TECHNICAL / READY_FOR_CENTRAL_AUDIT / DO_NOT_MERGE_AUTOMATICALLY

## Protected source
- branch: `codex/control-bridge-g2b`
- SHA: `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`

## Work branch
- branch: `team/g2b-task8-20260822`
- PR: #21
- validated functional SHA: `ac3e2f8a52b881bcd2b40acab0d723d547b90e81`

## Proven root causes and corrections
1. Attempt-3 `apply_g2b exit=2`: disposable inventory `ansible_become: false` overrode task-level `become: true / become_user: ubuntu`. The override was removed and a regression test retained.
2. `workspace.write` refusal: installed boundary passed the protected root-owned workspace parent to `execute_request`; the executor contract expects the already-resolved operational workspace. The pilot boundary now passes the exact fixed leaf `/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev`. Parent ownership protections remain unchanged.
3. Bounded cleanup dependency: rollback uses `lsof`, but the disposable fixture did not install it. `lsof` was added only to the fixture and guarded by regression test.
4. Bounded cleanup return code: fixture proved `lsof -nP -u <existing-user-with-no-open-files>` returns rc=0 with empty stdout/stderr. Rollback already allowed rc 0/1 during collection but asserted rc==1 afterward. Assertion now accepts rc in [0,1] and still requires stdout length == 0.

## Final validation on disposable local boundary
- repository clean: PASS
- secret policy: PASS
- unit tests: 373/373 PASS
- Ansible syntax: 9/9 PASS
- focused G2-B tests: PASS
- lifecycle exit: 0
- required acceptance markers: 13/13, exactly once, required order
- abort markers: 0
- `G2B_BOUNDED_CLEANUP_PASS`: present
- residual G2-B processes: 0
- residual G2-B containers: 0
- residual G2-B images: 0
- `NO_G2B_NODE01_WRITE=PASS`

## Required marker record
1. `G2B_DISPOSABLE_IDENTITY_PASS`
2. `G2B_TRANSPORT_DIRECT_WRITE_REFUSED`
3. `G2B_GRANT_24H_PASS`
4. `G2B_WRITE_PASS`
5. `G2B_REPLAY_PASS`
6. `G2B_REQUEST_ID_CONFLICT_PASS`
7. `G2B_CONCURRENCY_PASS`
8. `G2B_AUDIT_PASS`
9. `G2B_ROLLBACK_PASS`
10. `G2B_FINAL_STATE_PASS`
11. `G2B_REVOKE_PASS`
12. `G2B_POST_REVOKE_REFUSAL_PASS`
13. `G2B_BOUNDED_CLEANUP_PASS`

## GitHub-hosted checks after candidate publication
The following validate jobs failed before code execution:
- control-bridge-g2b-ci run `32624457045`, job `97157525706`;
- docker-boundary-ci run `32624457027`, job `97157525783`;
- foundation-ci run `32624457060`, job `97157525839`.

All have `runner_id=0`, `steps=[]`, and the GitHub annotation states that the job was not started because recent account payments failed or the spending limit needs to be increased. Classification: `BLOCKED_BY_BILLING_BEFORE_EXECUTION`.

## Safety boundaries
- real NODE-01 G2-B write: NOT_EXECUTED
- `main`: NOT MODIFIED BY THIS FRONT
- protected source branch: NOT REWRITTEN
- Tasks 9/10: NOT STARTED
- HUMAN_GATE: NOT CROSSED
- merge: NOT EXECUTED

## Acceptance decision
Task 8 technical acceptance is PASS based on the exact validated disposable lifecycle and repository test evidence. PR #21 remains draft/unmerged for central audit. Hosted GitHub checks remain externally blocked by billing and must not be misreported as repository test failures.
