# Repository Hygiene — Before

Snapshot: 2026-08-22 (America/Recife)
Repository: `leon337/cloud-infrastructure`

## Protected refs

- `main` — `f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`
- `mcf/mission-001-control-bridge-g1` — `3e34044c0fb10429fe2f7a262dec21932479f143`
- `codex/control-bridge-g2b` — `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`

No protected ref may be deleted, rewritten or force-pushed by this mission.

## Branches before sanitization (23)

1. `codex/control-bridge-g2b`
2. `codex/mission-001-f1-2c-network-enforcement`
3. `codex/mission-001-foundations-f1-1`
4. `codex/mission-001-foundations-f1-2b-preparation`
5. `codex/mission-001`
6. `codex/r8-task7-candidate-20260822`
7. `continuity-protocol-v1-final`
8. `continuity-protocol-v1-review`
9. `continuity-protocol-v1-staging`
10. `continuity-protocol-v1`
11. `fix/f1-2c-systemd-runtime-lock`
12. `main`
13. `mcf/f1-2c-exact-head-ci-20260819`
14. `mcf/mission-001-control-bridge-g1`
15. `mcf/terminal-hell-word-main-test`
16. `mcf/terminal-hell-word-test`
17. `ops/g2b-cancel-long-waiters-20260822`
18. `ops/g2b-status-output-20260822`
19. `ops/open-browser-vps-20260822`
20. `ops/r8-task7-syntax-selfhosted-20260822`
21. `ops/vps-sync-bootstrap-20260821`
22. `test/caixa-de-pandora`
23. `validation/evidence-inheritance-tool-20260819`

Sanitization branches created after this snapshot are intentionally excluded from the before-count.

## Pull requests before sanitization

Open drafts observed: `#1`, `#2`, `#3`, `#7`, `#8`, `#9`, `#11`.

Closed PRs observed: `#6`, `#12`, `#13`, `#14`, `#18`.

`#11` is the active G2-B draft and is explicitly protected from closure or redesign by this mission.

## Issues before sanitization

- Open: `#4` G1 handshake evidence; `#5` G2-A read-only evidence.
- Closed/completed: `#10` continuity hardening; `#15`, `#16`, `#17` temporary terminal/probe missions.

## Workflows observed

No persistent workflow remained visible on `main` after the temporary terminal workflows were removed on 2026-08-22. The active protected G2-B line contains:

- `.github/workflows/control-bridge-g1.yml`
- `.github/workflows/control-bridge-g2a-bootstrap.yml`
- `.github/workflows/control-bridge-g2a.yml`
- `.github/workflows/control-bridge-g2b-ci.yml`
- `.github/workflows/control-bridge-g2b.yml`
- `.github/workflows/docker-boundary-ci.yml`
- `.github/workflows/foundation-ci.yml`

The first five inspected Control Bridge jobs use bounded timeouts; self-hosted Control Bridge jobs use `timeout-minutes: 10`. The G2-B disposable lifecycle runs on GitHub-hosted `ubuntu-24.04`, not on the NODE-01 self-hosted runner.

## Initial constraints

- G2-B code/design/state on the protected branch is read-only for this mission.
- F1.2c parallel work is preserved.
- No NODE-01 privileged operation is required for repository hygiene.
- Branch deletion is forbidden until preservation evidence and final integration tests exist.
