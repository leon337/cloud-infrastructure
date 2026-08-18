# Control Bridge G2-A Read-Only Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved G2-A read-only Workspace Core so agents can inspect local project workspaces on NODE-01 through GitHub without shell, sudo, Docker, writes, clone/materialization, or a second project registry.

**Architecture:** Keep GitHub transport concerns outside the Core. The Core validates a transport-neutral request, resolves `tenant/name/environment` through the existing Project manifests, resolves the transitional workspace root `/home/ubuntu/mcf-workspaces`, confines every filesystem path after realpath/symlink resolution, executes only nine allowlisted read-only capabilities, and returns a structured result. A thin GitHub adapter extracts the transport envelope, invokes the Core, publishes a short summary, and uploads large bounded payloads as Actions Artifacts.

**Tech Stack:** Python 3.12 standard library, existing `PyYAML==6.0.3`, `jsonschema==4.26.0`, existing strict YAML loader, Git CLI, `unittest`, GitHub Actions self-hosted runner `node-01+mcf-control`.

**Spec:** `docs/51-control-bridge-g2a-design.md`

## Global Constraints

- G2-A is read-only. No `workspace.write`, `mkdir`, `delete`, Git mutation, clone, provisioning, shell, sudo, Docker, systemd mutation, network mutation, package management, secrets administration, deploy, backup/rollback, or production action.
- Core protocol: `MCF_WORKSPACE_CONTROL_V1`; result protocol: `MCF_WORKSPACE_CONTROL_RESULT_V1`.
- Core request contains only `protocol`, `request_id`, `project`, `operation`, and `arguments`; `issue_number`, run IDs, GitHub tokens, and event metadata remain in the GitHub adapter.
- Project identity source of truth remains `platform/manifests/**/*.yaml`; do not create `registry.json`, SQLite, or another project database.
- Transitional workspace root: `/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>`.
- Core operations are exactly: `project.list`, `project.get`, `workspace.stat`, `workspace.list`, `workspace.read`, `git.status`, `git.branch`, `git.head`, `git.diff`.
- `workspace.list` is non-recursive and capped at 500 direct children per request.
- `workspace.read` accepts UTF-8 text only and is capped at 65,536 bytes inline. Files above the limit return `REFUSED` with `file_too_large`; invalid UTF-8 returns `REFUSED` with `binary_or_non_utf8`.
- `git.diff` captures at most 1,048,576 bytes. Up to 131,072 bytes may be placed inline; larger output is returned as a generic attachment payload for the transport adapter to upload as an Artifact. Output above 1,048,576 bytes returns `REFUSED` with `diff_too_large`.
- Per-operation subprocess timeout: 15 seconds. Timeout maps to Core status `TIMEOUT`.
- `workspace.read` refuses `.git/**` and any path rejected by the repository's existing secret-path policy in `scripts/check_repository_secrets.py` (`.env*`, private-key filenames, key stores, `secret(s)` and `credential(s)` paths). `.env.example` remains allowed because the existing repository policy explicitly allows it.
- Filesystem confinement is based on resolved paths and ancestry, not string filtering alone. Absolute paths, `~`, `..` escape, symlink escape, and cross-project escape must fail closed.
- G2-A does not create a persistent dedupe store or local lock manager. `request_id` is correlation only.
- The branch workflow remains push-bootstrap-only for the first real G2-A proof. Do not activate an Issue-triggered command bus on the default branch as part of this plan.
- Production remains unauthorized. PR #3 remains draft and must not be merged by this plan.

---

### Task 1: Make manifest validation reusable without creating a second registry

**Files:**
- Modify: `scripts/validate_manifests.py`
- Create: `tests/test_manifest_catalog.py`

**Interfaces:**
- Produces: `load_validated_manifests(manifest_directory: pathlib.Path = MANIFEST_DIRECTORY) -> list[dict[str, Any]]`
- Produces: `project_key(manifest: dict[str, Any]) -> tuple[str, str, str]`
- Existing CLI `python3 scripts/validate_manifests.py` must keep the same PASS/FAIL behavior.

- [ ] **Step 1: Write failing tests for reusable validated manifest loading**

