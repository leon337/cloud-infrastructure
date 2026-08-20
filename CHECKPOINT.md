# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-20 após recuperação, publicação remota do G2-B e reconciliação das entradas canônicas de contexto.

## Missão ativa

```text
MISSION=REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING
MISSION_ISSUE=10
MISSION_DOC=docs/53-repository-continuity-context-recovery-mission.md
MISSION_STATE=state/active-mission.yaml
G2B_RECOVERY_CHECKPOINT=docs/54-control-bridge-g2b-recovery-checkpoint.md
STATUS=ACTIVE
AUTHORITY=LEANDRO
ORCHESTRATOR=MESTRE_MCF
ROADMAP_R1=COMPLETE
ROADMAP_R2=COMPLETE
ROADMAP_R3=NEXT
NEXT_EXACT_STEP=R3_DEFINE_MANDATORY_AI_PROJECT_STARTUP_AND_RECOVERY_PROTOCOL
```

Esta missão é transversal. Ela não reabre o desenho G2-B nem autoriza mutação do NODE-01.

## Checkpoint remoto recuperado do G2-B

```text
BRANCH=codex/control-bridge-g2b
BASE=mcf/mission-001-control-bridge-g1
RECOVERY_CHECKPOINT_SHA=7205a647f918580d09c87ed44f38b0a433552a51
PR=11_DRAFT_DO_NOT_MERGE
COMMITS_AHEAD_OF_BASE_AT_RECOVERY=25
TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
TASK_7=PARTIAL
TASK_7_TESTS=6_PASS_1_FAIL
KNOWN_RED=EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED
KNOWN_RED_LITERAL=g2b_issue_existing_grant.keys()
ANSIBLE_SYNTAX=NOT_EXECUTED_CURRENT_LOCAL_ENVIRONMENT
TASKS_8_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
G2B_REAL_ROLLBACK=NOT_EXECUTED
G2B_REAL_REVOCATION=NOT_EXECUTED
MCF_EFFECTIVE_USE=NOT_EXECUTED
```

O commit `7205a647...` é um **checkpoint de preservação WIP**, não uma aceitação da Task 7.

## HUMAN_GATEs e limites fechados

```text
NODE01_G2B_BOOTSTRAP=NOT_AUTHORIZED
REAL_GRANT_ISSUE_OR_REISSUE=NOT_AUTHORIZED
REAL_BOUNDED_WRITE=NOT_AUTHORIZED
PRODUCTION_MUTATION=NOT_AUTHORIZED
MERGE_G2B=NO
TASK_8=DO_NOT_START_WHILE_TASK_7_PARTIAL
```

Nenhuma dessas condições pode ser inferida como autorizada a partir de commits, PR, issue, testes ou documentação.

## Trabalho paralelo isolado

```text
F1_2C_BRANCH=fix/f1-2c-systemd-runtime-lock
F1_2C_FOR_THIS_MISSION=ISOLATED_DO_NOT_MODIFY
F1_2C_OWNER=MESTRE_MCF_AND_LEANDRO
```

A trilha F1.2c mantém sua própria evidência e seu próximo passo histórico/técnico. Ela não é o próximo passo da missão ativa de continuidade.

## Trilhas já comprovadas

### F1.1

`DONE` no NODE-01 com check mode, backup off-host, apply, idempotência e invariância comprovados. Evidência detalhada permanece nos documentos e estados históricos da trilha principal.

### F1.2b

`DONE` com runtime Docker vazio, lifecycle controlado e invariância real comprovada. Primeiro workload continua condicionado à network enforcement.

### F1.2c

A base de enforcement foi aplicada e testada historicamente; o trabalho posterior da branch `fix/f1-2c-systemd-runtime-lock` permanece paralelo e fora de escopo desta missão. Não executar ações nessa branch a partir deste checkpoint.

### Control Bridge G1/G2-A

```text
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
SHELL=NOT_IMPLEMENTED
SUDO=NOT_GRANTED
DOCKER_SOCKET=NOT_GRANTED
PRODUCTION=NOT_AUTHORIZED
```

Fonte detalhada: `docs/52-control-bridge-g2a-implementation-checkpoint.md`.

## Fontes canônicas para retomada

1. `state/active-mission.yaml`
2. `CONTEXT.md`
3. `CHECKPOINT.md`
4. `state/current.yaml`
5. `state/control-bridge-g2b.yaml`
6. `docs/53-repository-continuity-context-recovery-mission.md`
7. `docs/54-control-bridge-g2b-recovery-checkpoint.md`
8. Issue #10
9. PR #11
10. spec e plano G2-B
11. evidência Git/CI aplicável

Em caso de divergência, reconciliar antes de agir. Chats não são fonte canônica.

## Próximo passo exato da missão ativa

```text
R3_DEFINE_MANDATORY_AI_PROJECT_STARTUP_AND_RECOVERY_PROTOCOL
```

## Próximo passo técnico G2-B — BLOQUEADO ATÉ R8

```text
FIX_EXISTING_GRANT_EXACT_KEY_SCHEMA_THEN_RETEST_TASK_7
```

Não executar esse passo agora. Ele existe apenas para permitir recuperação precisa do ponto técnico quando o roadmap chegar ao R8.

## Estado da trilha principal da plataforma

O status executivo F1.2c ainda é projetado pela região `PROJECT_STATUS` do README a partir de `state/current.yaml` e `docs/45-revised-implementation-roadmap.md`. Essa projeção representa a trilha principal e não substitui a missão transversal ativa.

Produção continua `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` e rotação de credenciais continua `DEFERRED_BY_HUMAN_DECISION`.
