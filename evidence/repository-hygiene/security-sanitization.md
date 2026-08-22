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
