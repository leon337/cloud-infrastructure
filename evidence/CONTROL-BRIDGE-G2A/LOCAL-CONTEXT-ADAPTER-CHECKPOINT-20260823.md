# G2-A local Context adapter — provider fixture and real MCF AppModule lab evidence

Status: `REAL_MCF_APPMODULE_WITH_DISPOSABLE_CLOUD_PROCESS_HISTORICALLY_VERIFIED_DISABLED_BY_DEFAULT`.

Semantic synchronization observed at `2026-08-24T03:22:59Z`.

This record preserves two distinct evidence layers without promoting either into current operational
freshness:

1. the Cloud-owned disposable fixture proved the one-line provider boundary with `PASS_13_OF_13`;
2. the real MCF `AppModule` later consumed that boundary in a disposable local lab with
   `PASS_3_OF_3`.

After teardown the capability is `DISCONNECTED`, `INACTIVE`, `HISTORICALLY_VERIFIED`, and
`LIVE_REQUIRED`. This is not an activation record and does not make historical NODE-01 evidence
current.

## Exact provider interface consumed by MCF

The MCF client uses this exact process boundary from a disposable Cloud workspace whose final path
is `.../leon337/g2a-smoke/dev`:

```text
python -I platform/control-bridge/mcf-cloud-context-read
```

It must set only the explicit lab opt-in below in addition to a minimal process environment:

```text
MCF_CLOUD_CONTEXT_READ_ENABLE=DISPOSABLE_LOCAL_LAB_ONLY
```

It sends exactly one UTF-8 JSON line on stdin:

```json
{"protocol":"MCF_CLOUD_CONTEXT_READ_V1","request_id":"<1-128 allowlisted characters>","project_id":"cloud-infrastructure","operation":"context.get","arguments":{}}
```

For the preserved lab E2E the concrete line was:

```json
{"protocol":"MCF_CLOUD_CONTEXT_READ_V1","request_id":"MCF-CLOUD-G2A-E2E-20260823","project_id":"cloud-infrastructure","operation":"context.get","arguments":{}}
```

The adapter returns exactly one compact JSON line on stdout. The MCF client is required to:

1. require exit code `0`, empty stderr, and one stdout line;
2. reject duplicate JSON keys;
3. validate the response with `platform/schemas/mcf-cloud-context-read-result.schema.json` using Draft 2020-12 and format checking;
4. require `status=PASS`, `error=null`, the same request ID, `project_id=cloud-infrastructure`, and `operation=context.get`;
5. recompute every provenance SHA-256 from the fixed source paths and require an exact match;
6. treat `freshness.workspace_observation=LIVE_LOCAL_DISPOSABLE` only as a fresh read of that local disposable copy;
7. keep `freshness.operational_state=LIVE_REQUIRED` because the run does not inspect NODE-01 or the VPS.

All non-PASS responses exit with code `2`. Inside this provider boundary there is no HTTP route,
bearer token, caller-supplied path, arbitrary operation, SSH, or VPS transport. MCF exposes a
separate guarded HTTP ingress and still supplies only the fixed stdio request.

## Security boundary

- input maximum: 4096 bytes;
- output maximum: 65536 bytes;
- source maximum: 262144 bytes each;
- source set: 13 fixed regular files with symlinks refused;
- adapter activation: absent by default and `NOT_AUTHORIZED` outside the explicit disposable lab opt-in;
- process isolation: Python `-I`;
- bytecode writes: disabled before repository modules are imported;
- runtime audit hook: refuses filesystem mutation, socket creation/use, process spawn/exec, and shell execution;
- implementation surface: no imports for socket, HTTP, requests, subprocess, or urllib;
- adapter result projection: read-only, no caller-supplied path, no mutation capability.

Both the historical fixture and the real MCF AppModule necessarily start the adapter process because
stdio is the transport. The zero-subprocess claim applies inside the Cloud adapter: it cannot start a
child process. The only adapter output write is its required stdout result; the disposable Cloud
filesystem remains byte-for-byte and mode-for-mode identical.

