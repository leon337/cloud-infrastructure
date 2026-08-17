# Evidence — SLICE-002B Docker runtime boundary

Esta pasta contém o contrato e a evidência sanitizada do desired state e da
integração privilegiada em VM descartável. Nenhum resultado prova instalação no
NODE-01.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Seleção/pins/licença | `RECORDED` |
| Desired state | `PASS_LOCAL_COMMIT_7015C80` |
| Suíte estática | `PASS_63_TESTS_6_SHELLCHECK_6_ANSIBLE_SYNTAX` |
| CI estática | `PASS_RUN_31996516019_COMMIT_FA66F10` |
| VM Ubuntu 24.04 descartável — check mode | `PASS_NO_MUTATION` |
| VM descartável — apply | `PASS_CHANGED_13` |
| VM descartável — segunda reconciliação | `PASS_CHANGED_0` |
| VM descartável — security/restart/negative checks | `PASS` |
| VM descartável — rollback e cleanup | `PASS_CLEAN` |
| Pré-requisito F1.1 no NODE-01 | `BLOCKED_NOT_APPLIED` |
| Check mode F1.2b no NODE-01 | `NOT_EXECUTED` |
| Apply F1.2b no NODE-01 | `NOT_EXECUTED` |
| Primeiro workload no NODE-01 | `BLOCKED_BY_F1_2C` |

O run `31996516019` está ligado ao commit
`fa66f1049bac5540a5b12219186a421cc39dcbc0` e cobre APT, systemd, Docker vazio,
limites de socket/rede, recusas e rollback na VM descartável. `NOT_EXECUTED` no
NODE-01 nunca deve ser interpretado como `PASS`; a atualização documental
posterior também não muda o escopo do run commit-bound.

## Limite da evidência

O último baseline read-only conhecido continua em SLICE-001, onde Docker e
containerd estavam ausentes. F1.2b não reobservou nem alterou a VPS. O teste
privilegiado completo é permitido somente em VM descartável comprovada pelo
harness, nunca na Workstation ou no NODE-01.

Mesmo depois de CI verde e instalação vazia, F1.2b não prova Q20/Q34 e não
autoriza workloads. F1.2c precisa demonstrar isolamento, egress e service
discovery antes do primeiro container.
