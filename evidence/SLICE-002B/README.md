# Evidence — SLICE-002B Docker runtime boundary

Esta pasta contém o contrato e a evidência sanitizada do desired state e da
integração privilegiada em VM descartável, além do preview real sem mutação. O
apply no NODE-01 continua não executado.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Seleção/pins/licença | `RECORDED` |
| Desired state | `PASS_LOCAL_COMMIT_7015C80` |
| Suíte estática | `PASS_66_TESTS_6_SHELLCHECK_6_ANSIBLE_SYNTAX` |
| CI estática | `PASS_RUN_31996516019_COMMIT_FA66F10` |
| VM Ubuntu 24.04 descartável — check mode | `PASS_NO_MUTATION` |
| VM descartável — apply | `PASS_CHANGED_13` |
| VM descartável — segunda reconciliação | `PASS_CHANGED_0` |
| VM descartável — security/restart/negative checks | `PASS` |
| VM descartável — rollback e cleanup | `PASS_CLEAN` |
| Pré-requisito F1.1 no NODE-01 | `DONE_APPLY_7_IDEMPOTENCE_0_INVARIANCE_PASS` |
| Check mode F1.2b no NODE-01 | `PASS_NO_MUTATION_2026-08-17T08:37:46Z` |
| Apply F1.2b no NODE-01 | `NOT_EXECUTED` |
| Primeiro workload no NODE-01 | `BLOCKED_BY_F1_2C` |

O run `31996516019` está ligado ao commit
`fa66f1049bac5540a5b12219186a421cc39dcbc0` e cobre APT, systemd, Docker vazio,
limites de socket/rede, recusas e rollback na VM descartável. O guard corrigido
passou no run `32007871491`, commit `9e9ae28`. O apply `NOT_EXECUTED` no NODE-01
nunca deve ser interpretado como `PASS`.

## Limite da evidência

O fechamento real F1.1 em `2026-08-17T06:58:43Z` confirmou Docker e containerd
ausentes e liberou o check mode F1.2b. O preview passou sem mutação e a leitura
posterior confirmou o runtime ainda ausente. O teste
privilegiado completo é permitido somente em VM descartável comprovada pelo
harness, nunca na Workstation ou no NODE-01.

Mesmo depois de CI verde e instalação vazia, F1.2b não prova Q20/Q34 e não
autoriza workloads. F1.2c precisa demonstrar isolamento, egress e service
discovery antes do primeiro container.
