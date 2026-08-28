# G2-B promotion audit — 2026-08-28

Scope: repository and GitHub metadata audit only. No VPS, SSH, runtime, grant,
write, push, pull request, merge, or production action is authorized by this
record.

## Exact references observed

| Reference | SHA | Assessment |
| --- | --- | --- |
| `origin/main` | `ce829067a9a04eceaa6eaefd9553899b2ce14da1` | Current main at audit time; Merge PR #37. |
| `origin/mcf/mission-001-control-bridge-g1` | `38cd22e0a814bdf4957edcf5bb30506a4810bda0` | MCF integration line; Merge PR #27. |
| `origin/codex/control-bridge-g2b` | `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a` | Historical G2-B publication line. |
| `origin/team/g2b-task8-20260822` | `f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8` | Task 8 evidence branch; PR #21 remains open. |
| `origin/recovery/g2b-ssh-local-preservation-20260828` | `7fa9ab996be6cdffd4ea3913c082e3da7090fff4` | Preserved local SSH delta; not a promotion candidate. |

The recovery branch also contains the historical local parent
`ef2d10a85dc3d880f4c50f25eb4e0f10caa3aa04` (exact existing-grant-schema
fix). It is not proof that either change is already reconciled with the
canonical target.

## Divergence and pull-request status

At audit time, GitHub comparison reported merge-base
`987c5359ea948d1903355e98177ae1eb2f1849d5` for the main/MCF and
main/recovery comparisons:

| Comparison | Result |
| --- | --- |
| `main...mcf/mission-001-control-bridge-g1` | diverged; MCF ahead 370 and behind 81. |
| `main...recovery/g2b-ssh-local-preservation-20260828` | diverged; recovery ahead 218 and behind 81. |
| `mcf/mission-001-control-bridge-g1...recovery/g2b-ssh-local-preservation-20260828` | diverged; recovery ahead 2 and behind 154; merge-base `7205a647f918580d09c87ed44f38b0a433552a51`. |
| `codex/control-bridge-g2b...recovery/g2b-ssh-local-preservation-20260828` | diverged; recovery ahead 2 and behind 87; same `7205a647` merge-base. |

Relevant pull requests are: #11, G2-B to MCF, merged at `fbef3d4`; #26,
context/G2-A to MCF, merged at `dbd772a6c37452008b7c8debd58d2782127514db`;
#27, capsule synchronization to MCF, merged at `38cd22e`; and #21, G2-B Task
8 evidence to the historical G2-B branch, still open. Main does not contain a
safe, reviewed direct promotion of the divergent MCF line.

## Material content and available evidence

The MCF line contains G1/G2-A bounded read/context work and G2-B contracts,
executor, confined workspace writes, rollback/revocation, sudo boundary, and
disposable lifecycle work. Representative G2-B commits include `342f139`,
`0a0997e`, `25e02e4`, `8cd7d01`, `047495c`, `1a17bbd`, and `fbef3d4`.

The preserved recovery commit `7fa9ab9` contains the direct SSH adapter,
SSH-specific grant entrypoint, documentation/example, and related artifact and
adapter tests. It is preservation evidence only: it was created from a
divergent historical line and must not be merged directly.

For the exact preserved SSH payload, repository validation recorded 13 adapter
tests plus 7 bootstrap-artifact tests passing (20 total). The four requested
Ansible syntax checks remain pending because `ansible-playbook` was unavailable
in that controller environment. A regex secret scan over the staged payload and
`git diff --check` were clean; a full secret scanner still must run on the
replayed candidate.

Task 8 CI is not green: the latest checks visible for PR #21 failed before
meaningful validation, with disposable jobs skipped. Historical lab evidence,
including a 13/13 lifecycle record, does not convert those failed checks into
a green promotion gate and does not authorize a VPS action.

## Promotion decision

**Do not merge directly.** Do not merge MCF into main, do not merge the
recovery branch, and do not treat PR #21 as promotion-ready.

Create a fresh clean branch from the then-canonical target. Replay reviewed
components selectively in small, independently testable changes. In particular,
attempt `7fa9ab9` as a selective replay (not a branch merge), resolve and
review conflicts, and separately determine whether `ef2d10a` remains needed.
Before any pull request, run a full secret scanner, the 13+7 repository tests,
all four Ansible syntax checks, and CI on the new target SHA. A separate human
authorization is required for every VPS, SSH, grant, write, rollback,
revocation, activation, or production action.