Add tests that create a temporary manifest directory containing two valid `Project` manifests and assert:

```python
manifests = MODULE.load_validated_manifests(temp_manifest_root)
projects = [item for item in manifests if item["kind"] == "Project"]
self.assertEqual(
    [MODULE.project_key(item) for item in projects],
    [("tenant-a", "project-a", "dev"), ("tenant-b", "project-b", "staging")],
)
```

Also add a duplicate-key/invalid-manifest test that asserts `ManifestValidationError` is raised and that the exception message contains the path but not secret values.

- [ ] **Step 2: Run the new tests and verify failure**

Run:

```bash
python3 -m unittest tests.test_manifest_catalog -v
```

Expected: FAIL because `load_validated_manifests`, `project_key`, and `ManifestValidationError` do not exist.

- [ ] **Step 3: Refactor the current validator into reusable functions**

Keep existing schema and semantic checks, but add:

```python
class ManifestValidationError(ValueError):
    def __init__(self, failures: list[str]):
        super().__init__("; ".join(failures))
        self.failures = failures


def project_key(manifest: dict[str, Any]) -> tuple[str, str, str]:
    metadata = manifest["metadata"]
    return metadata["tenant"], metadata["name"], metadata["environment"]


def load_validated_manifests(
    manifest_directory: pathlib.Path = MANIFEST_DIRECTORY,
) -> list[dict[str, Any]]:
    # Move the existing schema-load + YAML-load + schema-validation + semantic-check
    # logic here. Return manifests only when the entire catalog validates.
    # Raise ManifestValidationError(failures) on any validation failure.
```

Change `main()` to call `load_validated_manifests()` and preserve:

```text
MANIFEST_VALIDATION_PASS count=<n>
MANIFEST_VALIDATION_FAIL <message>
```

- [ ] **Step 4: Run manifest tests and the existing repository validator**

Run:

```bash
python3 -m unittest tests.test_manifest_catalog tests.test_manifest_negative_cases -v
python3 scripts/validate_manifests.py
```

Expected: PASS and existing manifest validation output remains compatible.

- [ ] **Step 5: Commit the reusable catalog change**

```bash
git add scripts/validate_manifests.py tests/test_manifest_catalog.py
git commit -m "refactor(g2a): expose validated project manifest catalog"
```

---

### Task 2: Add the transport-neutral Core protocol

**Files:**
- Create: `control_plane/__init__.py`
- Create: `control_plane/g2a/__init__.py`
- Create: `control_plane/g2a/protocol.py`
- Create: `tests/test_g2a_protocol.py`
- Modify: `scripts/test.sh`

**Interfaces:**
- Produces: `ProjectKey(tenant: str, name: str, environment: str)`
- Produces: `CoreRequest(protocol: str, request_id: str, project: ProjectKey, operation: str, arguments: dict[str, Any])`
- Produces: `Attachment(name: str, media_type: str, content: bytes)`
- Produces: `CoreExecution(result: dict[str, Any], attachment: Attachment | None)`
- Produces: `parse_request(value: dict[str, Any]) -> CoreRequest`

- [ ] **Step 1: Write failing protocol tests**

Tests must prove a valid request parses and each forbidden transport/core confusion fails:

```python
VALID = {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-000001",
    "project": {"tenant": "tenant-a", "name": "project-a", "environment": "dev"},
    "operation": "git.status",
    "arguments": {},
}

request = parse_request(VALID)
self.assertEqual(request.project, ProjectKey("tenant-a", "project-a", "dev"))

for forbidden in ("issue_number", "cwd", "argv", "command", "workspace"):
    candidate = dict(VALID)
    candidate[forbidden] = 1
    with self.assertRaisesRegex(ValueError, "unexpected_request_field"):
        parse_request(candidate)
```

Also reject unknown operations, invalid `request_id`, missing project keys, and invalid environments outside `dev|staging`.

- [ ] **Step 2: Run protocol tests and verify failure**

```bash
python3 -m unittest tests.test_g2a_protocol -v
```

Expected: FAIL because the G2-A package does not exist.

