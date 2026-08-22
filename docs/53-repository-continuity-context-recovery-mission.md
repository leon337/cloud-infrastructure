# 53 — Repository Continuity & Context Recovery Hardening

Data: 2026-08-20  
Status: **COMPLETE — R1–R8**
Prioridade: **P0 transversal**  
Autoridade humana: **LEANDRO**  
Orquestração: **MESTRE / MCF**  
Issue remota: **#10**  
Branch ativa: `codex/control-bridge-g2b`  
PR: **#11 — DRAFT / DO NOT MERGE**

## Objetivo

Tornar o próprio repositório a fonte canônica e recuperável de contexto para que uma nova instância autorizada de ChatGPT, Codex ou outra IA consiga reconstruir o estado real do projeto sem depender de histórico de chat, memória de sessão ou de um único computador.

Esta missão não reabre o desenho técnico aprovado do G2-B e não autoriza mutações no NODE-01. Ela consolida, publica, documenta e endurece a continuidade do trabalho já realizado.

## Evento que originou a missão

Em 2026-08-20, várias horas de implementação do G2-B permaneceram apenas em um worktree local. Um reinício inesperado do computador encerrou subagentes temporários. Os commits e arquivos sobreviveram no disco, mas a branch ainda não estava publicada no GitHub. Mais tarde, o Codex atingiu o limite de mensagens durante a Task 7.

A recuperação exigiu reconstrução manual usando conversa, screenshots, Git worktrees, commits locais, reflog, ledger e arquivos não rastreados. O evento demonstrou uma lacuna de engenharia: a continuidade ainda dependia excessivamente de memória de sessão e estado local.

O relato histórico permanente deste incidente foi criado no R5 em `history/memos/2026-08-20-g2b-local-work-recovery-incident.md`. Este documento registra a missão e o estado corrente; o memo histórico preserva o que aconteceu e por que importou.

## Estado recuperado e publicado — snapshot histórico pré-R8

```text
BRANCH=codex/control-bridge-g2b
BASE=mcf/mission-001-control-bridge-g1
RECOVERY_CHECKPOINT_SHA=7205a647f918580d09c87ed44f38b0a433552a51
PR=11_DRAFT_DO_NOT_MERGE
TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
TASK_7=PARTIAL
TASK_7_TESTS=6_PASS_1_FAIL
KNOWN_RED=EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED
ANSIBLE_SYNTAX=NOT_EXECUTED_CURRENT_LOCAL_ENVIRONMENT
TASKS_8_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
NODE01_G2B_GATE=CLOSED
F1_2C=PARALLEL_ISOLATED_DO_NOT_MODIFY
```

O checkpoint remoto é preservação, não aceitação da Task 7.

## Fontes canônicas de continuidade

- protocolo obrigatório: `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`;
- contrato machine-readable do protocolo: `state/startup-recovery-protocol.yaml`;
- política de persistência para missões longas: `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`;
- contrato machine-readable de persistência: `state/mission-persistence-policy.yaml`;
- memória institucional: `state/institutional-memory.yaml` e `history/memos/`;
- controles de drift: `governance/CONTINUITY-DRIFT-CONTROLS.md`, `state/continuity-drift-controls.yaml`, `scripts/check_continuity_drift.py`;
- evidência de cold start: `state/cold-start-validation.yaml`, `docs/55-cold-start-recovery-validation-2026-08-21.md`;
- estado estruturado da missão ativa: `state/active-mission.yaml`;
- porta de entrada: `CONTEXT.md`;
- checkpoint corrente: `CHECKPOINT.md`;
- estado geral estruturado: `state/current.yaml`;
- estado específico G2-B: `state/control-bridge-g2b.yaml`;
- checkpoint técnico G2-B recuperado: `docs/54-control-bridge-g2b-recovery-checkpoint.md`;
- especificação G2-B: `docs/superpowers/specs/2026-08-20-control-bridge-g2b-bounded-write-design.md`;
- plano G2-B: `docs/superpowers/plans/2026-08-20-control-bridge-g2b-bounded-write.md`;
- Issue #10: tracker remoto desta missão;
- PR #11: preservação remota do G2-B recuperado.

