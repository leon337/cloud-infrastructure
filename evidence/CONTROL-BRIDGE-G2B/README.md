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
