# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Regra zero — execute o protocolo antes de implementar

Não assuma que `main`, o último chat ou a última missão conhecida ainda representam o trabalho ativo.

Os controles obrigatórios estão em:

- `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`;
- `state/startup-recovery-protocol.yaml`;
- `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`;
- `state/mission-persistence-policy.yaml`.

Regras vinculantes:

```text
NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS
NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS
MAX_MATERIAL_WORK_WITHOUT_REMOTE_CHECKPOINT=30_MINUTES
WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE
```

Antes de qualquer mudança:

1. confirmar o repositório `leon337/cloud-infrastructure`;
2. identificar missão ativa, branch/base/PR e HEAD remoto reais;
3. quando houver acesso local, identificar worktree, HEAD, upstream, divergência local/remota, staged, unstaged e untracked;
4. ler `state/active-mission.yaml`, este `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml` e o estado específico da missão/capability;
5. verificar Issue/PR/commits/CI/evidência indicados pelo estado ativo;
6. identificar tarefas completas/parciais/bloqueadas, testes, blockers, ownership paralelo e HUMAN_GATEs;
7. produzir o recovery report definido pelo protocolo;
8. se as fontes divergirem, parar em `BLOCKED_RECONCILIATION`;
9. se a ação depender de autorização humana fechada, parar em `WAITING_HUMAN_GATE`;
10. para missão longa, verificar capacidade de persistência remota antes de acumular trabalho material e obedecer ao limite de 30 minutos;
11. nunca pedir, registrar ou versionar secrets.

Em modo remoto sem acesso ao computador, `LOCAL_STATE=UNVERIFIED`; isso não significa `CLEAN`.

## Precedência de verdade

```text
1. instrução atual explícita de LEANDRO
2. infraestrutura verificável para fatos operacionais do host
3. Git/GitHub live do branch/PR/SHA aplicável
4. state/active-mission.yaml
5. state/current.yaml + estado específico da capability
6. CHECKPOINT.md
7. decisões e especificações aprovadas
8. docs/runbooks/findings/evidence
9. history (registro histórico, não estado atual)
10. chats/sessões anteriores
```

Nenhuma fonte inferior pode sobrescrever silenciosamente uma superior. Histórico não deve ser reescrito para parecer estado presente.

## Missão ativa — continuidade e recuperação de contexto

```text
MISSION=REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING
MISSION_ISSUE=10
MISSION_DOC=docs/53-repository-continuity-context-recovery-mission.md
MISSION_STATE=state/active-mission.yaml
STARTUP_PROTOCOL=governance/AI-STARTUP-RECOVERY-PROTOCOL.md
STARTUP_PROTOCOL_STATE=state/startup-recovery-protocol.yaml
PERSISTENCE_POLICY=governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md
PERSISTENCE_POLICY_STATE=state/mission-persistence-policy.yaml
STATUS=ACTIVE
PRIORITY=P0_TRANSVERSAL
AUTHORITY=LEANDRO
ORCHESTRATOR=MESTRE_MCF
ACTIVE_BRANCH=codex/control-bridge-g2b
ACTIVE_PR=11_DRAFT_DO_NOT_MERGE
RECOVERY_CHECKPOINT_SHA=7205a647f918580d09c87ed44f38b0a433552a51
ROADMAP_R1=COMPLETE
ROADMAP_R2=COMPLETE
ROADMAP_R3=COMPLETE
ROADMAP_R4=COMPLETE
ROADMAP_R5=NEXT
NEXT_EXACT_STEP=R5_CREATE_INSTITUTIONAL_PROJECT_MEMORY_AND_FIRST_INCIDENT_MEMO
```

Objetivo: fazer o repositório explicar a si próprio e permitir recuperação de contexto sem depender de memória de chat ou de uma única máquina.

## G2-B — estado exato recuperado

```text
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
G2B_TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
G2B_TASK_7=PARTIAL
G2B_TASK_7_TESTS=6_PASS_1_FAIL
G2B_KNOWN_RED=EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED
G2B_KNOWN_RED_LITERAL=g2b_issue_existing_grant.keys()
G2B_ANSIBLE_SYNTAX=NOT_EXECUTED_CURRENT_LOCAL_ENVIRONMENT
G2B_TASKS_8_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
G2B_REAL_ROLLBACK=NOT_EXECUTED
G2B_REAL_REVOCATION=NOT_EXECUTED
NODE01_G2B_GATE=CLOSED
MERGE_G2B=NO
```

Fontes: `state/control-bridge-g2b.yaml`, `docs/54-control-bridge-g2b-recovery-checkpoint.md`, PR #11, especificação e plano G2-B.

