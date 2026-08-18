# Control Bridge G2-A Read-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved G2-A read-only Workspace Core so agents can inspect local project workspaces on NODE-01 through GitHub without shell, sudo, Docker, writes, clone/materialization, or a second project registry.

**Architecture:** GitHub transport stays outside the Core. The Core validates a transport-neutral request, resolves `tenant/name/environment` through existing validated Project manifests, maps that identity into the transitional workspace root `/home/ubuntu/mcf-workspaces`, confines filesystem access after symlink/realpath resolution, executes exactly nine read-only capabilities, and returns a structured result. The GitHub adapter owns Issue/run metadata, summaries, and optional Actions Artifacts.

**Tech Stack:** Python 3.12, existing `PyYAML==6.0.3` and `jsonschema==4.26.0`, strict YAML loader, Git CLI, `unittest`, GitHub Actions self-hosted runner `node-01+mcf-control`.

**Spec:** `docs/51-control-bridge-g2a-design.md`

## Global Constraints

- G2-A is read-only. No `workspace.write`, `mkdir`, `delete`, Git mutation, clone, provisioning, shell, sudo, Docker, systemd mutation, network mutation, APT/system package management, secrets administration, deploy, backup/rollback, or production action.
- Core protocol: `MCF_WORKSPACE_CONTROL_V1`; result protocol: `MCF_WORKSPACE_CONTROL_RESULT_V1`.
- Core request fields are exactly `protocol`, `request_id`, `project`, `operation`, and `arguments`; GitHub Issue/run/event metadata never enters the Core request/result.
- Project identity/desired state comes only from validated `platform/manifests/**/*.yaml`; no `registry.json`, SQLite, or parallel project database.
- Files under `platform/manifests/examples/` remain validation fixtures/documentation and are **not** runtime project registrations.
- Transitional workspace root: `/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>`.
- Core operations are exactly: `project.list`, `project.get`, `workspace.stat`, `workspace.list`, `workspace.read`, `git.status`, `git.branch`, `git.head`, `git.diff`.
- `workspace.list`: one directory level, sorted, maximum 500 direct entries.
- `workspace.read`: UTF-8 text only, maximum 65,536 bytes inline. Larger -> `REFUSED/file_too_large`; invalid UTF-8 -> `REFUSED/binary_or_non_utf8`.
- `git.status`: maximum captured stdout 262,144 bytes; larger -> `REFUSED/git_status_too_large`.
- `git.diff`: maximum captured output 1,048,576 bytes. Up to 131,072 bytes inline; 131,073..1,048,576 bytes -> generic attachment for the GitHub adapter; above 1,048,576 -> `REFUSED/diff_too_large`.
- Subprocess timeout: 15 seconds. Timeout -> Core `TIMEOUT`.
- `workspace.read` and `git.diff` fail closed on paths/content matching the existing repository secret policy. `.git/**`, `credentials.json`, `credentials.yaml`, and `credentials.yml` are additionally refused. `.env.example` remains allowed by the existing policy.
- Filesystem confinement is based on resolved paths/ancestry, not only string filtering. Absolute paths, `~`, `..` escape, workspace symlink roots, symlink escape, and cross-project escape fail closed.
- Git inspection must reject a repository whose resolved Git directory escapes the selected workspace. Linked worktrees with an external gitdir are therefore out of G2-A bootstrap scope.
- Git commands disable optional locks, user/system config influence where practical, fsmonitor hooks, external diff, textconv, and color. No request supplies argv.
- G2-A has no persistent dedupe store and no local lock manager. `request_id` is correlation only.
- The first real G2-A workflow is push-bootstrap-only. No Issue-triggered command bus is activated by this plan.
- **The implementation commit must not create `control/dispatch/g2a.json`.** The live dispatch file is created only after exact-head CI is green and LEANDRO authorizes the separate real execution gate.
- Production remains unauthorized. PR #3 remains draft and is not merged by this plan.

