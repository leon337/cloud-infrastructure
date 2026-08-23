# Security / Sanitization Audit

No secret values are reproduced in this report.

## Findings

1. PR #18's final reconciliation diff did not introduce a secret; current `main` is its squash `f2e01dfa`.
2. Repository/full-history scanning still reports **9 pre-existing historical `credential-in-uri` findings**. Values remain redacted. Classification: `HISTORICAL_SECURITY_DEBT_REQUIRES_SEPARATE_REVIEW`.
3. `platform/sudoers/mcf-control-g2b` on the active protected line contains intentional constrained `NOPASSWD`, not `NOPASSWD: ALL`: it is limited to four exact executor subcommands and switches to the dedicated `mcf-workspace` service account.
4. The G2-B installed executor refuses root, checks the service-account UID, constrains imports and operations, clears the environment and bounds input/output. Removing that boundary as generic sudo hygiene would redesign G2-B and is prohibited.
5. No evidence inspected supports generic `docker.sock` authority or an arbitrary-shell interface for agents.
6. Temporary terminal/probe residues are addressed through branch lifecycle; current main already removed their temporary workflows.

## Result

`SECURITY_SANITIZATION=PASS_CURRENT_DIFF_WITH_HISTORICAL_DEBT`

No history rewrite or G2-B security-boundary change was performed. The nine historical scanner hits remain a redacted follow-up review item.

## Revalidation addendum — 2026-08-23

The 2026-08-22 finding that nine historical `credential-in-uri` blobs required separate review is now **superseded as a current blocker**. PR #22 head `f39464daf4a4c5508d891e61f4ddd6394afd08fd` classified all 9/9 through a full private mirror as symbolic GitHub workflow runtime authentication references, with **0 literal historical credential URI findings**. The scanner now distinguishes symbolic runtime references from literal credentials while remaining fail-closed for literals. No history rewrite, force-push or credential rotation was required.

Current security revalidation evidence: `evidence/repository-hygiene/revalidation-2026-08-23.md`.
