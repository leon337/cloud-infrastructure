# PRE_REBOOT_CHECKPOINT — NODE-01 — 2026-08-29

Status: `VERIFIED_PRE_REBOOT_CHECKPOINT_V2`.

## Scope

This evidence records the bounded pre-reboot checkpoint for NODE-01 (`vmi3506102`). It does not authorize or execute reboot, package updates, `systemd-networkd` restart/reconfigure, `netplan apply`, SSH changes, production promotion, or other privileged writes.

## Pre-check baseline

Before checkpoint creation: kernel `6.8.0-137-generic`; `/var/run/reboot-required` present; SSH/UFW/Fail2ban/Docker/containerd/systemd-networkd/F1.2c services/runner/SentinelX/XRDP/LightDM/backup timer active; `eth0 AdministrativeState=configured`, routable and online; `169.58.128.1/32 scope link` present; connected `169.58.128.0/17` route absent as designed; both real `systemd-networkd-wait-online` predicates returned success.

The boot-current failed-unit baseline contains only `systemd-networkd-wait-online.service`, a historical failed state from before the runtime convergence repair. The current wait-online predicates pass; the unit was not reset or restarted during this checkpoint.

## V1 rejected

The first archive `pre-reboot-checkpoint-20260829T202714Z.tar.gz` had a valid outer SHA-256 and safe archive paths, but its internal `SHA256SUMS` incorrectly included `SHA256SUMS` itself while being generated. All other member hashes passed, but the self-hash failed. V1 is preserved as rejected evidence and is not accepted for reboot readiness.

## V2 accepted

Accepted archive: `pre-reboot-checkpoint-20260829T203736Z.tar.gz`.

- archive SHA-256: `8fe354e44c5d7948a9e87f0ab57cb9dd261fd438791f10964001158d800e0b42`;
- root metadata on NODE-01: `root:adm 0640`;
- outer SHA verification: PASS;
- archive path/link safety: PASS;
- all internal `SHA256SUMS` entries: PASS;
- P2 recovery check: PASS / `RECOVERED`;
- F1.2c helper check: PASS;
- base enforcement check: PASS;
- `eth0 AdministrativeState=configured`;
- both wait-online predicates: PASS;
- gateway host-route `/32`: present;
- default route: preserved;
- connected `/17`: absent-preserved;
- Docker snapshot: 4 containers, 4 running, 2 images, 0 volumes, 4 custom networks.

Associated canonical backup: `cloud-infrastructure-config-20260829T203734Z.tar.gz`, SHA-256 `ce85092790cfbfe7b3aec675f12b3ef28e890c2e5ccb492c345a408118271c20`.

## Off-host verification

RECOVERY-P2 pulled the associated canonical backup to `/home/leo/Backups/cloud-infrastructure/recovery/20260829T203850Z` with `RESTORE_SMOKE=PASS`, `RECOVERY_P2=PASS`, secret scan PASS, archive path/link safety PASS and the same root-backup SHA-256.

The V2 checkpoint archive and sidecar were copied to `/home/leo/Backups/cloud-infrastructure/pre-reboot/20260829T203736Z`; local SHA-256 matched the root sidecar and all internal member hashes passed after extraction in a disposable tmpfs directory.

## Boundary after checkpoint

`PRE_REBOOT_CHECKPOINT` is complete. Reboot and updates remain not authorized. The next operational gate is `UPDATE_AND_CONTROLLED_REBOOT`; any material reboot/update action requires a separate explicit human authorization and post-reboot validation must follow.