Em divergência, nenhuma fonte documental deve ser escolhida silenciosamente. O executor deve executar o protocolo e parar em `BLOCKED_RECONCILIATION` até Git/GitHub, estado estruturado, checkpoint, evidência e instrução humana estarem reconciliados.

## Roadmap oficial

### R1 — Preserve and publish recovered G2-B state

**Status:** COMPLETE.

A branch local foi publicada, o checkpoint WIP foi preservado e o PR #11 foi criado como draft. Nenhuma conclusão indevida da Task 7 foi declarada.

### R2 — Reconcile canonical project entrypoints

**Status:** COMPLETE.

Foram reconciliados `README.md`, `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml`, `state/control-bridge-g2b.yaml`, `state/active-mission.yaml`, este documento, `docs/54-control-bridge-g2b-recovery-checkpoint.md` e o teste de continuidade correspondente.

A trilha principal F1.2c permanece preservada como projeção separada; a missão transversal ativa possui estado explícito e próximo passo próprio.

### R3 — Mandatory AI/project startup and recovery protocol

**Status:** COMPLETE.

Foi formalizado `CLOUD_INFRA_AI_STARTUP_RECOVERY_V1` em duas camadas:

- `governance/AI-STARTUP-RECOVERY-PROTOCOL.md` — regra normativa;
- `state/startup-recovery-protocol.yaml` — contrato machine-readable.

O protocolo exige, antes de implementação, reconstrução da identidade do repositório, missão, branch/base/PR/HEAD, estado local quando disponível, fontes canônicas, evidência GitHub, tarefas/testes/blockers, ownership, HUMAN_GATEs e próximo passo exato.

Veredictos permitidos:

```text
PASS
PASS_READ_ONLY
BLOCKED_RECONCILIATION
WAITING_HUMAN_GATE
```

Regra central:

```text
NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS
```

`PASS` não abre HUMAN_GATE. Em modo remoto sem acesso local, o estado local deve ser `UNVERIFIED`, nunca inferido como `CLEAN`.

### R4 — Persistence policy for long-running missions

**Status:** COMPLETE.

Foi formalizado `CLOUD_INFRA_LONG_RUNNING_MISSION_PERSISTENCE_V1` em duas camadas:

- `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md` — política normativa;
- `state/mission-persistence-policy.yaml` — contrato machine-readable.

Regras centrais:

```text
NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS
MAX_MATERIAL_WORK_WITHOUT_REMOTE_CHECKPOINT=30_MINUTES
WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE
SESSION_STATE_IS_NOT_DURABLE_STATE
```

A política determina checkpoint por Task/slice, revisão/correção material, mudança de estado, HUMAN_GATE, pausa/handoff e limite temporal; preflight de persistência; WIP sem falsa aceitação; sincronização de estado/Git; responsabilidade do controlador pela durabilidade; recuperação obrigatória após reboot/rate-limit/perda de sessão; e fail-closed quando persistência remota quebra.

### R5 — Institutional project memory

**Status:** COMPLETE.

Foi criado o mecanismo institucional append-oriented:

- `history/memos/README.md`;
- `state/institutional-memory.yaml`;
- `history/memos/2026-08-20-g2b-local-work-recovery-incident.md`.

O primeiro memo preserva o incidente de 20/08/2026, seu impacto, limites de evidência, recuperação, lacuna comprovada, ações corretivas/preventivas e riscos residuais. Correções históricas materiais exigem novo memo/adendo; não existe reescrita retrospectiva silenciosa.

### R6 — Consistency and drift controls

**Status:** COMPLETE.

Foram criados:

- `governance/CONTINUITY-DRIFT-CONTROLS.md`;
- `state/continuity-drift-controls.yaml`;
- `scripts/check_continuity_drift.py`;
- `tests/test_continuity_drift_controls.py`;
- integração do checker em `scripts/test.sh`.

Regra central:

```text
NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT
```

Os controles cobrem identidade da missão, branch/PR, lifecycle do roadmap, next exact step, coerência das entradas canônicas, preservação do estado G2-B, HUMAN_GATEs, ownership paralelo, memória institucional, `state/current.yaml`, PASS sem evidência e requisito de evidência para R7.

### R7 — Cold-start recovery validation

**Status:** COMPLETE.

Artefatos:

- `scripts/reconstruct_cold_start.py`;
- `tests/test_cold_start_recovery.py`;
- `docs/55-cold-start-recovery-validation-2026-08-21.md`;
- `state/cold-start-validation.yaml`.

