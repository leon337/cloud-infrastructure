# 53 — Repository Continuity & Context Recovery Hardening

Data: 2026-08-20  
Status: **ACTIVE**  
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

O relato histórico permanente deste incidente será criado na etapa R5 como memorando institucional; este documento registra a missão e o estado corrente, não substitui o futuro memo histórico.

## Estado recuperado e publicado

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

- estado estruturado da missão ativa: `state/active-mission.yaml`;
- porta de entrada: `CONTEXT.md`;
- checkpoint corrente: `CHECKPOINT.md`;
- estado geral estruturado: `state/current.yaml`;
- estado específico G2-B: `state/control-bridge-g2b.yaml`;
- especificação G2-B: `docs/superpowers/specs/2026-08-20-control-bridge-g2b-bounded-write-design.md`;
- plano G2-B: `docs/superpowers/plans/2026-08-20-control-bridge-g2b-bounded-write.md`;
- Issue #10: tracker remoto desta missão;
- PR #11: preservação remota do G2-B recuperado.

Em divergência, nenhuma fonte documental deve ser escolhida silenciosamente. O executor deve reconciliar Git/GitHub, estado estruturado, checkpoint, evidência e instrução humana antes de continuar.

## Roadmap oficial

### R1 — Preserve and publish recovered G2-B state

**Status:** COMPLETE.

A branch local foi publicada, o checkpoint WIP foi preservado e o PR #11 foi criado como draft. Nenhuma conclusão indevida da Task 7 foi declarada.

### R2 — Reconcile canonical project entrypoints

**Status:** COMPLETE nesta revisão documental.

Reconciliar `README.md`, `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml`, estado G2-B e documentos de continuidade para distinguir a missão ativa da trilha principal F1.2c.

### R3 — Mandatory AI/project startup and recovery protocol

**Status:** NEXT.

Definir protocolo obrigatório de identificação de repositório, branch/worktree, divergência local/remota, fontes canônicas, missão ativa, testes, blockers, HUMAN_GATEs e reconciliação fail-closed antes de implementação.

### R4 — Persistence policy for long-running missions

**Status:** NOT_STARTED.

Definir commits por Task, checkpoints WIP, persistência remota segura, sincronização do ledger e retomada após reboot, rate limit ou perda de sessão.

### R5 — Institutional project memory

**Status:** NOT_STARTED.

Criar mecanismo permanente de memorandos para incidentes, mudanças de objetivo, decisões, descobertas e recuperações. O primeiro memorando registrará o incidente de 2026-08-20.

### R6 — Consistency and drift controls

**Status:** NOT_STARTED.

Criar controles para detectar documentação stale, missão/branch incompatível, ledger atrás do Git, PASS sem evidência, HUMAN_GATE ambíguo e ausência de próximo passo.

### R7 — Cold-start recovery validation

**Status:** NOT_STARTED.

Uma IA sem contexto anterior deverá reconstruir corretamente o projeto usando apenas o repositório/GitHub.

### R8 — Resume G2-B Task 7

**Status:** NOT_STARTED.

Somente após a fundação de continuidade: corrigir o gap exato do schema do grant existente, rerodar testes, validar sintaxe Ansible em ambiente aprovado, revisar independentemente a Task 7 e apenas então considerar Task 8.

## Limites atuais

Não estão autorizados por esta missão:

- bootstrap G2-B no NODE-01;
- emissão ou reemissão real de grant;
- escrita real G2-B;
- produção;
- merge do G2-B;
- alteração ou tomada de ownership da branch `fix/f1-2c-systemd-runtime-lock`;
- marcação da Task 7 como concluída sem evidência.

## Próximo passo exato

```text
R3_DEFINE_MANDATORY_AI_PROJECT_STARTUP_AND_RECOVERY_PROTOCOL
```
