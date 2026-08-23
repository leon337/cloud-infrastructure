# Control Bridge G2-B Bounded Write Design

Status: **PROPOSED — HUMAN REVIEW REQUIRED BEFORE IMPLEMENTATION**

Date: 2026-08-20

Authority: **LEANDRO**

Orchestration: **MESTRE / MCF**

Implementation branch: `codex/control-bridge-g2b`

Base: `origin/mcf/mission-001-control-bridge-g1` at `8ee1fd719a50d0c9440a10a11a372dda8af1f457`

## 1. Purpose

G2-B gives MESTRE/MCF a real but narrowly bounded write capability on NODE-01.
It extends the proven G1 transport and G2-A read-only Workspace Core without
granting an unrestricted shell, root, the Docker socket, host administration,
production access, or a permanent administrative credential.

The first grant is deliberately limited to the rebuildable DEV fixture
`leon337/g2a-smoke/dev`. Expansion to real projects requires a later grant and
an explicit human gate after the pilot passes.

## 2. Recovered baseline

The design is based on the following verified state:

- GitHub self-hosted runner `node--1-mcf-control` is online, idle, version
  `2.336.0`, and routed by `node-01` plus `mcf-control` labels;
- the runner service executes as Linux user `ubuntu` without passwordless
  generic sudo and without Docker socket access;
- G1 returned real NODE-01 probes to GitHub Issues;
- G2-A proved all nine bounded read operations, path-escape refusal,
  cross-project isolation, and a no-mutation roundtrip on NODE-01;
- PR #3 remains draft and G2-A lives on
  `mcf/mission-001-control-bridge-g1` rather than `main`;
- GitHub-hosted jobs are currently blocked before runner assignment by account
  billing/spending state, while the NODE-01 self-hosted runner remains online;
- `main` still contains stale contingency text that describes Codex as
  unavailable and manual LEANDRO + MESTRE execution as the current mode;
- the parallel branch `fix/f1-2c-systemd-runtime-lock` and its uncommitted
  changes belong to MESTRE/MCF + LEANDRO and are outside this work;
- the isolated G2-B baseline passes 180 repository tests with zero failures.

Historical proofs remain historical. Before the real pilot, G2-A must perform a
fresh read-only observation of the runner, fixture, and NODE-01 boundaries.

## 3. Mandatory ordering

Implementation proceeds in this order:

1. reconcile canonical documentation against GitHub refs, live GitHub state,
   existing bridge code, and fresh read-only NODE-01 evidence;
2. implement and test G2-B entirely in repository/disposable fixtures;
3. publish and review the exact candidate;
4. perform one human bootstrap on NODE-01;
5. run the bounded end-to-end pilot;
6. prove rollback, revocation, final state, and reissuance;
7. checkpoint the evidence;
8. require LEANDRO + MESTRE/MCF + Codex alignment before assigning later work.

No G2-B code may be installed on NODE-01 before the documentation reconciliation
and repository/disposable gates pass.

## 4. Ownership and isolation

The G2-B worktree is separate from the active F1.2c worktree. G2-B must not
modify, reset, rebase, cherry-pick into, or clean the following without a later
explicit handoff:

- branch `fix/f1-2c-systemd-runtime-lock`;
- its local modifications;
- its KVM evidence or pending post-Docker-restart diagnosis.

G2-B owns only its dedicated branch, Control Bridge documents, G2-B code,
G2-B tests, the protected smoke fixture created by its bootstrap, and G2-B
evidence.

## 5. Threat boundary discovered during design

The existing G2-A workspace lives below `/home/ubuntu`, and the self-hosted
runner also executes as `ubuntu`. A workflow could therefore bypass a
policy-only Python Core and write directly to that workspace. Validation inside
the existing process would not be an effective security boundary.

G2-B corrects this by separating the transport identity from the mutation
identity and by moving the pilot target below a parent the runner cannot rename
or replace.

## 6. Architecture

```text
ChatGPT / MCF
    |
    | commit of one fixed dispatch file
    v
GitHub Actions on codex/control-bridge-g2b
    |
    | self-hosted runner, user ubuntu
    v
fixed sudoers entry (four exact commands only)
    |
    | run as mcf-workspace, never root
    v
root-owned G2-B executor
    |
    +--> root-owned grant validation
    +--> protected local lock/dedupe/audit state
    +--> protected smoke workspace
    `--> structured result on stdout
             |
             v
       Issue / Job Summary / Artifact
