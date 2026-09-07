# G2-A Protected Read + G2-B Receipt Observability Design

**Date:** 2026-09-07
**Status:** SPEC_APPROVED
**Base SHA:** `c6a8206e40137f930f6a963c185c2bdc1f7c3ff2`
**Human authority:** LEANDRO
**Coordinator:** MESTRE

## 1. Problem

Task 10 requires G2-A to read the real `G2B-PILOT.txt` created by G2-B and correlate that observation with the G2-B receipt.

The current G2-A reads `/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>`, while the protected G2-B workspace is `/var/lib/mcf-control-bridge/workspaces/<tenant>/<project>/<environment>` and is owned by `mcf-workspace` with mode `0700`.

Relaxing ownership, ACLs, or modes would weaken a boundary already proven on NODE-01. Copying the pilot file into the legacy G2-A tree would observe a copy rather than the real G2-B target.

A second gap exists in publication: G2-B receipts are persisted under a deterministic SHA-256-derived filename, but the public publisher currently renders `receipt ID: none`.

## 2. Goals

- Let G2-A observe the real protected G2-B pilot file without giving `ubuntu` direct filesystem access.
- Preserve the existing G2-A read-only protocol and G2-B write boundary.
- Expose a deterministic, content-free receipt identifier for audit correlation.
- Add no generic shell, sudo, Docker, network, package, production, or arbitrary-path capability.

## 3. Non-goals

- Do not make `ubuntu` a member of `mcf-workspace`.
- Do not add ACLs or broaden modes on the G2-B workspace or state directories.
- Do not create a new `mcf-observer` account.
- Do not expose receipt JSON, snapshot bytes, recovery bytes, audit content, or file content through G2-B publication.
- Do not add G2-A write, delete, rename, mkdir, Git mutation, shell, or arbitrary subprocess operations.
- Do not issue or reissue a G2-B grant as part of this correction.
- Do not merge PR #56 or start unrelated platform work.

## 4. Architecture

```text
GitHub Actions runner (`ubuntu`)
        |
        | exact sudo rule only
        v
`mcf-workspace`
        |
        | root-owned fixed entrypoint
        v
G2-A protected reader
        |
        v
/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev
```

The existing unprivileged G2-A backend remains unchanged for its transitional `/home/ubuntu/mcf-workspaces` use cases.

## 5. Protected-reader contract

The protected reader is a separate installed component, not part of the G2-B executor bundle. Its proposed fixed entrypoint is:

```text
/usr/local/libexec/mcf-control-g2a-protected-read
```

Installation ownership/mode: `root:root 0555`. The runtime identity is `mcf-workspace`; root execution is refused by the entrypoint.

The sudo rule permits `ubuntu` to run only that exact entrypoint as `mcf-workspace`, with no caller-controlled executable, interpreter, shell, environment override, cwd, or arbitrary argv.

The entrypoint consumes one bounded UTF-8 JSON request on stdin and emits one bounded JSON result on stdout. Stderr must contain no request content.

The protected route is accepted only when all of these are true:

- protocol is the existing G2-A workspace-control protocol;
- project is exactly `leon337/g2a-smoke/dev`;
- operation is `workspace.stat` or `workspace.read`;
- the physical root is fixed internally to `/var/lib/mcf-control-bridge/workspaces`;
- path remains relative and confined after realpath/symlink resolution;
- existing G2-A size, encoding, sensitive-path, timeout, and secret-like-content refusals remain effective.

For `workspace.read`, the only accepted relative path in this slice is exactly `G2B-PILOT.txt`. The implementation must not special-case its content or expected hash. `workspace.stat` remains a workspace-level observation.

## 6. Adapter routing

The GitHub-facing G2-A adapter remains the transport boundary. It validates the envelope before selecting a backend.

Backend selection is deterministic and not caller-selectable:

- requests matching the exact protected project plus `workspace.stat`/`workspace.read` use the protected reader;
- all other currently valid G2-A requests continue through the existing unprivileged backend;
- no request field such as `backend`, `workspace_root`, `sudo`, `uid`, `cwd`, or executable path is introduced.

The adapter invokes the protected reader with a fixed argv array and `shell=False`, a minimal fixed environment, bounded stdin/stdout/stderr, and the existing operation timeout budget.

A protected-reader invocation failure must map to a bounded fail-closed G2-A result without echoing raw subprocess text.

## 7. Installation boundary

The protected reader is installed independently from the G2-B executor so this correction does not change the already-qualified G2-B executor digest.

A dedicated Ansible role/playbook must:

- assert the existing `mcf-workspace` account has the exact locked/nologin boundary;
- assert the G2-B protected workspace parent is managed as expected;
- install the root-owned reader, its root-owned immutable application bundle, and one dedicated sudoers fragment;
- ensure the privileged entrypoint imports no Python/module/code from the GitHub Actions checkout or another runner-writable path;
- validate the sudoers fragment with `visudo -cf` before activation;
- add no grant file and make no change to G2-B grant/revocation state;
- be idempotent and support bounded rollback of only the objects it owns.

