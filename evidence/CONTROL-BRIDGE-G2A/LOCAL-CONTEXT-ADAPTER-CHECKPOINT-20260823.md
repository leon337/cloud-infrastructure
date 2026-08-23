# G2-A local Context adapter — preservation checkpoint — 2026-08-23

Status: `IMPLEMENTED_LOCALLY_DISABLED_BY_DEFAULT_UNIT_PASS_E2E_PENDING`.

This checkpoint preserves the bounded implementation before the approved disposable end-to-end proof. It is not an activation record.

## Implemented boundary

- transport: one JSON document on stdin and one compact JSON result on stdout
- protocol: `MCF_CLOUD_CONTEXT_READ_V1`
- single operation: `context.get`
- single identity mapping: `cloud-infrastructure` to `leon337/g2a-smoke/dev`
- activation: absent by default; the exact lab-only opt-in is `MCF_CLOUD_CONTEXT_READ_ENABLE=DISPOSABLE_LOCAL_LAB_ONLY`
- configuration and source paths: fixed in `platform/control-bridge/mcf-cloud-context-read-config.yaml`
- input: exact-key parser, duplicate-key refusal, UTF-8 only, 4096-byte maximum, no caller-supplied path
- output: strict Draft 2020-12 schema, 65536-byte maximum, provenance SHA-256 per source and explicit freshness
- filesystem: fixed repository layout, confined regular files, no symlinks, maximum 262144 bytes per source
- mutation surface: no filesystem writes, network module, external process, shell, SSH, or HTTP

## Validation completed

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_mcf_cloud_context_read_adapter -v
```

Result: `9 / 9 PASS`.

Full repository unit discovery after the adapter checkpoint: `390 / 390 PASS`.

The tests cover default refusal before source reads, exact request projection, strict schemas, bounded/duplicate-key input, wrong project/layout, symlink escape, tampered contract, one-line CLI behavior, and absence of network/subprocess/shell/write surfaces.

## Explicitly pending

- disposable MCF-client to adapter to Cloud-state E2E: `NOT_EXECUTED`
- repository fingerprint before/after that E2E: `NOT_EXECUTED`
- E2E evidence marker set: `NOT_CREATED`
- adapter activation: `NOT_AUTHORIZED`
- HTTP/token transport: `NOT_IMPLEMENTED` and unnecessary for the current stdio boundary
- VPS, SSH, external network, deployment, push acceptance, PR, and merge: not proven by this checkpoint

The next exact step is to build and run the disposable local-copy E2E, require strict client-side schema validation, and compare repository fingerprints before and after. Until that passes, the Capsule and mapping must keep the adapter disabled and E2E-pending.
