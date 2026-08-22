# F1.2c network-services recovery — 2026-08-22

Status: REQUIRES_REVIEW / ROOT_CAUSE_CONFIRMED / NODE_01_READ_ONLY_COMPLETE / DISPOSABLE_INTEGRATION_PENDING

## Mission boundary

This branch is an isolated child of `fix/f1-2c-systemd-runtime-lock` and does not replace, reset, rebase, force-push, or merge the existing F1.2c branches.

Selected remote base after live GitHub inspection:

- `codex/mission-001-f1-2c-network-enforcement`: base lineage for PR #9;
- `fix/f1-2c-systemd-runtime-lock`: current correction lineage, 45 commits ahead of the codex branch and 0 behind at inspection time;
- `mcf/f1-2c-exact-head-ci-20260819`: divergent older validation lineage, not selected as recovery base;
- selected SHA: `48be17ccec2dcac5d4f11999466060f9da9d6b8e`.

The 2026-08-22 main reconciliation records local, unpublished F1.2c work (2 modified + 1 untracked at that checkpoint). That local state was not overwritten or treated as remotely available.

## Root cause

The original NODE-01 failure occurred on the first controlled F1.2c service apply with:

```text
/usr/local/libexec/cloud-platform-network-services: line 30: /run/lock/cloud-platform-network-services.lock: Read-only file system
```

The installed unit has `ProtectSystem=strict`, while the installed helper attempts to create its lock directly below `/run/lock`. The effective installed unit does not define a writable runtime directory for that helper. The systemd sandbox therefore rejects the lock creation before the network-services lifecycle can complete.

This is a systemd filesystem-sandbox/runtime-lock defect. It is not evidence that project isolation or egress policy itself failed.

## Fresh NODE-01 read-only evidence

One bounded, unprivileged diagnostic was executed through GitHub Actions and then its temporary workflow was retired so later commits do not repeat the probe.

- workflow run: `32604494038`
- job: `97107494671`
- result: `SUCCESS`
- captured at: `2026-08-22T23:10:37Z`
- runner: `node--1-mcf-control` on `vmi3506102`
- mutation performed by diagnostic: none

Observed service state:

- `cloud-platform-network-services.service`: `failed`, `Result=exit-code`, `ExecMainStatus=1`;
- failure timestamp remains `2026-08-19 14:26:10 -03`;
- journal still contains the exact `/run/lock/cloud-platform-network-services.lock: Read-only file system` error and no later start attempt;
- effective network-services unit still lacks `RuntimeDirectory=` and has no `ReadWritePaths=` exception;
- `/run/cloud-platform-network-services` does not exist;
- legacy `/run/lock/cloud-platform-network-services.lock` exists as an empty root-owned file;
- `cloud-platform-network-enforcement.service`: `active (exited)`, `Result=success`, `ExecMainStatus=0`;
- `net.ipv4.ip_forward=0`;
- `net.ipv6.conf.all.forwarding=0`;
- only `lo` and `eth0` were visible; no managed `cp*` or `cpeg*` interfaces were observed;
- unprivileged Docker API access was denied as intended.

Installed SHA-256 inventory captured read-only:

```text
06d0f016809a2e8d9cf0be5a258766563cc686fe40b21ec3578a99c731421060  /usr/local/libexec/cloud-platform-network-services
dfe10b0e0046242695fe5ba03215f49aa938cf94b733bba3b1a2ba9cfad7e6d1  /etc/systemd/system/cloud-platform-network-services.service
11468ad2031e65d9824c77ed15222ed520251aff07d32d6b85a6484af21d24b4  /usr/local/libexec/cloud-platform-network-enforcement
32a200e1512c64af055278ba37d760c73979cf1fd4fff438d10148f33e67fb62  /etc/systemd/system/cloud-platform-network-enforcement.service
```

## Existing minimal correction carried by the selected base

PR #9 already contains the root-cause correction and is therefore preserved rather than reimplemented destructively:

- network-services helper lock moved to `/run/cloud-platform-network-services/lock`;
- `RuntimeDirectory=cloud-platform-network-services`;
- `RuntimeDirectoryMode=0700`;
- `ProtectSystem=strict` retained;
- later integration finding: the service invokes the base-enforcement `check`, whose lock remains in `/run/lock`, so the current candidate also grants `ReadWritePaths=/run/lock` to the network-services unit;
- KVM guest provisioning now requires Compose V2;
- exact-systemd disposable harness includes failure and post-Docker-restart diagnostics.

The network policy itself remains fail-closed in the candidate: project scope networks are internal, inter-container communication is disabled, host binding is loopback, private/link-local/CGNAT destinations are dropped on the egress bridge, IPv6 egress is dropped, and only the explicit DNS/proxy egress paths are allowlisted.

## Validation state

Historical static evidence on predecessor candidates is green, but executable content changed afterward, so it is not inherited as final acceptance evidence.

At current remote base `48be17ccec2dcac5d4f11999466060f9da9d6b8e`, GitHub-hosted `foundation-ci` and `docker-boundary-ci` runs terminate in the `validate` job before downstream disposable jobs run. The old job logs are unavailable and the current GitHub-hosted jobs also expose no executed steps, so the cause is recorded as **NOT VERIFIED** rather than guessed.

This recovery branch adds a bounded self-hosted **unprivileged static-only** validation workflow. It refuses passwordless sudo and writable Docker socket access, runs the focused F1.2c regressions, then `scripts/test.sh` with Ansible explicitly non-required. Full privileged network lifecycle is intentionally not run on NODE-01.

## Remaining acceptance gate

A fresh full disposable KVM run on the operator workstation remains mandatory on the final executable SHA. It must exercise the exact systemd unit, initial apply, isolation/DNS/proxy/direct-egress policy, Docker restart/reconciliation, idempotence, and bounded rollback.

Until that evidence is PASS:

- do not restart or reapply F1.2c on NODE-01;
- do not alter firewall/network state on NODE-01;
- do not merge PR #9 or this recovery PR as an accepted fix;
- state remains `REQUIRES_REVIEW`.

No production action, G2-B change, Control Bridge change, branch rewrite, or NODE-01 privileged mutation was performed by this recovery mission.
