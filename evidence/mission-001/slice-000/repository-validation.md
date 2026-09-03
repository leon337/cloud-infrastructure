# Evidence — Mission 001 / Slice 000 Repository Validation

Date: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Slice: `000 — REPRODUCIBLE_FOUNDATION_BASELINE`
Scope of this evidence: repository artifacts only

## Validated revision

- repository: `leon337/cloud-infrastructure`
- branch: `codex/mission-001`
- validated SHA: `f2716e367d302aca700a5f41451e3fa2b7800f00`
- base `main` SHA at mission recovery: `987c5359ea948d1903355e98177ae1eb2f1849d5`

## GitHub Actions validation

Workflow: `mission-001-validate`

Successful run:

- run ID: `31940420737`
- run number: `4`
- head SHA: `f2716e367d302aca700a5f41451e3fa2b7800f00`
- status: `completed`
- conclusion: `success`
- execution environment: GitHub-hosted `ubuntu-latest`; not NODE-01 and not a self-hosted VPS runner

Successful checks:

1. checkout of the reviewed revision with `persist-credentials: false` and checkout action pinned by commit SHA;
2. repository whitespace validation;
3. pinned `ansible-core==2.21.2` validator installation;
4. YAML parsing for `infra/ansible/**` and canonical `state/**` YAML files;
5. `ansible-playbook --syntax-check` for all Mission 001 playbooks;
6. scan for common committed private-key/token patterns;
7. scan rejecting inventory/authentication password/private-key-content variables.

All listed checks concluded `success`.

## Failed validation retained as evidence

Initial workflow run `31940274977` failed before Ansible validation because the whitespace step referenced `HEAD^` while the default checkout was shallow. The failure was not ignored or marked valid.

Correction:

- workflow changed to `fetch-depth: 2`;
- subsequent runs passed;
- final validated run above passed all checks.

This is a validator defect history, not evidence that NODE-01 was changed or that an Ansible apply failed.

## Repository implementation covered

The validated revision includes, among other Mission 001 artifacts:

- canonical requirements/architecture/threat model/blueprint/roadmap;
- initial technology mappings;
- component inventory;
- read-only NODE-01 prechecks;
- prechange checkpoint role;
- guarded Tailscale installation role;
- guarded Docker/Compose installation role;
- conservative Slice 001/002 rollback playbooks;
- Mission 001 foundations runbook;
- Mission 001 CI validation workflow.

## Security properties of the repository slice

At the validated revision:

- no NODE-01 private SSH key is stored in Mission 001 inventory/configuration;
- no sudo password is stored;
- no Tailscale auth key is stored;
- no provider/API token is intentionally stored;
- Tailscale and Docker installation roles fail closed until exact version/checksum inputs are supplied after live precheck;
- Tailscale installation does not enroll NODE-01;
- Docker installation does not add human/agent users to the `docker` group;
- Docker installation does not publish a project/application host port;
- existing SSH/UFW recovery checks are part of apply/rollback contracts.

## What this evidence does NOT prove

This evidence does not prove current NODE-01 state, package versions, firewall state, SSH reachability, Tailscale behavior, Docker runtime behavior, reboot behavior, backup/restore behavior or idempotent execution on the VPS.

Those remain blocked on `HG-EXECUTION-ACCESS-001` because the current executor has no secure authenticated live execution channel to NODE-01.

## Mutation statement

- NODE-01 changes performed by this mission at this checkpoint: **NONE**.
- production changes: **NONE**.
- credential rotations: **NONE**.

## Next gate

`HG-EXECUTION-ACCESS-001` must be cleared through a secure existing authenticated access/session mechanism. Do not paste the private key or password into chat and do not weaken the canonical SSH policy.
