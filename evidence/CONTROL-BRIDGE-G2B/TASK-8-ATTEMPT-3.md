# G2-B Task 8 — Attempt 3 preserved evidence

Status: FAILED / ROOT CAUSE UNDETERMINED

## Immutable candidate

- protected lineage: `codex/control-bridge-g2b`
- candidate SHA: `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`
- candidate commit: `fix(g2b): create libexec parent in disposable bootstrap`
- original PR: #11

## Terminal attempt-3 evidence

PR #11 recorded at 2026-08-22T12:56:11Z:

```text
MCF_G2B_TASK8_FINISHER
UTC=2026-08-22T12:56:11Z
CANDIDATE=fbef3d407dbd9b7947b6c100a63d098eaebe2b6a
TASK8_STATUS=2
G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0
RESOURCE=RESOURCE_UPDATE_PASS container=control-bridge-g2b-test-20260822115505-4579-6146 cpus=5 memory=8g
TASK8_ACCEPTANCE=FAIL_OR_NOT_TERMINAL
```

The live monitor subsequently confirmed:

```text
HOST_MONITOR_STATUS=2
QEMU=ALIVE
PORT_22284=LISTEN
GUEST_SSH=PASS
GUEST_TASK8_STATUS=2
MARKERS=0
REPO_HEAD=fbef3d407dbd9b7947b6c100a63d098eaebe2b6a
REPO_DIRTY_COUNT=0
```

## Existing read-only audit evidence

Run `32577551012`, job `97041975190` (2026-08-22T14:03Z) proved:
- NODE-01 repository was clean on `codex/control-bridge-g2b@fbef3d4`;
- no harness or ansible-playbook process remained;
- QEMU PID 775679 was still active;
- disposable workdir was `/tmp/g2b-task8-vm3.4UklnBQQ`.

Run `32577659953`, job `97042247009` (2026-08-22T14:05Z) proved:
- guest SSH was reachable on `127.0.0.1:22284`;
- QEMU name `g2b-disposable-task8-vm3`;
- 6 vCPU / 12288 MiB;
- overlay, seed, serial log and disposable SSH key still existed in the attempt-specific workdir;
- no `harness.log`, `guest.log`, `result.log` or `run.log` existed in the outer workdir.

Run `32577815107`, job `97042636952` (2026-08-22T14:09Z) read the guest status without G2-B mutation and proved:

```text
/home/ubuntu/g2b-task8.status = 2
/home/ubuntu/g2b-task8.log size = 267 bytes
G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0
```

The same audit recovered `run-task8.sh`, which executed:

```text
G2B_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_UBUNTU_24_04_ONLY \
G2B_CANDIDATE_SHA=fbef3d407dbd9b7947b6c100a63d098eaebe2b6a \
./scripts/test_control_bridge_g2b_vm.sh > /home/ubuntu/g2b-task8.log 2>&1
```

## Exact failing process boundary

Inside `scripts/test_control_bridge_g2b_vm.sh`, `CURRENT_STAGE=apply_g2b` executes the same command twice:

```text
docker exec --workdir /workspace/cloud-infrastructure/automation/ansible <container> \
  /opt/foundation-test-venv/bin/ansible-playbook \
  --inventory inventory/test-container/hosts.yml \
  playbooks/apply-control-bridge-g2b.yml
```

Both invocations are redirected with `>/dev/null`. The outer task log captures stderr but not Ansible stdout. The preserved 267-byte log contains no failing task name or Ansible fatal record. Therefore the evidence proves `apply_g2b exit=2`, but does not prove which of the two playbook invocations failed or which Ansible task caused it.

## Previous and next stages

Previous successful harness boundary:
- fixture built and started;
- systemd reached `running|degraded`;
- `ubuntu` identity existed or was created.

External resource watcher also recorded `RESOURCE_UPDATE_PASS`.

Immediately following step that did not occur:
- service-account/entrypoint/workspace identity assertions;
- marker `G2B_DISPOSABLE_IDENTITY_PASS`.

No acceptance marker was emitted.

## Residue / cleanup

- inner Docker harness cleanup: `cleanup=0` — success.
- outer QEMU guest: still alive at the last preserved audit, 2026-08-22T14:09Z.
- current outer-QEMU cleanup state after that audit: **NOT VERIFIED**.
- do not destroy the preserved VM/workdir until the central auditor confirms evidence sufficiency or an equivalent forensic capture exists.

## Evidence references

- PR #11: https://github.com/leon337/cloud-infrastructure/pull/11
- run 32577551012: https://github.com/leon337/cloud-infrastructure/actions/runs/32577551012
- run 32577659953: https://github.com/leon337/cloud-infrastructure/actions/runs/32577659953
- run 32577815107: https://github.com/leon337/cloud-infrastructure/actions/runs/32577815107
- candidate: https://github.com/leon337/cloud-infrastructure/commit/fbef3d407dbd9b7947b6c100a63d098eaebe2b6a
