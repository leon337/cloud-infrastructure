# Control Bridge G2-B Bounded Write Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a 24-hour, project- and path-scoped, auditable, revocable, reversible write capability from MESTRE/MCF through the existing GitHub Control Bridge to the NODE-01 smoke workspace.

**Architecture:** Keep GitHub Actions transport on user `ubuntu`, but move the pilot workspace behind a root-owned parent and execute mutations as a locked non-login user `mcf-workspace` through four exact sudoers commands. A root-owned Python executor validates a root-owned grant, serializes and deduplicates requests, performs atomic compare-and-swap writes, records protected receipts, and supports fail-closed rollback and irreversible grant revocation.

**Tech Stack:** Python 3.12 standard library, `unittest`, GitHub Actions, Ansible Core 2.21.3, Linux users/filesystem permissions, sudoers, `flock`, Git, JSON/YAML.

**Spec:** `docs/superpowers/specs/2026-08-20-control-bridge-g2b-bounded-write-design.md`

## Global Constraints

- LEANDRO is the final human authority; MESTRE/MCF orchestrates; Codex is a parallel executor.
- Do not modify, reset, rebase, clean, or assume ownership of `fix/f1-2c-systemd-runtime-lock` or its local changes.
- Reconcile documentation before implementing executable G2-B code.
- Pilot scope is exactly `leon337/g2a-smoke/dev` and `G2B-PILOT.txt`.
- The initial grant is valid for exactly 24 hours and permits at most one active mutation.
- Normal mutations run as `mcf-workspace`, never root.
- No arbitrary shell, argv, cwd, environment, sudo flags, Docker socket, Git mutation, host administration, secrets, deploy, or production capability.
- GitHub `declared_actor=MESTRE_MCF` is transitional attribution; do not overclaim independent cryptographic agent identity.
- The transport user `ubuntu` must be unable to directly mutate the protected workspace and protected G2-B state.
- Every mutation requires `ABSENT` or exact SHA-256 precondition, an exclusive local lock, a receipt, a bounded result, and fail-closed behavior.
- LEANDRO types sudo credentials directly; credentials never enter Git, chat, logs, Issues, Artifacts, requests, or receipts.
- Hosted GitHub CI may remain `BLOCKED_EXTERNAL_BILLING`; local and disposable evidence must be distinguished from unavailable hosted evidence.

---

### Task 1: Reconcile canonical continuity and Control Bridge ownership

**Files:**

- Create: `tests/test_control_bridge_continuity.py`
- Create: `state/control-bridge-g2b.yaml`
- Create: `history/SESSION-2026-08-20-021.md`
- Modify: `README.md`
- Modify: `CONTEXT.md`
- Modify: `CHECKPOINT.md`
- Modify: `state/current.yaml`
- Modify: `docs/45-revised-implementation-roadmap.md`
- Modify: `docs/49-control-bridge-g1.md`
- Modify: `docs/50-control-bridge-g1-handshake-checkpoint.md`
- Modify: `docs/51-control-bridge-g2a-design.md`
- Modify: `docs/52-control-bridge-g2a-implementation-checkpoint.md`
- Modify: `docs/CODEX-EXECUTION-MISSION-001.md`

**Interfaces:**

- Consumes: GitHub `main=9cc71f2`, G1/G2-A head `8ee1fd7`, PR #3, Issues #4/#5, live runner API observation, approved G2-B spec.
- Produces: canonical `control_bridge` and `work_ownership` mappings in `state/current.yaml`; dedicated G2-B state file consumed by later documentation and acceptance tasks.

- [ ] **Step 1: Write the failing continuity test**

Create `tests/test_control_bridge_continuity.py` with assertions equivalent to:

```python
from __future__ import annotations

import pathlib
import unittest

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]


class ControlBridgeContinuityTests(unittest.TestCase):
    def test_current_state_records_p0_bridge_and_parallel_ownership(self):
        state = yaml.safe_load((ROOT / "state/current.yaml").read_text())
        bridge = state["control_bridge"]
        self.assertEqual(bridge["priority"], "P0")
        self.assertEqual(bridge["g1"], "PASS_REAL_NODE_01_ROUNDTRIP")
        self.assertEqual(bridge["g2a"], "PASS_REAL_NODE_01_READ_ONLY")
        self.assertEqual(bridge["g2b"], "DESIGN_APPROVED_IMPLEMENTATION_PENDING")
        self.assertEqual(
            state["work_ownership"]["f1_2c_systemd_runtime_lock"]["owner"],
            "MESTRE_MCF_AND_LEANDRO",
        )
        self.assertTrue(
            state["work_ownership"]["f1_2c_systemd_runtime_lock"]["frozen_for_codex"]
        )

    def test_entrypoints_no_longer_claim_codex_is_unavailable(self):
        for relative in ("README.md", "CONTEXT.md", "CHECKPOINT.md"):
            text = (ROOT / relative).read_text()
            self.assertNotIn("Codex está indisponível", text)
            self.assertIn("CONTROL_BRIDGE_G2B", text)

    def test_g2b_state_is_fail_closed_before_real_acceptance(self):
        state = yaml.safe_load((ROOT / "state/control-bridge-g2b.yaml").read_text())
        self.assertEqual(state["status"], "DESIGN_APPROVED_IMPLEMENTATION_PENDING")
        self.assertEqual(state["pilot"]["project"], "leon337/g2a-smoke/dev")
        self.assertEqual(state["pilot"]["path"], "G2B-PILOT.txt")
        self.assertEqual(state["pilot"]["grant_duration_hours"], 24)
        self.assertFalse(state["evidence"]["real_write"])
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```bash
python3 -m unittest tests.test_control_bridge_continuity -v
```

Expected: `ERROR` or `FAIL` because `state/control-bridge-g2b.yaml` and the new canonical mappings do not exist.

- [ ] **Step 3: Add the canonical G2-B state**

Create `state/control-bridge-g2b.yaml` with these exact initial semantics:

```yaml
protocol_version: MCF_CONTROL_BRIDGE_G2B_STATE_V1
updated_at: 2026-08-20
scope: TRANSVERSAL_CONTROL_PLANE
priority: P0
repository: leon337/cloud-infrastructure
branch: codex/control-bridge-g2b
base_branch: mcf/mission-001-control-bridge-g1
base_sha: 8ee1fd719a50d0c9440a10a11a372dda8af1f457
status: DESIGN_APPROVED_IMPLEMENTATION_PENDING
pilot:
  project: leon337/g2a-smoke/dev
  path: G2B-PILOT.txt
  grant_duration_hours: 24
  active_mutations_max: 1
  production: false
