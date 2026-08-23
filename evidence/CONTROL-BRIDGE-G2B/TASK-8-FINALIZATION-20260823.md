# G2-B Task 8 — Finalization checkpoint — 2026-08-23

Status: BLOCKED / REQUIRES_REVIEW

## Root cause proven

The original protected candidate `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a` was reproduced with full Ansible output in run `32609821992`, job `97120897002`.

The first `apply-control-bridge-g2b.yml` invocation failed at:

`control_bridge_g2b : Verify ubuntu direct write is denied by the protected parent`

Observed command/result:

```text
cmd: ["test", "!", "-w", "/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev"]
rc: 1
G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0
```

The exact test inventory in the original candidate contained:

```yaml
ansible_connection: local
ansible_become: false
```

That inventory-level `ansible_become: false` overrides the task-level `become: true` / `become_user: ubuntu`, so the direct-write proof runs with the controller's privileged context instead of `ubuntu`. For a root-capable context, `test -w` succeeds against the 0700 workspace, causing the negated assertion to fail and Ansible to return exit 2.

## Minimal correction retained

The isolated branch removes only `ansible_become: false` from:

`automation/ansible/inventory/test-container/hosts.yml`

and adds the regression test:

`test_disposable_inventory_does_not_override_task_become`

in `tests/test_g2b_disposable_integration.py`.

A later experimental role change that explicitly used `sudo -u ubuntu` was reverted before finalization because it was redundant once the proven inventory override was identified.

## Safety boundaries

- real G2-B write on NODE-01: NOT EXECUTED
- main: NOT MODIFIED
- codex/control-bridge-g2b: NOT REWRITTEN
- Tasks 9/10: NOT STARTED
- HUMAN_GATE: NOT CROSSED
- merge: NOT EXECUTED

The full-output reproduction explicitly emitted `NO_G2B_NODE01_WRITE=PASS`.

## Validation after correction

A clean candidate with only the proven inventory fix + regression test (plus evidence/PRF) was produced at:

`7c0b7c627279aab0820298dd44127d216ec3b699`

Permanent `control-bridge-g2b-ci` run:

- run: `32618746863`
- validate job: `97143542157` — FAILURE
- disposable-lifecycle: SKIPPED

Attempts to retrieve the validate log returned GitHub `BlobNotFound`; therefore the validation failure cause is NOT VERIFIED and is not attributed to the functional correction.

A temporary hosted validation attempt also ended failure, but its job log was likewise unavailable. Temporary diagnostic/application/validation workflows were removed from the final branch tree.

## Acceptance decision

Task 8 cannot receive PASS because no post-fix complete disposable lifecycle with exit 0 and all 13 acceptance markers is available for the final corrected candidate.

State: BLOCKED / REQUIRES_REVIEW

Required continuation if central audit reopens the task: obtain readable CI output for the clean candidate, run the complete disposable lifecycle, and require all acceptance markers before PASS. Do not merge or start Tasks 9/10 before that evidence exists.