- [ ] **Step 3: Implement immutable protocol dataclasses and strict parsing**

Use `@dataclass(frozen=True)` and an exact operation set:

```python
OPERATIONS = frozenset({
    "project.list", "project.get", "workspace.stat", "workspace.list",
    "workspace.read", "git.status", "git.branch", "git.head", "git.diff",
})
```

Reject unknown top-level fields and unknown project fields. Keep status generation separate from transport metadata.

- [ ] **Step 4: Extend repository compile coverage and run tests**

Change:

```bash
"$PYTHON" -m compileall -q scripts tests
```

to:

```bash
"$PYTHON" -m compileall -q scripts tests control_plane
```

Then run:

```bash
python3 -m unittest tests.test_g2a_protocol -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 5: Commit protocol skeleton**

```bash
git add control_plane scripts/test.sh tests/test_g2a_protocol.py
git commit -m "feat(g2a): add transport-neutral workspace protocol"
```

---

### Task 3: Resolve Projects and workspaces from existing manifests

**Files:**
- Create: `control_plane/g2a/projects.py`
- Create: `tests/test_g2a_projects.py`

**Interfaces:**
- Consumes: `scripts.validate_manifests.load_validated_manifests`
- Consumes: `ProjectKey`
- Produces: `ProjectRecord(key: ProjectKey, manifest_path: pathlib.Path, manifest: dict[str, Any])`
- Produces: `ProjectResolver.list() -> list[ProjectRecord]`
- Produces: `ProjectResolver.get(key: ProjectKey) -> ProjectRecord`
- Produces: `workspace_path(workspace_root: pathlib.Path, key: ProjectKey) -> pathlib.Path`

- [ ] **Step 1: Write failing multi-project resolution tests**

Create two temporary Project manifests and assert deterministic sort order, exact lookup, duplicate logical key refusal, and no use of `spec.capabilities` as an ACL.

Expected workspace mapping:

```python
self.assertEqual(
    workspace_path(pathlib.Path("/tmp/root"), ProjectKey("tenant-a", "project-a", "dev")),
    pathlib.Path("/tmp/root/tenant-a/project-a/dev"),
)
```

- [ ] **Step 2: Run tests and verify failure**

```bash
python3 -m unittest tests.test_g2a_projects -v
```

Expected: FAIL because resolver functions do not exist.

- [ ] **Step 3: Implement resolver as a view over validated manifests**

`ProjectResolver` must load the existing catalog every request or invocation; do not persist a second registry. Duplicate `tenant/name/environment` must raise `ValueError("duplicate_project_key")`.

`project.get` response must omit `secretRefs` values entirely and return only non-secret desired-state metadata needed for inspection: identity, criticality, source repository/revision, persistence booleans, sandbox limits/network profile, preview enabled, and production gate state.

- [ ] **Step 4: Run resolver tests and full static suite**

```bash
python3 -m unittest tests.test_g2a_projects -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 5: Commit project resolution**

```bash
git add control_plane/g2a/projects.py tests/test_g2a_projects.py
git commit -m "feat(g2a): resolve projects from canonical manifests"
```

---

### Task 4: Implement workspace confinement and read-only filesystem operations

**Files:**
- Create: `control_plane/g2a/workspace.py`
- Create: `tests/test_g2a_workspace.py`

**Interfaces:**
- Produces: `resolve_confined(workspace: pathlib.Path, relative_path: str) -> pathlib.Path`
- Produces: `workspace_stat(workspace: pathlib.Path) -> dict[str, Any]`
- Produces: `workspace_list(workspace: pathlib.Path, relative_path: str = ".") -> dict[str, Any]`
- Produces: `workspace_read(workspace: pathlib.Path, relative_path: str) -> dict[str, Any]`

- [ ] **Step 1: Write failing confinement tests**

Use temporary `project-a` and `project-b` directories. Required tests:

```python
with self.assertRaisesRegex(ValueError, "absolute_path_refused"):
    resolve_confined(project_a, "/etc/passwd")

with self.assertRaisesRegex(ValueError, "path_escape_refused"):
    resolve_confined(project_a, "../project-b/private.txt")
```