boundaries:
  transport_user: ubuntu
  execution_user: mcf-workspace
  normal_execution_root: false
  arbitrary_shell: false
  docker_socket: false
  git_mutation: false
  host_administration: false
evidence:
  g1_real_roundtrip: true
  g2a_real_read: true
  real_write: false
  real_rollback: false
  real_revocation: false
  mcf_effective_use: false
next_exact_step: RECONCILE_DOCUMENTATION_THEN_IMPLEMENT_G2B_REPO_ONLY
```

- [ ] **Step 4: Reconcile the entrypoints and roadmap**

Make the smallest consistent edits so every listed document states:

```text
CONTROL_BRIDGE_G2B=P0_DESIGN_APPROVED_IMPLEMENTATION_PENDING
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
G2B_REAL_WRITE=NOT_EXECUTED
CODEX=AVAILABLE_PARALLEL_EXECUTOR
MESTRE_MCF=ORCHESTRATOR
LEANDRO=FINAL_HUMAN_AUTHORITY
F1_2C_SYSTEMD_RUNTIME_LOCK=FROZEN_FOR_CODEX_OWNED_BY_MESTRE_MCF_AND_LEANDRO
GITHUB_HOSTED_CI=BLOCKED_EXTERNAL_BILLING
SELF_HOSTED_NODE_01_RUNNER=ONLINE_OBSERVED_2026_08_20
```

Preserve F1.2c operational facts as historical/current with their existing timestamps. Do not claim a fresh VPS observation from the GitHub runner API alone.

Add to `state/current.yaml`:

```yaml
control_bridge:
  priority: P0
  g1: PASS_REAL_NODE_01_ROUNDTRIP
  g2a: PASS_REAL_NODE_01_READ_ONLY
  g2b: DESIGN_APPROVED_IMPLEMENTATION_PENDING
  self_hosted_runner: ONLINE_OBSERVED_2026_08_20_GITHUB_API
  hosted_ci: BLOCKED_EXTERNAL_BILLING
  source: state/control-bridge-g2b.yaml
work_ownership:
  f1_2c_systemd_runtime_lock:
    branch: fix/f1-2c-systemd-runtime-lock
    owner: MESTRE_MCF_AND_LEANDRO
    frozen_for_codex: true
  control_bridge_g2b:
    branch: codex/control-bridge-g2b
    owner: CODEX
    orchestrator: MESTRE_MCF
```

- [ ] **Step 5: Record the evidence reconciliation**

In `history/SESSION-2026-08-20-021.md`, record the stale claim, replacement, and evidence source in a table with these rows:

```text
Codex unavailable -> Codex available as parallel executor -> current LEANDRO instruction
G2-A read pending -> real NODE-01 read PASS -> Issue #5 + docs/52 + state/control-bridge-g2a.yaml
G2-B undefined -> design approved / implementation pending -> approved spec commit
runner state unknown -> GitHub API online/idle -> observed 2026-08-20
hosted CI code failure -> external billing refusal before job start -> check annotations
F1.2c available to Codex -> frozen parallel ownership -> current LEANDRO instruction
```

- [ ] **Step 6: Run documentation and state verification**

Run:

```bash
python3 -m unittest tests.test_control_bridge_continuity -v
python3 scripts/check_markdown_links.py
python3 scripts/validate_yaml.py
python3 scripts/validate_state.py
python3 scripts/generate_project_status.py --check-readme
python3 scripts/check_repository_secrets.py --revision HEAD
git diff --check
```

Expected: all commands exit `0`; no state validator overclaim; README generated block remains consistent.

- [ ] **Step 7: Commit the reconciled documentation**

```bash
git add README.md CONTEXT.md CHECKPOINT.md state/current.yaml \
  state/control-bridge-g2b.yaml docs/45-revised-implementation-roadmap.md \
  docs/49-control-bridge-g1.md docs/50-control-bridge-g1-handshake-checkpoint.md \
  docs/51-control-bridge-g2a-design.md \
  docs/52-control-bridge-g2a-implementation-checkpoint.md \
  docs/CODEX-EXECUTION-MISSION-001.md history/SESSION-2026-08-20-021.md \
  tests/test_control_bridge_continuity.py
git commit -m "docs(g2b): reconcile control bridge priority and ownership"
```

---

### Task 2: Define the G2-B request, result, and root-owned grant contracts

**Files:**

- Create: `control_plane/g2b/__init__.py`
- Create: `control_plane/g2b/errors.py`
- Create: `control_plane/g2b/protocol.py`
- Create: `control_plane/g2b/grant.py`
- Create: `tests/test_g2b_protocol.py`
- Create: `tests/test_g2b_grant.py`

**Interfaces:**

- Consumes: JSON dictionaries from the GitHub adapter and `/etc/mcf-control-bridge/g2b-grant.json`.
- Produces: `MutationRequest`, `ProjectKey`, `Precondition`, `Grant`, `parse_request()`, `load_grant()`, `validate_grant_for_request()`.

- [ ] **Step 1: Write failing protocol tests**

Define tests that import these exact interfaces:

```python
from control_plane.g2b.protocol import (
    MUTATION_PROTOCOL,
    MutationRequest,
    parse_request,
)

