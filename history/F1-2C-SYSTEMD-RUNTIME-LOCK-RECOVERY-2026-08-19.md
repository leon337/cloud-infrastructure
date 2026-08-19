# F1.2c systemd runtime-lock recovery — 2026-08-19

Status: IN_PROGRESS — FIX_STATIC_GREEN / DISPOSABLE_INTEGRATION_PENDING / NODE_01_PARTIAL_STATE_PRESERVED

## Observed NODE-01 failure

Canonical candidate `c9f909945b544d22dbabc619252456f7190f7ae9` passed its pre-apply gates, then the first real network-services apply stopped at the exact systemd service boundary:

`/usr/local/libexec/cloud-platform-network-services: line 30: /run/lock/cloud-platform-network-services.lock: Read-only file system`

The unit retained `ProtectSystem=strict`; the helper attempted to create its lock directly under `/run/lock`. The systemd unit therefore failed before the service helper could complete its network-services lifecycle.

The exact allowlisted rollback was attempted once and refused fail-closed with `NETWORK_SERVICES_REFUSED reason=check_failed` / `MISSION_ROLLBACK_REFUSED reason=service_drift`. No ad-hoc cleanup was performed.

Essential access and host services remained active: SSH, UFW, fail2ban, XRDP, Docker, containerd, and `cloud-platform-network-enforcement.service`. The failed state remains limited to `cloud-platform-network-services.service` and its partial installed service surface.

## Root-cause fix branch

Draft PR #9, branch `fix/f1-2c-systemd-runtime-lock`.

Current fix commit: `5cb4ea6868562083cca1cfaee47c8c1e7c127cd5`.

The minimal fix keeps `ProtectSystem=strict`, moves the lock to `/run/cloud-platform-network-services/lock`, and adds the systemd-managed private runtime directory:

- `RuntimeDirectory=cloud-platform-network-services`
- `RuntimeDirectoryMode=0700`

The immutable source SHA inventory used by the Mission-001 apply operation is updated accordingly.

## TDD and regression evidence

The runtime-directory contract was first added as a failing regression test and RED was confirmed on the unprivileged self-hosted runner. After the minimal fix, the focused test and complete static suite passed.

A second gap was then identified: the previous disposable NODE-01 network-services harness invoked the service helper directly and did not start the exact `cloud-platform-network-services.service` unit. Therefore the previous disposable evidence could not detect this class of systemd sandbox failure.

A second regression test was added and RED was confirmed. The disposable harness was then extended so the future disposable run must install and exercise the exact systemd unit, verify its journal and active state, verify idempotence, restart Docker and observe systemd reconciliation, and perform bounded cleanup.

Fresh unprivileged verification on exact commit `5cb4ea6868562083cca1cfaee47c8c1e7c127cd5`:

- focused exact-systemd harness regression: PASS;
- complete static suite: PASS;
- unit tests: 125 PASS;
- shell syntax: 15 PASS;
- generic passwordless sudo: unavailable as intended;
- Docker socket read/write: unavailable as intended.

## Free disposable-environment investigation

A read-only capability probe was executed on NODE-01 through the unprivileged MCF runner.

Unavailable on NODE-01: `systemd-nspawn`, `machinectl`, `debootstrap`, `mmdebstrap`, QEMU/KVM user tooling, Firecracker, Podman, Incus/LXC, RootlessKit, slirp4netns, `newuidmap`, `newgidmap`, and `dockerd-rootless.sh`.

`unshare` and bubblewrap are present, but an unprivileged user+mount+pid namespace creation attempt failed with `write failed /proc/self/uid_map: Operation not permitted`. Therefore NODE-01 does not currently provide a safe unprivileged disposable VM/container boundary adequate for the full privileged Docker/systemd/iptables integration harness.

## Gate

Because PR #9 changes executable/operational content and because the approved evidence-inheritance policy is fail-closed for such changes, the old disposable integration evidence is not inherited. PR #9 must remain draft/unmerged and must not be applied to NODE-01 until a fresh full disposable integration run exercises the updated exact-systemd harness.
