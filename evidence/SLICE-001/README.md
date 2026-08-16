# Evidence — SLICE-001 Foundations F1.1

Esta pasta contém evidência sanitizada do primeiro incremento. Evidência de
preparação não prova aplicação na VPS.

## Cadeia

| Etapa | Estado |
|---|---|
| Mission Acceptance + Recovery | `RECORDED` |
| GitHub `main`/SHA/cleanliness | `HISTORICAL_BASELINE_PASS` |
| VPS read-only baseline | `OBSERVED_AT_2026-08-16T19:46:14Z` |
| Unprivileged DEV identity preflight | `PASS_CHANGED_0_AT_2026-08-16T20:58:00Z` |
| Physical-host test-inventory guard | `REFUSED_BEFORE_MUTATION_EXIT_2` |
| Technology Mapping official-source review | `REVIEWED_AT_2026-08-16` |
| Desired-state unit/schema/negative tests | `PASS_CURRENT_WORKTREE_NOT_COMMIT_BOUND` |
| Ansible syntax check | `PASS_CURRENT_WORKTREE_NOT_COMMIT_BOUND` |
| Disposable Ubuntu check mode | `PENDING_REVALIDATION_AFTER_REVIEW_DELTA` |
| Disposable Ubuntu apply/idempotence/rollback | `PENDING_REVALIDATION_AFTER_REVIEW_DELTA` |
| Real VPS privileged check mode | `WAITING_HUMAN_INTERACTION` |
| VPS apply | `NOT_EXECUTED` |
| Second reconcile `changed=0` | `NOT_EXECUTED` |
| Post-apply invariance | `NOT_EXECUTED` |
| Rollback drill | `NOT_EXECUTED` |

`NOT_EXECUTED` nunca deve ser interpretado como `PASS`.

Os resultados históricos da fixture continuam registrados em `test-results.md`,
mas não valem para o delta revisado até nova execução completa. O commit/CI final
deve vincular os testes ao tree efetivamente publicado antes do checkpoint.