### Python runtime trusted computing base

The real MCF lab bound a copied-venv Python ELF and the complete 16-file repository execution
closure, then proved the copied venv fingerprint unchanged. This does not attest Python's standard
library, site-packages, native extensions, or transitive dependencies; they remain a residual trusted
computing base. The provider audit hook is defense in depth, not an operating-system sandbox, and no
production supply-chain claim is made.

## Cloud-owned disposable fixture E2E — historical layer

Harness:

```text
PYTHONDONTWRITEBYTECODE=1 python -B scripts/run_mcf_cloud_context_read_e2e.py
```

The harness creates a temporary copy at the exact final layout `.../workspaces/leon337/g2a-smoke/dev`, invokes the exact client command, validates the response independently, compares fingerprints, and removes the whole temporary directory in `finally`.

Required ordered markers, all observed:

```text
MCF_CLOUD_CONTEXT_DISPOSABLE_LAYOUT_PASS
MCF_CLOUD_CONTEXT_EXACT_REQUEST_PASS
MCF_CLOUD_CONTEXT_RESULT_SCHEMA_PASS
MCF_CLOUD_CONTEXT_STATUS_PASS
MCF_CLOUD_CONTEXT_PROVENANCE_PASS
MCF_CLOUD_CONTEXT_FRESHNESS_PASS
MCF_CLOUD_CONTEXT_ADAPTER_NO_NETWORK_SURFACE_PASS
MCF_CLOUD_CONTEXT_ADAPTER_NO_SUBPROCESS_SURFACE_PASS
MCF_CLOUD_CONTEXT_ADAPTER_NO_SHELL_SURFACE_PASS
MCF_CLOUD_CONTEXT_ADAPTER_NO_FILESYSTEM_WRITE_PASS
MCF_CLOUD_CONTEXT_GIT_FINGERPRINT_PASS
MCF_CLOUD_CONTEXT_FILESYSTEM_FINGERPRINT_PASS
MCF_CLOUD_CONTEXT_CLEANUP_PASS
```

Result: `PASS_13_OF_13`.

The source-repository Git fingerprint includes `HEAD` plus porcelain-v2 branch/worktree state with optional locks disabled. The disposable filesystem fingerprint includes every relative path, object type, mode, and file SHA-256. Both values were identical before and after the request. The disposable root did not exist after cleanup.

## Real MCF AppModule E2E — historical layer

The full path was proven in a disposable local lab:

```text
MCF AppModule HTTP
  -> global abuse protection
  -> dedicated Cloud ingress guard
  -> bounded MCF child-process adapter
  -> Cloud-owned stdio CLI
  -> Cloud schemas and state
```

Pinned evidence:

- Cloud provider feature content: `cb97df4bcc0bb374c7524e6aa395309af8967297`;
- Cloud PR #26 safe-target merge: `dbd772a6c37452008b7c8debd58d2782127514db`;
- MCF PR #160 main merge: `efe5164290d56f22023f07de073e2ad7c027fb95`;
- MCF staging run `32685810702`: `PASS` at that exact MCF main SHA, with the Cloud provider
  connection not activated;
- canonical MCF evidence:
  `repo://leon337/multiagent-collaboration-framework/docs/integrations/evidence/MCF-CLOUD-CONTEXT-LOCAL-READ-E2E-20260824.md`.

The real suite passed `3 / 3`: fail-closed HTTP/authentication and injection boundaries, one real
read, and persistence/rate-limit proof. The route was
`GET /v1/mcf/context/cloud/g2a`, protected by its dedicated pairwise-distinct ingress token. Its
10/minute policy used an HMAC-hashed direct socket peer, so eleven rotating client-selected Bearers
remained in one bucket and the eleventh request returned `429` before provider execution. MCF did
not persist the provider payload and used no paid API.

