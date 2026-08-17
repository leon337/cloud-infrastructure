# Evidence — SLICE-002B Docker runtime boundary

Esta pasta contém o contrato e a evidência sanitizada do desired state repo-only
do runtime. Neste checkpoint, nenhum resultado prova integração privilegiada ou
instalação no NODE-01.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Seleção/pins/licença | `RECORDED` |
| Desired state | `PASS_LOCAL_COMMIT_7015C80` |
| Suíte estática local do delta final | `PASS_55_TESTS_6_SHELLCHECK_6_ANSIBLE_SYNTAX` |
| CI estática | `PENDING` |
| VM Ubuntu 24.04 descartável — check mode | `PENDING` |
| VM descartável — apply | `PENDING` |
| VM descartável — segunda reconciliação | `PENDING` |
| VM descartável — security/restart/negative checks | `PENDING` |
| VM descartável — rollback e cleanup | `PENDING` |
| Pré-requisito F1.1 no NODE-01 | `BLOCKED_NOT_APPLIED` |
| Check mode F1.2b no NODE-01 | `NOT_EXECUTED` |
| Apply F1.2b no NODE-01 | `NOT_EXECUTED` |
| Primeiro workload no NODE-01 | `BLOCKED_BY_F1_2C` |

`PENDING` e `NOT_EXECUTED` nunca devem ser interpretados como `PASS`. O PASS local
cobre parsing/policies/unitários/ShellCheck/syntax-check, não APT, systemd,
Docker, firewall ou rollback dinâmicos. Uma execução CI futura precisa registrar
URL, run ID, commit e jobs no `baseline.yaml`; texto manual não pode antecipar o
resultado.

## Limite da evidência

O último baseline read-only conhecido continua em SLICE-001, onde Docker e
containerd estavam ausentes. F1.2b não reobservou nem alterou a VPS. O teste
privilegiado completo é permitido somente em VM descartável comprovada pelo
harness, nunca na Workstation ou no NODE-01.

Mesmo depois de CI verde e instalação vazia, F1.2b não prova Q20/Q34 e não
autoriza workloads. F1.2c precisa demonstrar isolamento, egress e service
discovery antes do primeiro container.