```

### 6.1 Identities

`ubuntu`
: Runs the GitHub self-hosted transport. It cannot directly mutate the protected
  workspace or G2-B state.

`mcf-workspace`
: A locked, non-login service account. It owns only the protected smoke
  workspace and G2-B operational state. It has no sudo, Docker group, host
  administration, or production authority.

`root`
: Installs immutable executor material, the grant, directory parents, and
  sudoers policy during a human bootstrap. Normal requests do not execute as
  root.

### 6.2 Protected paths

```text
/etc/mcf-control-bridge/g2b-grant.json
/usr/local/libexec/mcf-control-g2b
/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev
/var/lib/mcf-control-bridge/state/g2b/
/var/log/mcf-control-bridge/g2b/
/run/lock/mcf-control-bridge-g2b.lock
```

All parents capable of redirecting the workspace are root-owned. The existing
fixture below `/home/ubuntu/mcf-workspaces` is preserved and not deleted.

### 6.3 Sudo boundary

The only passwordless transitions granted to `ubuntu` are exact invocations:

```text
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2b execute
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2b rollback
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2b status
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2b revoke
```

No path, command, interpreter, environment assignment, shell, or variable
argument is accepted by sudoers. JSON input is read from standard input and is
fully validated by the immutable executor. The executor sanitizes its
environment and uses literal roots.

## 7. Transitional identity model

GitHub currently authenticates dispatch pushes as account `leon337`. The
existing connector does not provide a cryptographically distinct identity for
LEANDRO versus MESTRE/ChatGPT.

Every record separates:

- `transport_principal`: GitHub actor login and numeric ID from the workflow;
- `declared_actor`: fixed value `MESTRE_MCF` in the pilot grant;
- `authority`: fixed value `LEANDRO`;
- `mission_id` and `request_id`.

The design does not overclaim `declared_actor` as an independently authenticated
agent identity. The effective local caller is the tightly constrained `ubuntu`
to `mcf-workspace` sudo transition. GitHub App/OIDC identity is a later
hardening step, not a hidden prerequisite for this pilot.

## 8. Root-owned grant

The pilot grant is non-secret JSON with an exact schema. It includes:

```text
protocol
grant_id
enabled
authority
transport_principal_login
transport_principal_id
declared_actor
mission_id
project tenant/name/environment
allowed_operations
allowed_paths
max_content_bytes
max_active_mutations
not_before
not_after
executor_sha256
```

Pilot values are fixed to:

- project `leon337/g2a-smoke/dev`;
- actor `MESTRE_MCF` under authority `LEANDRO`;
- operations `workspace.write`, `rollback`, `status`, and `revoke`;
- path `G2B-PILOT.txt` only;
- UTF-8 content no larger than 65,536 bytes;
- at most one active mutation;
- validity of exactly 24 hours from human activation;
- exact SHA-256 of the installed executor bundle.

The executor refuses a missing, disabled, malformed, expired, future, wrongly
owned, overly writable, or hash-mismatched grant.

## 9. Request protocol

The mutation protocol is `MCF_WORKSPACE_MUTATION_V1`. A write request is:

```json
{
  "protocol": "MCF_WORKSPACE_MUTATION_V1",
  "request_id": "G2B-NODE01-20260820-001",
  "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
  "declared_actor": "MESTRE_MCF",
  "project": {
    "tenant": "leon337",
    "name": "g2a-smoke",
    "environment": "dev"
  },
  "operation": "workspace.write",
  "arguments": {
    "path": "G2B-PILOT.txt",
    "content": "bounded pilot content\n",
    "precondition": {"state": "ABSENT"}
  }
}
```

The request has exact fields. It never accepts `cwd`, absolute workspace,
`argv`, shell text, executable path, environment variables, sudo flags, Docker
operations, or arbitrary capability names.

Supported write preconditions are:

- `{"state":"ABSENT"}`;
- `{"sha256":"<current exact lowercase SHA-256>"}`.

## 10. Write transaction

Under the workspace lock, the executor performs:

1. validate its identity, environment, installed hash, grant, time, revocation
   state, request schema, actor, mission, project, operation, and limits;
2. canonicalize the request and compute its digest;
3. check dedupe state;
4. resolve the literal protected workspace and confined relative path;
5. reject absolute paths, traversal, tilde paths, symlinks, hardlinks, devices,
   sockets, FIFOs, directories, unexpected owner/mode, and target escape;
6. scan requested content and existing content for secret-like material;
7. enforce `ABSENT` or exact current SHA-256 precondition;
8. preserve safe prior bytes in a private `0600` rollback snapshot when
   overwriting;
9. create a same-directory private temporary regular file, write, flush,
   `fsync`, set the expected mode, atomically rename, and `fsync` the directory;
10. verify the final path, type, owner, mode, size, and SHA-256;
11. persist the receipt and append a bounded audit event;
12. return a redacted structured result.

New files use mode `0644`. A future allowed overwrite preserves a validated
regular file mode. The pilot uses only the absent-file path.

## 11. Locking, dedupe, and concurrency

GitHub workflow `concurrency` serializes transport requests without cancelling
in-progress work. It is not the security boundary.

The executor additionally acquires a local exclusive `flock` before reading or
changing mutation state. The lock covers precondition, write, verification,
receipt, rollback, and revocation state transitions.

Dedupe rules:

- same `request_id` and same canonical request digest: return the stored result
  as `replayed=true`, without another write;
- same `request_id` and a different digest: return `CONFLICT`;
- a second mutation while the single active mutation is unresolved: return
  `CONFLICT`;
- lock timeout: return `TIMEOUT`, never proceed unlocked.

## 12. Audit and evidence

The protected local receipt records:

- protocol and request digest;
- request, mission, grant, actor, authority, and project identifiers;
- operation and relative path;
- start and finish timestamps;
- precondition;
- before and after existence, size, mode, and SHA-256;
- result/status code;
- rollback or revocation linkage.

The receipt never stores submitted content. Prior bytes needed for rollback live
in a separate `0600` snapshot and are removed after successful rollback. Audit
events are append-only from the runner's perspective because `ubuntu` cannot
write the state directory directly.

The GitHub adapter publishes a compact result to an Issue and Job Summary.
Large safe evidence may use a seven-day Artifact. GitHub transport evidence and
the local receipt are complementary; neither is described as an immutable
platform-wide ledger.

## 13. Rollback

Rollback identifies the original `request_id` and receipt. Under the same lock,
the executor:

1. validates the grant or the specifically permitted rollback grace rule;
2. confirms the mutation has not already been rolled back;
3. confirms the current target still matches the recorded post-write type,
   owner, mode, size, and SHA-256;
4. deletes the exact newly created file, or restores the private snapshot by
   atomic rename for a future overwrite;
5. verifies the original state;
6. records a linked rollback receipt;
7. deletes the content snapshot after successful restoration.

Any drift causes a fail-closed `CONFLICT`; no best-effort overwrite or deletion
is attempted.

Rollback remains permitted for an already accepted active mutation until the
earlier of successful rollback, explicit revocation, or a short bounded grace
period recorded in the grant. The pilot is completed and rolled back before
revocation.

## 14. Revocation and expiry

The pilot grant lasts exactly 24 hours. Expiry is checked using UTC on every
operation.

`revoke` creates a protected, irreversible sentinel tied to `grant_id`. Once
present, execute and rollback requests not already covered by the explicit
rollback rule are refused. The runner cannot remove the sentinel or issue a new
grant.

The real acceptance sequence proves revocation after successful rollback. A new
grant of at least 24 hours requires a human bootstrap/reissue by LEANDRO.

Runner label removal, service stop, sudoers removal, and grant removal remain
additional emergency revocation paths, but they are not substitutes for the
protocol-level revocation proof.

## 15. Result model and safe failures

Public statuses are:

```text
PASS
REFUSED
CONFLICT
FAILED
TIMEOUT
ROLLED_BACK
REVOKED
```

Errors expose fixed codes, not raw exceptions or file content. Missing result,
malformed request, invalid grant, wrong actor/project/path, secret-like content,
precondition mismatch, lock timeout, drift, and internal failure all fail
closed. Publication failure does not convert an execution failure to success;
the local receipt remains available for bounded recovery.

## 16. GitHub transport

The G2-B workflow triggers only when
`control/dispatch/g2b.json` changes on `codex/control-bridge-g2b`. It checks out
without persisted credentials and receives only `contents: read` plus the
minimum Issue/Artifact permissions needed for results.

The workflow:

1. validates the push event and fixed dispatch envelope;
2. adds GitHub actor metadata outside the Core request;
3. invokes one exact sudo command with request JSON on standard input;
4. captures bounded stdout as the structured result;
5. publishes the compact result even when the executor refuses;
6. never interpolates request fields into shell commands.

The root-owned executor and protected target preserve the boundary even if the
checked-out workflow code is changed: `ubuntu` still cannot directly write the
target or state and sudoers exposes only the fixed executor verbs.

## 17. Documentation reconciliation

Before code implementation, reconcile at least:

- `README.md`;
- `CONTEXT.md`;
- `CHECKPOINT.md`;
- `state/current.yaml`;
- `docs/45-revised-implementation-roadmap.md`;
- G1/G2-A/G2-B documents and state;
- `docs/CODEX-EXECUTION-MISSION-001.md` where current execution ownership is
  described;
- runbooks for runner/bootstrap/operation;
- history and ownership record for the parallel F1.2c branch.

The reconciliation must state:

- Codex is available as a parallel executor;
- MESTRE remains orchestrator and LEANDRO remains final authority;
- G1 handshake and G2-A real read proof are complete;
- G2-B is the P0 active transversal mission until acceptance;
- F1.2c remains advanced, incomplete, frozen, and owned by MESTRE/MCF + LEANDRO;
- the NODE-01 F1.2c partial state is preserved;
- GitHub-hosted CI is blocked externally by billing/spending state;
- the self-hosted runner is independently online;
- no stale text may describe the initial G2-A read as pending;
- no unverified VPS fact is promoted from historical to current.

Each corrected document records which prior claim was stale and the evidence
used to replace it.

## 18. Testing strategy

### 18.1 Static and unit tests

- exact request/grant/result schemas;
- unknown fields and operations refused;
- actor, authority, mission, project, grant, executor hash, and time checks;
- secret-like content and path policy;
- traversal, symlink, hardlink, special-file, owner, mode, and root escape;
- absent and hash preconditions;
- atomic new write and future overwrite behavior;
- same-ID replay and changed-ID conflict;
- local lock serialization and timeout;
- receipt redaction and linkage;
- rollback success and drift refusal;
- expiry and irreversible revocation;
- exact sudoers commands and bootstrap provenance;
- GitHub workflow permissions, branch/path trigger, no interpolation, and
  compact publisher behavior;
- documentation/state cross-checks.

### 18.2 Disposable integration

Use temporary protected roots and distinct OS identities where available. Prove
that the transport identity cannot directly write the target or state, while
the exact executor identity can perform only the granted operation. Where a
local unprivileged fixture cannot model sudo/ownership, preserve those checks as
static gates and run the exact identity boundary in the existing KVM lab or a
purpose-built disposable systemd VM before NODE-01.

### 18.3 Real NODE-01 acceptance

The real pilot must prove, in order:

1. fresh G1/G2-A read and runner identity/status;
2. protected target absent and transport identity denied direct write;
3. grant active with at least 24 hours validity;
4. authorized write succeeds;
5. G2-A reads the exact expected safe content and hash;
6. identical request replay causes no second mutation;
7. changed request under the same ID returns `CONFLICT`;
8. concurrent request is serialized or refused;
9. audit receipt and GitHub result correlate;
10. rollback deletes the exact pilot file;
11. G2-A confirms the original final state;
12. revoke succeeds;
13. a subsequent write is refused as revoked;
14. LEANDRO reissues a new grant of at least 24 hours;
15. MESTRE/MCF successfully performs one authorized bounded operation through
    the reissued channel.

No user workload, production, Docker, network, SSH, UFW, package, service, or
secret mutation is part of this acceptance test.

## 19. Human gates

Human intervention is required for:

1. approval of this design;
2. review of the implementation plan;
3. installation of the exact reviewed bootstrap on NODE-01;
4. creation of the first 24-hour grant;
5. reissuance after the real revocation proof;
6. any expansion beyond the smoke project, pilot path, or allowed operations.

LEANDRO types any required sudo credential directly. It is never sent to an
agent, repository, Issue, Artifact, log, or receipt.

## 20. Explicit non-goals

G2-B does not deliver:

- arbitrary shell or arbitrary command execution;
- root execution for normal requests;
- Docker socket, Docker group, `docker exec`, or Compose authority;
- Git fetch/pull/checkout/commit/push;
- deletion outside exact rollback;
- host services, systemd mutation, SSH, UFW, network, APT, package, or secret
  management;
- production access;
- a permanent credential;
- a complete Capability Core, Node Agent, workflow engine, MCP endpoint, GitHub
  App, OIDC identity, or tamper-proof global audit ledger;
- automatic reassignment of the F1.2c branch after G2-B completion.

## 21. Completion criteria

G2-B is complete only when:

```text
DOCUMENTATION_RECONCILED=PASS
G1_FRESH_READ=PASS
G2A_FRESH_READ=PASS
TRANSPORT_DIRECT_WRITE=DENIED
SEPARATE_EXECUTION_IDENTITY=PASS
ROOT_OWNED_EXECUTOR_AND_GRANT=PASS
GRANT_24H=PASS
ALLOWLIST=PASS
LOCK_AND_DEDUPE=PASS
ATOMIC_WRITE=PASS
AUDIT_CORRELATION=PASS
ROLLBACK=PASS
FINAL_STATE_RESTORED=PASS
REVOCATION=PASS
POST_REVOCATION_REFUSAL=PASS
REISSUED_GRANT=PASS
MCF_EFFECTIVE_USE=PASS
NO_SHELL=PASS
NO_ROOT_NORMAL_EXECUTION=PASS
NO_DOCKER_SOCKET=PASS
NO_PRODUCTION=PASS
```

After these pass, LEANDRO + MESTRE/MCF + Codex explicitly redistribute the next
work. Codex does not automatically resume or claim the parallel F1.2c branch.