---

### Task 1: Expose the existing manifest validator as a reusable catalog

**Files:**
- Modify: `scripts/validate_manifests.py`
- Create: `tests/test_manifest_catalog.py`

**Interfaces:**
- Produces: `ValidatedManifest(path: pathlib.Path, value: dict[str, Any])`
- Produces: `ManifestValidationError(failures: list[str])`
- Produces: `load_validated_manifests(manifest_directory: pathlib.Path = MANIFEST_DIRECTORY) -> list[ValidatedManifest]`
- Produces: `project_key(manifest: dict[str, Any]) -> tuple[str, str, str]`
- Existing CLI behavior remains `MANIFEST_VALIDATION_PASS/FAIL`.

- [ ] **Step 1: Write failing catalog tests**

Create two valid temporary Project YAML files and assert:

```python
records = MODULE.load_validated_manifests(temp_root)
self.assertEqual(
    [MODULE.project_key(r.value) for r in records],
    [("tenant-a", "project-a", "dev"), ("tenant-b", "project-b", "staging")],
)
self.assertTrue(all(r.path.is_absolute() for r in records))
```

Add an invalid/duplicate-key manifest and assert `ManifestValidationError`; its message may contain the relative path and validation reason but not raw secret values.

- [ ] **Step 2: Verify the tests fail**

```bash
python3 -m unittest tests.test_manifest_catalog -v
```

Expected: FAIL because the reusable types/functions do not exist.

- [ ] **Step 3: Make `yaml_strict` import work both as CLI and imported module**

Replace the current import with:

```python
try:
    from .yaml_strict import load_strict
except ImportError:  # direct execution: python3 scripts/validate_manifests.py
    from yaml_strict import load_strict
```

- [ ] **Step 4: Add the reusable types/functions and move existing validation through them**

Add:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class ValidatedManifest:
    path: pathlib.Path
    value: dict[str, Any]

class ManifestValidationError(ValueError):
    def __init__(self, failures: list[str]):
        self.failures = tuple(failures)
        super().__init__("; ".join(failures))

def project_key(manifest: dict[str, Any]) -> tuple[str, str, str]:
    metadata = manifest["metadata"]
    return metadata["tenant"], metadata["name"], metadata["environment"]