def valid_request():
    return {
        "protocol": MUTATION_PROTOCOL,
        "request_id": "G2B-TEST-0001",
        "mission_id": "CONTROL-BRIDGE-G2B-PILOT",
        "declared_actor": "MESTRE_MCF",
        "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
        "operation": "workspace.write",
        "arguments": {
            "path": "G2B-PILOT.txt",
            "content": "pilot\n",
            "precondition": {"state": "ABSENT"},
        },
    }
```

Cover exact fields, request ID regex `^[A-Z0-9][A-Z0-9-]{0,127}$`, exact pilot actor/mission, project DNS labels, `dev|staging`, operations, UTF-8 string content, `ABSENT` versus lowercase 64-hex SHA-256 preconditions, 65,536-byte limit, and rejection of `cwd`, `argv`, environment, shell, and unknown fields.

- [ ] **Step 2: Run protocol tests and verify RED**

```bash
python3 -m unittest tests.test_g2b_protocol -v
```

Expected: import failure because `control_plane.g2b` does not exist.

- [ ] **Step 3: Implement the protocol types and safe errors**

In `errors.py`, define:

```python
class G2BError(Exception):
    status = "FAILED"
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code

class RefusedError(G2BError): status = "REFUSED"
class ConflictError(G2BError): status = "CONFLICT"
class TimeoutError(G2BError): status = "TIMEOUT"
```

In `protocol.py`, define frozen dataclasses and constants:

```python
MUTATION_PROTOCOL = "MCF_WORKSPACE_MUTATION_V1"
RESULT_PROTOCOL = "MCF_WORKSPACE_MUTATION_RESULT_V1"
OPERATIONS = frozenset({"workspace.write", "rollback", "status", "revoke"})
MAX_CONTENT_BYTES = 65_536

@dataclass(frozen=True)
class ProjectKey: tenant: str; name: str; environment: str

@dataclass(frozen=True)
class Precondition: state: str | None = None; sha256: str | None = None

@dataclass(frozen=True)
class MutationRequest:
    protocol: str
    request_id: str
    mission_id: str
    declared_actor: str
    project: ProjectKey
    operation: str
    path: str | None
    content: bytes | None
    precondition: Precondition | None
    original_request_id: str | None
```

`parse_request(value: dict[str, Any]) -> MutationRequest` must normalize UTF-8 content to bytes but never include content in validation errors.

- [ ] **Step 4: Write failing grant tests**

Test a `Grant` with exact fields from the spec. Cover:

```python
load_grant(path, now=...)
validate_grant_for_request(grant, request, transport_principal)
canonical_bundle_sha256(installed_root)
```

Require owner UID `0`, regular non-symlink file, mode `0644`, exact protocol, enabled true, exact 24-hour interval, `not_before <= now < not_after`, max active mutations `1`, exact actor/mission/project/path/operations, and installed bundle digest match. Tests must prove missing, future, expired, overlong, overly writable, wrong-owner, changed-project, changed-path, and digest mismatch refusals.

- [ ] **Step 5: Implement grant loading and validation**

Use only `json`, `pathlib`, `os.stat`, `datetime`, and `hashlib`. Define:

```python
@dataclass(frozen=True)
class TransportPrincipal:
    login: str
    actor_id: int

@dataclass(frozen=True)
class Grant:
    grant_id: str
    authority: str
    principal: TransportPrincipal
    declared_actor: str
    mission_id: str
    project: ProjectKey
    allowed_operations: frozenset[str]
    allowed_paths: frozenset[str]
    max_content_bytes: int
    max_active_mutations: int
    not_before: datetime
    not_after: datetime
    executor_sha256: str
```

Canonical bundle hashing must sort relative file names and hash records formatted as `sha256  relative/path\n`; it must reject symlinks and files outside the installed root.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest tests.test_g2b_protocol tests.test_g2b_grant -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the contracts**

```bash
git add control_plane/g2b tests/test_g2b_protocol.py tests/test_g2b_grant.py
git commit -m "feat(g2b): define bounded mutation and grant contracts"
```

---

### Task 3: Implement confined atomic workspace writes

**Files:**

- Create: `control_plane/g2b/workspace.py`
- Create: `tests/test_g2b_workspace.py`

**Interfaces:**

- Consumes: `MutationRequest`, literal workspace root, expected execution UID.
- Produces: `inspect_target() -> TargetState`, `atomic_write() -> WriteOutcome`, `atomic_restore()`, `atomic_delete()`.

- [ ] **Step 1: Write failing filesystem tests**

Create a temporary protected-root fixture and test:

```python
state = inspect_target(workspace, "G2B-PILOT.txt", expected_uid=os.getuid())
outcome = atomic_write(
    workspace,
    "G2B-PILOT.txt",
    b"pilot\n",
    precondition=Precondition(state="ABSENT"),
    expected_uid=os.getuid(),
)
assert outcome.before.exists is False
assert outcome.after.sha256 == hashlib.sha256(b"pilot\n").hexdigest()
assert (workspace / "G2B-PILOT.txt").stat().st_mode & 0o777 == 0o644
```

Add negative cases for absolute path, `..`, tilde, nested path, workspace symlink, target symlink, hardlink count greater than one, FIFO/socket/device/directory, wrong owner, unsafe mode, secret-like content, invalid UTF-8, size overflow, wrong `ABSENT`, wrong SHA-256, and target replacement between inspection and mutation.

- [ ] **Step 2: Run workspace tests and verify RED**

```bash
python3 -m unittest tests.test_g2b_workspace -v
```

Expected: import failure for `control_plane.g2b.workspace`.

- [ ] **Step 3: Implement confined target inspection**

Define:

```python
@dataclass(frozen=True)
class TargetState:
    exists: bool
    size: int | None
    mode: int | None
    uid: int | None
    device: int | None
    inode: int | None
    sha256: str | None

