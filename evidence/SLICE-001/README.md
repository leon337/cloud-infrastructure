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
| Desired-state unit/schema/negative tests | `PASS_CI_RUN_31972460567_COMMIT_EDD2497D` |
| Ansible syntax check | `PASS_CI_RUN_31972460567_COMMIT_EDD2497D` |
| Disposable Ubuntu check mode/invariance | `PASS_CI_RUN_31972460567_COMMIT_EDD2497D` |
| Disposable Ubuntu apply/idempotence/rollback | `PASS_CI_RUN_31972460567_COMMIT_EDD2497D` |
| Checkpoint HEAD CI | `PASS_RUN_31973125852_COMMIT_DA7DF70` |
| Fresh pre-preview DEV baseline | `PASS_READ_ONLY_AT_2026-08-16T21:23:21Z` |
| Real VPS privileged check mode | `PASS_NO_MUTATION_AT_2026-08-17T05:48:16Z` |
| Post-preview read-only invariance | `PASS_AT_2026-08-17T05:52:15Z` |
| VPS apply | `NOT_EXECUTED` |
| Second reconcile `changed=0` | `NOT_EXECUTED` |
| Post-apply invariance | `NOT_EXECUTED` |
| Rollback drill | `NOT_EXECUTED` |

`NOT_EXECUTED` nunca deve ser interpretado como `PASS`.

O run GitHub Actions
[`31972460567`](https://github.com/leon337/cloud-infrastructure/actions/runs/31972460567)
passou para o commit de implementação
`edd2497d657cc9bc35952f5dfc71090a18dade53`. Os resultados anteriores da fixture
continuam registrados apenas como histórico. Esta atualização de evidência é
posterior àquele SHA. O check mode privilegiado real foi executado depois, sem
mutação, e não é atribuído ao run descartável.

O checkpoint posterior `da7df7070b31c019242900375664ab9eada3894f` também passou
integralmente no run
[`31973125852`](https://github.com/leon337/cloud-infrastructure/actions/runs/31973125852).
O baseline read-only imediatamente posterior confirmou ausência de drift e de
objetos/lock F1.1. Esta atualização de evidência é posterior ao run e não altera
nenhum artefato executável.

Em `2026-08-17T05:48:16Z`, LEANDRO digitou a senha sudo somente no prompt local
do Ansible. O preview real terminou com `localhost ok=6 changed=0` e `node-01
ok=28 changed=4 failed=0 unreachable=0 skipped=22`. Os quatro grupos simulados
foram marker, grupo técnico, declaração tmpfiles e duas slices de accounting.
O log local sanitizado tem SHA-256
`370d53f6dd1c9138cc0bab7ce852edb32f05d4f8c0b7359d7fb372f8edd479d6`;
nenhuma senha ou chave foi persistida. A leitura posterior confirmou todos os
objetos F1.1 ainda ausentes e os serviços essenciais invariantes.
