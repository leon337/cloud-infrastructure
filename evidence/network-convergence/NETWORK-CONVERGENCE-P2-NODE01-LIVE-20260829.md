# NETWORK_CONVERGENCE_P2 — NODE-01 live closeout — 2026-08-29

Status: `VERIFIED_LIVE_NETWORK_CONVERGENCE_P2`.

## Scope

This evidence records the bounded recovery of `systemd-networkd` convergence on NODE-01 (`vmi3506102`). It does not authorize reboot, production promotion, G2-B writes, SSH changes, package updates, or future privileged reapply.

## Proven functional cause

The live host remained `online/routable` while `eth0` stayed `AdministrativeState=configuring` and both real `systemd-networkd-wait-online` predicates timed out. A disposable Ubuntu 24.04 KVM reproduced the same signature by removing only the connected IPv4 route `169.58.128.0/17` while preserving the configured addresses and default routes.

Restoring reachability to the IPv4 gateway with only `169.58.128.1/32 scope link` changed the guest to `AdministrativeState=configured` and both wait-online predicates passed. The exact agent that removed the connected `/17` on NODE-01 remains `NOT_VERIFIED`.

`/etc/cron.d/staticroute` originated from initial NoCloud/cloud-init user-data and was preserved. Its command alone did not reproduce the defect in KVM, so it is not classified as the unique root cause.

## Validated correction

The recovery adds only a Netplan overlay for `169.58.128.1/32` with `scope: link`, runs `netplan generate`, and materializes only that gateway host-route at runtime. It does not restore the whole `/17` connected route and does not execute `netplan apply`, `networkctl reconfigure`, `systemd-networkd` restart, or reboot.

## Candidate and validation chain

- Initial P2 implementation PR: `#42`; validated head `5955fcf467bddb3525dae564c2d61878e0fad96a`; lineage merge `63b4409b678f14dca3be55f249e57f750d020f90`.
- First live precheck failed closed with `generated_network_drift`; no P2 apply executed. Root read-only inspection proved the generated `.network` content remained byte-identical (`0f25043db9ffc67594a6d723a69550105fa8fb8d5ae2040905b1aff964042858`) and the mismatch was metadata only: expected incorrectly as `root:root 0644`, live canonical Netplan output `root:systemd-network 0640`.
- Metadata correction PR: `#43`; exact applied candidate `682c3e55d835ebea4bcc2edd297a8b819b2df434`; lineage merge `badad65ae583f159347c2219e1561a9a4a245152`.
- Local validation on the correction: focused contracts `10/10 PASS`, full unit suite `162/162 PASS`, pinned ShellCheck `v0.11.0 PASS`, Markdown/YAML/manifests/state/project-status/Python/shell/diff checks PASS, disposable KVM PASS.
- Hosted exact-head static validation: run `33270932935`, `SUCCESS`.
- Hosted exact-head KVM: run `33270932950`, `SUCCESS`; markers included `generated_metadata_match=PASS`, broken signature reproduction, precheck/apply/check PASS, checkpoint hash match, `AdministrativeState=configured`, wait-online PASS, rollback PASS with `runtime_reconfigure=NOT_FORCED`, baseline re-evaluation to `configuring` + timeout, and `NETWORK_CONVERGENCE_VM_PASS`.
- Generic `foundation-ci` and `docker-boundary-ci` failures were reclassified from logs as `PREEXISTING_HISTORY_ONLY_GATE`, exclusively on historical secret-scanner blobs; no P2 correction file appeared in those findings.

## Live authorized rollout

The exact candidate `682c3e55d835ebea4bcc2edd297a8b819b2df434` was packaged as a signed Git bundle and staged root-owned after signature/hash/head verification. A precheck-only launcher returned:

```text
NETWORK_CONVERGENCE_PRECHECK=PASS state=KNOWN_BROKEN candidate=682c3e55d835ebea4bcc2edd297a8b819b2df434
NETWORK_P2_PRECHECK=PASS candidate=682c3e55d835ebea4bcc2edd297a8b819b2df434
```
After explicit human authorization, the material launcher completed with `rc=0`:

```text
NETWORK_CONVERGENCE_APPLY=PASS changed=1 candidate=682c3e55d835ebea4bcc2edd297a8b819b2df434
NETWORK_CONVERGENCE_CHECK=PASS state=RECOVERED candidate=682c3e55d835ebea4bcc2edd297a8b819b2df434
NETWORK_P2_ROLLOUT_FINAL=PASS candidate=682c3e55d835ebea4bcc2edd297a8b819b2df434 admin_state=configured wait_online=pass gateway_host_route=present provider_files=preserved
```

Independent unprivileged postverify confirmed both services active, `eth0 AdministrativeState=configured`, gateway host-route present, both wait-online predicates returning success, default route preserved, and the connected `/17` still absent.

Independent root postverify returned `NETWORK_P2_ROOT_POSTVERIFY=PASS`, `state=RECOVERED`, and recovery `check` PASS. The pre-write backup `cloud-infrastructure-config-20260829T194958Z.tar.gz` passed its SHA-256 sidecar check; checkpoint `created_at=2026-08-29T19:50:01Z`. The overlay is root-owned `0600` with SHA-256 `e7a55b96a2ba848ffd70867b7ca9415abdfb51b81c19e9de5be96f5471277060`; the original Netplan hash remains `9ad2689b534bdb090060a51b3a1c0785384c65c2bd1bf3e42b9bbfdc76685790`; `staticroute` remains `4a0ab05ddb6ef718acc644f656d865b1129f0ec4996e1bf2725156042a913163`; generated networkd metadata is `root:systemd-network 0640` and contains the `/32` link-scope route.

`systemd-networkd` retained start timestamp `Sat 2026-08-29 06:52:24 -03`, proving this rollout did not restart the service.

## Boundaries after success

The one-shot P2 authorization is consumed. There is no standing authorization for P2 reapply, rollback, reboot, package updates, production, or other privileged writes. The next operational step is `PRE_REBOOT_CHECKPOINT`; reboot remains blocked until that checkpoint exists and a separate human gate authorizes the reboot.
