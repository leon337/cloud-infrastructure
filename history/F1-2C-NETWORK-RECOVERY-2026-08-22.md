# F1.2c network-services recovery — 2026-08-22

Status: IN_PROGRESS / READ_ONLY_DIAGNOSTIC_PENDING

## Mission boundary

This branch is an isolated child of `fix/f1-2c-systemd-runtime-lock` and does not replace, reset, rebase, or merge the existing F1.2c branches.

Selected remote base after live GitHub inspection:

- `codex/mission-001-f1-2c-network-enforcement`: base lineage for PR #9;
- `fix/f1-2c-systemd-runtime-lock`: current correction lineage, 45 commits ahead of the codex branch and 0 behind at inspection time;
- `mcf/f1-2c-exact-head-ci-20260819`: divergent older validation lineage, not selected as recovery base;
- selected SHA: `48be17ccec2dcac5d4f11999466060f9da9d6b8e`.

The 2026-08-22 main reconciliation also records local, unpublished F1.2c work. That local state is not overwritten or treated as remotely available.

## Preserved incident facts

The original NODE-01 failure occurred on the first controlled F1.2c service apply with:

```text
/usr/local/libexec/cloud-platform-network-services: line 30: /run/lock/cloud-platform-network-services.lock: Read-only file system
```

The unit had `ProtectSystem=strict`. No second apply was attempted. The allowlisted rollback refused fail-closed because the service state was already partial. Host access/core services stayed active, no managed cp/cpeg links were observed, and IPv4/IPv6 forwarding remained disabled at that preserved checkpoint.

PR #9 moved the network-services helper lock to `/run/cloud-platform-network-services/lock` and added a systemd-managed private runtime directory while retaining `ProtectSystem=strict`. Later disposable-lab work found additional integration gaps; the current remote HEAD includes post-Docker-restart diagnostic instrumentation and is not accepted as fully validated.

## Current read-only gate

Before any restart/reapply, collect from NODE-01 without sudo or mutation:

- effective service status/show/cat and journal;
- installed helper/unit hashes;
- runtime lock paths and metadata;
- base enforcement service state;
- forwarding, links, routes and listeners;
- unprivileged Docker visibility only;
- systemd security summary.

No restart, reapply, reinstall, firewall change, network change, production action, merge, or G2-B/Control Bridge change is authorized by this checkpoint.