```

`load_validated_manifests()` must execute the same schema loading, strict YAML loading, JSON Schema validation, and `semantic_checks()` currently performed by `main()`. It returns `ValidatedManifest(path.resolve(), manifest)` only if the whole catalog validates; otherwise it raises `ManifestValidationError(failures)`. `main()` calls it and preserves current CLI output.

- [ ] **Step 5: Run catalog + existing validation**

```bash
python3 -m unittest tests.test_manifest_catalog tests.test_manifest_negative_cases -v
python3 scripts/validate_manifests.py
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate_manifests.py tests/test_manifest_catalog.py
git commit -m "refactor(g2a): expose validated manifest catalog"
```

---

### Task 2: Add transport-neutral protocol and error types

**Files:**
- Create: `control_plane/__init__.py`
- Create: `control_plane/g2a/__init__.py`
- Create: `control_plane/g2a/protocol.py`
- Create: `control_plane/g2a/errors.py`
- Create: `tests/test_g2a_protocol.py`
- Modify: `scripts/test.sh`

**Interfaces:**
- `ProjectKey(tenant: str, name: str, environment: str)`
- `CoreRequest(protocol: str, request_id: str, project: ProjectKey, operation: str, arguments: dict[str, Any])`
- `Attachment(name: str, media_type: str, content: bytes)`
- `CoreExecution(result: dict[str, Any], attachment: Attachment | None)`
- `G2AError(code: str, status: str)` plus `RefusedError`, `NotFoundError`, `OperationTimeout`
- `parse_request(value: dict[str, Any]) -> CoreRequest`

- [ ] **Step 1: Write failing strict-protocol tests**

```python
VALID = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-000001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "git.status",
    "arguments": {},
}
request = MODULE.parse_request(VALID)
self.assertEqual(request.project, MODULE.ProjectKey("tenant-a", "project-a", "dev"))
```

For each of `issue_number`, `cwd`, `argv`, `command`, `workspace`, add it as a top-level field and require `RefusedError("unexpected_request_field")`. Also reject unknown operations, `request_id` empty/>128 chars, unknown project keys, and environment outside `dev|staging`.

- [ ] **Step 2: Verify failure**

```bash
python3 -m unittest tests.test_g2a_protocol -v
```

- [ ] **Step 3: Implement immutable dataclasses and exact operation allowlist**

```python
OPERATIONS = frozenset({
    "project.list", "project.get", "workspace.stat", "workspace.list",
    "workspace.read", "git.status", "git.branch", "git.head", "git.diff",
})
```

Use `@dataclass(frozen=True)`. Do not add a generic execution/argv field.

- [ ] **Step 4: Extend compile coverage**

Change `scripts/test.sh` compile step to:

```bash
"$PYTHON" -m compileall -q scripts tests control_plane
```

- [ ] **Step 5: Run tests/full suite and commit**

```bash
python3 -m unittest tests.test_g2a_protocol -v
scripts/test.sh
git add control_plane scripts/test.sh tests/test_g2a_protocol.py
git commit -m "feat(g2a): add transport-neutral core protocol"
```

---

### Task 3: Resolve runtime Projects from validated manifests without a registry

**Files:**
- Create: `control_plane/g2a/projects.py`
- Create: `tests/test_g2a_projects.py`

**Interfaces:**
- Consumes: `ValidatedManifest`, `load_validated_manifests`, `ProjectKey`
- `ProjectRecord(key: ProjectKey, manifest_path: pathlib.Path, manifest: dict[str, Any])`
- `ProjectResolver.list() -> list[ProjectRecord]`
- `ProjectResolver.get(key: ProjectKey) -> ProjectRecord`
- `workspace_path(workspace_root: pathlib.Path, key: ProjectKey) -> pathlib.Path`
- `project_public_view(record: ProjectRecord) -> dict[str, Any]`

- [ ] **Step 1: Write failing multi-project tests**

Build a temporary catalog containing `examples/project.example.yaml`, `project-a.yaml`, and `project-b.yaml`. Require:

```python
self.assertEqual(
    [r.key for r in resolver.list()],
    [ProjectKey("tenant-a", "project-a", "dev"), ProjectKey("tenant-b", "project-b", "staging")],
)
```

The `examples/` record must validate but not appear in the runtime list. Duplicate logical keys must raise `RefusedError("duplicate_project_key")`. Changing `spec.capabilities` must not deny G2-A inspection.

- [ ] **Step 2: Verify failure**

```bash
python3 -m unittest tests.test_g2a_projects -v
```

- [ ] **Step 3: Implement the resolver as a view over the canonical catalog**

Filter runtime Project records with:

```python
relative = record.path.relative_to(manifest_root.resolve())
if relative.parts and relative.parts[0] == "examples":
    continue
if record.value.get("kind") != "Project":
    continue
```

Sort by `(tenant, name, environment)`. `get()` raises `NotFoundError("project_not_found")`.

`project_public_view()` omits `secretRefs` entirely. It may return only identity, criticality, source repository/revision, persistence booleans, sandbox limits/network profile, preview enabled, and production gate state.

- [ ] **Step 4: Implement deterministic workspace mapping**

```python
def workspace_path(root: pathlib.Path, key: ProjectKey) -> pathlib.Path:
    return root / key.tenant / key.name / key.environment
