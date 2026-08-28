# CONTEXT — Porta de entrada canônica

Checklist de leitura rápida: `ROADMAP-CHECKLIST.md`.

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Regra zero — execute o protocolo antes de implementar

Não assuma que `main`, o último chat ou a última missão conhecida ainda representam o trabalho ativo.

Os controles obrigatórios estão em:

- `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`;
- `state/startup-recovery-protocol.yaml`;
- `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`;
- `state/mission-persistence-policy.yaml`;
- `state/institutional-memory.yaml`;
- `governance/CONTINUITY-DRIFT-CONTROLS.md`;
- `state/continuity-drift-controls.yaml`;
- `state/cold-start-validation.yaml`.

Regras vinculantes:

```text
NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS
NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS
MAX_MATERIAL_WORK_WITHOUT_REMOTE_CHECKPOINT=30_MINUTES
WIP_CHECKPOINT_DOES_NOT_IMPLY_ACCEPTANCE
NO_CONTINUITY_ADVANCE_WITH_UNEXPLAINED_CANONICAL_DRIFT
```

Antes de qualquer mudança:

1. confirmar o repositório `leon337/cloud-infrastructure`;
2. identificar missão ativa, branch/base/PR e HEAD remoto reais;
3. quando houver acesso local, identificar worktree, HEAD, upstream, divergência local/remota, staged, unstaged e untracked;
4. ler `state/active-mission.yaml`, este `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml` e o estado específico da missão/capability;
5. verificar Issue/PR/commits/CI/evidência indicados pelo estado ativo;
6. identificar tarefas completas/parciais/bloqueadas, testes, blockers, ownership paralelo e HUMAN_GATEs;
7. produzir o recovery report definido pelo protocolo;
8. executar `scripts/check_continuity_drift.py` quando o ambiente do repositório estiver disponível;
9. se as fontes divergirem, parar em `BLOCKED_RECONCILIATION`;
10. se a ação depender de autorização humana fechada, parar em `WAITING_HUMAN_GATE`;
11. para missão longa, verificar capacidade de persistência remota antes de acumular trabalho material e obedecer ao limite de 30 minutos;
12. nunca pedir, registrar ou versionar secrets.

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

## Missão ativa — Control Bridge G2-B

```text
MISSION=CONTROL_BRIDGE_G2B
MISSION_STATE=state/active-mission.yaml
CONTINUITY_MISSION=REPOSITORY_CONTINUITY_CONTEXT_RECOVERY_HARDENING
CONTINUITY_MISSION_ISSUE=10
CONTINUITY_MISSION_STATUS=COMPLETE
CONTINUITY_MISSION_DOC=docs/53-repository-continuity-context-recovery-mission.md
AUTHORITY=LEANDRO
ORCHESTRATOR=MESTRE_MCF
ACTIVE_BRANCH=codex/context-bridge-reconcile-20260823
ACTIVE_PR=NONE_LOCAL_ONLY_NO_PUSH
ROADMAP_R1=COMPLETE
ROADMAP_R2=COMPLETE
ROADMAP_R3=COMPLETE
ROADMAP_R4=COMPLETE
ROADMAP_R5=COMPLETE
ROADMAP_R6=COMPLETE
ROADMAP_R7=COMPLETE
ROADMAP_R8=COMPLETE
R7_VERDICT=PASS_REPOSITORY_ONLY_STATE_RECONSTRUCTION_HISTORICAL_SNAPSHOT
NEXT_EXACT_STEP=REVIEW_LOCAL_RECONCILED_CANDIDATE_BEFORE_PUBLICATION_OR_TASK_9
```

A missão de continuidade concluiu R1–R8 e devolveu a missão ativa ao G2-B. Os controles criados continuam obrigatórios. O R7 permanece evidência histórica do estado pré-R8 e não deve ser reescrito.

## G2-B — estado atual

```text
G1=PASS_REAL_NODE_01_ROUNDTRIP_HISTORIC_LIVE_REQUIRED
G2A=PASS_REAL_NODE_01_READ_ONLY_HISTORIC_LIVE_REQUIRED
G2B_TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
G2B_TASK_7=COMPLETE
G2B_TASK_7_TESTS=7_PASS_0_FAIL
G2B_KNOWN_RED=RESOLVED_EXISTING_GRANT_EXACT_KEY_SET_ENFORCED
G2B_ANSIBLE_SYNTAX=PASS_3_SELF_HOSTED_TARGET_SHA_604E6D0E
G2B_TASK_8=PASS_DISPOSABLE_NOTEBOOK_DOCKER_13_OF_13
G2B_TASK_8_CANDIDATE_SHA=570779b75ba41ac3725ef16bc65a163e01631a1c
G2B_LIFECYCLE=LAB_VALIDATED_INACTIVE
TASKS_9_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
G2B_REAL_ROLLBACK=NOT_EXECUTED
G2B_REAL_REVOCATION=NOT_EXECUTED
NODE01_G2B_GATE=CLOSED
MERGE_G2B=NO
```