The E2E itself did not use staging, SSH, NODE-01, or the VPS. The later exact-SHA MCF staging success
proves the integrated MCF code revision was deployed; it does not prove a connected Cloud provider,
remote freshness, or adapter activation.

## Validation

Focused adapter plus E2E suite:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest \
  tests.test_mcf_cloud_context_read_adapter \
  tests.test_mcf_cloud_context_read_e2e -v
```

Result: `12 / 12 PASS`.

Full unit discovery after the E2E implementation: `396 / 396 PASS`.

The complete candidate gate was then run with locked Python dependencies, Ansible, and pinned ShellCheck required. Result:

```text
SECRET_POLICY_PASS scope=revision:HEAD
UNIT_TESTS_PASS count=396
SHELL_SYNTAX_PASS count=16
ANSIBLE_SYNTAX_PASS count=9
SHELLCHECK_PASS count=16
FOUNDATION_STATIC_TESTS_PASS
```

The previously blocked aggregate repository gate was environmental: two zero-byte loose objects lived in the shared Git object database. Another parallel mission reconstructed them. This workstream did not perform that repair. A later read-only `git fsck --full --no-dangling` returned `0`, and no zero-byte loose object remained, so the blocker is now resolved without attributing the repair to this workstream.

Once the object database was readable, the explicit `--all-refs` history audit exposed 11 policy findings on unrelated refs. None of those blobs is reachable from candidate `HEAD` or from `origin/mcf/mission-001-control-bridge-g1`. The candidate gate invokes `scripts/check_repository_secrets.py --revision HEAD` and scans worktree files plus every blob reachable from `HEAD`, including merged ancestry. The separate `--all-refs` mode remains fail-closed for repository-wide review. Tests create an isolated Git graph and prove that merged ancestry is included, a blob held only by a non-ancestral ref is excluded from candidate mode but detected in all-refs mode, and an uncommitted worktree finding is detected in both modes. No history was rewritten and no matched value was printed.

Global findings recorded without contents:

```text
0a5c72448f76 credential-in-uri
1463aa5966fc credential-in-uri
26662227662e credential-in-uri
43322571c9ce credential-in-uri
54dcadd6c80d credential-in-uri
5a8cf172a30d credential-in-uri
9d45a9b256f4 credential-in-uri
af1ce6811000 secret-like-assignment
b3cb6dcbce59 credential-in-uri
e3100a22210d credential-in-uri
ed89ae930c82 credential-in-uri
```

## Non-claims and remaining gates

- current provider connection or runtime: `DISCONNECTED` / `INACTIVE`;
- current verification: historical only; operational freshness remains `LIVE_REQUIRED`;
- adapter default activation: false;
- adapter activation: `NOT_AUTHORIZED`;
- NODE-01/VPS freshness: `NOT_OBSERVED_LIVE_REQUIRED`;
- VPS access, SSH, Cloud-provider deployment, and production mutation: not executed; the separate
  MCF staging code deployment is recorded above;
- G2-B Tasks 9 and 10: not started;
- G2-B real write, rollback, revocation, and effective MCF use: not proven;
- complete Python runtime or production supply-chain attestation: not proven;
- the exact-SHA MCF staging deployment is not evidence of provider activation or remote freshness.

## Publication checkpoint

- branch: `codex/context-bridge-reconcile-20260823`;
- pull request: `https://github.com/leon337/cloud-infrastructure/pull/26`;
- safe target: `mcf/mission-001-control-bridge-g1`;
- merge: `MERGED_SAFE_TARGET` at `dbd772a6c37452008b7c8debd58d2782127514db`;
- MCF integration: PR #160 merged to MCF `main` at
  `efe5164290d56f22023f07de073e2ad7c027fb95`, with exact-SHA staging run `32685810702` passing
  while the provider remained disconnected;
- push/PR workflows: GitHub-hosted disposable validation only for this branch/event; no NODE-01 dispatch path was changed.