```

This function does not create directories.

- [ ] **Step 5: Run suite and commit**

```bash
python3 -m unittest tests.test_g2a_projects -v
scripts/test.sh
git add control_plane/g2a/projects.py tests/test_g2a_projects.py
git commit -m "feat(g2a): resolve projects from canonical manifests"
```

---

### Task 4: Implement workspace confinement, sensitive-content refusal, and bounded reads

**Files:**
- Create: `control_plane/g2a/workspace.py`
- Create: `tests/test_g2a_workspace.py`

**Interfaces:**
- `resolve_confined(workspace: pathlib.Path, relative_path: str) -> pathlib.Path`
- `workspace_stat(workspace: pathlib.Path) -> dict[str, Any]`
- `workspace_list(workspace: pathlib.Path, relative_path: str = ".") -> dict[str, Any]`
- `workspace_read(workspace: pathlib.Path, relative_path: str) -> dict[str, Any]`

- [ ] **Step 1: Write failing path-confinement tests**

Require refusal for absolute paths, `~`, traversal, symlink root, and symlink/cross-project escape:

```python
with self.assertRaisesRegex(RefusedError, "absolute_path_refused"):
    resolve_confined(project_a, "/etc/passwd")
with self.assertRaisesRegex(RefusedError, "path_escape_refused"):
    resolve_confined(project_a, "../project-b/private.txt")
```

A symlink inside A targeting B must also produce `path_escape_refused`; an internal symlink to a file still inside A may resolve successfully.

- [ ] **Step 2: Write failing size/encoding/sensitive-data tests**

Require:

```text
65,536 UTF-8 bytes -> PASS
65,537 bytes -> REFUSED/file_too_large
invalid UTF-8 -> REFUSED/binary_or_non_utf8
501 direct entries -> REFUSED/list_entry_limit
```

Paths `.git/config`, `.env`, `secrets/token.txt`, `credentials.json`, `credentials.yaml`, `credentials.yml`, `id_ed25519`, and `certificate.key` must be refused. `.env.example` must remain allowed.

Create a normal-looking `notes.txt` containing synthetic `password=abcdefghijk` and require `REFUSED/secret_like_content`; no secret-like bytes may appear in the exception/result.

- [ ] **Step 3: Verify failure**

```bash
python3 -m unittest tests.test_g2a_workspace -v
```

- [ ] **Step 4: Implement confinement**

Rules:

```python
raw = pathlib.PurePath(relative_path)
if pathlib.Path(relative_path).is_absolute():
    raise RefusedError("absolute_path_refused")
if relative_path.startswith("~"):
    raise RefusedError("tilde_path_refused")
if workspace.is_symlink():
    raise RefusedError("workspace_symlink_refused")
workspace_real = workspace.resolve(strict=True)
target = (workspace_real / relative_path).resolve(strict=True)
if target != workspace_real and workspace_real not in target.parents:
    raise RefusedError("path_escape_refused")
