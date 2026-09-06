# POST-REBOOT LIVE VERIFICATION — NODE-01 — 2026-09-06

## Scope

This receipt records the authorized update + reboot of NODE-01 and the final live verification after boot.
It does not authorize a future update, reboot, network reapply, deployment, or merge.

Human authority: `LEANDRO`.
Authorization consumed: `B_UPDATES_AND_REBOOT`.
Authorization model: one-shot, consumed by this maintenance window.

## Maintenance execution

Pre-maintenance state:
- hostname: `vmi3506102`;
- boot ID: `19d49be9-8d30-4e3d-b3d2-bae23f5fcb75`;
- kernel: `6.8.0-138-generic`;
- target kernel package: `6.8.0-139.139`;
- `reboot-required=YES`;
- system `running`, zero failed units;
- 22 packages upgradable;
- Network P2/F1.2c/SSH/runner and critical services healthy in the immediate precheck.

The package transaction completed with `APT_UPGRADE_RC=0` and zero packages remaining upgradable.
No package removal was introduced by the simulated/selected upgrade path.
## Reboot result

The reboot was initiated only after the post-upgrade technical recheck passed.

Post-boot state:
- boot ID: `0d8df458-4f6f-4db6-84a4-d51b393d6743`;
- kernel: `6.8.0-139-generic`;
- system: `running`;
- failed units: `0`;
- `reboot-required=NO`;
- zero packages upgradable.

F1.2c post-reboot checks passed for network enforcement and network services.

## Network P2 checker correction

The previously installed P2 checker returned `REFUSED reason=recovered_state_invalid` after reboot.
Read-only decomposition showed the runtime gateway host route as:

`169.58.128.1 dev eth0 proto static scope link`

The refusal was traced to presentation-string parsing that did not tolerate `proto static` metadata.
The runtime network itself remained healthy.

PR #51 carries the parser correction. Final candidate:
`9070c24e637e6d571bc53c66d0c54d3825340ffb`.
The candidate passed exact-head local validation, hosted static validation, ShellCheck, and disposable KVM validation before any live use.

## Authorized live check-only

LEANDRO separately authorized materializing the exact candidate in an isolated root-owned directory and executing only `check`.

Materialized path:
`/opt/mcf-p2-checkers/9070c24e637e6d571bc53c66d0c54d3825340ffb`

Guards:
- owner/mode: `root:root:755`;
- exact HEAD: `9070c24e637e6d571bc53c66d0c54d3825340ffb`;
- expected-parent ancestry: PASS;
- worktree: CLEAN;
- checker SHA256: `0051b8a4a1975ca17b4dc41dc65240f17418343a3a5849fa7d39b8cc774a84d9`.

Formal live result:
`NETWORK_CONVERGENCE_CHECK=PASS state=RECOVERED candidate=9070c24e637e6d571bc53c66d0c54d3825340ffb`

`CHECK_RC=0`; wrapper return code `0`.

No installed operational checker was replaced.
No P2 `apply`, `rollback`, `netplan apply/generate`, or networkd restart/reconfigure was executed by this validation.
## Independent postverify

A separate SentinelX read-only collection confirmed:
- host `vmi3506102` on boot ID `0d8df458-4f6f-4db6-84a4-d51b393d6743`;
- kernel `6.8.0-139-generic`;
- system `running`, zero failed units;
- host route `169.58.128.1 proto static scope link`;
- provider subnet route `169.58.128.0/17 via 169.58.128.1`;
- direct `169.58.128.0/17 scope link` in IPv4 main table: ABSENT;
- default route `default via 169.58.128.1 proto static`;
- DSH local endpoint: HTTP `200`;
- 9Router local endpoint: HTTP `307`;
- systemd-networkd, F1.2c enforcement/services, Docker, containerd, SSH, SentinelX, XRDP and LightDM: active;
- isolated checker remains exact-head and clean.

## Operational integration after live verification

LEANDRO authorized alternative A: merge PR #51 first, verify the integrated result, then revalidate PR #50.

PR #51 was merged into `fix/f1-2c-systemd-runtime-lock` with merge commit:
`d5508e1ed417b85bd4863ae5771605079d15aa99`.

The merge tree `b0a51bef522bbb6c872baf5f4ef15116d6f584b0` is byte-identical to the previously qualified candidate tree. A fresh isolated post-merge run on `d5508e1...` passed 166/166 tests, shell syntax 21/21, Ansible syntax 6/6, and remained clean. No workflow was automatically triggered for the merge SHA.

PR #50 remains unmerged and requires a separate LEANDRO human gate.

## Result and boundaries

Maintenance result: `PASS_POST_REBOOT_LIVE_VERIFIED`.
Network P2 result: `COMPLETE_LIVE_VERIFIED` with corrected exact-candidate check PASS.

Current update/reboot authorization: `false`; the one-shot authorization was consumed.
Production promotion, G2-B real write, network reapply, and PR #50 canonical merge remain separately gated. PR #51 operational integration is complete.

Next exact step:
`HUMAN_GATE_PR50_CANONICAL_MERGE`.