@dataclass(frozen=True)
class WriteOutcome:
    path: str
    before: TargetState
    after: TargetState
```

For the pilot, require `relative_path == "G2B-PILOT.txt"` through the grant and require a single path component in the filesystem helper. Open the workspace with a directory file descriptor, use `lstat`, `O_NOFOLLOW`, and `dir_fd` operations, and reject any target not owned by the expected execution UID.

- [ ] **Step 4: Implement content and precondition validation**

Reuse `scripts.check_repository_secrets.content_findings` without echoing matches. Require content decode as UTF-8, byte length at most the grant limit, and no secret-like findings. `ABSENT` succeeds only when the target does not exist. SHA-256 succeeds only for a regular, single-link file whose digest exactly matches.

- [ ] **Step 5: Implement atomic write, restore, and delete**

Use same-directory names derived internally from a random token, never from the request. Sequence:

```text
os.open(temp, O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0600, dir_fd=workspace_fd)
write all bytes
os.fsync(temp_fd)
os.fchmod(temp_fd, target_mode)
re-lstat target and compare frozen device/inode/state
os.rename(temp, target, src_dir_fd=workspace_fd, dst_dir_fd=workspace_fd)
os.fsync(workspace_fd)
inspect and verify final target
```

Cleanup removes only the exact internally generated temp name. Never use `rm -rf`, globbing, recursive deletion, or a caller-provided deletion path.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest tests.test_g2b_workspace -v
```

Expected: all tests pass, including race/refusal cases.

- [ ] **Step 7: Commit confined writes**

```bash
git add control_plane/g2b/workspace.py tests/test_g2b_workspace.py
git commit -m "feat(g2b): add confined atomic workspace writes"
```

---

### Task 4: Add protected lock, dedupe, receipts, rollback, and revocation

**Files:**

- Create: `control_plane/g2b/state.py`
- Create: `control_plane/g2b/executor.py`
- Create: `tests/test_g2b_state.py`
- Create: `tests/test_g2b_executor.py`

**Interfaces:**

- Consumes: validated request/grant, protected state root, lock path, workspace root, UTC clock.
- Produces: `StateStore`, `execute_request() -> dict[str, Any]`, receipt JSON, rollback linkage, revocation sentinel.

- [ ] **Step 1: Write failing state-store tests**

Cover exact behaviors:

```python
with store.exclusive_lock(timeout_seconds=1): ...
store.lookup_request(request_id)
store.record_write(receipt)
store.record_rollback(receipt)
store.revoke(grant_id, actor="MESTRE_MCF", at=now)
store.is_revoked(grant_id)
```

Require state root and child directories to be real directories owned by the execution UID with modes `0700`; lock file `0600`; receipts `0600`; request IDs mapped through a SHA-256 filename rather than interpolated directly; atomic receipt writes; and JSONL audit lines without content or raw exceptions.

- [ ] **Step 2: Run state tests and verify RED**

```bash
python3 -m unittest tests.test_g2b_state -v
```

Expected: import failure.

- [ ] **Step 3: Implement `StateStore`**

Use `fcntl.flock(LOCK_EX | LOCK_NB)` with a monotonic timeout no longer than 10 seconds. Define canonical request digest as SHA-256 of UTF-8 JSON with `sort_keys=True`, `separators=(",", ":")`, and no insignificant whitespace.

Receipt fields must be:

```text
protocol, request_id, request_digest, mission_id, declared_actor, authority,
transport_principal, grant_id, project, operation, path, started_at, finished_at,
precondition, before, after, status, replayed, rollback_request_id,
revocation_request_id, error
```

Reject receipt schema expansion and scan serialized receipts with the repository secret policy before persistence.

- [ ] **Step 4: Write failing executor lifecycle tests**

Build requests with an injectable clock and temporary roots. Prove:

1. authorized absent-file write returns `PASS` and receipt;
2. identical request returns the stored result with `replayed=true` and unchanged inode/mtime;
3. same ID with changed content returns `CONFLICT`;
4. second unresolved mutation returns `CONFLICT`;
5. rollback deletes an exact newly created file and returns `ROLLED_BACK`;
6. target drift causes rollback `CONFLICT` without deletion;
7. revocation after rollback returns `REVOKED`;
8. post-revocation write returns `REFUSED`;
9. expired/future/invalid grant returns `REFUSED`;
10. internal exceptions return `FAILED/internal_error` without exception text.

- [ ] **Step 5: Implement `execute_request()`**

Use dependency injection:

```python
def execute_request(
    request_value: dict[str, Any],
    *,
    transport_principal: TransportPrincipal,
    grant_path: pathlib.Path,
    installed_root: pathlib.Path,
    workspace_root: pathlib.Path,
    state_root: pathlib.Path,
    lock_path: pathlib.Path,
    expected_uid: int,
    now: Callable[[], datetime],
) -> dict[str, Any]:
    ...
```

The function must return safe structured results for every `G2BError`. It must not catch `BaseException`. For `workspace.write`, persist the pre-write snapshot before replacement and receipt after verification. For rollback, require exact post-state match. For revoke, require zero active mutations.

- [ ] **Step 6: Run state and executor tests**

```bash
python3 -m unittest tests.test_g2b_state tests.test_g2b_executor -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit transaction state**

```bash
git add control_plane/g2b/state.py control_plane/g2b/executor.py \
  tests/test_g2b_state.py tests/test_g2b_executor.py
