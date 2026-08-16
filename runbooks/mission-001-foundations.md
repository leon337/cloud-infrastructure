# Runbook — CODEX Mission 001 Foundations

Mission: `CODEX-EXECUTION-MISSION-001`
Scope: `DEV/LAB ONLY`

This runbook governs Slice 000 recovery and the first host-changing foundations, Slice 001 Tailscale client installation and Slice 002 Docker/Compose installation.

## 1. Non-negotiable guards

- Never paste or commit the SSH private key, key passphrase, sudo password, Tailscale auth material, API token or provider credential.
- Do not rotate existing credentials.
- Do not accept an unexpected SSH host key.
- Do not weaken the existing OpenSSH/UFW/fail2ban recovery path.
- Do not publish project/container ports in the Docker foundation slice.
- Do not add LEANDRO, agents or project users to the `docker` group.
- Stop on material drift; do not reinterpret drift as a reason to force the desired state.

Expected canonical ED25519 SSH host fingerprint at mission start:

```text
SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4
```

## 2. Slice 000 — live recovery prerequisite

From the secure operator/execution environment with the existing approved SSH key:

1. verify the live host key fingerprint independently;
2. run `infra/ansible/playbooks/precheck-readonly.yml`;
3. run `infra/ansible/playbooks/precheck-privileged-readonly.yml` with interactive `--ask-become-pass`;
4. compare hostname, OS, kernel, package/runtime state, listeners, interfaces/routes, UFW/nftables, SSH policy, fail2ban, backup timer and recovery configuration to the canonical Git state;
5. record every material divergence;
6. do not set `mission_live_precheck_passed=true` unless the reconciled result is explicitly accepted for the next slice.

The private key path is provided only at runtime from the secure local environment.

## 3. Version/checksum pinning before apply

Before Slice 001 or 002:

- query the official upstream package repository from the secure execution environment;
- record the exact package version selected;
- download/read the official repository-signing key and repository definition without executing them;
- calculate and record SHA-256 values required by the Ansible role;
- ensure the package is absent or already exactly at the reviewed version;
- if another runtime/version is present, stop and assess impact rather than auto-removing/upgrading it.

The values may be supplied through a reviewed non-secret vars file or command-line vars. Signing-key checksums and package versions are not secrets; authentication material is.

## 4. Prechange checkpoint

Every host-changing playbook requires a stable `mission_checkpoint_id`.

The `prechange_checkpoint` role captures a protected local baseline under:

```text
/var/backups/cloud-infrastructure/mission-001/<checkpoint-id>
```

It records package inventory, interfaces/routes, listeners, UFW, nftables, key service states, apt source definitions and hashes.

A checkpoint is not an off-host full backup. Existing recovery mechanisms and off-host config backups remain required.

## 5. Slice 001 — Tailscale client installation

### Goal

Install the private-management-overlay client without enrolling NODE-01 and without changing the existing SSH fallback.

### Apply prerequisites

- live precheck PASS;
- expected host fingerprint verified;
- exact Tailscale package version selected;
- repository key/list SHA-256 values selected;
- current Tailscale package/repo state inspected;
- stable checkpoint ID chosen.

### Apply

Use:

```text
playbooks/slice-001-tailscale-install.yml
```

Required runtime gates:

```text
mission_live_precheck_passed=true
mission_expected_fingerprint_verified=true
mission_checkpoint_id=<reviewed-id>
```

plus exact Tailscale package/checksum variables.

### Expected effect

- official Tailscale apt source/key installed at reviewed checksums;
- exact reviewed Tailscale package installed;
- `tailscaled` enabled/started;
- **no `tailscale up`**;
- no auth key consumed;
- SSH fallback remains active.

### Validation

- SSH service active;
- UFW/firewall baseline remains understood;
- listeners reviewed for unintended public exposure;
- no enrollment occurred automatically;
- package version equals selected version.

### Enrollment gate

Enrollment is a separate operation requiring approved LEANDRO device/user identity and deny-by-default Tailscale Grants. Do not enable Tailscale SSH in the initial slice.

### Rollback

`playbooks/slice-001-tailscale-rollback.yml` may remove the client only if checkpoint evidence proves Tailscale was introduced by this slice and rollback is explicitly confirmed. If Tailscale existed beforehand, restore its prior state instead of removing it.

Verify SSH and UFW again after rollback.

## 6. Slice 002 — Docker/Compose runtime foundation

### Goal

Install Docker Engine + Compose as a protected platform runtime with no agent Docker authority and no public project workload.

### Apply prerequisites

- live precheck PASS;
- expected host fingerprint verified;
- exact versions selected for Docker CE, CLI, containerd.io, Buildx and Compose plugin;
- Docker repository-key SHA-256 recorded;
- current runtime/package state inspected;
- conflicting `docker.io`, `containerd`, `runc`, `podman-docker` or similar packages resolved by explicit decision, never automatic removal;
- stable checkpoint ID chosen.

### Apply

Use:

```text
playbooks/slice-002-docker-install.yml
```

The playbook blocks implicit upgrades/downgrades and conflicting runtimes.

### Expected effect

- official Docker apt source/key installed;
- exact reviewed packages installed;
- Docker service enabled/started;
- `docker` group has no human/agent member;
- Docker daemon has no TCP API listener;
- no project workload or host application port is created.

### Security validation

After installation inspect all three views:

```text
ss -lntup
ufw status verbose
nft list ruleset
```

Docker's firewall integration must be treated as effective policy, not inferred from UFW output alone. Any unintended public listener or rule is a failed slice.

Also verify:

- SSH/fail2ban remain healthy;
- Docker/Compose report the exact selected versions;
- no unauthorized Docker group member;
- reboot/reconnect path when the slice reaches that validation stage;
- second desired-state reconciliation does not introduce unexpected changes.

### Rollback

`playbooks/slice-002-docker-rollback.yml` is allowed only while checkpoint evidence proves Docker packages were introduced by Slice 002 and no later platform/project workload depends on the runtime.

Rollback stops/removes the packages and apt source but does **not** purge `/var/lib/docker`, volumes or project data. SSH and UFW are verified afterward.

## 7. Evidence

For each execution store only sanitized evidence containing:

- timestamp;
- branch/repository SHA;
- target node;
- verified host fingerprint result;
- selected exact versions/checksums;
- precheck assertions;
- detected drift;
- apply changed/ok/failed counts;
- listener/firewall/service validation;
- rollback test/result when applicable;
- next gate.

Never store raw secrets, token values, private keys, passphrases or connection strings.

## 8. Failure policy

A failed precheck/apply/validation does not become `DONE` because a later manual command appears to work. Stop that slice, preserve evidence and recovery access, classify the failure, update desired state/runbook if required, then rerun the complete relevant validation path.