O checkpoint WIP remoto preserva o trabalho incompleto; ele não transforma a Task 7 em `PASS`.

## Trabalho paralelo isolado

A trilha F1.2c continua existente e possui fatos/evidências próprios, porém não é o trabalho ativo desta missão.

```text
F1_2C_BRANCH=fix/f1-2c-systemd-runtime-lock
F1_2C_FOR_THIS_MISSION=ISOLATED_DO_NOT_MODIFY
F1_2C_OWNER=MESTRE_MCF_AND_LEANDRO
```

Não use o `next_exact_step` da trilha principal F1.2c como autorização para tocar nessa branch durante a missão de continuidade.

## Mapa canônico

| Pergunta | Fonte |
|---|---|
| Protocolo obrigatório de inicialização/recuperação | `governance/AI-STARTUP-RECOVERY-PROTOCOL.md` |
| Contrato machine-readable do protocolo | `state/startup-recovery-protocol.yaml` |
| Política de persistência para missões longas | `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md` |
| Contrato machine-readable de persistência | `state/mission-persistence-policy.yaml` |
| Qual missão está ativa? | `state/active-mission.yaml` |
| Documento da missão ativa | `docs/53-repository-continuity-context-recovery-mission.md` |
| Estado exato de continuidade | `CHECKPOINT.md` |
| Estado operacional estruturado | `state/current.yaml` |
| Estado específico G2-B | `state/control-bridge-g2b.yaml` |
| Checkpoint técnico recuperado G2-B | `docs/54-control-bridge-g2b-recovery-checkpoint.md` |
| Spec G2-B | `docs/superpowers/specs/2026-08-20-control-bridge-g2b-bounded-write-design.md` |
| Plano G2-B Tasks 1–10 | `docs/superpowers/plans/2026-08-20-control-bridge-g2b-bounded-write.md` |
| Checkpoint G2-A | `docs/52-control-bridge-g2a-implementation-checkpoint.md` |
| Platform Discovery Q1–Q40 | `state/platform-discovery.yaml` |
| Missão Codex original | `docs/CODEX-EXECUTION-MISSION-001.md` |
| Arquitetura / threat model | `docs/42-target-architecture.md`, `docs/43-threat-model-and-autonomy-boundaries.md` |
| Roadmap da trilha principal | `docs/45-revised-implementation-roadmap.md` |
| Histórico | `history/` |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md` |

## Baseline operacional da VPS — não confundir com observação fresca

Último baseline consolidado relevante permanece histórico e deve ser revalidado antes de mutações:

- Ubuntu 24.04.4 LTS, KVM/QEMU, 8 CPUs, ~23 GiB RAM, sem swap;
- SSH público em TCP 22, `ubuntu` por public key; root/password login desabilitados;
- UFW ativo/default deny incoming e fail2ban protegendo SSH;
- sudo exige senha; sem `NOPASSWD`; `ubuntu` fora do grupo `lxd` e LXD inativo;
- Cloud Workstation XFCE/LightDM/XRDP sobre túnel SSH validada historicamente;
- backup sanitizado ativo, porém restore/rebuild funcional amplo ainda não provado;
- produção continua não autorizada e rotação de credenciais permanece adiada por decisão humana.

Fatos voláteis devem ser medidos novamente antes de qualquer operação real.

## Guardrails centrais

- LEANDRO é a autoridade humana final.
- HUMAN_GATE sempre exige autorização explícita de LEANDRO.
- MESTRE/MCF orquestra a missão ativa.
- `RECOVERY_VERDICT=PASS` não abre automaticamente nenhum HUMAN_GATE.
- Missões longas devem persistir trabalho material remotamente no máximo a cada 30 minutos, ou antes quando ocorrer um trigger obrigatório.
- WIP remoto preserva continuidade; não prova aceitação.
- Se persistência remota falhar, preservar localmente, registrar o blocker e não continuar acumulando horas de trabalho material.
- Capabilities devem ser escopadas e auditáveis; não existe autorização administrativa genérica implícita.
- Secrets continuam proibidos no Git.
- Mudanças críticas exigem impacto, rollback e evidência.
- Produção externa continua sujeita a HUMAN_GATE.
- G2-B não autoriza shell arbitrário, root direto, Docker socket, Git mutante, administração do host ou produção.

## Ponto exato

A missão de continuidade concluiu R1, R2, R3 e R4. O próximo passo é exclusivamente:

```text
R5_CREATE_INSTITUTIONAL_PROJECT_MEMORY_AND_FIRST_INCIDENT_MEMO
```

A retomada técnica da Task 7 do G2-B pertence ao R8. Até lá, não corrigir o RED da Task 7, não iniciar Task 8 e não executar bootstrap/grant/write no NODE-01.
