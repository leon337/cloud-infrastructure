# 56 — G2-B Task 8 — VPS QEMU/TCG Disposable Boundary Plan

Status: **PLANNED — HUMAN PACKAGE-INSTALL GATE REQUIRED**
Updated: **2026-08-22**
Repository: `leon337/cloud-infrastructure`
Active branch: `codex/control-bridge-g2b`

## Objective

Complete G2-B Task 8 on the existing VPS without using NODE-01 itself as the disposable test boundary and without depending on GitHub-hosted Actions.

## Verified host facts

- host: `vmi3506102`, Ubuntu 24.04.4 LTS, x86_64;
- `/dev/kvm`: absent;
- QEMU/libvirt/systemd-nspawn tooling: not installed;
- Docker: installed, but privileged Docker directly on NODE-01 is forbidden for this proof;
- available capacity observed: ~15 GiB RAM available and ~270 GiB disk free;
- Ubuntu repositories offer `qemu-system-x86`, `qemu-utils`, and `cloud-image-utils`.

## Decision

Use **QEMU x86_64 with TCG software emulation**. KVM is not required. The QEMU guest, not NODE-01, becomes the Ubuntu 24.04/systemd disposable boundary.

Do not reuse or modify the frozen F1.2c branch. Do not run the existing privileged lifecycle harness directly on `vmi3506102`.
## Boundary architecture

```text
NODE-01 / vmi3506102
  └─ unprivileged QEMU process (`-accel tcg`)
      └─ disposable Ubuntu 24.04 VM + systemd
          └─ Docker/Ansible test tooling
              └─ existing G2-B lifecycle harness
```

The guest uses its own qcow2 overlay and cloud-init seed. SSH is exposed only through a localhost host-forward. No host directory is bind-mounted into the guest.

The exact candidate is transferred as an archive produced from the clean Git commit. The guest must verify the expected SHA before any lifecycle test begins.

## Host prerequisites — HUMAN_GATE

Install only:

```text
qemu-system-x86
qemu-utils
cloud-image-utils
```

This is the only required privileged host mutation for the disposable proof. Installation must be explicitly authorized and performed through normal sudo handling; credentials are never captured or relayed.

## Execution sequence

1. Revalidate branch, exact HEAD, clean worktree, NODE-01 G2-B absence and available capacity.
2. Download/cache the official Ubuntu 24.04 cloud image and record its SHA-256.
3. Create an ephemeral qcow2 overlay, cloud-init seed and ephemeral SSH key under a dedicated temporary directory.
4. Boot QEMU explicitly with TCG, bounded CPU/RAM, user-mode NAT and localhost-only SSH forwarding.
5. Require guest identity: Ubuntu 24.04, systemd, expected architecture and disposable marker.
6. Transfer the exact clean candidate archive; do not mount the host checkout into the guest.
7. Install guest-only test prerequisites and execute `scripts/test_control_bridge_g2b_vm.sh` inside the guest.
8. Require every Task 8 lifecycle marker exactly once and exit `0`.
9. Persist only sanitized evidence: candidate SHA, image SHA, timestamps, marker names, status/error codes, hashes, owners/modes and cleanup result.
10. Shut down QEMU and delete the guest overlay, seed, ephemeral key and temporary archive.
11. Revalidate NODE-01 to prove no G2-B marker, grant, lock, workspace mutation or service account was created on the host.
12. Update canonical state, checklist and PR evidence before advancing to Task 9.

## Task 8 acceptance

All of the following are mandatory:

- Ubuntu 24.04/systemd guest identity proven;
- exact candidate SHA proven;
- 13 required G2-B lifecycle markers appear once and in order;
- write, replay, request-ID conflict, concurrency refusal, audit, rollback, revoke and post-revoke refusal pass;
- bounded cleanup passes inside the guest;
- guest artifacts are destroyed on the host;
- NODE-01 remains unchanged by G2-B;
- sanitized evidence is committed and published.

If any item fails, Task 8 remains `PARTIAL` or `BLOCKED`; Task 9 does not start.

## Rollback / containment

Before Task 8 acceptance there is no NODE-01 G2-B bootstrap. A failed VM test is contained by terminating QEMU and deleting only the named temporary directory. Host package removal is optional and must be a separate explicit decision; it is not part of automated cleanup.

## Canonical next action

`HUMAN_AUTHORIZE_QEMU_TCG_HOST_PACKAGES_THEN_EXECUTE_G2B_TASK8_DISPOSABLE_VM`

## Gate executado em 2026-08-22

LEANDRO autorizou a instalação dos três pacotes host. O runtime remoto usado pelo MESTRE bloqueou comandos privilegiados antes da execução; nenhum pacote foi instalado pela automação.

A próxima ação exige execução direta no terminal da VPS:

```bash
sudo apt-get update && sudo apt-get install -y qemu-system-x86 qemu-utils cloud-image-utils
```

Após isso, o MESTRE deve verificar versões, criar a VM TCG descartável e continuar a Task 8 sem instalar G2-B diretamente no NODE-01.
