# SLICE-001 test results

Static suite re-executed: 2026-08-16 21:03 UTC
Controller: Linux, Python 3.12, Ansible Core 2.21.3

## Static and policy suite

```text
SECRET_POLICY_PASS
LOCAL_MARKDOWN_LINKS_PASS
YAML_PARSE_PASS count=20
MANIFEST_VALIDATION_PASS count=2
STATE_CROSSCHECK_PASS decisions=Q1-Q40-exact artifacts=12 gates=preserved real_apply=NOT_EXECUTED timestamps=aligned
UNIT_TESTS_PASS count=37
SHELL_SYNTAX_PASS count=4
ANSIBLE_SYNTAX_PASS count=3
SHELLCHECK_PASS count=4
FOUNDATION_STATIC_TESTS_PASS
```

This result is current for the uncommitted worktree observed at that timestamp,
not yet bound to a published Git tree. The configured GitHub workflow is the
commit-bound gate for this delta.

The hardened secret policy scans tracked/untracked files plus every reachable Git
blob for its high-confidence rules without printing matched values. CI fetches
full history before making that claim.

ShellCheck 0.9.0 was obtained from the Ubuntu Noble package without host-level
installation and passed locally. CI installs and requires it. Shell syntax
discovery covers every tracked/unignored file with a supported shell shebang.

## Unprivileged target preflight

Re-executed against the real DEV inventory at 2026-08-16 20:58 UTC. The
controller-key mode/fingerprint, exact SSH profile, login `ubuntu`, IP, hostname
and normalized machine-id hash all passed; recap was `changed=0`, `failed=0`.
No sudo was requested and no VPS state was changed.

The test inventory was also invoked from the physical Workstation. Its Docker
fixture boundary (`/.dockerenv`, `systemd-detect-virt=docker`, canonical baked
inventory/root) was absent and the preflight refused the target with exit `2`,
before any mutation.

## Historical disposable Ubuntu 24.04/systemd integration test

Executed: 2026-08-16 20:09 UTC. These results applied to the pre-review input and
are retained as history; they are **not current PASS evidence** after the test and
role review delta. Current status is `PENDING_REVALIDATION_AFTER_REVIEW_DELTA`.

Fixture base:
`ubuntu@sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea`

The fixture had no published network and contained no project credential.

```text
FIRST_APPLY: ok=21 changed=7 failed=0 unreachable=0
SECOND_APPLY: ok=20 changed=0 failed=0 unreachable=0
ACCOUNT_GROUP_NEGATIVE_TEST: PASS
OWNERSHIP_AND_MODE_TEST: PASS
SYSTEMD_UNIT_VERIFY: PASS
ROLLBACK: ok=10 changed=6 failed=0 unreachable=0
ROLLBACK_ABSENCE_TEST: PASS
FOUNDATION_CONTAINER_TEST_PASS apply_changed idempotent_changed_0 rollback_clean
```

At that historical run, the container and intermediate image were removed. The
base image digest alone does not pin packages installed from the live Ubuntu
repository during fixture build.

## Evidence boundary

The historical run proved the then-current role against a disposable Ubuntu
24.04/systemd fixture. It does not prove the reviewed worktree, privileged apply,
idempotence, restart behavior or rollback on the real VPS. Those real-VPS rows
remain `NOT_EXECUTED` in `baseline.yaml` until LEANDRO performs interactive sudo
authentication. The final disposable rerun and GitHub CI must bind fresh results
to the published commit/tree.