A reconstrução repository-only recuperou corretamente:

```text
ACTIVE_MISSION=REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING
BRANCH=codex/control-bridge-g2b
PR=11_DRAFT_DO_NOT_MERGE
TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
TASK_7=PARTIAL_6_PASS_1_FAIL
KNOWN_RED=EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED
TASKS_8_10=NOT_STARTED
F1_2C=ISOLATED_DO_NOT_MODIFY
NODE01_G2B_GATE=CLOSED_NOT_AUTHORIZED
REAL_GRANT_GATE=CLOSED_NOT_AUTHORIZED
REAL_WRITE_GATE=CLOSED_NOT_AUTHORIZED
REAL_WRITE_EXECUTED=false
MERGE_G2B=CLOSED_NOT_AUTHORIZED
```

Veredicto:

```text
PASS_REPOSITORY_ONLY_STATE_RECONSTRUCTION
```

Limitação explícita: o papel validador executou dentro da mesma sessão MCF; o R7 prova suficiência e coerência das fontes de repositório/GitHub, não independência cognitiva de uma instância externa separada.

O commit de reconciliação final de `state/current.yaml` foi auditado e alterou apenas a região de continuidade/missão, preservando evidências históricas não relacionadas.

A CI GitHub permanece tratada como `INCONCLUSIVE` quando jobs `validate` falham antes de expor steps/logs; isso não é reinterpretado como falha ou PASS de conteúdo.

### R8 — Resume G2-B Task 7

**Status:** COMPLETE.

A sessão executou novamente o protocolo de startup/recovery e obteve `RECOVERY_VERDICT=PASS`. O RED conhecido foi reproduzido em 6/7 e corrigido de forma fail-closed exigindo o conjunto exato de chaves do grant existente.

Evidências:

```text
TASK_7_CANDIDATE_SHA=604e6d0e1fb1feddb7f271c58c9e8baf2cc0b390
FOCUSED_TESTS=7_PASS_0_FAIL
LOCAL_REGRESSION=PASS_367_TESTS_15_SHELL_SYNTAX
ANSIBLE_SYNTAX=PASS_3_SELF_HOSTED
GITHUB_HOSTED_FOUNDATION_RUN=32548752333_INCONCLUSIVE_PRE_STEP_ZERO_STEPS_BLOB_NOT_FOUND
ROLE_REVIEW=PASS_SAME_SESSION_MCF_ROLE_NOT_EXTERNAL_INDEPENDENT
```

A prova self-hosted foi limitada a testes e `--syntax-check`; não executou apply, bootstrap, emissão de grant ou escrita real. A falha do GitHub-hosted runner foi classificada como infraestrutura pré-step e não como falha de conteúdo.

Após o encerramento da missão de continuidade, Task 8 foi iniciada pela missão G2-B. O harness e os contratos estáticos foram implementados e validados, mas a prova privilegiada em boundary Ubuntu 24.04/systemd está `BLOCKED_EXTERNAL`: o run `32551353362` e sua reexecução falharam antes de qualquer step (`steps=0`, logs `BlobNotFound`). O plano proíbe reroteamento para NODE-01.

## Limites atuais

Continuam fechados:

- bootstrap G2-B no NODE-01;
- emissão ou reemissão real de grant;
- escrita real G2-B;
- produção;
- merge do G2-B;
- alteração ou tomada de ownership da branch `fix/f1-2c-systemd-runtime-lock`;
- marcação da Task 7 como concluída sem evidência.

## Próximo passo exato

A missão de continuidade está concluída e a missão ativa retorna ao Control Bridge G2-B:

```text
HUMAN_REVIEW_AND_AUTHORIZE_QEMU_TCG_HOST_PACKAGES
```

Task 8 deve respeitar o plano aprovado: boundary Ubuntu 24.04/systemd descartável, nunca NODE-01.

## Encerramento da missão de continuidade

R1–R8 estão `COMPLETE`. Os protocolos, memória institucional, drift controls e cold-start evidence permanecem ativos como infraestrutura permanente de continuidade. O snapshot R7 continua histórico; o estado corrente está em `state/active-mission.yaml`, `state/current.yaml` e `state/control-bridge-g2b.yaml`.
