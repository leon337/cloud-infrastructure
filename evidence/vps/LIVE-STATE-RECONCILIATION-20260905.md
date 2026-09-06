# LIVE STATE RECONCILIATION — NODE-01 — 2026-09-05

Status: `READ_ONLY_RECONCILIATION_VERIFIED`.

## Scope

This receipt reconciles the canonical `IMPLEMENTAÇÃO DA VPS` projection with current
GitHub evidence and a bounded read-only observation of NODE-01 (`vmi3506102`). It does
not authorize or execute deploy, restart, package update, firewall change, G2-B real
write, F1.2c/Network P2 reapply, production promotion or reboot.

Base canonical `main`: `34248311116e2282950fe560639873c8e5d2f81c`.

## GitHub lineage findings

- PR #21 is open, Draft and unmerged. Head `f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8`
  records G2-B Task 8 technical PASS: 373/373 unit tests, 9/9 Ansible syntax, 13/13
  required lifecycle markers, bounded cleanup and no G2-B NODE-01 write. Classification:
  `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.
- PR #23 is still an old Draft/unmerged disposable-KVM gate. It is retained as historical
  evidence and is superseded operationally by later validated F1.2c lineage.
- PR #35 is merged and contains the fail-closed partial-state recovery lineage that enabled
  later live F1.2c recovery.
- PR #41 is open against an older main snapshot. Its F1.2c, Network P2 and pre-reboot
  evidence is useful, but the PR itself is not a current merge candidate because later main
  changes include the completed runner-isolation closeout.

## NODE-01 fresh read-only observations

Observed through the existing administrative SSH/Tailscale path; no command mutated host state.

### F1.2c

- `cloud-platform-network-services.service`: `active` + `enabled`.
- `systemctl --failed`: zero failed units at observation time.
- installed helper SHA-256:
  `b69f41cd1c66000da239f39c09a46681afd5098a311065adf76b3c7aae35b9a3`.
- installed unit SHA-256:
  `c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b`.
- unit preserves `ProtectSystem=strict` and uses
  `RuntimeDirectory=cloud-platform-network-services`, `RuntimeDirectoryMode=0700`.

Conclusion: `COMPLETE_LIVE_VERIFIED`. The old
`F1_2C_NODE01_ROLLOUT_HUMAN_GATE` is no longer a current operational step.

### Network Convergence P2

- `eth0`: `routable (configured)`.
- online state: `online`.
- address: `169.58.171.192`.
- gateway: `169.58.128.1`.
- route: `169.58.128.1 dev eth0 proto static scope link`.
- `systemd-networkd-wait-online.service`: active in the fresh reboot-precondition read.

Conclusion: `COMPLETE_LIVE_VERIFIED`.

### Docker workload presence

Without invoking privileged Docker operations, process cgroups proved four current Docker
workload processes in `cloud-platform.slice`:

- 2 CoreDNS;
- 2 Squid.

This proves container presence, not a complete semantic Docker inventory.

### Kernel / reboot freshness

- running kernel: `6.8.0-138-generic`.
- `/var/run/reboot-required`: present.
- packages requiring reboot: `linux-image-6.8.0-139-generic`, `linux-base`.
- latest on-host config backup observed:
  `/var/backups/cloud-infrastructure/cloud-infrastructure-config-20260905T030614Z.tar.gz`.

The accepted checkpoint V2 from 2026-08-29 was created while running kernel
`6.8.0-137-generic`. It remains valid historical evidence but is not accepted as the
checkpoint for the current reboot candidate. Classification:
`HISTORICAL_VERIFIED_REFRESH_REQUIRED`.

### Runner

The GitHub Actions runner service was active in the fresh reboot-precondition read. The
canonical runner-isolation proof remains run `33998487949`, with global STARTED/COMPLETED
hooks and cross-job isolation PASS. No runner mutation belongs to this reconciliation.

### SentinelX direct connectivity

`sentinelx-cloud-core` was observed active + enabled. Recent journal entries showed direct
hub connections interleaved with WebSocket close `1006`, hub restart `1012`, HTTP `502`
and subsequent reconnects. The direct-hub criterion was therefore not stable during this
reconciliation.

Classification: `INTERMITTENT_NOT_CLOSED`.
Current root cause: `NOT_VERIFIED`.

No restart, package update or configuration change was attempted.

## External-service boundary

DeepSeek Harness and 9router are owned by another team and remain
`EXTERNALLY_MANAGED_OBSERVE_ONLY`.

This reconciliation did not:

- edit their files or configuration;
- invoke them as execution routes;
- restart/stop their processes;
- alter supervisor/cron/package state;
- actively probe them for functional acceptance.

A VPS reboot would inherently interrupt both services. Therefore the next maintenance gate
must include external-owner coordination before any reboot authorization is consumed.

## Canonical classifications produced

```text
F1_2C_NODE01_ROLLOUT            COMPLETE_LIVE_VERIFIED
NETWORK_CONVERGENCE_P2          COMPLETE_LIVE_VERIFIED
RUNNER_ISOLATION                ACTIVE_VERIFIED / NEXT=NONE
G2B_TASK8                       TECHNICAL_PASS_DRAFT_UNINTEGRATED
SENTINELX_DIRECT                INTERMITTENT_NOT_CLOSED
PRE_REBOOT_CHECKPOINT           HISTORICAL_VERIFIED_REFRESH_REQUIRED
NEXT_EXACT_STEP                 PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE
UPDATE_AND_REBOOT               NOT_AUTHORIZED_HUMAN_GATE_REQUIRED
```

## Evidence inheritance

Detailed historical live receipts are preserved unchanged in:

- `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`;
- `evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`;
- `evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md`.

This receipt changes the current projection only where newer verifiable evidence supersedes
the older checklist/state. Unverified causes remain explicitly `NOT_VERIFIED`.