git commit -m "feat(g2b): add auditable write rollback and revocation"
```

---

### Task 5: Build the immutable installed executor and exact sudo boundary

**Files:**

- Create: `platform/control-bridge/mcf-control-g2b`
- Create: `platform/sudoers/mcf-control-g2b`
- Create: `platform/tmpfiles.d/mcf-control-bridge-g2b.conf`
- Create: `tests/test_g2b_installed_boundary.py`

**Interfaces:**

- Consumes: request JSON on stdin, fixed command word in `sys.argv[1]`, fixed installed paths.
- Produces: exactly one bounded JSON result on stdout and exit `0` for completed protocol outcomes, exit `2` for malformed invocation/bootstrap boundary failure.

- [ ] **Step 1: Write failing installed-boundary tests**

Assert exact shebang and paths:

```python
self.assertEqual(lines[0], "#!/usr/bin/python3 -I")
self.assertIn("/usr/local/lib/mcf-control-bridge", text)
self.assertIn("/etc/mcf-control-bridge/g2b-grant.json", text)
self.assertIn("/var/lib/mcf-control-bridge/workspaces", text)
self.assertIn("/var/lib/mcf-control-bridge/state/g2b", text)
self.assertIn("/run/lock/mcf-control-bridge-g2b.lock", text)
```

Parse sudoers text and require only the four exact commands from the spec, run as `mcf-workspace`, with no wildcard, shell, Python interpreter, editor, environment assignment, or root runas target. Require tmpfiles to create only the exact lock file as `mcf-workspace:mcf-workspace 0600`.

- [ ] **Step 2: Run boundary tests and verify RED**

```bash
python3 -m unittest tests.test_g2b_installed_boundary -v
```

Expected: missing artifact failures.

- [ ] **Step 3: Implement the installed entrypoint**

The entrypoint accepts exactly one of `execute|rollback|status|revoke`, rejects extra arguments, clears environment-dependent behavior through isolated Python and fixed paths, requires `uid == mcf-workspace UID`, reads at most 131,072 bytes from stdin, parses one JSON object, requires request operation to match the command, and calls `execute_request()`.

Write only JSON to stdout:

```python
sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
```

Never log request content.

- [ ] **Step 4: Add exact sudoers and tmpfiles artifacts**

Sudoers semantic content:

```sudoers
Cmnd_Alias MCF_G2B = /usr/local/libexec/mcf-control-g2b execute, \
                     /usr/local/libexec/mcf-control-g2b rollback, \
                     /usr/local/libexec/mcf-control-g2b status, \
                     /usr/local/libexec/mcf-control-g2b revoke
ubuntu ALL=(mcf-workspace) NOPASSWD: MCF_G2B
```

Tmpfiles semantic content:

```text
f /run/lock/mcf-control-bridge-g2b.lock 0600 mcf-workspace mcf-workspace -
```

Validate the final sudoers file with `visudo -cf` in integration tests before installation.

- [ ] **Step 5: Run focused verification**

```bash
python3 -m unittest tests.test_g2b_installed_boundary -v
python3 -m py_compile platform/control-bridge/mcf-control-g2b
```

Expected: tests pass and Python compilation exits `0`.

- [ ] **Step 6: Commit the installed boundary**

```bash
git add platform/control-bridge platform/sudoers platform/tmpfiles.d \
  tests/test_g2b_installed_boundary.py
git commit -m "feat(g2b): add immutable executor and exact sudo boundary"
```

---

### Task 6: Add the GitHub G2-B adapter, workflow, and safe publisher

**Files:**

- Create: `control/dispatch/g2b.json`
- Create: `control/examples/g2b-request.example.json`
- Create: `scripts/control_bridge_g2b.py`
- Create: `scripts/control_bridge_g2b_publish.py`
- Create: `.github/workflows/control-bridge-g2b.yml`
- Create: `tests/test_control_bridge_g2b_adapter.py`

**Interfaces:**

- Consumes: fixed push dispatch envelope and GitHub actor context.
- Produces: normalized executor stdin JSON, exact sudo invocation, compact Issue/Job Summary result.

- [ ] **Step 1: Write failing adapter/workflow tests**

Require an envelope with only:

```json
{
  "transport": {"issue_number": 6},
  "request": {"protocol": "MCF_WORKSPACE_MUTATION_V1"}
}
```

The test must assert:

- only `push` is accepted;
- workflow branch is exactly `codex/control-bridge-g2b`;
- path trigger is exactly `control/dispatch/g2b.json`;
- runner labels are `[self-hosted, linux, x64, node-01, mcf-control]`;
- permissions are `contents: read`, `issues: write`, and no `id-token`, packages, deployments, or broad write;
- checkout has `persist-credentials: false`;
- request fields are not interpolated into shell;
- subprocess argv is one of the four exact sudo commands;
- timeout is at most 10 minutes;
- `concurrency.cancel-in-progress` is false;
- publisher escapes Markdown and never includes content/snapshot bytes.

- [ ] **Step 2: Run adapter tests and verify RED**

```bash
python3 -m unittest tests.test_control_bridge_g2b_adapter -v
```

Expected: missing modules/workflow.

- [ ] **Step 3: Implement transport normalization**

`scripts/control_bridge_g2b.py` accepts fixed CLI flags for event path, dispatch file, request output, result output, GitHub actor login, and actor ID. It validates the envelope, adds:

```json
{
  "transport_principal": {"login": "leon337", "actor_id": 25374535}
}
```

outside the Core request, writes the executor input to a private runner-temp file, and invokes:

```python
subprocess.run(
    ["sudo", "-n", "-u", "mcf-workspace", "/usr/local/libexec/mcf-control-g2b", command],
    input=payload,
    capture_output=True,
    check=False,
    timeout=60,
    shell=False,
    env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
)
```

The command is selected only from the parsed operation mapping, never from raw text.

- [ ] **Step 4: Implement compact publication**

Publish only request ID, operation, project, relative path, status, error code, grant ID, started/finished timestamps, before/after hashes, replay flag, and receipt ID. Cap the comment below 60,000 characters and never emit content.

- [ ] **Step 5: Add the dormant pilot dispatch and workflow**

The committed dispatch example must be non-executing until its `request_id` is intentionally changed during the real pilot. Use Issue `6` as a placeholder only after verifying that Issue exists; otherwise keep `issue_number: null` and require a deliberate live edit.

- [ ] **Step 6: Run focused tests**

```bash
python3 -m unittest tests.test_control_bridge_g2b_adapter -v
python3 scripts/check_repository_secrets.py --revision HEAD
python3 scripts/validate_yaml.py
```

Expected: all pass.

- [ ] **Step 7: Commit the transport**

```bash
git add control/dispatch/g2b.json control/examples/g2b-request.example.json \
  scripts/control_bridge_g2b.py scripts/control_bridge_g2b_publish.py \
  .github/workflows/control-bridge-g2b.yml \
  tests/test_control_bridge_g2b_adapter.py
