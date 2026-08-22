# CONTROL BRIDGE G2-B — Evidence

Status: `TASK_8_BLOCKED_EXTERNAL_DISPOSABLE_BOUNDARY`

## Scope

This directory records sanitized G2-B lifecycle evidence. It must never contain request content, credentials, snapshots, environment dumps, `/etc/shadow`, private keys, tokens, or unrelated host state.

## Task 7 accepted baseline

- focused bootstrap tests: `7 PASS / 0 FAIL`
- Ansible syntax checks: `3 PASS` on bounded self-hosted validation
- R8 completion commit: `047495c5c4215fc82d9e52d30114608af56deee5`
- reconciled pre-Task-8 head: `945052dc2503ba18a0e96ef03237c620ef336f9f`

## Task 8 pre-publication evidence

- local command: `./scripts/test.sh`
- local unit/static result: `371 PASS`
- shell syntax result: `16 PASS`
- local Ansible execution: `SKIP_CONTROLLER_MISSING_ANSIBLE_PLAYBOOK`
- disposable lifecycle: `SKIPPED` because hosted validate never started a step
- GitHub-hosted workflow: `control-bridge-g2b-ci` run `32551353362`
- validate attempt 1: `FAILURE / 0 STEPS / BlobNotFound`
- validate controlled retry: `FAILURE / 0 STEPS / BlobNotFound`
- lifecycle job: `SKIPPED`
- candidate SHA: `8e696288cb8f02b79ee130ac7cc5eca42ab6c961`
- classification: `BLOCKED_EXTERNAL_GITHUB_HOSTED_PRE_STEP`; causal billing claim is **not proven**

The privileged lifecycle harness explicitly refuses `node-01` and `vmi3506102`. The plan requires a disposable Ubuntu 24.04/systemd proof before Task 9. This evidence must not be relabeled as a code failure and must not be rerouted to NODE-01.

## Task 8 VPS QEMU/TCG attempt 1 and authorized retry

- boundary: `QEMU_TCG_UBUNTU_24_04` on NODE-01 host, with no host checkout mount
- host packages authorized and installed: `qemu-system-x86`, `qemu-utils`, `cloud-image-utils`
- official Ubuntu 24.04.4 cloud image SHA-256: `6e40c07ae715f744f84af0bec76415cc1987dd115b4b8de437818561f01a3733`
- attempt-1 candidate: `1f95cc22ecf570394b62d79f5cc217db062b9007`
- attempt-1 VM resources: `2 vCPU / 4 GiB RAM / TCG`
- attempt-1 result: `EXIT_9` before lifecycle markers; sanitized cause: `ubuntu user already exists` in the disposable fixture
- attempt-1 cleanup: `cleanup=0`; NODE-01 G2-B boundary remained absent
- harness correction: create the fixture `ubuntu` user only when absent and remove it only when created by the harness
- contract regression after correction: `371 PASS`, shell syntax `16 PASS`, continuity drift `PASS`
- LEANDRO authorized a resource resize for the retry
- post-attempt host capacity: ~`16 GiB MemAvailable`, `8` logical CPUs, no swap
- retry resource decision: `6 vCPU / 12 GiB RAM / TCG multi-thread`; 14 GiB was rejected to preserve host safety margin

Attempt 1 is a real disposable-harness compatibility failure, not a G2-B executor acceptance failure and not an authorized-resize abort. Task 8 remains unaccepted until a fresh exact candidate completes all 13 lifecycle markers and cleanup in the resized disposable VM.
