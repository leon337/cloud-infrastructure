# F1.2c NODE-01 partial recovery preparation — 2026-08-28

Status: **ROOT_CAUSE_RECONFIRMED / PARTIAL_STATE_CLASSIFIED / RECOVERY_IMPLEMENTED_FOR_KVM_VALIDATION / NODE01_WRITE_NOT_AUTHORIZED**

## Authority and boundary

This work is a child of `fix/f1-2c-systemd-runtime-lock` at validated parent
`80a1579bf6525029be8085fa1d1cbdec602ddfbd`. It does not modify the current NODE-01
runtime during preparation and does not weaken SSH, UFW, Docker, systemd sandboxing,
network isolation, DNS/proxy policy, production boundaries or sudo policy.

The interactive notebook→VPS SSH path confirmed by LEANDRO is a required dependency and
must remain available throughout any later rollout.

## Fresh read-only NODE-01 classification

The 2026-08-28 read-only collection reconfirmed the historical systemd sandbox failure:

```text
/run/lock/cloud-platform-network-services.lock: Read-only file system
```

The installed `cloud-platform-network-services.service` still has
`ProtectSystem=strict` without the corrected private runtime directory. The service is
failed while the base network-enforcement unit and the required human services remain
active.

The installed SHA-256 inventory still matches the known historical partial lineage:

```text
06d0f016809a2e8d9cf0be5a258766563cc686fe40b21ec3578a99c731421060  network-services helper
dfe10b0e0046242695fe5ba03215f49aa938cf94b733bba3b1a2ba9cfad7e6d1  network-services unit
11468ad2031e65d9824c77ed15222ed520251aff07d32d6b85a6484af21d24b4  enforcement helper
32a200e1512c64af055278ba37d760c73979cf1fd4fff438d10148f33e67fb62  enforcement unit
a83bff96d635e0d13227d50e2f34512824e0389d6dd925ba681d334256bb0cc0  Docker enforcement drop-in
a2a00688b6f566d94ad43cebd13da2f4abcec76815b9fce11dab36b137be0c39  forwarding sysctl file
```

A stronger finding was also established: the service marker exists, but the entire
`/etc/cloud-platform/network-services` configuration tree is absent. No managed
`cp*`/`cpeg*` link was observed and runtime IPv4/IPv6 forwarding remained `0/0`.

This is a **partial first-apply state**, not merely one stale unit file.

## Why normal apply/rollback are not used

The normal candidate `apply` treats an existing service marker as managed state and
requires all installed service files to match the candidate digests. The current partial
state therefore fails closed on drift/missing configuration.

The normal candidate `rollback` requires the service helper `check` to pass before
removing the layer. The current partial state cannot satisfy that precondition.

Running either path blindly is therefore rejected by design and is not a recovery plan.

## Dedicated recovery

`automation/mission-001/operations/recover-network-services-partial` is deliberately
separate from the already KVM-validated normal lifecycle. It recognizes only the exact
partial-state signature above, verifies source hashes, creates a root-owned checkpoint,
runs the existing configuration backup, installs the corrected surface and verifies the
full helper/service state.

A rollback is allowed only from a completely healthy recovered state. Unclassified
mid-apply failures preserve the checkpoint and emit `RECOVERY_HUMAN_GATE_REQUIRED`
instead of attempting broad cleanup.

## Execution transport observation

The historical `/usr/local/sbin/codex-mission-001-runner` is still bound to branch
`codex/mission-001-f1-2c-network-enforcement` and its root-owned checkout remains on an
older source state. Its former temporary NOPASSWD authorization is not active; `sudo -n`
requires authentication.

The recovery preparation does not bypass or reactivate that authorization. A later live
rollout must use an explicitly reviewed, root-owned exact candidate source and a current
LEANDRO authorization.

## Acceptance still required before live mutation

Before any NODE-01 write:

- focused recovery contracts must pass;
- full repository tests must remain green;
- disposable Ubuntu 24.04 KVM must reproduce the historical partial failure and prove
  recovery `precheck → apply → check → idempotence → rollback → cleanup`;
- the exact candidate SHA and KVM evidence must be presented at the HUMAN_GATE;
- a privileged live precheck must still match the known partial signature.

Until that gate is approved, NODE-01 write state is **NOT_AUTHORIZED**.