Fontes atuais: `.mcf/project-capsule.yaml`, `context/mcf-cloud-context.yaml`, `state/control-bridge-g2b.yaml`, `state/active-mission.yaml` e `evidence/CONTROL-BRIDGE-G2B/TASK-8-RECONCILED-LAB-20260823.md`. O checkpoint `docs/54-control-bridge-g2b-recovery-checkpoint.md`, Issue #10 e PR #11 permanecem históricos.

Task 8 passou apenas no laboratório Docker descartável do notebook (`--network none`) com 13/13 marcadores e cleanup. Esse resultado não ativa G2-B e não autoriza Tasks 9/10, transporte mutante pelo Context, NODE-01, grant real, escrita real, publicação, merge ou produção. G2-A preserva evidência histórica read-only, mas todo uso material requer verificação live.

## Trabalho paralelo isolado

A trilha F1.2c continua existente e possui fatos/evidências próprios, porém não é o trabalho ativo desta missão.

```text
F1_2C_BRANCH=fix/f1-2c-systemd-runtime-lock
F1_2C_FOR_THIS_MISSION=ISOLATED_DO_NOT_MODIFY
F1_2C_OWNER=MESTRE_MCF_AND_LEANDRO
```

Não use o `next_exact_step` da trilha principal F1.2c como autorização para tocar nessa branch durante a missão de continuidade.

## Memória institucional

Eventos históricos materiais são preservados separadamente do estado corrente:

- contrato: `state/institutional-memory.yaml`;
- memos: `history/memos/`;
- primeiro memo: `history/memos/2026-08-20-g2b-local-work-recovery-incident.md`.

Memos são append-oriented e não devem ser silenciosamente reescritos para parecer entendimento posterior. Correções materiais exigem novo registro ou adendo explícito.

## Controles de drift

A coerência entre as fontes canônicas é validada por:

- `governance/CONTINUITY-DRIFT-CONTROLS.md`;
- `state/continuity-drift-controls.yaml`;
- `scripts/check_continuity_drift.py`;
- `tests/test_continuity_drift_controls.py`;
- `scripts/test.sh` / Foundation CI.

Um drift inexplicado bloqueia avanço de continuidade; não deve ser mascarado por escolha silenciosa de uma fonte.

## Validação de cold start

R7 está registrado em:

- `docs/55-cold-start-recovery-validation-2026-08-21.md`;
- `state/cold-start-validation.yaml`;
- `scripts/reconstruct_cold_start.py`;
- `tests/test_cold_start_recovery.py`.

Veredicto: `PASS_REPOSITORY_ONLY_STATE_RECONSTRUCTION`. GitHub Actions permaneceu inconclusiva como evidência de conteúdo quando os jobs falharam antes de expor steps/logs.

## Mapa canônico

| Pergunta | Fonte |
|---|---|
| Protocolo obrigatório de inicialização/recuperação | `governance/AI-STARTUP-RECOVERY-PROTOCOL.md` |
| Contrato machine-readable do protocolo | `state/startup-recovery-protocol.yaml` |
| Política de persistência para missões longas | `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md` |
| Contrato machine-readable de persistência | `state/mission-persistence-policy.yaml` |
| Memória institucional | `state/institutional-memory.yaml`, `history/memos/` |
| Controles de drift | `governance/CONTINUITY-DRIFT-CONTROLS.md`, `state/continuity-drift-controls.yaml` |
| Evidência R7 cold start | `state/cold-start-validation.yaml`, `docs/55-cold-start-recovery-validation-2026-08-21.md` |
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
- R8 concluída não equivale a autorização de bootstrap, grant, escrita, produção ou merge.
- Antes de iniciar Task 8, executar novamente o protocolo de startup/recovery e reconciliar estado local/remoto aplicável.
- Missões longas devem persistir trabalho material remotamente no máximo a cada 30 minutos, ou antes quando ocorrer um trigger obrigatório.
- WIP remoto preserva continuidade; não prova aceitação.
- Se persistência remota falhar, preservar localmente, registrar o blocker e não continuar acumulando horas de trabalho material.
- Capabilities devem ser escopadas e auditáveis; não existe autorização administrativa genérica implícita.
- Secrets continuam proibidos no Git.
- Mudanças críticas exigem impacto, rollback e evidência.
- Produção externa continua sujeita a HUMAN_GATE.
- G2-B não autoriza shell arbitrário, root direto, Docker socket, Git mutante, administração do host ou produção.

## Ponto exato

A missão de continuidade concluiu R1–R8 e a Task 7 está aceita. O próximo passo técnico é:

```text
G2B_TASK8_PROVE_COMPLETE_LIFECYCLE_DISPOSABLE_BOUNDARY
```

Task 8 permanece `NOT_STARTED`; nenhum HUMAN_GATE foi aberto pela conclusão da R8.
