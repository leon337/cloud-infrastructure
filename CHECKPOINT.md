# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Checklist canônico de leitura rápida: `ROADMAP-CHECKLIST.md`.

Atualizado em 2026-08-23 após reconciliar G1/G2-A e comprovar a Task 8 somente em laboratório local descartável.

## Missão ativa

```text
MISSION=CONTROL_BRIDGE_G2B
MISSION_STATE=state/active-mission.yaml
CONTINUITY_MISSION_ISSUE=10
CONTINUITY_MISSION_STATUS=COMPLETE
CONTINUITY_MISSION_DOC=docs/53-repository-continuity-context-recovery-mission.md
STARTUP_PROTOCOL=governance/AI-STARTUP-RECOVERY-PROTOCOL.md
PERSISTENCE_POLICY=governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md
INSTITUTIONAL_MEMORY=state/institutional-memory.yaml
R8_MEMO=history/memos/2026-08-22-r8-task7-completion.md
DRIFT_CONTROLS=governance/CONTINUITY-DRIFT-CONTROLS.md
COLD_START_R7_SNAPSHOT=state/cold-start-validation.yaml
G2B_RECOVERY_CHECKPOINT=docs/54-control-bridge-g2b-recovery-checkpoint.md
STATUS=REVIEW_REQUIRED
AUTHORITY=LEANDRO
ORCHESTRATOR=MESTRE_MCF
ROADMAP_R1=COMPLETE
ROADMAP_R2=COMPLETE
ROADMAP_R3=COMPLETE
ROADMAP_R4=COMPLETE
ROADMAP_R5=COMPLETE
ROADMAP_R6=COMPLETE
ROADMAP_R7=COMPLETE
ROADMAP_R8=COMPLETE
TASK_7=COMPLETE_7_PASS_0_FAIL
TASK_7_ANSIBLE_SYNTAX=PASS_3_SELF_HOSTED
ACTIVE_BRANCH=codex/context-bridge-reconcile-20260823
ACTIVE_PR=NONE_LOCAL_ONLY_NO_PUSH
TASK_8=PASS_DISPOSABLE_NOTEBOOK_DOCKER_13_OF_13
TASK_8_CANDIDATE_SHA=570779b75ba41ac3725ef16bc65a163e01631a1c
G2B_LIFECYCLE=LAB_VALIDATED_INACTIVE
TASKS_9_10=NOT_STARTED
NEXT_EXACT_STEP=REVIEW_LOCAL_RECONCILED_CANDIDATE_BEFORE_PUBLICATION_OR_TASK_9
```

A missão transversal de continuidade foi concluída. Seus controles permanecem ativos. O laboratório Task 8 passou com 13/13 marcadores e cleanup, mas G2-B permanece inativo e não abriu Tasks 9/10, transporte mutante pelo Context, NODE-01, grant real, escrita real, produção, publicação ou merge.

## Regras obrigatórias de retomada, persistência, memória e drift

Qualquer nova IA/agente ou operador recuperando o projeto deve executar `CLOUD_INFRA_AI_STARTUP_RECOVERY_V1` antes de implementar.

```text
NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS
```

Toda missão longa também deve obedecer `CLOUD_INFRA_LONG_RUNNING_MISSION_PERSISTENCE_V1`:

```text
NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS
MAX_MATERIAL_WORK_WITHOUT_REMOTE_CHECKPOINT=30_MINUTES
WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE
SESSION_STATE_IS_NOT_DURABLE_STATE
```

Memória institucional:

```text
HISTORICAL_MEMORY_IS_APPEND_ORIENTED
NO_SILENT_RETROACTIVE_REWRITE
```

Drift de continuidade:

```text
NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT
```

Fontes:

- `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`;
- `state/startup-recovery-protocol.yaml`;
- `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`;
- `state/mission-persistence-policy.yaml`;
- `state/institutional-memory.yaml`;
- `history/memos/`;
- `governance/CONTINUITY-DRIFT-CONTROLS.md`;
- `state/continuity-drift-controls.yaml`;
- `scripts/check_continuity_drift.py`;
- `state/cold-start-validation.yaml`;
- `docs/55-cold-start-recovery-validation-2026-08-21.md`.

Veredictos válidos do protocolo de recuperação:

```text
PASS
PASS_READ_ONLY
BLOCKED_RECONCILIATION
WAITING_HUMAN_GATE
```

