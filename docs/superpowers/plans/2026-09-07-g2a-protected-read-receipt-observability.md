# G2-A Protected Read + G2-B Receipt Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let G2-A read the real protected G2-B pilot target without relaxing filesystem permissions, and publish a deterministic safe receipt correlation ID.

**Architecture:** Keep the existing unprivileged G2-A backend unchanged for normal reads. Route only `leon337/g2a-smoke/dev` `workspace.stat` and exact `workspace.read(G2B-PILOT.txt)` through a fixed root-owned reader executed as `mcf-workspace`; install that reader in a bundle root separate from the G2-B executor tree. Derive receipt IDs in the G2-B publisher only after strict result validation and only when canonical semantics imply a persisted receipt.

**Tech Stack:** Python 3.12 stdlib, `unittest`, Ansible Core 2.21.3, sudoers/`visudo`, GitHub Actions YAML.

**Spec:** `docs/superpowers/specs/2026-09-07-g2a-protected-read-receipt-observability-design.md`

## Global Constraints

- Base lineage is `c6a8206e40137f930f6a963c185c2bdc1f7c3ff2`; implementation branch is `team/g2b-task10-g2a-protected-read-receipt-20260907`.
- Protected project is exactly `leon337/g2a-smoke/dev`.
- Protected read path is exactly `G2B-PILOT.txt`; `workspace.stat` remains workspace-level.
- Runtime identity is existing locked `mcf-workspace`; do not create another service account.
- Protected installed root is `/usr/local/lib/mcf-control-bridge-g2a-protected`, separate from `/usr/local/lib/mcf-control-bridge` so the G2-B executor digest cannot drift.
- Entrypoint is exactly `/usr/local/libexec/mcf-control-g2a-protected-read`, root-owned and non-writable.
- No ACL/mode/ownership relaxation on the G2-B workspace, no generic sudo, no shell, no Docker, no package/network change, no grant/reissue, no PR #56 merge.
- No NODE-01 mutation during Tasks 1-7; live activation remains a separate LEANDRO gate after exact-head CI.

---

### Task 1: Add the specialized protected-reader core

**Files:**
- Create: `control_plane/g2a/protected_reader.py`
- Create: `tests/test_g2a_protected_reader.py`

**Interfaces:**
- Produces: `execute_protected(request_value: dict[str, Any]) -> CoreExecution` using fixed `/var/lib/mcf-control-bridge/workspaces`.
- Test-only helper: `_execute_at_root(request_value: dict[str, Any], workspace_root: Path) -> CoreExecution`; no transport/argv field can select this root.
- Produces the existing top-level G2-A result protocol; protected `workspace.read` adds safe `sha256` beside `path`, `size`, `encoding`, and `content`.

- [ ] **Step 1: Write failing protected-core tests**

```python
request = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-PROTECTED-001",
    "project": {"tenant": "leon337", "name": "g2a-smoke", "environment": "dev"},
    "operation": "workspace.read",
    "arguments": {"path": "G2B-PILOT.txt"},
}
result = PROTECTED._execute_at_root(request, root).result
self.assertEqual(result["status"], "PASS")
self.assertEqual(result["result"]["sha256"], hashlib.sha256(content).hexdigest())
```

Add cases for `workspace.stat`, missing pilot (`NOT_FOUND/path_not_found`), wrong project, every operation other than stat/read, every read path other than literal `G2B-PILOT.txt`, symlink target, hardlink (`st_nlink != 1`), wrong owner, unsafe mode, oversize, binary/non-UTF-8, and secret-like content. Capture `(dev, ino, size, mode, uid, nlink, mtime_ns, sha256)` before/after successful read and require no change.

- [ ] **Step 2: Run and confirm RED**

```bash
python3 -m unittest tests.test_g2a_protected_reader -v
```
Expected: FAIL because the protected module is absent.

- [ ] **Step 3: Implement descriptor-confined read semantics**

