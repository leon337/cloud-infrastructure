# G2-B Task 8 — reconciled local lab evidence — 2026-08-23

Status: `PASS_DISPOSABLE_NOTEBOOK_DOCKER` for Task 8 only.

Capability lifecycle: `LAB_VALIDATED_INACTIVE`.

This evidence supersedes the earlier Task 8 blocker only for the exact local disposable candidate below. It does not rewrite the historical hosted/QEMU attempts and does not prove staging, NODE-01, production, real MCF use, or Tasks 9/10.

## Reconciled lineage

- mature G1/G2-A base: `mcf/mission-001-control-bridge-g1` at `3e34044c0fb10429fe2f7a262dec21932479f143`
- G2-B Task 8 input: `team/g2b-task8-20260822` at `f116f168b5fda3ca990edc2c67b5235a3c1f2ec0`
- two-parent reconciliation merge: `9359450742020d1c99b298379b8a29fefce6294f`
- exact successful lab candidate: `570779b75ba41ac3725ef16bc65a163e01631a1c`
- local branch: `codex/context-bridge-reconcile-20260823`
- push / pull request / merge: not executed

The reconciliation merge has the mature G1/G2-A revision and the Task 8 input revision as its two parents. The safe future pull-request target is `mcf/mission-001-control-bridge-g1`; this evidence is not authorization to publish or merge it.

## Reproduced corrections

Only failures reproduced in the local disposable lifecycle were corrected:

1. The installed wrapper selected the workspace catalog while the executor requires the exact fixed pilot leaf. The wrapper now binds to `/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev`.
2. The disposable Ubuntu fixture lacked the bounded rollback inspection dependency `lsof`.
3. An empty successful `lsof` probe returns exit code 0; cleanup had incorrectly required exit code 1.

The harness also reports only a sanitized failed Ansible task label on cleanup failure; it does not print request, grant, content, or raw playbook logs.

## Local disposable proof

Boundary and invocation:

- host: developer notebook, explicitly not `node-01` or `vmi3506102`
- fixture: Ubuntu 24.04 with systemd inside a disposable privileged Docker container
- container network: `--network none`
- candidate binding: `G2B_CANDIDATE_SHA=570779b75ba41ac3725ef16bc65a163e01631a1c`
- exact confirmation: `G2B_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_UBUNTU_24_04_ONLY`
- result: exit 0
- cleanup: pass

The harness emitted all 13 required markers in order:

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

## Other gates

- full unit discovery at reconciliation merge `9359450`: `372 / 372 PASS`
- full unit discovery after Capsule, mapping, state, and continuity reconciliation: `381 / 381 PASS`
- focused/static tests after the reproduced corrections: pass
- aggregate `scripts/test.sh`: blocked before its test phase by two pre-existing zero-byte loose objects in the shared Git object database (`c4a178587bcc1e469452bf1705a91c894e36049c` and `fa506a3ce9b6f6d75128f07985cee78d53ed903b`)

The aggregate failure is classified as a local shared-repository/history-scanner blocker, not as a passing or failing result for the candidate. The shared object database was not repaired or modified.

## Boundaries that remain closed

- G2-B Tasks 9 and 10: `NOT_STARTED`
- Context-to-G2-B mutating transport: `NOT_IMPLEMENTED`
- G2-B activation: `NOT_AUTHORIZED`
- NODE-01 bootstrap: `NOT_AUTHORIZED`
- real grant/write/rollback/revocation: `NOT_EXECUTED`
- effective MCF use of G2-B: `NOT_EXECUTED`
- staging and production: `NOT_EXECUTED`
- push, pull request, and merge: `NOT_EXECUTED`