git commit -m "feat(g2b): add bounded GitHub mutation adapter"
```

---

### Task 7: Implement idempotent NODE-01 bootstrap and bounded rollback

**Files:**

- Create: `automation/ansible/roles/control_bridge_g2b/vars/main.yml`
- Create: `automation/ansible/roles/control_bridge_g2b/tasks/main.yml`
- Create: `automation/ansible/playbooks/apply-control-bridge-g2b.yml`
- Create: `automation/ansible/playbooks/rollback-control-bridge-g2b.yml`
- Create: `automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml`
- Create: `runbooks/control-bridge-g2b.md`
- Create: `tests/test_g2b_bootstrap_artifacts.py`

**Interfaces:**

- Consumes: exact repo payloads and explicit human grant timestamps.
- Produces: locked `mcf-workspace` account, protected directories, installed root-owned bundle, exact sudoers/tmpfiles, protected smoke fixture, 24-hour root-owned grant, and provenance marker.

- [ ] **Step 1: Write failing bootstrap artifact tests**

Require vars to pin every destination and SHA-256, including:

```text
/usr/local/libexec/mcf-control-g2b
/usr/local/lib/mcf-control-bridge/control_plane/g2b/*
/etc/sudoers.d/mcf-control-g2b
/etc/tmpfiles.d/mcf-control-bridge-g2b.conf
/etc/mcf-control-bridge/g2b-grant.json
/etc/mcf-control-bridge-g2b.managed
/var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev
/var/lib/mcf-control-bridge/state/g2b
/var/log/mcf-control-bridge/g2b
```

Assert account shell `/usr/sbin/nologin`, locked password, no supplementary privileged groups, root-owned non-writable parents, workspace/state ownership, `visudo -cf`, tmpfiles apply, exact bundle hashes, and refusal of preexisting unmanaged objects.

- [ ] **Step 2: Run bootstrap tests and verify RED**

```bash
python3 -m unittest tests.test_g2b_bootstrap_artifacts -v
```

Expected: missing role/playbooks.

- [ ] **Step 3: Implement prechecks and installation role**

The role must:

1. assert target hostname/machine identity through the existing inventory guards;
2. inspect every managed path without following symlinks;
3. refuse preexisting objects unless the exact external marker and installed hashes match;
4. create the locked service account and exact parents;
5. materialize a fresh smoke fixture from the reviewed repository fixture without touching the legacy home fixture;
6. install package files and entrypoint root:root, non-writable;
7. validate sudoers before atomic install;
8. install/apply tmpfiles;
9. verify `ubuntu` direct write is denied;
10. verify exact sudo status command reaches the executor as `mcf-workspace`;
11. place the provenance marker last.

Check mode must not create users, paths, grant, fixture, or marker.

- [ ] **Step 4: Implement separate grant issuance**

`issue-control-bridge-g2b-grant.yml` requires explicit non-secret extra vars:

```text
g2b_grant_id
g2b_grant_not_before
g2b_grant_not_after
g2b_executor_sha256
```

It parses UTC timestamps and asserts exactly `86400` seconds between them. It refuses an existing active or revoked grant rather than silently extending it. The rendered JSON is root:root `0644`, validated before rename, and contains only the approved pilot values.

- [ ] **Step 5: Implement bounded bootstrap rollback**

Rollback is allowed only when:

- marker and hashes prove ownership;
- grant is absent, expired, or revoked;
- no active mutation/snapshot remains;
- pilot file is absent;
- state contains no unresolved receipt;
- service account owns no process or open file;
- protected trees contain only exact baseline entries.

Remove exact leaf files and empty directories only; no recursion, glob, `find` over broad parents, `userdel -r`, or `apt autoremove`. Remove the marker last.

- [ ] **Step 6: Write the human runbook**

Document precheck, impact, exact commands, required second SSH session, direct sudo entry, grant timestamp generation, apply, idempotence, status, acceptance sequence, revoke/reissue, emergency stop, rollback gates, and explicit non-goals. Never include a real token, password, private key, or future grant ID.

- [ ] **Step 7: Run artifact and Ansible syntax tests**

```bash
python3 -m unittest tests.test_g2b_bootstrap_artifacts -v
cd automation/ansible
ansible-playbook playbooks/apply-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/rollback-control-bridge-g2b.yml --syntax-check
ansible-playbook playbooks/issue-control-bridge-g2b-grant.yml --syntax-check
```

Expected: all pass.

- [ ] **Step 8: Commit bootstrap desired state**

```bash
git add automation/ansible/roles/control_bridge_g2b \
  automation/ansible/playbooks/apply-control-bridge-g2b.yml \
  automation/ansible/playbooks/rollback-control-bridge-g2b.yml \
  automation/ansible/playbooks/issue-control-bridge-g2b-grant.yml \
  runbooks/control-bridge-g2b.md tests/test_g2b_bootstrap_artifacts.py
git commit -m "feat(g2b): add protected NODE-01 bootstrap and grant lifecycle"
```

---

### Task 8: Prove the complete lifecycle in a disposable system boundary

**Files:**

- Create: `scripts/test_control_bridge_g2b_vm.sh`
- Create: `.github/workflows/control-bridge-g2b-ci.yml`
- Create: `tests/test_g2b_disposable_integration.py`
- Create: `evidence/CONTROL-BRIDGE-G2B/README.md`

**Interfaces:**

- Consumes: exact candidate commit and all G2-B artifacts.
- Produces: sanitized proof of identity separation, direct-write denial, grant enforcement, write/replay/conflict/concurrency/rollback/revocation, and bounded cleanup.

- [ ] **Step 1: Write failing disposable-harness contract tests**

Require the harness to prove these markers in order:

```text
G2B_DISPOSABLE_IDENTITY_PASS
G2B_TRANSPORT_DIRECT_WRITE_REFUSED
G2B_GRANT_24H_PASS
G2B_WRITE_PASS
G2B_REPLAY_PASS
G2B_REQUEST_ID_CONFLICT_PASS
G2B_CONCURRENCY_PASS
G2B_AUDIT_PASS
G2B_ROLLBACK_PASS
G2B_FINAL_STATE_PASS
G2B_REVOKE_PASS
G2B_POST_REVOKE_REFUSAL_PASS
G2B_BOUNDED_CLEANUP_PASS
```

Require a disposable Ubuntu 24.04/systemd boundary, never NODE-01, with a fixed confirmation token and identity marker. Require cleanup traps and sanitized evidence even on failure.

- [ ] **Step 2: Run contract test and verify RED**

```bash
python3 -m unittest tests.test_g2b_disposable_integration -v
```

Expected: missing harness/workflow.

- [ ] **Step 3: Implement the disposable lifecycle**

Reuse existing disposable infrastructure patterns without importing or editing the frozen F1.2c KVM branch. The harness must create disposable `ubuntu` and `mcf-workspace` identities, apply the exact Ansible role, issue a fixed-time test grant, invoke the installed executor through exact sudoers, run all positive/negative tests, rollback, revoke, and remove only its named test objects.

Capture only:

```text
candidate SHA, image identity, timestamps, exit codes, status/error codes,
hashes, owners/modes, marker names, and cleanup results
```

Do not capture request content, snapshots, credentials, `/etc/shadow`, environment dumps, or unrelated host state.

- [ ] **Step 4: Add commit-bound workflow**

Pin checkout/actions by full commit SHA. Run static validation before integration. The integration job uses only a GitHub-hosted disposable runner and must be skipped rather than rerouted to NODE-01 when hosted CI is unavailable.

- [ ] **Step 5: Run the complete local static suite**

```bash
./scripts/test.sh
```

Expected: all unit/static tests pass; report optional Ansible/ShellCheck skips honestly if unavailable.

- [ ] **Step 6: Run disposable integration where the exact boundary is available**

```bash
G2B_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_UBUNTU_24_04_ONLY \
  scripts/test_control_bridge_g2b_vm.sh
```

Expected: every marker above appears once, exit `0`, no named disposable object remains.

- [ ] **Step 7: Record evidence without overclaiming hosted CI**

Update `evidence/CONTROL-BRIDGE-G2B/README.md` with exact candidate SHA, commands, counts, environment, results, and `GITHUB_HOSTED_CI=BLOCKED_EXTERNAL_BILLING` if jobs could not start. Do not label a local run as GitHub CI.

- [ ] **Step 8: Commit integration evidence**

```bash
git add scripts/test_control_bridge_g2b_vm.sh \
  .github/workflows/control-bridge-g2b-ci.yml \
  tests/test_g2b_disposable_integration.py \
  evidence/CONTROL-BRIDGE-G2B/README.md
git commit -m "test(g2b): prove bounded write lifecycle in disposable system"
```

---

### Task 9: Publish the reviewed candidate and stop at the NODE-01 human bootstrap gate

**Files:**

- Modify: `state/control-bridge-g2b.yaml`
- Modify: `CHECKPOINT.md`
- Modify: `evidence/CONTROL-BRIDGE-G2B/README.md`

**Interfaces:**

- Consumes: clean exact candidate, full local/static tests, disposable proof, reviewed diff.
- Produces: published branch/PR and a precise `WAITING_FOR_HUMAN_GATE_G2B_NODE01_BOOTSTRAP` checkpoint.

- [ ] **Step 1: Run final verification on the exact HEAD**

```bash
git status --short --branch
git diff --check
./scripts/test.sh
python3 -m unittest tests.test_g2b_disposable_integration -v
git log -1 --format='%H'
```

Expected: clean worktree, all static tests pass, contract test passes, exact SHA captured.

- [ ] **Step 2: Review scope and forbidden surfaces**

```bash
git diff --stat origin/mcf/mission-001-control-bridge-g1...HEAD
git diff --name-only origin/mcf/mission-001-control-bridge-g1...HEAD
rg -n 'docker.sock|NOPASSWD: ALL|/bin/(ba)?sh|shell=True|rm -rf|production.*true' \
  control_plane/g2b platform/control-bridge platform/sudoers \
  automation/ansible/roles/control_bridge_g2b scripts/control_bridge_g2b.py
```

Expected: only the exact sudoers `NOPASSWD` commands are present; no forbidden capability is introduced.

- [ ] **Step 3: Update pre-bootstrap checkpoint**

Set:

```yaml
status: WAITING_FOR_HUMAN_GATE_G2B_NODE01_BOOTSTRAP
evidence:
  repository_static: true
  disposable_lifecycle: true
  real_write: false
  real_rollback: false
  real_revocation: false
  mcf_effective_use: false
next_exact_step: HUMAN_REVIEW_AND_NODE01_G2B_BOOTSTRAP
```

Record exact candidate SHA and evidence command outputs in CHECKPOINT/evidence.

- [ ] **Step 4: Commit the gate checkpoint**

```bash
git add state/control-bridge-g2b.yaml CHECKPOINT.md \
  evidence/CONTROL-BRIDGE-G2B/README.md
git commit -m "checkpoint(g2b): request controlled NODE-01 bootstrap gate"
```

- [ ] **Step 5: Publish branch and open/update a draft PR**

```bash
git push -u origin codex/control-bridge-g2b
gh pr create \
  --draft \
  --base mcf/mission-001-control-bridge-g1 \
  --head codex/control-bridge-g2b \
  --title "G2-B — bounded write control bridge" \
  --body-file docs/superpowers/specs/2026-08-20-control-bridge-g2b-bounded-write-design.md
```

If a PR already exists, update it instead of creating another. Do not merge.

- [ ] **Step 6: Stop for LEANDRO intervention**

Provide:

- exact candidate SHA;
- changed-file inventory;
- static/disposable results;
- hosted CI status separated from code status;
- impact and rollback summary;
- exact runbook link;
- confirmation that F1.2c was untouched;
- the single next human action.

Do not execute NODE-01 bootstrap, grant issuance, real write, revocation, or reissuance until LEANDRO reviews the exact candidate and explicitly opens the gate.

---

### Task 10: Execute the real NODE-01 pilot after the explicit human gate

**Files:**

- Modify: `state/control-bridge-g2b.yaml`
- Modify: `CHECKPOINT.md`
- Modify: `docs/52-control-bridge-g2a-implementation-checkpoint.md`
- Create: `docs/53-control-bridge-g2b-acceptance-checkpoint.md`
- Create: `evidence/CONTROL-BRIDGE-G2B/node-01-acceptance.md`

**Interfaces:**

- Consumes: explicit LEANDRO gate, exact reviewed SHA, second SSH/recovery readiness, direct sudo entry, live self-hosted runner.
- Produces: real read/write/audit/rollback/revocation/reissue/MCF-use evidence or a fail-closed checkpoint with preserved state.

- [ ] **Step 1: Revalidate live state read-only**

Use G1/G2-A to confirm runner identity, NODE-01 hostname, essential services, legacy and protected fixture state, no existing G2-B marker/grant/lock, and no concurrent bridge mutation. Record timestamps and safe hashes only.

- [ ] **Step 2: LEANDRO performs exact bootstrap and first grant issuance**

Follow `runbooks/control-bridge-g2b.md` from the reviewed commit. LEANDRO enters sudo directly. Abort on identity drift, unmanaged path collision, existing lock, nonempty unexpected target, failed backup/recovery precheck, or changed candidate SHA.

- [ ] **Step 3: Prove post-bootstrap boundaries before mutation**

Require:

```text
runner ubuntu direct protected write = denied
mcf-workspace login = disabled
mcf-workspace privileged groups = none
generic sudo -n = denied
Docker socket access = denied
exact G2-B status command = PASS
grant interval = exactly 24h and grant active at issuance
pilot file = absent
```

- [ ] **Step 4: Dispatch the authorized write**

Change only `control/dispatch/g2b.json` with a unique request ID and approved safe content. Confirm result `PASS`, before absent, after exact hash, one local receipt, one GitHub result, and no unrelated workspace/host change.

- [ ] **Step 5: Prove replay, conflict, and concurrency**

Replay exact request and require `replayed=true` with unchanged inode/mtime. Submit changed content under the same ID and require `CONFLICT`. Submit two controlled requests and require local serialization or single-active-mutation refusal.

- [ ] **Step 6: Prove G2-A read and audit correlation**

Read `G2B-PILOT.txt` through G2-A. Compare its safe content/hash to the G2-B receipt and GitHub result. Confirm request ID, grant ID, actor, authority, project, timestamps, and hashes correlate without content in the receipt.

- [ ] **Step 7: Roll back and verify final state**

Dispatch rollback linked to the original request. Require `ROLLED_BACK`, pilot file absent, snapshot removed, linked receipt present, and G2-A final read reporting the original state.

- [ ] **Step 8: Revoke and prove refusal**

Dispatch `revoke`, require `REVOKED`, then submit a new write and require `REFUSED/grant_revoked`. Confirm the runner cannot remove the sentinel or reissue a grant.

- [ ] **Step 9: LEANDRO reissues a grant of at least 24 hours**

Use the runbook's explicit reissue path. Preserve the old revoked grant/receipt identity in evidence; do not delete or overwrite history ambiguously.

- [ ] **Step 10: MESTRE/MCF proves effective use**

MESTRE/MCF dispatches one authorized bounded operation through the reissued channel and receives the result without LEANDRO relaying stdout. Roll it back unless LEANDRO explicitly approves retaining the pilot file.

- [ ] **Step 11: Reconcile final documentation and evidence**

Only after every acceptance criterion passes, set G2-B `PASS_REAL_NODE_01_BOUNDED_WRITE` and record exact evidence. If any step fails, preserve the state, record the exact last safe checkpoint, and keep G2-B `PARTIAL` or `WAITING_FOR_HUMAN_GATE`; never infer completion.

- [ ] **Step 12: Commit and publish the acceptance checkpoint**

```bash
git add state/control-bridge-g2b.yaml CHECKPOINT.md \
  docs/52-control-bridge-g2a-implementation-checkpoint.md \
  docs/53-control-bridge-g2b-acceptance-checkpoint.md \
  evidence/CONTROL-BRIDGE-G2B/node-01-acceptance.md
git commit -m "evidence(g2b): record controlled NODE-01 write acceptance"
git push
```

Do not merge or return to F1.2c automatically. Stop for LEANDRO + MESTRE/MCF + Codex work-allocation alignment.
