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

The same static gate passed in GitHub Actions for implementation commit
`edd2497d657cc9bc35952f5dfc71090a18dade53`. Run
[`31972460567`](https://github.com/leon337/cloud-infrastructure/actions/runs/31972460567)
was triggered by `push`, completed successfully at `2026-08-16T21:08:05Z`, and
its `validate` job completed in 23 seconds. This is commit-bound evidence for
that SHA, not a claim that a later evidence-only commit has already run in CI.

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

## Commit-bound disposable Ubuntu 24.04/systemd integration

GitHub Actions run
[`31972460567`](https://github.com/leon337/cloud-infrastructure/actions/runs/31972460567),
job `disposable-integration` (`95226938043`), passed for commit
`edd2497d657cc9bc35952f5dfc71090a18dade53`. The job ran from
`2026-08-16T21:06:05Z` through `2026-08-16T21:08:04Z` on a GitHub-hosted Ubuntu
24.04 disposable VM. The privileged fixture gate accepted only
`DISPOSABLE_VM_ONLY`; the allowlisted bundle reported Git, virtualenv and
forbidden secret-bearing paths absent, and the test container used no network.
Content-level secret policy was proved separately by the required `validate` job.

```text
FOUNDATION_CHECK_MODE_INVARIANCE_PASS
FOUNDATION_PARTIAL_MARKER_CHECK_PASS
FIRST_APPLY: changed=7 failed=0 unreachable=0
SECOND_APPLY: changed=0 failed=0 unreachable=0
SECURITY_ASSERTIONS: PASS
ROLLBACK_REFUSAL marker_tampered: PASS_F1_1_MANAGED_SURFACE_INVARIANT
ROLLBACK_REFUSAL persistent_content: PASS_F1_1_MANAGED_SURFACE_INVARIANT
ROLLBACK_REFUSAL runtime_content: PASS_F1_1_MANAGED_SURFACE_INVARIANT
ROLLBACK_REFUSAL marker_absent: PASS_F1_1_MANAGED_SURFACE_INVARIANT
SUCCESSFUL_ROLLBACK: changed=7 failed=0 unreachable=0
FOUNDATION_CONTAINER_TEST_PASS check_mode partial_marker_check apply_changed idempotent_changed_0 security_assertions rollback_refusals_4 rollback_clean
FOUNDATION_CONTAINER_TEST_CLEANUP_PASS container=removed image=removed bundle=removed
```

The GitHub job completed in 1 minute 59 seconds. This proves the reviewed role's
check-mode invariance, apply, idempotence, security postconditions, fail-closed
rollback cases, successful rollback and cleanup of the named test image/container
and bundle in that disposable fixture. It does not claim removal of Docker base
layers or prove any privileged operation on the real VPS.

## Historical disposable Ubuntu 24.04/systemd integration test

Executed: 2026-08-16 20:09 UTC. These results applied to the pre-review input and
are retained as history; they are **not** the evidence used to pass the reviewed
delta. The commit-bound CI run above supersedes them for the disposable fixture.

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

Run `31972460567` proves only commit
`edd2497d657cc9bc35952f5dfc71090a18dade53` in the disposable CI fixture. These
subsequent evidence/state edits are not represented as having passed a final CI
run. The run does not prove privileged check mode, apply, idempotence, restart
behavior or rollback on the real VPS. Those real-VPS rows remain `NOT_EXECUTED`
in `baseline.yaml` until LEANDRO performs interactive sudo authentication.
