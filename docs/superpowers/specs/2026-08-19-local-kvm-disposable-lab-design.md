# Local KVM Disposable Integration Lab Design

Status: DESIGN_APPROVED_IN_CHAT — WRITTEN_SPEC_REVIEW_PENDING

Date: 2026-08-19

## Purpose

Provide a zero-additional-cost, disposable Ubuntu 24.04 integration laboratory on the operator's local Linux workstation using QEMU/KVM. The laboratory exists specifically to run the privileged F1.2c integration harness without using GitHub-hosted runners and without using NODE-01 as the test environment.

The laboratory must reproduce the host surfaces that matter to the current defect class: real `systemd`, real Docker daemon, real iptables/ip6tables, sysctl, service startup, Docker restart/reconciliation, idempotence and bounded rollback.

## Safety model

The local workstation is the hypervisor only. Privileged test operations execute inside a disposable VM, never on the workstation and never on NODE-01.

The host-side launcher must fail closed unless all of the following are true:

- `qemu-system-x86_64`, `qemu-img` and `cloud-localds` are present;
- `/dev/kvm` exists and is readable/writable by the current user;
- the host is not NODE-01 (`vmi3506102` / `node-01`);
- the source repository is clean for the exact candidate commit being tested;
- the Ubuntu base image digest matches an explicitly pinned SHA-256;
- a unique temporary working directory can be created;
- no privileged host networking, TAP device, bridge creation or host firewall modification is required.

The launcher itself must not require host `sudo` for normal execution.

## Isolation boundary

The VM uses QEMU/KVM with user-mode networking only (`-nic user` / SLIRP) and one localhost-only SSH forward. No TAP, bridge, macvtap, host network namespace changes, iptables changes or Docker socket access on the workstation are allowed.

The VM receives its own qcow2 overlay based on a read-only cached Ubuntu 24.04 cloud image. The overlay and cloud-init seed are unique per run and are deleted at the end of the run whether the test passes or fails.

The guest is considered disposable. Nothing inside the guest is a source of durable state.

## Base image and provenance

The first implementation targets the official Ubuntu 24.04 LTS cloud image for amd64.

The launcher may download the image into a user-owned cache directory such as `~/.cache/mcf-kvm-lab/`, but must verify a repository-pinned SHA-256 before use. A digest mismatch is a hard refusal.

The cached base image is never modified directly. Each run creates a qcow2 overlay using the cached image as its backing file.

## Guest bootstrap

Cloud-init creates one temporary administrative test user and installs only the packages required by the existing integration harness, including Docker Engine from the Ubuntu guest repositories and supporting utilities used by the test scripts.

Authentication is by an ephemeral SSH key generated for the run. The private key remains on the local workstation and is deleted with the run directory. Password login is disabled.

The guest does not receive the operator's GitHub credentials, SSH private keys, VPS credentials or production secrets.

## Candidate transfer

The private GitHub repository is not cloned from inside the VM.

The host launcher creates a Git bundle for the exact candidate commit from the local repository and copies that bundle into the guest over the localhost-only SSH forward. The guest reconstructs a working tree from that bundle and verifies that `git rev-parse HEAD` equals the requested candidate SHA before any privileged integration test begins.

This keeps GitHub authentication outside the guest and makes the tested commit explicit and reproducible.

## Test identity and fail-closed gate

The current disposable harness accepts only the GitHub-hosted identity string. That gate must not be weakened or replaced.

Instead, the harness will gain a second explicit laboratory identity for the local KVM environment. The new identity must require multiple independent proofs before privileged/destructive steps are enabled:

- exact local-KVM confirmation token;
- guest hostname with an MCF KVM lab prefix;
- `systemd-detect-virt` identifies KVM/QEMU virtualization;
- presence of a cloud-init marker unique to this lab implementation;
- expected Ubuntu 24.04 guest release;
- expected temporary test user;
- positive `sudo -n true` only inside the guest;
- negative check that hostname is not NODE-01;
- clean initial Docker containers/volumes/custom networks after guest bootstrap.

Any missing or contradictory proof aborts before destructive cleanup or network mutation.

## Integration lifecycle

Inside the guest, the existing F1.2c integration lifecycle remains authoritative. The local KVM path must exercise the same operational behavior as the disposable GitHub VM path, including:

1. install the base network enforcement payload;
2. apply and verify the base enforcement layer;
3. install network-services helper, configuration, sysctl file and the exact `cloud-platform-network-services.service` unit;
4. `systemctl daemon-reload` and start the exact unit through `systemd`;
5. require the unit to be active and require no relevant service error in the journal;
6. prove the service helper reports the expected healthy state;
7. prove a second apply is idempotent;
8. prove scoped DNS works;
9. prove direct egress remains denied;
10. prove permitted proxy egress works;
11. restart Docker;
12. prove the `systemd` unit reconciles after Docker restart;
13. re-check network-services state;
14. perform bounded rollback;
15. prove managed containers, custom networks, test images and forwarding state are cleaned as required by the harness.

The specific runtime-lock regression is therefore exercised through the same `systemd` sandbox that failed on NODE-01, not by invoking the helper directly.

## Host-side launcher behavior

A single user-facing script will orchestrate the laboratory. Its interface should be intentionally narrow, for example:

`./scripts/run_f1_2c_kvm_lab.sh <candidate-sha>`

No arbitrary guest command parameter is permitted.

The script is responsible for prerequisite checks, image verification, ephemeral key creation, qcow2 overlay creation, cloud-init seed generation, QEMU startup, readiness polling, bundle transfer, guest test invocation, result capture and cleanup.

The launcher records a concise evidence directory outside the disposable VM containing only non-secret artifacts such as candidate SHA, base-image digest, timestamps, QEMU version, guest release, test exit code and sanitized harness output.

## Cleanup and crash handling

Normal completion deletes the guest overlay, cloud-init seed, ephemeral SSH key and QEMU process state.

Signal and error traps must attempt bounded cleanup of the QEMU process and temporary files. The cached verified Ubuntu base image may remain because it is immutable and reusable.

The cleanup code must never recursively delete a caller-supplied path. All run artifacts live below a launcher-created directory with a fixed prefix and validated ownership.

## Resource defaults

Initial defaults:

- 2 vCPU;
- 4 GiB RAM;
- 24 GiB qcow2 overlay virtual size;
- headless QEMU;
- localhost-only dynamically selected high SSH port.

The launcher must perform a lightweight host capacity check and refuse cleanly if safe execution is not possible. Resource tuning is implementation detail; no automatic privileged host tuning is permitted.

## TDD requirements

Implementation follows test-first development.

Required test coverage includes:

- host prerequisite refusal cases;
- NODE-01 hostname refusal;
- KVM-access refusal;
- base-image digest mismatch refusal;
- dirty or wrong candidate refusal;
- fixed launcher CLI with no arbitrary guest-command escape hatch;
- user-mode networking only;
- localhost-only SSH forwarding;
- no host `sudo`, TAP, bridge, iptables or Docker socket use;
- exact Git bundle SHA verification in the guest;
- distinct GitHub-hosted and local-KVM disposable confirmation gates;
- local-KVM gate refusal when any virtualization/marker/hostname proof is missing;
- cleanup path boundedness;
- exact `systemd` unit lifecycle remains exercised by the VM harness.

Static tests must be runnable on the existing unprivileged NODE-01 self-hosted runner because they do not create a VM there.

The full KVM integration test is executed only on the operator's local workstation after the static implementation is green.

## Acceptance criteria

The local KVM laboratory is accepted only when all of the following are evidenced on one exact candidate commit:

- static repository tests pass;
- local KVM launcher prerequisites pass on the operator workstation;
- Ubuntu 24.04 guest boots under KVM without host sudo;
- candidate SHA is verified inside the guest;
- exact `systemd` network-services unit starts successfully under `ProtectSystem=strict` with its private runtime directory;
- F1.2c DNS/proxy/direct-egress/restart/idempotence checks pass;
- bounded rollback passes;
- guest test environment is deleted after completion;
- no NODE-01 mutation occurs during laboratory validation;
- no GitHub-hosted paid runner is required.

Only after this fresh disposable integration evidence exists may PR #9 proceed toward canonical integration and a separately gated NODE-01 recovery/reapply sequence.

## Non-goals

This design does not create a general-purpose VM platform, CI farm, developer desktop VM, production hypervisor, persistent local cluster or arbitrary command executor. It does not change the production HUMAN_GATE policy and does not authorize unrestricted root, Docker or network access on NODE-01.