The installed bundle must be non-writable by both `ubuntu` and `mcf-workspace`. The checkout may supply only bounded JSON data to the fixed entrypoint; it must never supply executable code, import paths, interpreters, or library roots.

## 8. Receipt observability

The G2-B executor result schema remains unchanged.

The public receipt identifier is derived only in the publisher:

```text
receipt_id = lowercase_hex_sha256(request_id_utf8)
```

It is exactly 64 lowercase hexadecimal characters and corresponds to the local receipt filename `<receipt_id>.json` used by the protected state store.

The publisher may render this identifier only after the full G2-B result has passed the existing strict result validation and correlation with the expected dispatch.

The identifier must not be accepted from executor output, dispatch input, transport metadata, environment variables, or GitHub payload fields.

The publication continues to expose only allowlisted metadata: request ID, operation, project, relative path, status, safe error code, grant ID, timestamps, before/after SHA-256, replay flag, and receipt ID.

No receipt body, request content, snapshot, recovery state, audit event body, local absolute path, UID, inode, or secret-like material is published.

## 9. Security invariants

The correction is invalid if any of these become false:

- direct `ubuntu` read of the G2-B protected workspace is denied;
- generic `sudo -n` for `ubuntu` remains denied;
- `ubuntu` cannot run arbitrary commands as `mcf-workspace`;
- `mcf-workspace` remains non-login and outside privileged groups;
- the protected reader has no write-capable operation or filesystem mutation path;
- protected-reader path resolution cannot escape the fixed workspace root through `..`, absolute paths, tilde expansion, symlinks, hardlinks, or nested unsafe targets;
- G2-B workspace ownership/modes are not relaxed;
- G2-B executor hash and revoked-grant history are not rewritten by this correction;
- no NODE-01 host mutation occurs before a separate implementation/apply gate.

## 10. Testing requirements

Implementation must use TDD and add focused tests before code.

Required automated proof includes:

1. adapter selects the protected backend only for the exact project and approved read operations;
2. no caller-controlled backend/root/uid/sudo/executable fields are accepted;
3. protected subprocess invocation uses one fixed argv array, `shell=False`, bounded I/O, timeout, and fixed environment;
4. entrypoint refuses root, wrong UID, extra argv, oversized/trailing input, invalid JSON, unknown fields, wrong project, wrong operation, and unsafe paths;
5. disposable protected workspace tests prove `workspace.stat` observes the real protected workspace, `workspace.read` observes the real pilot target, and the read path causes no hash/size/mtime change;
6. mutation attempts (`write`, rename, unlink, mkdir, chmod or arbitrary command) are impossible through the public contract;
7. Ansible artifact tests prove exact ownership/modes, exact sudoers command and idempotent rollback;
8. publisher tests prove `receipt_id == sha256(request_id)`, exact 64-hex shape, and no content/snapshot/audit leakage;
9. existing G2-A/G2-B tests remain green.

The repository-wide baseline at design time is `401/401` unit tests passing on `c6a8206...`.

## 11. NODE-01 acceptance after implementation

Live activation is a separate human-gated step after commit-bound CI.
Before applying anything to NODE-01, require exact-head CI, Ansible syntax validation, check-mode, runner idle state, second SSH recovery session, and explicit LEANDRO authorization.

Live acceptance must prove in order:

1. `ubuntu` direct read remains denied before and after installation;
2. generic sudo, Docker socket access, login as `mcf-workspace`, and privileged-group membership remain denied;
3. protected-reader install apply succeeds and second apply reports `changed=0`;
4. with no active G2-B grant, protected `workspace.stat` reports the real workspace present and protected `workspace.read` of `G2B-PILOT.txt` returns `NOT_FOUND/path_not_found`;
5. only after a later separately authorized G2-B reissue/write, G2-A protected `workspace.read` returns the real safe pilot content/hash;
6. the G2-A hash equals the G2-B `after.sha256` and the published receipt ID matches `sha256(original_request_id)`;
7. after G2-B rollback, G2-A protected observation reports the original absent state again;
8. protected-reader rollback removes only its own entrypoint/sudoers objects and restores the pre-install host boundary.

## 12. Failure handling

Any identity drift, ownership/mode drift, unexpected existing managed object, sudoers validation failure, path-confinement failure, test failure, or direct-read capability expansion stops the rollout fail-closed.

Do not repair a failed protected read by changing workspace permissions, granting group membership, using root shell, copying the target, or bypassing the adapter.

If receipt-ID derivation and local receipt naming ever diverge, publication must fail closed rather than publish an uncorrelated identifier.

## 13. Rollout and repository boundaries

Implementation work occurs on `team/g2b-task10-g2a-protected-read-receipt-20260907`, derived from exact SHA `c6a8206...`.

PR #56 remains untouched, Draft and unmerged. The historical G2-A transport branch is not rewritten during design or local implementation.

A later transport-integration decision must preserve commit-bound CI and must not trigger a real NODE-01 request merely by landing implementation code.

## 14. Acceptance for this design

This design is complete when LEANDRO reviews this committed spec and explicitly authorizes creation of the implementation plan. Code implementation is not authorized by spec publication alone.
