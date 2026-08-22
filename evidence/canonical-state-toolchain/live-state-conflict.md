# Live Canonical State Conflict — 2026-08-22

## Conflict

A final live GitHub reconciliation found that the current PR #11 description still projects G2-B Task 8 attempt 3 as `IN_PROGRESS_VPS_QEMU_TCG_DISPOSABLE_PROOF`. Its latest measurement comment inspected here was captured at `2026-08-22T12:22:40Z` and also reported `GUEST_TASK8_STATUS=running`.

That projection conflicts with later executable evidence and with the merged `main` reconciliation.

## Later executable evidence

GitHub Actions run `32577815107` (`vps-g2b-attempt3-audit-once`) completed successfully and executed a bounded read-only inspection of the disposable guest. At `2026-08-22T14:09:03Z`, the guest inspection returned:

```text
/home/ubuntu/g2b-task8.status = 2
G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0
```

The disposable QEMU VM was still present, but Task 8 acceptance was not proven. This is later than the running measurement in the PR comments.

## Integrated projection

`main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`, merged by PR #18, reconciles the project at approximately `2026-08-22T14:09Z` and records G2-B as `TASK_8_FAILED_ATTEMPT_3`, with Tasks 1–7 complete and Tasks 9–10 not started.

## Resolution under the mission truth order

The conflict is resolved in favor of the later executable audit plus the merged main reconciliation:

- PR #11 body: **STALE PROJECTION**;
- earlier PR comment reporting running: **HISTORICAL MEASUREMENT**;
- workflow run `32577815107`: **LATER EXECUTABLE EVIDENCE**;
- merged main README: **CURRENT INTEGRATED PROJECTION CONSISTENT WITH THE EXECUTABLE EVIDENCE**.

Canonical conclusion for this mission: G2-B Task 8 is `FAILED_ATTEMPT_3_NOT_ACCEPTED`. No G2-B code or branch state is changed by this conclusion.
