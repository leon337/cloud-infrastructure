# Security / Sanitization Audit

No secret values are reproduced in this report. Any potential secret-bearing material is referenced only by category and location class.

## Findings

### 1. Current reconciliation diff

PR #18 documented a focused secret scan of its final README-only reconciliation and reported no newly introduced secret. That PR was squash-merged to current `main` as `f2e01dfa`.

### 2. Historical repository scan debt

The same PR records that the repository-wide/full-history scanner still reports **9 pre-existing historical `credential-in-uri` findings**. Values are intentionally redacted here.

Classification: `HISTORICAL_SECURITY_DEBT_REQUIRES_SEPARATE_REVIEW`.

This hygiene mission must not rewrite Git history to erase them: rewriting would violate the protected-branch/no-history-rewrite boundary and could lose evidence. Whether the historical strings are live credentials, already-rotated placeholders or false positives must be verified separately without printing them.

### 3. NOPASSWD boundary in active G2-B

`platform/sudoers/mcf-control-g2b` contains an intentional `NOPASSWD` rule. It is **not** `NOPASSWD: ALL`; it is limited to four exact subcommands of `/usr/local/libexec/mcf-control-g2b` and executes as the dedicated `mcf-workspace` service account.

The installed Python boundary:

- refuses effective UID 0;
- requires the exact service-account UID;
- accepts only four fixed operations;
- constrains application imports to the installed root;
- clears the inherited environment;
- bounds stdin/stdout;
- converts unexpected failures to a bounded refusal.

Classification: `INTENTIONAL_CONSTRAINED_PRIVILEGE_BOUNDARY — KEEP`. Removing it as generic NOPASSWD hygiene would redesign G2-B and is prohibited.

### 4. Shell / Docker authority

In the inspected Control Bridge material:

- G2-A is read-only and does not grant shell, sudo or Docker socket access;
- G2-B workflow calls the bounded executor, not an arbitrary shell interface exposed to requests;
- no evidence reviewed in this mission supports a generic `docker.sock` grant to agents;
- G2-B's helper explicitly refuses root execution.

No correction is authorized or required here.

### 5. Temporary operational artifacts

Temporary terminal/probe branches exist and are addressed by branch hygiene. Current `main` has already removed the corresponding temporary workflows. Branches with exclusive commits must be archived/reviewed before deletion rather than deleted solely because they are test/ops refs.

### 6. Operational identifiers

Current state/history includes public infrastructure identifiers, SSH host fingerprints and local private-key *paths*. These are operational metadata, not private key material. No private key body was observed in the files inspected for this mission.

## Result

`SECURITY_SANITIZATION=PASS_CURRENT_DIFF_WITH_HISTORICAL_DEBT`

No security correction commit was made because the only material unresolved finding is historical and cannot be safely remediated within the no-history-rewrite boundary. The nine historical scanner hits remain a follow-up security review item; values must stay redacted.