Somente `PASS` permite considerar mutação dentro do escopo recuperado, e mesmo assim nenhum HUMAN_GATE é aberto automaticamente. Em modo remoto sem acesso ao computador, o estado local deve ser declarado `UNVERIFIED`, nunca presumido `CLEAN`.

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
TASK_8=BLOCKED_EXTERNAL
TASKS_9_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
G2B_REAL_ROLLBACK=NOT_EXECUTED
G2B_REAL_REVOCATION=NOT_EXECUTED
MCF_EFFECTIVE_USE=NOT_EXECUTED
```

O commit `7205a647...` é um **checkpoint de preservação WIP**, não uma aceitação da Task 7.

## R5 — memória institucional

R5 criou:

- `history/memos/README.md`;
- `history/memos/2026-08-20-g2b-local-work-recovery-incident.md`;
- `state/institutional-memory.yaml`.

O incidente de 20/08/2026 agora possui memo permanente separado do estado corrente. Memos são append-oriented e correções materiais exigem novo registro/adendo explícito.

## R6 — consistência e drift

R6 criou:

- `governance/CONTINUITY-DRIFT-CONTROLS.md`;
- `state/continuity-drift-controls.yaml`;
- `scripts/check_continuity_drift.py`;
- `tests/test_continuity_drift_controls.py`;
- integração do checker em `scripts/test.sh`.

O checker cobre identidade da missão, branch/PR, roadmap, próximo passo, preservação da Task 7, HUMAN_GATEs, ownership paralelo, memória institucional, coerência de `state/current.yaml` e exigência de evidência para R7.

## R7 — cold-start recovery validation

R7 criou:

- `scripts/reconstruct_cold_start.py`;
- `tests/test_cold_start_recovery.py`;
- `docs/55-cold-start-recovery-validation-2026-08-21.md`;
- `state/cold-start-validation.yaml`.

A reconstrução repository-only recuperou corretamente missão, branch, PR draft, Tasks 1–6, Task 7 `PARTIAL_6_PASS_1_FAIL`, RED conhecido, Tasks 8–10, isolamento F1.2c, gates fechados e próximo passo. O veredicto é:

```text
PASS_REPOSITORY_ONLY_STATE_RECONSTRUCTION
```

Limitação: o papel de validação foi executado na mesma sessão do MCF; isto prova suficiência/coerência das fontes, não independência cognitiva de uma instância externa.

GitHub Actions permaneceu `INCONCLUSIVE` como evidência de conteúdo quando jobs `validate` falharam sem steps e logs utilizáveis; nenhuma causa de conteúdo foi inferida.

## HUMAN_GATEs e limites fechados

```text
NODE01_G2B_BOOTSTRAP=NOT_AUTHORIZED
REAL_GRANT_ISSUE_OR_REISSUE=NOT_AUTHORIZED
REAL_BOUNDED_WRITE=NOT_AUTHORIZED
PRODUCTION_MUTATION=NOT_AUTHORIZED
MERGE_G2B=NO
TASK_8=DO_NOT_START_WHILE_TASK_7_PARTIAL
```

Nenhuma dessas condições pode ser inferida como autorizada a partir de R7, commits, PR, issue, testes, documentação, checkpoint remoto ou `RECOVERY_VERDICT=PASS`.

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
G1=PASS_REAL_NODE_01_ROUNDTRIP_HISTORIC_LIVE_REQUIRED
G2A=PASS_REAL_NODE_01_READ_ONLY_HISTORIC_LIVE_REQUIRED
SHELL=NOT_IMPLEMENTED
SUDO=NOT_GRANTED
DOCKER_SOCKET=NOT_GRANTED
PRODUCTION=NOT_AUTHORIZED
```

Fonte detalhada: `docs/52-control-bridge-g2a-implementation-checkpoint.md`.

## Fontes canônicas para retomada

1. `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`
2. `state/startup-recovery-protocol.yaml`
3. `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`
4. `state/mission-persistence-policy.yaml`
5. `state/institutional-memory.yaml`
6. `governance/CONTINUITY-DRIFT-CONTROLS.md`
7. `state/continuity-drift-controls.yaml`
8. `state/cold-start-validation.yaml`
9. `state/active-mission.yaml`
10. `CONTEXT.md`
11. `CHECKPOINT.md`
12. `state/current.yaml`
13. `state/control-bridge-g2b.yaml`
14. `docs/53-repository-continuity-context-recovery-mission.md`
15. `docs/54-control-bridge-g2b-recovery-checkpoint.md`
16. `docs/55-cold-start-recovery-validation-2026-08-21.md`
17. Issue #10
18. PR #11
19. spec e plano G2-B
20. evidência Git/CI aplicável

Em caso de divergência, aplicar o protocolo e parar em `BLOCKED_RECONCILIATION`. Chats não são fonte canônica.

## Próximo passo exato da missão ativa

```text
G2B_TASK8_PROVE_COMPLETE_LIFECYCLE_DISPOSABLE_BOUNDARY
```

## R8 — COMPLETE

Evidência de conclusão:

```text
RECOVERY_VERDICT=PASS
TASK_7_RED=RESOLVED_EXISTING_GRANT_EXACT_KEY_SET_ENFORCED
FOCUSED_TESTS=7_PASS_0_FAIL
LOCAL_REGRESSION=367_TESTS_PASS_15_SHELL_SYNTAX_PASS
ANSIBLE_SYNTAX=3_PASS_SELF_HOSTED
TASK_7_CANDIDATE_SHA=604e6d0e1fb1feddb7f271c58c9e8baf2cc0b390
GITHUB_HOSTED_CI=INCONCLUSIVE_ACTION_REQUIRED_NO_JOBS_OBSERVED_AFTER_R8_PUBLICATION
TASK_8=NOT_STARTED
```

A validação self-hosted executou somente testes e syntax-checks; não houve playbook apply, bootstrap NODE-01, grant, escrita real, produção ou merge.

## Estado da trilha principal da plataforma

O status executivo F1.2c ainda é projetado pela região `PROJECT_STATUS` do README a partir de `state/current.yaml` e `docs/45-revised-implementation-roadmap.md`. Essa projeção representa a trilha principal e não substitui a missão transversal ativa.

Produção continua `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` e rotação de credenciais continua `DEFERRED_BY_HUMAN_DECISION`.
