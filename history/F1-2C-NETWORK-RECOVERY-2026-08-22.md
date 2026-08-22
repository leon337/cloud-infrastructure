# F1.2c network-services recovery — 2026-08-22

Status: REQUIRES_REVIEW / ROOT_CAUSE_CONFIRMED / MINIMAL_FIX_IMPLEMENTED / STATIC_GREEN / DISPOSABLE_KVM_PENDING

## Mission boundary

This branch is an isolated child of `fix/f1-2c-systemd-runtime-lock` and does not replace, reset, rebase, force-push, or merge the existing F1.2c branches.

Selected remote base after live GitHub inspection:

- `codex/mission-001-f1-2c-network-enforcement`: base lineage for PR #9;
- `fix/f1-2c-systemd-runtime-lock`: current correction lineage, 45 commits ahead of the codex branch and 0 behind at inspection time;
- `mcf/f1-2c-exact-head-ci-20260819`: divergent older validation lineage, not selected as recovery base;
- selected base SHA: `48be17ccec2dcac5d4f11999466060f9da9d6b8e`.

The 2026-08-22 main reconciliation records local, unpublished F1.2c work (2 modified + 1 untracked at that checkpoint). That local state was not overwritten or treated as remotely available.

No production action, G2-B change, Control Bridge change, branch rewrite, protected-branch merge, or NODE-01 privileged mutation was performed by this recovery mission.

## Root cause on NODE-01

The original NODE-01 failure occurred on the first controlled F1.2c service apply with:

```text
/usr/local/libexec/cloud-platform-network-services: line 30: /run/lock/cloud-platform-network-services.lock: Read-only file system
```

The installed unit has `ProtectSystem=strict`, while the installed helper attempts to create its lock directly below `/run/lock`. The effective installed unit does not define a writable runtime directory for that helper. The systemd filesystem sandbox therefore rejects lock creation before the network-services lifecycle can complete.

This is a systemd runtime-lock/sandbox defect. It is not evidence that project isolation or egress policy itself failed.

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

## Existing correction lineage and secondary defects

PR #9 already moved the network-services helper's own lock to `/run/cloud-platform-network-services/lock` and added:

- `RuntimeDirectory=cloud-platform-network-services`;
- `RuntimeDirectoryMode=0700`;
- `ProtectSystem=strict` retained.

Later disposable-lab work correctly discovered that the network-services service invokes the base-enforcement `check`, whose lock remains `/run/lock/cloud-platform-network-enforcement.lock`. The remote base then granted `ReadWritePaths=/run/lock` to the network-services unit.

Fresh static validation on the selected remote base exposed two additional F1.2c defects:

1. granting the entire `/run/lock` directory contradicted the original private-runtime security contract and was broader than necessary;
2. `automation/mission-001/operations/apply` still pinned the pre-change service-unit hash, so the immutable apply would reject the modified unit as source drift.

These are directly related to F1.2c and were corrected in this isolated recovery branch.

## Minimal correction implemented

The operational correction is deliberately narrow:

- keep the network-services helper's own lock in its private systemd runtime directory;
- keep `ProtectSystem=strict`;
- replace broad `ReadWritePaths=/run/lock` with exactly:

```text
ReadWritePaths=/run/lock/cloud-platform-network-enforcement.lock
```

- synchronize the immutable source digest in `automation/mission-001/operations/apply` to the corrected service unit SHA-256:

```text
c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b
```

No network policy, firewall rule, Docker Compose service, project scope, DNS rule, proxy allowlist, forwarding policy, or rollback boundary was loosened by this recovery change.

The candidate network policy remains fail-closed: project scope networks are internal, inter-container communication is disabled, host binding is loopback, protected/private/link-local/CGNAT destinations are denied on the egress path, IPv6 egress remains denied, and outbound access is limited to the explicit DNS/proxy policy paths.

## Test evidence

### TDD RED

At branch SHA `cc5ae26beafed3681d3ed9f9b52518918e27bf04`:

- run `32604919528`;
- job `97108488964`;
- boundary check passed;
- Compose V2 and post-restart diagnostic regressions passed;
- the exact-lock sandbox regression failed because the unit still contained `ReadWritePaths=/run/lock`;
- workspace remained clean.

This established the expected failing security contract before implementation.

### Static GREEN precursor

At branch SHA `3be5c5b77325c0b2fae816411a1e243993449479`:

- run `32605036375`;
- job `97108763076`;
- result `SUCCESS`;
- 3 focused F1.2c regressions: PASS;
- local Markdown links: PASS;
- YAML parse: PASS, 40 files;
- manifest validation: PASS, 2 manifests;
- state cross-check: PASS;
- project-status check: PASS;
- unit tests: `138/138 PASS`;
- shell syntax: PASS, 16 scripts;
- ShellCheck: PASS, 16 scripts;
- workspace remained clean.

The first canonical `scripts/test.sh` attempt was also recorded and failed at the pre-existing repository-history secret scanner (`credential-in-uri` historical blobs). Repository hygiene is explicitly outside this mission's scope; the recovery branch did not modify or suppress that historical data. The F1.2c static workflow therefore excludes only that pre-existing history-only gate while preserving the relevant validators, full unit-test discovery, syntax checks, and ShellCheck.

A later workflow correction explicitly binds `actions/checkout` to `github.event.pull_request.head.sha`, because the default pull-request checkout uses a temporary merge ref. The final exact-head static result is to be attached to PR #20 after this checkpoint commit; this document does not self-claim a run that had not yet completed when written.

## Rollback and safety

No NODE-01 runtime mutation was made, so no NODE-01 rollback was required during this investigation.

For the code delta, rollback is bounded to reverting the exact service-unit path exception and its corresponding immutable digest/test expectations on this isolated branch. Existing F1.2c rollback logic remains unchanged and continues to refuse unsafe cleanup when managed interfaces/runtime state make rollback ambiguous.

Do not use NODE-01 as the privileged integration laboratory. The self-hosted runner is restricted here to short, unprivileged static/read-only work and refuses passwordless sudo or writable Docker socket access.

## Remaining acceptance gate

A fresh full disposable KVM run on the operator workstation remains mandatory on the final branch SHA. It must exercise the exact systemd unit and full privileged lifecycle, including:

- initial apply;
- service active/check state;
- project isolation;
- DNS behavior;
- proxy-mediated permitted egress;
- direct-egress denial;
- protected-destination denial;
- Docker restart and systemd reconciliation;
- idempotence;
- bounded rollback and cleanup.

Until that KVM evidence is PASS:

- do not restart or reapply F1.2c on NODE-01;
- do not alter firewall/network state on NODE-01;
- do not merge PR #9 or PR #20 as an accepted fix;
- do not claim the NODE-01 unit is repaired in runtime;
- state remains `REQUIRES_REVIEW`.

The next privileged action, if authorized, belongs only in the disposable local KVM boundary, not on NODE-01.