```python
PROTECTED_PROJECT = ProjectKey("leon337", "g2a-smoke", "dev")
PROTECTED_ROOT = pathlib.Path("/var/lib/mcf-control-bridge/workspaces")
PROTECTED_PATH = "G2B-PILOT.txt"
MAX_READ_BYTES = 65_536
SAFE_FILE_MODES = frozenset({0o600, 0o640, 0o644})

def execute_protected(request_value: dict[str, Any]) -> CoreExecution:
    return _execute_at_root(request_value, PROTECTED_ROOT)
```

Parse with existing `parse_request`. Require exact project; `workspace.stat` has empty arguments; `workspace.read` has exactly `{"path":"G2B-PILOT.txt"}`. Open the exact workspace directory with `os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)`, require owner=`os.geteuid()` and mode `0700`. Open the pilot by `dir_fd` with `O_RDONLY|O_NOFOLLOW`; require regular file, `st_nlink == 1`, owner=`os.geteuid()`, mode in `SAFE_FILE_MODES`, and size <=64 KiB. Read from that descriptor, re-`fstat` and require identity/metadata unchanged, run `control_plane.g2b.secret_policy.content_findings`, decode UTF-8, and calculate SHA-256 from the exact bytes.

Build the same top-level G2-A fields (`protocol`, request/project/operation/status/timestamps/result/error/evidence`). Use these exact failures: wrong valid project → `REFUSED/protected_project_refused`; valid but non-approved operation → `REFUSED/protected_operation_refused`; any non-literal read path → `REFUSED/protected_path_refused`; unsafe workspace descriptor/owner/mode → `REFUSED/protected_workspace_unsafe`; symlink/hardlink/wrong-owner/wrong-mode/non-regular/metadata-race target → `REFUSED/protected_target_unsafe`; oversize → `REFUSED/file_too_large`; secret-like bytes → `REFUSED/secret_like_content`; invalid UTF-8 → `REFUSED/binary_or_non_utf8`; missing pilot → `NOT_FOUND/path_not_found`; unexpected exceptions → `FAILED/internal_error`. Unknown protocol/fields still use the existing `parse_request` error codes. Do not import `control_plane.g2a.workspace`, Git modules, or repository scripts.

- [ ] **Step 4: Run focused + legacy regression tests**

```bash
python3 -m unittest tests.test_g2a_protected_reader tests.test_g2a_core tests.test_g2a_workspace tests.test_g2a_integration -v
```
Expected: PASS; legacy G2-A files remain byte-for-byte unchanged.

- [ ] **Step 5: Commit**

```bash
git add control_plane/g2a/protected_reader.py tests/test_g2a_protected_reader.py
git commit -m "feat(g2a): add descriptor-confined protected reader"
```

### Task 2: Add the isolated installed entrypoint

**Files:**
- Create: `platform/control-bridge/mcf-control-g2a-protected-read`
- Create: `tests/test_g2a_protected_installed_boundary.py`

**Interfaces:**
- Entrypoint: `/usr/local/libexec/mcf-control-g2a-protected-read` with **zero arguments**, one bounded request object on stdin, one bounded result object on stdout.
- Installed application root: `/usr/local/lib/mcf-control-bridge-g2a-protected`; no imports from checkout, site-packages, `PYTHONPATH`, or ambient cwd.

- [ ] **Step 1: Write failing installed-boundary tests**

Mirror the proven G2-B entrypoint harness but reduce capability:

```python
self.assertEqual(ENTRYPOINT.read_text().splitlines()[0], "#!/usr/bin/python3 -I")
for argv in ([str(ENTRYPOINT), "extra"], [str(ENTRYPOINT), "workspace.read"]):
    value = self.invoke(argv, valid_stdin)
    self.assertEqual(value["error"]["code"], "invalid_invocation")
```

Test: missing `mcf-workspace`, root execution, wrong effective UID, oversized/trailing stdin, malformed/non-object JSON, hostile environment, ambient module injection, symlinked installed module, import/BaseException normalization, output cap, and descriptor cleanup. Assert exactly one JSON line on stdout and empty stderr.

- [ ] **Step 2: Run and confirm RED**

```bash
python3 -m unittest tests.test_g2a_protected_installed_boundary -v
```
Expected: FAIL because the entrypoint is absent.

- [ ] **Step 3: Implement the isolated entrypoint**

Use the hardened G2-B entrypoint pattern, but accept no command argument:

```python
#!/usr/bin/python3 -I
_SERVICE_ACCOUNT = "mcf-workspace"
_INSTALLED_ROOT = Path("/usr/local/lib/mcf-control-bridge-g2a-protected")
_MAX_STDIN_BYTES = 131_072
_MAX_RESULT_BYTES = 131_072

class _BoundaryError(Exception):
    pass

def _emit_fixed_boundary_failure(code: str) -> int:
    payload = {"status": "REFUSED", "error": {"code": code}}
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    sys.stdout.buffer.write(encoded[:_MAX_RESULT_BYTES])
    return 2

def _resolve_service_uid() -> int:
    account = pwd.getpwnam("mcf-workspace")
    if account.pw_uid <= 0:
        raise _BoundaryError("root_execution_refused")
    return account.pw_uid
def _read_request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(_MAX_STDIN_BYTES + 1)
    if len(raw) > _MAX_STDIN_BYTES:
        raise _BoundaryError("stdin_too_large")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise _BoundaryError("input_must_be_object")
    return value
def _load_execute_protected() -> Callable[[dict[str, Any]], CoreExecution]:
    # validate fixed root/files, set isolated sys.path, then import exactly:
    from control_plane.g2a.protected_reader import execute_protected
    return execute_protected
def _emit_result(value: dict[str, Any]) -> int:
    encoded = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    if len(encoded) > _MAX_RESULT_BYTES:
        raise _BoundaryError("result_too_large")
    sys.stdout.buffer.write(encoded)
    return 0

def main() -> int:
    if len(sys.argv) != 1:
        return _emit_fixed_boundary_failure("invalid_invocation")
    expected_uid = _resolve_service_uid()
    if expected_uid == 0 or os.geteuid() == 0:
        return _emit_fixed_boundary_failure("root_execution_refused")
    if os.geteuid() != expected_uid:
        return _emit_fixed_boundary_failure("execution_uid_mismatch")
    request = _read_request()
    execute_protected = _load_execute_protected()
    return _emit_result(execute_protected(request).result)
```

Clear the environment before importing application code, set `sys.path` only to the installed root, refuse symlinks/non-regular installed files, redirect any import/core writes to `/dev/null`, and normalize every escaped `BaseException` to one fixed content-free failure result.

- [ ] **Step 4: Run installed-boundary tests**

```bash
python3 -m unittest tests.test_g2a_protected_installed_boundary tests.test_g2a_protected_reader -v
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add platform/control-bridge/mcf-control-g2a-protected-read \
  tests/test_g2a_protected_installed_boundary.py
git commit -m "feat(g2a): add isolated protected reader entrypoint"
```

### Task 3: Route the GitHub G2-A adapter through the protected boundary

**Files:**
- Modify: `scripts/control_bridge_g2a.py`
- Modify: `tests/test_control_bridge_g2a_adapter.py`

**Interfaces:**
- Add `_is_protected_request(request: CoreRequest) -> bool` with no caller-selectable backend field.
- Add `run_bounded_process(argv: list[str], payload: bytes, *, timeout_seconds: float) -> ProcessOutcome` using the proven G2-B drain/terminate/reap pattern.
- Add `_execute_protected(request: dict[str, Any]) -> CoreExecution` using the one fixed sudo argv.
- Add `execute_selected(request_value: dict[str, Any], *, manifest_root: pathlib.Path, workspace_root: pathlib.Path) -> CoreExecution`; it parses once, routes protected requests to `_execute_protected`, and passes every other request to existing `execute(request_value, manifest_root=manifest_root, workspace_root=workspace_root)`.

- [ ] **Step 1: Write failing adapter-routing tests**

```python
protected = dict(VALID_REQUEST,
    project={"tenant":"leon337","name":"g2a-smoke","environment":"dev"},
    operation="workspace.read", arguments={"path":"G2B-PILOT.txt"})
with patch.object(ADAPTER, "run_bounded_process", return_value=outcome) as invoked:
    execution = ADAPTER.execute_selected(
        protected,
        manifest_root=ROOT / "platform/manifests",
        workspace_root=pathlib.Path(temporary) / "workspaces",
    )
invoked.assert_called_once()
self.assertEqual(invoked.call_args.args[0], [
    "sudo", "-n", "-u", "mcf-workspace",
    "/usr/local/libexec/mcf-control-g2a-protected-read",
])
```

Prove ordinary project/Git/workspace requests still call the existing unprivileged Core and never sudo. Prove fields named `backend`, `workspace_root`, `sudo`, `uid`, `cwd`, or `executable` are rejected by the existing protocol before subprocess selection.

- [ ] **Step 2: Add strict protected-result validation tests**

For a PASS `workspace.read`, require exact top-level G2-A fields, request/project/operation correlation, `path == G2B-PILOT.txt`, `encoding == utf-8`, size <= 65536, 64-lowercase-hex SHA-256, `sha256 == sha256(content.encode('utf-8'))`, and no secret-like content. For `NOT_FOUND`, require `{}` result and exact `path_not_found`. Reject extra fields, mismatched IDs/projects, malformed timestamps, raw stderr, oversized output, timeout, and nonzero exit.

- [ ] **Step 3: Run focused adapter tests and confirm RED**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter -v
```
Expected: new routing/validation cases fail.

- [ ] **Step 4: Implement protected subprocess selection**

```python
_PROTECTED_EXECUTOR = "/usr/local/libexec/mcf-control-g2a-protected-read"
_PROTECTED_ENV = {"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"}
_PROTECTED_PROJECT = ProjectKey("leon337", "g2a-smoke", "dev")

def _is_protected_request(parsed: CoreRequest) -> bool:
    return parsed.project == _PROTECTED_PROJECT and parsed.operation in {"workspace.stat", "workspace.read"}
```

Encode only the validated core request, never transport metadata. Use the fixed argv above, `shell=False`, `start_new_session=True`, `close_fds=True`, max 15 seconds, bounded stdin/stdout/stderr, and terminate→kill→reap on timeout/overflow. Validate returned JSON independently before constructing `CoreExecution`; map transport failures to bounded G2-A `TIMEOUT/operation_timeout` or `FAILED/protected_reader_failed` without raw subprocess text.

- [ ] **Step 5: Run adapter + integration tests**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter tests.test_g2a_integration -v
```
Expected: PASS and existing unprivileged behavior unchanged.

- [ ] **Step 6: Commit**

```bash
git add scripts/control_bridge_g2a.py tests/test_control_bridge_g2a_adapter.py
git commit -m "feat(g2a): route protected reads through fixed boundary"
```

### Task 4: Install the protected reader with exact Ansible/sudoers boundaries

**Files:**
- Create: `platform/sudoers/mcf-control-g2a-protected-read`
- Create: `automation/ansible/roles/control_bridge_g2a_protected_read/vars/main.yml`
- Create: `automation/ansible/roles/control_bridge_g2a_protected_read/tasks/main.yml`
- Create: `automation/ansible/playbooks/apply-control-bridge-g2a-protected-read.yml`
- Create: `tests/test_g2a_protected_bootstrap_artifacts.py`

**Interfaces:**
- Own marker: `/etc/mcf-control-g2a-protected-read.managed`.
- Own install lock: `/run/lock/mcf-control-g2a-protected-read-install`.
- Own bundle root: `/usr/local/lib/mcf-control-bridge-g2a-protected`.
- Own sudoers fragment: `/etc/sudoers.d/mcf-control-g2a-protected-read`.

- [ ] **Step 1: Write failing artifact tests**

Require an immutable source→destination→SHA inventory containing only:

```text
control_plane/__init__.py
control_plane/g2a/__init__.py
control_plane/g2a/errors.py
control_plane/g2a/protocol.py
control_plane/g2a/protected_reader.py
control_plane/g2b/__init__.py
control_plane/g2b/secret_policy.py
platform/control-bridge/mcf-control-g2a-protected-read
platform/sudoers/mcf-control-g2a-protected-read
```

Test that none target `/usr/local/lib/mcf-control-bridge`, no grant/state/runtime-lock file is managed, and every installed bundle file is root-owned/non-writable.

Require exact sudoers semantics:

```text
Cmnd_Alias MCF_G2A_PROTECTED_READ = /usr/local/libexec/mcf-control-g2a-protected-read ""
ubuntu ALL=(mcf-workspace) NOPASSWD: MCF_G2A_PROTECTED_READ
```

The `""` argument constraint is mandatory so sudoers permits **zero arguments only**.

- [ ] **Step 2: Run artifact test and confirm RED**

```bash
python3 -m unittest tests.test_g2a_protected_bootstrap_artifacts -v
```
Expected: FAIL because the role/playbook/sudoers do not exist.

- [ ] **Step 3: Implement immutable vars and apply role**

The role must fail closed unless the existing G2-B marker and `mcf-workspace` identity are exact, the protected project workspace is an unlinked real directory owned `mcf-workspace:mcf-workspace` mode `0700`, and the existing protected `README.md` fixture is a regular single-link `mcf-workspace` file with its reviewed mode/hash. Source hashes are computed in the plan execution and pinned literally in role vars. The role may reuse `/usr/local/libexec` only if `root:root 0755`; its own bundle root/entrypoint/sudoers/marker must be absent unless its exact marker already exists.

Install files with `copy`, validate sudoers atomically with `/usr/sbin/visudo -cf %s`, and place the protected-reader marker last. Never modify the G2-B marker, grant, workspace owner/mode, G2-B installed root, state tree, or revocation files.

Post-install probes executed as `ubuntu` must prove:

```text
test ! -r /var/lib/mcf-control-bridge/workspaces/leon337/g2a-smoke/dev/README.md
sudo -n true                                  => denied
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2a-protected-read extra  => denied
sudo -n -u mcf-workspace /usr/local/libexec/mcf-control-g2a-protected-read        => reaches bounded workspace.stat
```

The probe stdin contains only a fixed safe G2-A `workspace.stat` request. Additional non-mutating role probes must require `mcf-workspace` shell `/usr/sbin/nologin`, group list exactly `[mcf-workspace]`, no intersection with `platform_foundation_privileged_groups`, and no read/write access to `/var/run/docker.sock` when that socket exists.

- [ ] **Step 4: Run artifact + syntax tests**

```bash
python3 -m unittest tests.test_g2a_protected_bootstrap_artifacts -v
cd automation/ansible
~/.cache/mcf/g2b-task9-venv-2.21.3/bin/ansible-playbook \
  playbooks/apply-control-bridge-g2a-protected-read.yml --syntax-check
```
Expected: PASS. Do not run the playbook against NODE-01.

- [ ] **Step 5: Commit**

```bash
git add platform/sudoers/mcf-control-g2a-protected-read \
  automation/ansible/roles/control_bridge_g2a_protected_read \
  automation/ansible/playbooks/apply-control-bridge-g2a-protected-read.yml \
  tests/test_g2a_protected_bootstrap_artifacts.py
git commit -m "feat(g2a): add protected reader install boundary"
```

### Task 5: Add bounded rollback, runbook, and disposable cross-lifecycle

**Files:**
- Create: `automation/ansible/playbooks/rollback-control-bridge-g2a-protected-read.yml`
- Create: `runbooks/control-bridge-g2a-protected-read.md`
- Create: `scripts/test_control_bridge_g2a_protected_vm.sh`
- Create: `.github/workflows/control-bridge-g2a-protected-ci.yml`
- Create: `tests/test_g2a_protected_disposable_integration.py`
- Modify: `tests/test_g2a_protected_bootstrap_artifacts.py`

**Interfaces:**
- Rollback removes only this slice's marker, sudoers, entrypoint, exact bundle files/directories, and install lock if owned by the current operation; it never recursively deletes shared/G2-B paths.
- Disposable harness requires exactly `G2A_PROTECTED_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_UBUNTU_24_04_ONLY` and `G2A_PROTECTED_CANDIDATE_SHA` matching `^[0-9a-f]{40}$`, refuses NODE-01, and runs only in an isolated systemd container with `--network none`.

- [ ] **Step 1: Write failing rollback and harness-contract tests**

Extend artifact tests to require exact rollback gates. Add `tests/test_g2a_protected_disposable_integration.py` that asserts the harness/workflow contain ordered markers and safety guards:

```python
markers = [
    "G2A_PROTECTED_G2B_BASELINE_PASS",
    "G2A_PROTECTED_APPLY_PASS",
    "G2A_PROTECTED_IDEMPOTENCE_PASS",
    "G2A_PROTECTED_DIRECT_READ_REFUSED",
    "G2A_PROTECTED_ABSENT_PASS",
    "G2A_PROTECTED_CROSS_READ_PASS",
    "G2A_PROTECTED_G2B_ROLLBACK_PASS",
    "G2A_PROTECTED_FINAL_ABSENT_PASS",
    "G2A_PROTECTED_CLEANUP_PASS",
]
for marker in markers:
    self.assertIn(marker, harness_text)
self.assertIn("runs-on: ubuntu-24.04", workflow_text)
self.assertNotIn("self-hosted", workflow_text)
```

Also assert the harness requires the exact confirmation/SHA, refuses hostnames `node-01`/`vmi3506102`, copies an explicit allowlist only, uses `--network none`, and never accepts a target host argument.

- [ ] **Step 2: Run and confirm RED**

```bash
python3 -m unittest \
  tests.test_g2a_protected_bootstrap_artifacts \
  tests.test_g2a_protected_disposable_integration -v
```
Expected: FAIL because rollback/harness/workflow are absent.

- [ ] **Step 3: Implement bounded rollback + runbook**

The rollback playbook imports `controller-preflight.yml`, validates exact NODE-01/disposable identity, G2-B coexistence, protected marker, payload hashes, account boundary, no active reader process/open file, and no unexpected object under its private bundle root. Delete each reviewed file explicitly, remove now-empty private directories with `rmdir`, and remove `/etc/mcf-control-g2a-protected-read.managed` last.

The runbook documents:

```text
read-only precheck -> exact-head CI -> --check -> recovery SSH -> LEANDRO gate
-> apply 1 -> apply 2 changed=0 -> protected NOT_FOUND proof
-> later separate G2-B reissue/write gate -> G2-A read/hash proof
-> G2-B rollback -> G2-A NOT_FOUND -> optional protected-reader rollback
```

Explicitly prohibit package install, permission relaxation, grant/reissue, and NODE-01 execution during implementation validation.

- [ ] **Step 4: Implement the disposable cross-lifecycle harness and hosted workflow**

Follow the existing `scripts/test_control_bridge_g2b_vm.sh` fixture pattern. Build a temporary allowlisted repository bundle, start the existing Ubuntu 24.04 systemd fixture as a privileged container with cgroup namespace isolation and `--network none`, and create `ubuntu` only inside that disposable container.

Within the container, execute in this exact order:

1. apply existing G2-B bootstrap twice to establish the protected workspace/account baseline;
2. apply the new protected-reader playbook once; capture a second real apply with `ANSIBLE_NOCOLOR=1` and require the `node-01` recap has `changed=0`, `unreachable=0`, `failed=0`;
3. prove `ubuntu` cannot read protected `README.md`, generic `sudo -n true` fails, and extra reader argv is denied;
4. invoke exact protected `workspace.read(G2B-PILOT.txt)` and require `NOT_FOUND/path_not_found`;
5. issue a disposable-only 24h G2-B grant, execute one safe G2-B write, capture its `after.sha256`;
6. invoke installed G2-A protected reader through exact sudo, require `PASS`, exact safe content, and `result.sha256 == G2-B after.sha256`;
7. rollback the G2-B write through the G2-B executor and require `ROLLED_BACK`;
8. repeat protected read and require `NOT_FOUND/path_not_found`;
9. run protected-reader rollback, prove its marker/sudoers/entrypoint/private bundle are absent while the G2-B marker/account/workspace remain intact.

No real NODE-01 address/key/inventory may be used. Cleanup always force-removes only the uniquely named disposable container/image/temp directory.

Create `.github/workflows/control-bridge-g2a-protected-ci.yml` with `pull_request:` and `workflow_dispatch:`, `permissions: contents: read`, `runs-on: ubuntu-24.04`, `actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`, and one disposable job invoking:

```bash
G2A_PROTECTED_TEST_PRIVILEGED_CONFIRM=DISPOSABLE_UBUNTU_24_04_ONLY \
G2A_PROTECTED_CANDIDATE_SHA="$GITHUB_SHA" \
  scripts/test_control_bridge_g2a_protected_vm.sh
```

- [ ] **Step 5: Run rollback syntax, contract tests, and local shell syntax**

```bash
python3 -m unittest \
  tests.test_g2a_protected_bootstrap_artifacts \
  tests.test_g2a_protected_disposable_integration -v
bash -n scripts/test_control_bridge_g2a_protected_vm.sh
cd automation/ansible
~/.cache/mcf/g2b-task9-venv-2.21.3/bin/ansible-playbook \
  playbooks/rollback-control-bridge-g2a-protected-read.yml --syntax-check
```
Expected: PASS. Running the privileged disposable harness locally is optional; hosted exact-head CI is mandatory before Task 7 closes. Never point this harness at NODE-01.

- [ ] **Step 6: Commit**

```bash
git add automation/ansible/playbooks/rollback-control-bridge-g2a-protected-read.yml \
  runbooks/control-bridge-g2a-protected-read.md \
  scripts/test_control_bridge_g2a_protected_vm.sh \
  .github/workflows/control-bridge-g2a-protected-ci.yml \
  tests/test_g2a_protected_bootstrap_artifacts.py \
  tests/test_g2a_protected_disposable_integration.py
git commit -m "test(g2a): prove protected reader disposable lifecycle"
```

### Task 6: Publish a deterministic G2-B receipt correlation ID

**Files:**
- Modify: `scripts/control_bridge_g2b_publish.py`
- Modify: `tests/test_control_bridge_g2b_adapter.py`
- Modify: `tests/test_g2b_executor.py` (test-only correlation guard; executor code remains unchanged)

**Interfaces:**
- Add `_receipt_id(request_id: str) -> str` returning lowercase SHA-256 hex.
- Populate public `receipt_id` only after `_valid_full_result(result, expected)` succeeds **and** canonical semantics imply persistence: successful terminal statuses (`PASS`, `ROLLED_BACK`, `REVOKED`) or `replayed is True`.
- Keep `receipt_id=None` for adapter-local results and transient non-persisted refusals/conflicts/timeouts.

- [ ] **Step 1: Write failing publisher tests**

```python
expected = hashlib.sha256("G2B-ADAPTER-0001".encode("utf-8")).hexdigest()
body = PUBLISH.markdown(envelope(), executor_result())
self.assertIn(f"receipt ID: {expected}", body)
```

Add a test-only storage correlation using the existing G2BExecutor fixture: execute a persisted successful request with `request_id = G2B-RECEIPT-ID-CORRELATION`, compute `expected = sha256(request_id)`, and require `(self.state_root / "receipts" / f"{expected}.json").is_file()`. This locks public derivation to the actual private filename algorithm without modifying `control_plane/g2b/state.py`.

Also require: replay publishes the same ID; rollback/revoke success publish IDs derived from their own request IDs; `grant_missing`, `request_id_conflict`, `grant_revoked`, timeout, malformed full result, and adapter-local failure render `receipt ID: none`. Mutating dispatch/result with a forged `receipt_id` must not control the published value.

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
python3 -m unittest tests.test_control_bridge_g2b_adapter -v
```
Expected: receipt-observability assertions fail while existing validator tests stay green.

- [ ] **Step 3: Implement derivation after strict validation**

```python
def _receipt_id(request_id: str) -> str:
    return hashlib.sha256(request_id.encode("utf-8")).hexdigest()

persisted = result["status"] in _SUCCESS_STATUSES or result["replayed"] is True
receipt_id = _receipt_id(result["request_id"]) if persisted else None
```

Apply this only inside the `_valid_full_result` branch of `_projection`; never read it from the executor result, dispatch, transport, environment, or GitHub payload.

- [ ] **Step 4: Run publisher/core cross-product tests**

```bash
python3 -m unittest tests.test_control_bridge_g2b_adapter tests.test_g2b_state tests.test_g2b_executor -v
```
Expected: PASS; executor result schema remains exactly 21 fields and unchanged.

- [ ] **Step 5: Commit**

```bash
git add scripts/control_bridge_g2b_publish.py tests/test_control_bridge_g2b_adapter.py tests/test_g2b_executor.py
git commit -m "feat(g2b): publish deterministic receipt correlation id"
```

### Task 7: Final repository validation, documentation state, and Draft PR

**Files:**
- Verify: `docs/superpowers/specs/2026-09-07-g2a-protected-read-receipt-observability-design.md` already records `SPEC_APPROVED`.
- Keep all implementation files from Tasks 1-6.

**Interfaces:**
- Produces one exact implementation HEAD with complete local evidence and a Draft PR; does not activate NODE-01.

- [ ] **Step 1: Verify the approved spec metadata is already current**

Require:
```text
**Status:** SPEC_APPROVED
```
If it is not current, stop and reconcile documentation before validating implementation; do not silently rewrite spec semantics during the implementation closeout.

- [ ] **Step 2: Run the complete local gate**

From repository root:

```bash
git diff --check
PYTHON=python3 REQUIRE_ANSIBLE=1 scripts/test.sh
python3 -m unittest
```

Use the existing Ansible 2.21.3 venv on PATH for `REQUIRE_ANSIBLE=1`. Expected: Secret Policy PASS, continuity/state PASS, all unit tests PASS, all playbook syntax checks PASS, shell syntax PASS. If `shellcheck` is unavailable locally, do not install it; require hosted CI to execute the pinned ShellCheck path before acceptance.

- [ ] **Step 3: Verify forbidden drift explicitly**

```bash
git diff c6a8206e40137f930f6a963c185c2bdc1f7c3ff2 -- \
  control_plane/g2b/executor.py control_plane/g2b/grant.py \
  platform/control-bridge/mcf-control-g2b \
  automation/ansible/roles/control_bridge_g2b/vars/main.yml
```

Expected: no unintended G2-B executor/grant/bundle-root changes. Confirm PR #56 remains open, Draft, unmerged.

- [ ] **Step 4: Push and open/update a Draft PR**

```bash
git push -u origin team/g2b-task10-g2a-protected-read-receipt-20260907
```

Create a **stacked Draft / DO NOT MERGE** PR against exact base `team/g2b-task9-prebootstrap-gate-20260907`, whose head must still be `c6a8206e40137f930f6a963c185c2bdc1f7c3ff2` when the PR is opened. Do not retarget or modify PR #56. Its body must state: no NODE-01 apply, no grant/reissue, no PR #56 merge, and activation requires a fresh LEANDRO gate after exact-head CI.

- [ ] **Step 5: Qualify hosted exact-head CI**

First require the normal stacked-PR hosted checks. Then use `workflow_dispatch` on the literal final implementation SHA for `foundation-ci`, `control-bridge-g2b-ci`, and `control-bridge-g2a-protected-ci`; require each run to check out that exact SHA. These runs must exercise repository validation, G2-A adapter tests, G2-B publisher tests, Ansible syntax, secret policy, required ShellCheck, and the protected-reader disposable lifecycle. Record exact HEAD and run/job IDs. Do not call the implementation `PASS_REAL_NODE_01` from CI alone.

- [ ] **Step 6: Stop at the activation gate**

Required checkpoint:

```text
IMPLEMENTATION_CODE=CI_QUALIFIED
NODE01_PROTECTED_READER=NOT_APPLIED
G2B_GRANT=REVOKED_NO_REISSUE
G2A_CROSS_READ=NOT_YET_LIVE_PROVEN
NEXT=LEANDRO_HUMAN_GATE_FOR_NODE01_PROTECTED_READER_CHECK_MODE_AND_APPLY
```

No check-mode, apply, reissue, write, rollback, or live dispatch begins without that next explicit human authorization.

---

## Plan self-review checklist

- Every spec security invariant maps to a task/test above.
- Installed reader bundle is separate from the G2-B digest root.
- No transport field selects backend/root/UID/executable.
- Receipt ID is a derived correlation identifier, not a caller-controlled field or proof of persistence for transient results.
- TDD precedes implementation in every code-bearing task.
- Rollback is explicit and non-recursive.
- Live NODE-01 activation is outside this implementation plan's automatic execution boundary.