Create a symlink inside A pointing to B and assert `symlink_escape_refused`. Assert a symlink whose target remains inside A is allowed.

- [ ] **Step 2: Write failing limit and sensitive-path tests**

Prove:

- 65,536-byte UTF-8 file succeeds;
- 65,537-byte file returns/refuses `file_too_large`;
- invalid UTF-8 refuses `binary_or_non_utf8`;
- `.git/config`, `.env`, `secrets/token.txt`, `credentials.json`, `id_ed25519`, and `certificate.key` are refused using the repository's existing secret-path policy;
- `.env.example` is allowed;
- a directory with 501 direct children refuses `list_entry_limit`.

- [ ] **Step 3: Run workspace tests and verify failure**

```bash
python3 -m unittest tests.test_g2a_workspace -v
```

Expected: FAIL because workspace operations do not exist.

- [ ] **Step 4: Implement realpath/ancestry confinement and bounded reads**

Core rule:

```python
workspace_real = workspace.resolve(strict=True)
target = (workspace_real / relative_path).resolve(strict=True)
if target != workspace_real and workspace_real not in target.parents:
    raise ValueError("path_escape_refused")
```

Before resolution, explicitly reject absolute paths and any path beginning with `~`. After resolution, enforce ancestry. For `workspace.read`, call the existing `scripts.check_repository_secrets.path_is_forbidden()` on the POSIX path relative to the workspace and additionally refuse any `.git` segment.

`workspace.list` is one level only, sorted by name, max 500 entries, returning only `name`, `type` (`file|directory|symlink`), and `size` for regular files. It must not follow child symlinks while listing.

- [ ] **Step 5: Run workspace tests and full suite**