```

Missing workspace/file maps to `NotFoundError`, never directory creation.

- [ ] **Step 5: Implement sensitive-path/content policy and bounded operations**

For reads, derive the resolved path relative to `workspace_real`. Refuse if any segment is `.git`, basename is one of `credentials.json|credentials.yaml|credentials.yml`, or `scripts.check_repository_secrets.path_is_forbidden(relative.as_posix())` returns true. Read at most 65,537 bytes; refuse over 65,536. Run `list(content_findings(data))`; if non-empty, return only `secret_like_content`, never the matched bytes/rule excerpt.

`workspace.list` is non-recursive, sorted, does not follow child symlinks, and returns `name`, `type` (`file|directory|symlink`), and `size` only for regular files. Refuse after the 500th entry.

- [ ] **Step 6: Run suite and commit**

```bash
python3 -m unittest tests.test_g2a_workspace -v
scripts/test.sh
git add control_plane/g2a/workspace.py tests/test_g2a_workspace.py
git commit -m "feat(g2a): add confined read-only workspace inspection"
```

---

### Task 5: Add bounded Git inspection without hooks, external diff, or external gitdir

**Files:**
- Create: `control_plane/g2a/git_inspection.py`
- Create: `tests/test_g2a_git_inspection.py`

**Interfaces:**
- `validate_git_repository(workspace: pathlib.Path, timeout: int = 15) -> pathlib.Path`
- `git_status(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- `git_branch(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- `git_head(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- `git_diff(workspace: pathlib.Path, timeout: int = 15) -> tuple[dict[str, Any], Attachment | None]`

- [ ] **Step 1: Write failing normal/detached/dirty tests**

Create a temporary repo with one commit, one staged modification, one unstaged modification, and one untracked file. Assert HEAD, branch/detached state, dirty state, and that `git.diff` includes both staged and unstaged tracked changes relative to HEAD.

- [ ] **Step 2: Write failing external-gitdir test**

Create a workspace whose `.git` file points to a gitdir outside the workspace. `validate_git_repository()` must raise `RefusedError("external_git_dir")`.

- [ ] **Step 3: Write failing timeout/output/secret-diff tests**

Mock timeout -> `OperationTimeout("git_timeout")`. Require `git.status` >262,144 bytes -> `git_status_too_large`. Diff exactly 131,072 bytes stays inline; 131,073..1,048,576 becomes `Attachment`; >1,048,576 -> `diff_too_large`.

Track a `.env` file or a normal tracked file whose diff contains synthetic `password=abcdefghijk`; `git.diff` must return `REFUSED/sensitive_path_in_diff` or `REFUSED/secret_like_content` without returning the secret-like content.

- [ ] **Step 4: Implement a fixed Git execution helper**

Use `shell=False`, `check=False`, `capture_output=True`, timeout 15, and an environment copied from `os.environ` with:

```python
env["GIT_OPTIONAL_LOCKS"] = "0"
env["GIT_CONFIG_NOSYSTEM"] = "1"
env["HOME"] = "/nonexistent"
env["XDG_CONFIG_HOME"] = "/nonexistent"
```

Prefix every Git invocation with fixed config:

```text
git -c core.fsmonitor=false -c core.hooksPath=/dev/null
```

No caller-controlled argv is accepted.

- [ ] **Step 5: Validate gitdir confinement before inspection**

Run fixed `git rev-parse --absolute-git-dir`, resolve the returned path, and require it to be the workspace's `.git` path or a descendant of the workspace. Otherwise refuse `external_git_dir`.

- [ ] **Step 6: Implement fixed inspection commands**

Use only:

```text
git ... status --porcelain=v1 --branch --untracked-files=normal
git ... symbolic-ref --quiet --short HEAD
git ... rev-parse --verify HEAD
git ... diff --name-only -z HEAD --
git ... diff --no-ext-diff --no-textconv --no-color HEAD --
```

The `HEAD` diff includes staged + unstaged tracked changes. Untracked files remain visible through status, not diff.

Before rendering diff content, parse the NUL-separated `--name-only` result and apply the same sensitive-path policy as Task 4. Then apply `content_findings()` to captured diff bytes. Fail closed before returning/uploading any sensitive content.

- [ ] **Step 7: Run suite and commit**

```bash
python3 -m unittest tests.test_g2a_git_inspection -v
scripts/test.sh
git add control_plane/g2a/git_inspection.py tests/test_g2a_git_inspection.py
git commit -m "feat(g2a): add bounded local git inspection"
```

---

### Task 6: Build explicit Core dispatcher and result serialization

**Files:**
- Create: `control_plane/g2a/core.py`
- Create: `tests/test_g2a_core.py`

**Interfaces:**
- `execute(request_value: dict[str, Any], *, manifest_root: pathlib.Path, workspace_root: pathlib.Path) -> CoreExecution`

- [ ] **Step 1: Write failing end-to-end Core tests for all nine operations**

Use temporary manifest/workspace roots. Require mappings:

```text
valid observation -> PASS
malformed/unknown operation -> REFUSED
missing project/workspace/file/non-git repo -> NOT_FOUND
confinement/sensitive policy -> REFUSED
subprocess timeout -> TIMEOUT
unexpected internal failure -> FAILED/internal_error
```

Every result must contain exactly `protocol, request_id, project, operation, status, started_at, finished_at, result, error, evidence`. Assert it contains no `issue_number`, GitHub token/run ID, absolute workspace path, or argv.

- [ ] **Step 2: Verify failure**

```bash
python3 -m unittest tests.test_g2a_core -v
```

- [ ] **Step 3: Implement explicit dispatch only**

Use a mapping whose keys equal `OPERATIONS`; no `else: subprocess` or shell fallback. `project.list` returns all runtime Project records and does not require the selected project to exist; every other operation resolves `request.project` first.

Catch `G2AError` and preserve its safe code/status. Catch unexpected exceptions as `FAILED/internal_error` without serializing raw exception text.

Evidence may contain logical project key, `workspace_state=PRESENT|ABSENT`, local Git HEAD, and dirty boolean. It must not contain absolute host paths.

- [ ] **Step 4: Run suite and commit**

```bash
python3 -m unittest tests.test_g2a_core -v
scripts/test.sh
git add control_plane/g2a/core.py tests/test_g2a_core.py
git commit -m "feat(g2a): add read-only workspace core dispatcher"
```

---

### Task 7: Add GitHub adapter/workflow without triggering the real VPS yet

**Files:**
- Create: `scripts/control_bridge_g2a.py`
- Create: `scripts/control_bridge_g2a_publish.py`
- Create: `tests/test_control_bridge_g2a_adapter.py`
- Create: `control/examples/g2a-request.example.json`
- Create: `.github/workflows/control-bridge-g2a.yml`
- Do **not** create: `control/dispatch/g2a.json`

**Interfaces:**
- Versioned example/envelope shape: `{ "transport": {...}, "request": {...} }`.
- Runtime outputs: `${RUNNER_TEMP}/g2a-envelope.json`, `${RUNNER_TEMP}/g2a-result.json`, optional `${RUNNER_TEMP}/g2a-attachment.bin`.
- Publisher reads Issue metadata from envelope only.

- [ ] **Step 1: Write failing adapter/publisher tests**

Example request:

```json
{
  "transport": {"issue_number": 1},
  "request": {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-EXAMPLE-001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "project.get",
    "arguments": {}
  }
}
```

Assert Core request is unchanged, `issue_number` exists only in envelope, publisher gets Issue number only from envelope, and Markdown is HTML-escaped/capped at 60,000 characters. Attachment bytes never enter Issue Markdown.

- [ ] **Step 2: Verify failure**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter -v
```

- [ ] **Step 3: Implement adapter CLI with injectable roots**

Arguments:

```text
--event-name --event-path --dispatch-file --envelope-file --result-file
--attachment-file --manifest-root --workspace-root
```

Real defaults are checkout `platform/manifests` and `/home/ubuntu/mcf-workspaces`; tests pass temporary roots. Adapter never creates workspace root.

- [ ] **Step 4: Implement publisher with compact safe output**

Publisher skips if envelope has no positive `issue_number`. It posts request ID, operation, status, logical project key, safe summary, and artifact-present marker. It never posts raw attachment bytes or raw unexpected exception text.

- [ ] **Step 5: Create non-triggering example request**

Version `control/examples/g2a-request.example.json` with the exact example above. The live path `control/dispatch/g2a.json` remains absent.

- [ ] **Step 6: Create push-bootstrap workflow**

Use:

```yaml
name: control-bridge-g2a
on:
  push:
    branches: [mcf/mission-001-control-bridge-g1]
    paths: [control/dispatch/g2a.json]
permissions:
  contents: read
  issues: write
concurrency:
  group: control-bridge-g2a-${{ github.ref }}
  cancel-in-progress: false
jobs:
  inspect:
    runs-on: [self-hosted, linux, x64, node-01, mcf-control]
    timeout-minutes: 10
```

Checkout stays pinned to `actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`.

Create a job-local venv only under `${RUNNER_TEMP}` and avoid persistent pip cache:

```bash
python3 -m venv "${RUNNER_TEMP}/g2a-venv"
"${RUNNER_TEMP}/g2a-venv/bin/pip" install --disable-pip-version-check --no-cache-dir -r requirements-dev.lock
```

This does not use sudo or install system packages. Invoke the adapter with `${RUNNER_TEMP}/g2a-venv/bin/python`.

For optional attachment, pin `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`, `retention-days: 7`, and `if-no-files-found: ignore`.

- [ ] **Step 7: Prove workflow creation cannot execute G2-A yet**

Before commit:

```bash
test ! -e control/dispatch/g2a.json
```

Expected: exit 0. Review the workflow path filter and confirm the commit changes no matching live dispatch path.

- [ ] **Step 8: Run suite and commit**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter -v
scripts/test.sh
test ! -e control/dispatch/g2a.json
git add scripts/control_bridge_g2a.py scripts/control_bridge_g2a_publish.py \
  tests/test_control_bridge_g2a_adapter.py control/examples/g2a-request.example.json \
  .github/workflows/control-bridge-g2a.yml
git commit -m "feat(g2a): add dormant github read-only adapter"
```

---

### Task 8: Prove multi-project isolation entirely in disposable test directories

**Files:**
- Create: `tests/test_g2a_integration.py`
- Create: `tests/fixtures/g2a/README.md`

**Interfaces:**
- Temporary manifests and Git workspaces only; no NODE-01 workspace mutation.

- [ ] **Step 1: Build two isolated fixture projects in the test**

Create `tenant-a/project-a/dev` and `tenant-b/project-b/dev`, each with independent Git history. Add an escape symlink in A pointing into B. Include a tracked sensitive-path fixture and synthetic secret-like-content fixture for refusal tests.

- [ ] **Step 2: Assert the complete read-only boundary**

Require:

```text
project.list sees A and B but not examples/
project.get omits secretRefs
workspace.stat A/B = PRESENT
A cannot read B using ../ or symlink
a sensitive path/content is REFUSED without content disclosure
git status/head/branch/diff stay project-local
external gitdir is REFUSED
large safe diff becomes Attachment
Core result contains no absolute workspace path or GitHub metadata
```

- [ ] **Step 3: Run integration and full repository validation**

```bash
python3 -m unittest tests.test_g2a_integration -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_g2a_integration.py tests/fixtures/g2a/README.md
git commit -m "test(g2a): prove multi-project read-only isolation"
```

---

### Task 9: Require green exact-head CI before any live dispatch exists

**Files:**
- No new live dispatch file.
- No VPS workspace changes.

**Interfaces:**
- Gate: `foundation-ci` and `docker-boundary-ci` both `completed/success` for the exact implementation HEAD.

- [ ] **Step 1: Push implementation HEAD and wait for PR checks**

Do not create `control/dispatch/g2a.json` while checks are pending.

- [ ] **Step 2: If CI fails, inspect root cause and correct code/tests only**

Do not weaken existing validation, skip tests, change runner labels, grant sudo, or add Docker access.

- [ ] **Step 3: Record exact green HEAD and run IDs in the future G2-A checkpoint draft**

Keep repository CI evidence distinct from real-node evidence.

---

### Task 10: Separate HUMAN_GATE for the first real G2-A roundtrip

**Files/objects created only after explicit gate:**
- Create GitHub result Issue dedicated to G2-A.
- Create then update: `control/dispatch/g2a.json` (each update intentionally triggers one read-only request).
- After evidence: create `docs/52-control-bridge-g2a-checkpoint.md`.
- After evidence: update G2-A status in `docs/51-control-bridge-g2a-design.md` and PR #3 body.

**Precondition:** A non-critical, already materialized workspace must match a non-example valid Project manifest. G2-A itself does not create/clone/materialize it. If absent, stop as `AGUARDANDO_DEPENDENCIA_EXTERNA` and request a separate bootstrap decision.

- [ ] **Step 1: Reconfirm runner boundary read-only**

Use G1 evidence/current read-only probe to confirm runner online as `ubuntu`, passwordless sudo still refused, no Docker socket/group grant added, and no new inbound port required.

- [ ] **Step 2: Confirm a real registered fixture exists without creating it**

Require valid non-example Project manifest + expected workspace at `/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>`. If either is absent, stop; do not clone or mkdir.

- [ ] **Step 3: Create a dedicated result Issue and first live dispatch**

Create `control/dispatch/g2a.json` for `project.list`, pointing its transport envelope to the dedicated Issue. This file creation is the intentional first G2-A execution trigger.

- [ ] **Step 4: Execute positive observations sequentially**

Update the dispatch file with unique request IDs for:

```text
project.get
workspace.stat
workspace.list
workspace.read (known non-sensitive fixture text)
git.status
git.branch
git.head
git.diff
```

Each request must return through GitHub before the next request is issued. No remote Git source lookup is duplicated through the runner.

- [ ] **Step 5: Execute one negative confinement proof**

Dispatch `workspace.read` with an argument containing `../` and require `REFUSED/path_escape_refused`. Do not target a real host secret as a positive read.

- [ ] **Step 6: Prove no mutation**

Compare fixture file hash/size/mtime and local Git HEAD/status before vs after. Require no G2-A-caused content change. Reconfirm `sudo -n true` refused and no Docker group/socket privilege was added.

- [ ] **Step 7: Write checkpoint only after complete evidence**

`docs/52-control-bridge-g2a-checkpoint.md` records exact implementation HEAD, CI run IDs, request IDs, dedicated Issue/result references, positive PASSes, negative REFUSED evidence, and:

```text
G2A_READ_ONLY=PASS
G2B_WRITE=NOT_IMPLEMENTED
SHELL=NOT_IMPLEMENTED
SUDO=NOT_GRANTED
DOCKER_SOCKET=NOT_GRANTED
PRODUCTION=NOT_AUTHORIZED
```

- [ ] **Step 8: Commit checkpoint and require CI again**

```bash
git add docs/52-control-bridge-g2a-checkpoint.md docs/51-control-bridge-g2a-design.md
git commit -m "docs(g2a): record read-only workspace proof"
```

The checkpoint HEAD must pass commit-bound CI before any merge discussion.

---

## Plan Self-Review

**Spec coverage:** Tasks 1/3 cover manifest-backed multi-project resolution; 2/6 transport-neutral Core; 3 transitional root/no materialization; 4 path/symlink/cross-project confinement and bounded reads; 5 bounded local Git inspection; 7 transport envelope/summaries/artifacts without premature live trigger; 8 disposable integration; 9 exact-head CI; 10 separate real-node gate. G2-B remains outside this plan.

**Security review:** The plan additionally closes four implementation-level gaps without expanding capability: runtime examples are not registrations; secret-like content is not returned through read/diff; Git directories may not escape the workspace; and creating the G2-A workflow cannot itself trigger the runner because the live dispatch file remains absent until Task 10.

**Type consistency:** `ValidatedManifest -> ProjectRecord -> ProjectKey`; `CoreRequest -> ProjectResolver/workspace/Git operations -> CoreExecution`; `Attachment` belongs to Core output but Issue/run metadata remains in the adapter envelope.

**Execution boundary:** Creating or editing this plan does **not** authorize implementation. Tasks 1-9 require a separate implementation authorization. Task 10 requires a second explicit HUMAN_GATE for the first real G2-A request on NODE-01.