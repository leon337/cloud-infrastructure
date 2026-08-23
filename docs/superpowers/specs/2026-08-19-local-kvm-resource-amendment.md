# Local KVM Disposable Lab — Resource Amendment

Status: APPROVED

Date: 2026-08-19

Approver: LEANDRO

## Scope

This amendment supersedes only the RAM defaults in `docs/superpowers/specs/2026-08-19-local-kvm-disposable-lab-design.md` and the corresponding Task 4 resource values in `docs/superpowers/plans/2026-08-19-local-kvm-disposable-lab.md` for the F1.2c local disposable KVM laboratory.

The original profile required a 4 GiB guest and at least 5 GiB of host `MemAvailable`. The operator workstation was measured before VM creation and reported approximately 7.7 GiB total RAM and 4.3 GiB available, causing the launcher to refuse safely with `KVM_LAB_REFUSED reason=insufficient_host_memory`.

## Approved resource profile

- guest RAM: **3072 MiB**;
- minimum host `MemAvailable`: **4 GiB**;
- vCPU: **2**, unchanged;
- qcow2 virtual size: **24 GiB**, unchanged;
- QEMU remains headless;
- SSH remains localhost-only on a dynamically selected high port.

## Safety invariants

This amendment does not relax any isolation or privilege boundary. In particular, it does not authorize host `sudo`, TAP, bridge networking, host iptables changes, host Docker socket access, NODE-01 execution, production access, reusable credentials, or arbitrary guest commands.

The launcher remains fail-closed below the 4 GiB host-memory floor. The guest remains disposable and the full exact-systemd privileged lifecycle remains required before PR #9 can satisfy its disposable-integration gate.

## TDD evidence requirement

The resource change must be implemented test-first. A regression test must fail against the old `-m 4096` / 5 GiB host-floor implementation, then pass only when the launcher uses `-m 3072` and a 4 GiB `MemAvailable` floor. Fresh complete static verification is required on the unprivileged NODE-01 runner, followed by a fresh full KVM disposable integration run on the operator workstation.

No NODE-01 reapply or canonical merge is authorized by this amendment alone.