```bash
python3 -m unittest tests.test_g2a_workspace -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit confinement and reads**

```bash
git add control_plane/g2a/workspace.py tests/test_g2a_workspace.py
git commit -m "feat(g2a): add confined read-only workspace operations"
```

---

### Task 5: Add bounded local Git inspection

**Files:**
- Create: `control_plane/g2a/git_inspection.py`
- Create: `tests/test_g2a_git_inspection.py`

**Interfaces:**
- Produces: `git_status(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- Produces: `git_branch(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- Produces: `git_head(workspace: pathlib.Path, timeout: int = 15) -> dict[str, Any]`
- Produces: `git_diff(workspace: pathlib.Path, timeout: int = 15) -> tuple[dict[str, Any], Attachment | None]`

- [ ] **Step 1: Write failing Git fixture tests**

Create a temporary repository with one commit, a modified tracked file, and one untracked file. Assert:

```python
self.assertEqual(git_head(repo)["head"], expected_sha)
self.assertEqual(git_branch(repo)["detached"], False)
self.assertTrue(git_status(repo)["dirty"])
self.assertIn("tracked.txt", git_diff(repo)[0]["files"])
```

Also test detached HEAD and a non-Git directory returning `NOT_FOUND`/`not_git_repository` through the Core mapping.

- [ ] **Step 2: Write failing timeout/output-bound tests**

Mock `subprocess.run` to raise `subprocess.TimeoutExpired` and assert timeout is preserved distinctly. Create diff output at 131,072 bytes (inline), 131,073 bytes (attachment), and above 1,048,576 bytes (`diff_too_large`).

- [ ] **Step 3: Run tests and verify failure**

```bash
python3 -m unittest tests.test_g2a_git_inspection -v
```

Expected: FAIL because Git inspection module does not exist.

- [ ] **Step 4: Implement only fixed Git argv**

Internal helper may accept argv, but no Core request may supply argv. Public functions must hard-code:

```text
git status --porcelain=v1 --branch --untracked-files=normal
git symbolic-ref --quiet --short HEAD
git rev-parse --verify HEAD
git diff --no-ext-diff --no-textconv --
```

Run with `cwd=workspace`, `shell=False`, `check=False`, `capture_output=True`, `timeout=15`, and environment `GIT_OPTIONAL_LOCKS=0`. Never run fetch, pull, checkout, commit, push, reset, clean, add, restore, switch, or submodule mutation.

- [ ] **Step 5: Run Git tests and full suite**

```bash
python3 -m unittest tests.test_g2a_git_inspection -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 6: Commit Git inspection**

```bash
git add control_plane/g2a/git_inspection.py tests/test_g2a_git_inspection.py
git commit -m "feat(g2a): add bounded local git inspection"
```

---

### Task 6: Build the Core dispatcher and result serialization

**Files:**
- Create: `control_plane/g2a/core.py`
- Create: `tests/test_g2a_core.py`

**Interfaces:**
- Consumes: protocol, ProjectResolver, workspace operations, Git inspection.
- Produces: `execute(request_value: dict[str, Any], *, manifest_root: pathlib.Path, workspace_root: pathlib.Path) -> CoreExecution`

- [ ] **Step 1: Write failing end-to-end Core tests**

Use temporary manifest and workspace roots to prove all nine operations route correctly. Include exact status mapping:

```text
valid observation -> PASS
unknown/malformed request -> REFUSED
missing project/workspace/file/non-git repo -> NOT_FOUND
path/sensitive policy rejection -> REFUSED
subprocess timeout -> TIMEOUT
unexpected OSError/subprocess failure -> FAILED
```

Assert every result contains exactly:

```python
{
    "protocol", "request_id", "project", "operation", "status",
    "started_at", "finished_at", "result", "error", "evidence"
}
```

and contains no `issue_number`, GitHub token, workflow/run ID, absolute workspace path, or arbitrary argv.

- [ ] **Step 2: Run Core tests and verify failure**

```bash
python3 -m unittest tests.test_g2a_core -v
```

Expected: FAIL because dispatcher does not exist.

- [ ] **Step 3: Implement explicit operation dispatch**

Use a dictionary whose keys are exactly `OPERATIONS`; do not implement a generic command fallback. `project.list` may ignore the request's project selector for lookup but the request still carries a syntactically valid project object for protocol uniformity; document returned list as catalog-wide. All other operations must resolve the selected Project first.

Evidence may include logical project key, workspace state (`PRESENT|ABSENT`), local Git HEAD, and dirty boolean. Evidence must not include absolute host paths.

- [ ] **Step 4: Run Core tests and full suite**

```bash
python3 -m unittest tests.test_g2a_core -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 5: Commit Core dispatcher**

```bash
git add control_plane/g2a/core.py tests/test_g2a_core.py
git commit -m "feat(g2a): add read-only workspace core dispatcher"
```

---

### Task 7: Add the GitHub adapter, result publisher, and artifact path

**Files:**
- Create: `scripts/control_bridge_g2a.py`
- Create: `scripts/control_bridge_g2a_publish.py`
- Create: `tests/test_control_bridge_g2a_adapter.py`
- Create: `control/dispatch/g2a.json`
- Create: `.github/workflows/control-bridge-g2a.yml`

**Interfaces:**
- Adapter input on push: one transport document with `{ "transport": {...}, "request": {...} }`.
- Adapter output files: `${RUNNER_TEMP}/g2a-envelope.json`, `${RUNNER_TEMP}/g2a-result.json`, optional `${RUNNER_TEMP}/g2a-attachment.bin`.
- Publisher consumes envelope + Core result; Core result remains transport-neutral.

- [ ] **Step 1: Write failing adapter parsing tests**

Push fixture:

```json
{
  "transport": {"issue_number": 4},
  "request": {
    "protocol": "MCF_WORKSPACE_CONTROL_V1",
    "request_id": "G2A-BOOTSTRAP-001",
    "project": {"tenant": "example-tenant", "name": "example-project", "environment": "dev"},
    "operation": "project.get",
    "arguments": {}
  }
}
```

Assert the adapter returns the Core request unchanged and writes `issue_number` only to the envelope. Assert missing/invalid transport metadata cannot alter Core fields.

- [ ] **Step 2: Write failing publisher tests**

Mock `urllib.request.urlopen`. Assert Markdown contains request ID, operation, status, logical project key, compact result summary, and artifact marker when attachment metadata exists. Assert publisher reads `issue_number` from the envelope, not the Core result.

- [ ] **Step 3: Run adapter tests and verify failure**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter -v
```

Expected: FAIL because adapter/publisher do not exist.

- [ ] **Step 4: Implement adapter CLI**

CLI arguments:

```text
--event-name
--event-path
--dispatch-file
--envelope-file
--result-file
--attachment-file
--manifest-root
--workspace-root
```

Defaults for the real workflow:

```text
manifest-root = <checkout>/platform/manifests
workspace-root = /home/ubuntu/mcf-workspaces
```

For tests, both roots must be injectable. The adapter must never create the workspace root.

- [ ] **Step 5: Implement publisher and bounded Markdown**

Cap Issue Markdown at 60,000 characters, HTML-escape untrusted output, and never dump attachment bytes into the Issue. Publisher skips when no positive `issue_number` exists.

- [ ] **Step 6: Add push-bootstrap workflow**

Create `.github/workflows/control-bridge-g2a.yml` with:

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

Pin checkout to the repository's existing SHA:

```yaml
uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5
```

Upload the optional attachment with:

```yaml
uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02 # v4.6.2
with:
  name: g2a-${{ github.run_id }}
  path: ${{ runner.temp }}/g2a-attachment.bin
  if-no-files-found: ignore
  retention-days: 7
```

Do not add an Issue trigger in this first workflow.

- [ ] **Step 7: Run adapter tests and repository suite**

```bash
python3 -m unittest tests.test_control_bridge_g2a_adapter -v
scripts/test.sh
```

Expected: PASS.

- [ ] **Step 8: Commit adapter/workflow**

```bash
git add scripts/control_bridge_g2a.py scripts/control_bridge_g2a_publish.py \
  tests/test_control_bridge_g2a_adapter.py control/dispatch/g2a.json \
  .github/workflows/control-bridge-g2a.yml
git commit -m "feat(g2a): add github adapter for read-only workspace core"
```

---

### Task 8: Prove multi-project isolation in integration before touching NODE-01 workspaces

**Files:**
- Create: `tests/test_g2a_integration.py`
- Create: `tests/fixtures/g2a/README.md`

**Interfaces:**
- Uses only temporary directories and temporary Git repositories; no VPS mutation.

- [ ] **Step 1: Write the integration fixture builder in the test module**

The test must create two manifests (`tenant-a/project-a/dev`, `tenant-b/project-b/dev`) and two workspaces with independent Git histories. Create an escape symlink in A pointing into B.

- [ ] **Step 2: Add integration assertions**

Prove in one test suite:

```text
project.list sees A and B
project.get A does not expose secretRefs
workspace.stat A/B = PRESENT
workspace.read A cannot read B via ../
workspace.read A cannot read B via symlink
git.status/head/branch/diff are project-local
Core result contains no absolute workspace path
large diff produces Attachment, not oversized inline Issue payload
```

- [ ] **Step 3: Run integration tests**

```bash
python3 -m unittest tests.test_g2a_integration -v
```

Expected: PASS.

- [ ] **Step 4: Run complete repository validation**

```bash
scripts/test.sh
```

Expected: existing repository checks plus all new G2-A tests PASS.

- [ ] **Step 5: Commit integration proof**

```bash
git add tests/test_g2a_integration.py tests/fixtures/g2a/README.md
git commit -m "test(g2a): prove multi-project read-only isolation"
```

---

### Task 9: Close repository CI before any real G2-A request

**Files:**
- No code changes unless CI reveals a defect.

**Interfaces:**
- Gate: both `foundation-ci` and `docker-boundary-ci` must be `completed/success` for the exact implementation HEAD.

- [ ] **Step 1: Push implementation HEAD and wait for PR checks**

Do not trigger G2-A against NODE-01 until the exact HEAD has green repository CI.

- [ ] **Step 2: If CI fails, inspect the failing job and fix only the root cause**

Re-run local/full tests before the correction commit. Do not weaken existing validation, skip tests, or broaden runner permissions.

- [ ] **Step 3: Record exact green run IDs and HEAD SHA in the implementation checkpoint draft**

The checkpoint must distinguish repository CI from real-node evidence.

---

### Task 10: Run the first real read-only G2-A proof under a separate execution gate

**Files:**
- Modify only `control/dispatch/g2a.json` to issue each read-only request.
- Create after success: `docs/52-control-bridge-g2a-checkpoint.md`
- Update after success: `docs/51-control-bridge-g2a-design.md` status section only.
- Update after success: PR #3 body.

**Interfaces:**
- Requires an already materialized non-critical fixture workspace matching an existing valid Project manifest.
- G2-A must not create/clone/materialize that workspace. If none exists, stop with `AGUARDANDO_DEPENDENCIA_EXTERNA` and request a separate bootstrap decision.

- [ ] **Step 1: Precheck without mutation**

Use the existing G1 probe or equivalent read-only evidence to confirm runner online, `ubuntu` identity, no passwordless sudo, and no new privilege grant. Confirm the target fixture workspace exists before dispatching G2-A.

- [ ] **Step 2: Dispatch `workspace.stat` and require PASS**

Expected evidence: logical project key + `workspace_state=PRESENT`; no absolute host path in the Core result.

- [ ] **Step 3: Dispatch `workspace.list` and `workspace.read` on a known non-sensitive fixture file**

Expected: bounded UTF-8 output; no mutation of mtime/content/hash.

- [ ] **Step 4: Dispatch `git.status`, `git.branch`, `git.head`, and `git.diff`**

Expected: local observed state only. No fetch/pull/checkout/commit/push occurs.

- [ ] **Step 5: Prove negative confinement on the real runner**

Dispatch a request containing `../` and require `REFUSED`. Do not use an actual sensitive path as a positive target.

- [ ] **Step 6: Compare before/after fixture state**

Capture read-only hashes/stat before and after; require no content mutation. Confirm `sudo -n true` is still refused and no Docker group/socket privilege was added.

- [ ] **Step 7: Write the G2-A checkpoint only after evidence is complete**

`docs/52-control-bridge-g2a-checkpoint.md` must record exact HEAD, CI run IDs, request IDs, Issue/result links, PASS/REFUSED evidence, and explicit non-claims:

```text
G2A_READ_ONLY=PASS
G2B_WRITE=NOT_IMPLEMENTED
SHELL=NOT_IMPLEMENTED
SUDO=NOT_GRANTED
DOCKER_SOCKET=NOT_GRANTED
PRODUCTION=NOT_AUTHORIZED
```

- [ ] **Step 8: Commit checkpoint documentation**

```bash
git add docs/52-control-bridge-g2a-checkpoint.md docs/51-control-bridge-g2a-design.md
git commit -m "docs(g2a): record read-only workspace proof"
```

Run commit-bound CI again after the checkpoint commit before any merge discussion.

---

## Plan Self-Review

### Spec coverage

- Multi-project Project resolution: Tasks 1 and 3.
- Transport-neutral Core request/result: Tasks 2 and 6.
- Transitional workspace root and no materialization: Tasks 3, 7, 10.
- Path traversal/symlink/cross-project refusal: Tasks 4 and 8.
- `project.list/get`: Tasks 3 and 6.
- `workspace.stat/list/read`: Tasks 4 and 6.
- `git.status/branch/head/diff`: Tasks 5 and 6.
- Source state vs workspace state: enforced by scope; no GitHub-remote read capability is added.
- Small result vs Artifact: Tasks 5 and 7.
- No dedupe/locks/writes: Global Constraints and all task interfaces.
- Unit tests, integration tests, exact-head CI, real read-only proof: Tasks 1-10.
- G2-B remains outside this plan.

### Type consistency

The plan uses `ProjectKey`, `CoreRequest`, `Attachment`, and `CoreExecution` from Task 2 consistently. `ProjectResolver` consumes `ProjectKey`; Core consumes resolver/workspace/Git modules; GitHub adapter consumes `CoreExecution` and keeps the envelope separate.

### Execution boundary

Creating this plan does **not** authorize implementation. Code changes begin only after an explicit implementation gate. The real NODE-01 proof in Task 10 is a second gate after unit/integration tests and green commit-bound CI.