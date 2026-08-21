# Cloud Infrastructure

## MISSÃO ATIVA DE CONTINUIDADE

A missão transversal ativa é **Repository Continuity & Context Recovery Hardening**.

```text
MISSION_ISSUE=10
MISSION_DOC=docs/53-repository-continuity-context-recovery-mission.md
MISSION_STATE=state/active-mission.yaml
STARTUP_PROTOCOL=governance/AI-STARTUP-RECOVERY-PROTOCOL.md
STARTUP_PROTOCOL_STATE=state/startup-recovery-protocol.yaml
PERSISTENCE_POLICY=governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md
PERSISTENCE_POLICY_STATE=state/mission-persistence-policy.yaml
INSTITUTIONAL_MEMORY=state/institutional-memory.yaml
FIRST_INCIDENT_MEMO=history/memos/2026-08-20-g2b-local-work-recovery-incident.md
DRIFT_CONTROLS=governance/CONTINUITY-DRIFT-CONTROLS.md
DRIFT_CONTROLS_STATE=state/continuity-drift-controls.yaml
DRIFT_CHECKER=scripts/check_continuity_drift.py
G2B_RECOVERY_CHECKPOINT=docs/54-control-bridge-g2b-recovery-checkpoint.md
ACTIVE_BRANCH=codex/control-bridge-g2b
ACTIVE_PR=11_DRAFT_DO_NOT_MERGE
RECOVERY_CHECKPOINT_SHA=7205a647f918580d09c87ed44f38b0a433552a51
TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
TASK_7=PARTIAL_6_PASS_1_FAIL
TASKS_8_10=NOT_STARTED
NODE01_G2B_GATE=CLOSED
F1_2C=PARALLEL_ISOLATED_DO_NOT_MODIFY
ROADMAP_R1=COMPLETE
ROADMAP_R2=COMPLETE
ROADMAP_R3=COMPLETE
ROADMAP_R4=COMPLETE
ROADMAP_R5=COMPLETE
ROADMAP_R6=COMPLETE
ROADMAP_R7=NEXT
ROADMAP_R8=NOT_STARTED
R2_STRUCTURAL_RECONCILIATION=PASS
GITHUB_ACTIONS_CONTENT_VALIDATION=PENDING_CURRENT_HEAD
NEXT_EXACT_STEP=R7_EXECUTE_COLD_START_RECOVERY_VALIDATION
```

> Nova IA/agente: execute primeiro [`governance/AI-STARTUP-RECOVERY-PROTOCOL.md`](governance/AI-STARTUP-RECOVERY-PROTOCOL.md), usando o contrato [`state/startup-recovery-protocol.yaml`](state/startup-recovery-protocol.yaml). Depois leia [`state/active-mission.yaml`](state/active-mission.yaml), [`CONTEXT.md`](CONTEXT.md) e [`CHECKPOINT.md`](CHECKPOINT.md). Não implemente antes de `RECOVERY_VERDICT=PASS` e não assuma estado local `CLEAN` quando ele não puder ser verificado.

> Missões longas também devem obedecer [`governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`](governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md) e [`state/mission-persistence-policy.yaml`](state/mission-persistence-policy.yaml). Trabalho material não deve ficar mais de 30 minutos sem checkpoint remoto recuperável quando o remoto estiver disponível; WIP publicado não significa aceitação.

> Eventos materiais devem ser preservados pela memória institucional em [`history/memos/`](history/memos/) e [`state/institutional-memory.yaml`](state/institutional-memory.yaml). Drift entre fontes canônicas deve falhar fechado conforme [`governance/CONTINUITY-DRIFT-CONTROLS.md`](governance/CONTINUITY-DRIFT-CONTROLS.md) e `scripts/check_continuity_drift.py`.

> A seção `PROJECT_STATUS` abaixo é uma projeção gerada da **trilha principal da plataforma**. Ela não substitui o estado da missão transversal ativa acima.

<!-- PROJECT_STATUS:START -->
## STATUS ATUAL

- **Status geral:** `IMPLEMENTATION_IN_PROGRESS`
- **Progresso:** 3/32 slices `DONE`; slice atual `PARTIAL`
- **Slice atual:** `F1.2c` — Network Enforcement
- **Concluídos:** S0, F1.1, F1.2b
- **Próximos:** F1.3, F1.4, F1.5
- **HUMAN_GATEs no roadmap:** 4 (F1.2a, F1.5, F1.6, F5.4)
- **Próximo passo exato:** `SLICE_002C_VERIFY_RUNNER_AND_APPLY_NODE_01_NETWORK_SERVICES`
- **Último checkpoint:** `F1_2C_NODE_01_SERVICES_COMMIT_BOUND_CI_PASS`
- **Último commit relevante:** [`f771cfd`](https://github.com/leon337/cloud-infrastructure/commit/f771cfd09f1824562ddfdaea507fb3cb0781f6ac)
- **Última CI material:** [run `32131461110`](https://github.com/leon337/cloud-infrastructure/actions/runs/32131461110) — `PASS`
- **GitHub Project:** `BLOCKED_EXTERNAL_MISSING_READ_PROJECT_AND_PROJECT_SCOPES`
- **Produção:** `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`
- **Rotação de credenciais:** `DEFERRED_BY_HUMAN_DECISION`
- **Atualizado em:** `2026-08-20`

> Esta seção é gerada das fontes canônicas; não edite manualmente.
<!-- PROJECT_STATUS:END -->

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO aprende a administrar, diagnosticar, recuperar e reconstruir o ambiente com mínima dependência de IA. O projeto é separado do MCF; a VPS poderá hospedar o framework e outros sistemas, mas a infraestrutura não pertence estruturalmente a ele.

## Continuidade

O repositório implementa o PUC v1.0. `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`, `state/startup-recovery-protocol.yaml`, `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`, `state/mission-persistence-policy.yaml`, `state/institutional-memory.yaml`, `governance/CONTINUITY-DRIFT-CONTROLS.md`, `state/continuity-drift-controls.yaml`, `state/active-mission.yaml`, `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml` formam a entrada de continuidade. `docs/`, `decisions/`, `findings/`, `history/`, `runbooks/`, `recovery/`, `assets/` e `governance/` preservam o contexto por tipo. Chats e sessões de subagentes são temporários; Git/GitHub devem conter o estado recuperável antes de uma missão depender deles.

A capability transversal **MCF VPS Control Plane / Control Bridge** possui continuidade própria para não sobrescrever a trilha principal F1.2c. O estado específico está em `state/control-bridge-g2b.yaml`; o checkpoint técnico recuperado está em `docs/54-control-bridge-g2b-recovery-checkpoint.md`; o estado da missão de recuperação está em `state/active-mission.yaml` e `docs/53-repository-continuity-context-recovery-mission.md`.

GitHub live, branch/PR aplicável, código, testes e evidência do SHA aplicável prevalecem sobre afirmações históricas. Em divergência entre fontes, o agente deve retornar `BLOCKED_RECONCILIATION`; não deve escolher silenciosamente a versão mais conveniente.

## Control Bridge — estado transversal reconciliado

```text
CONTROL_BRIDGE_G2B=TASK_7_PARTIAL_RECOVERED_REMOTE
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
G2B_TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
G2B_TASK_7=PARTIAL_6_PASS_1_FAIL
G2B_TASKS_8_10=NOT_STARTED
G2B_REAL_WRITE=NOT_EXECUTED
G2B_PR=11_DRAFT_DO_NOT_MERGE
MESTRE_MCF=CURRENT_ORCHESTRATOR
LEANDRO=FINAL_HUMAN_AUTHORITY
F1_2C_SYSTEMD_RUNTIME_LOCK=PARALLEL_ISOLATED_DO_NOT_MODIFY
NODE01_G2B_GATE=CLOSED
```

O checkpoint remoto `7205a647f918580d09c87ed44f38b0a433552a51` preserva o WIP recuperado e **não** significa aceitação da Task 7. O RED conhecido é a ausência da validação exata de chaves do grant existente (`g2b_issue_existing_grant.keys()`); a sintaxe Ansible da Task 7 ainda não foi executada no ambiente local recuperado.

## Estado operacional — baseline reconciliada em 16/08/2026

- FASE 0, FASE 1 e FASE 2: **DONE**.
- `ubuntu`/publickey é o único login SSH permitido; root e autenticação SSH por senha estão desabilitados pela política efetiva.
- UFW está ativo com `deny incoming` e somente OpenSSH em TCP 22; fail2ban protege o SSH.
- sudo exige senha; não existe regra `NOPASSWD`; `ubuntu` saiu do grupo `lxd` e o LXD está desabilitado/inativo.
- VNC do provedor foi revalidado como console out-of-band; Rescue está disponível, snapshots não estão configurados, backup do provedor não está contratado e firewall do provedor não está configurado.
- backup diário sanitizado de configurações está ativo; a primeira cópia off-host teve hash validado e o archive passou em teste de extração, não em restore funcional.
- zero atualizações APT pendentes após upgrade e reboot final.

## Cloud Workstation

A Cloud Workstation está **FUNCTIONAL_AND_VALIDATED**: XFCE + LightDM, XRDP restrito a `127.0.0.1:3389` e acesso somente por túnel SSH. Firefox oficial em pacote DEB, VS Code, terminal, Thunar, múltiplas janelas, clipboard bidirecional, resolução dinâmica, logout/login, desconexão/reconexão, persistência e reboot foram testados.

Recursos são fatos voláteis. A recuperação da missão observou 8 CPUs, 23 GiB de RAM total, sem swap e raiz de 290 GiB; uso atual deve ser medido antes de cada slice. Os números de ~2,2 GiB RAM/~7,5 GiB disco pertencem ao snapshot histórico da validação final da Workstation.

## Implementação atual

Q1–Q39 definem a arquitetura vinculante e Q40-D autoriza o Codex a selecionar as tecnologias e implementar incrementalmente a plataforma DEV/lab. A missão está em [`docs/CODEX-EXECUTION-MISSION-001.md`](docs/CODEX-EXECUTION-MISSION-001.md) e o roadmap da trilha principal em [`docs/45-revised-implementation-roadmap.md`](docs/45-revised-implementation-roadmap.md). A camada de acompanhamento está documentada em [`docs/48-status-layer-v1.md`](docs/48-status-layer-v1.md).

F1.1 e F1.2b estão concluídos no NODE-01. A trilha F1.2c mantém seu próprio estado e evidência, mas está isolada desta missão de continuidade. O `PROJECT_STATUS` continua representando essa trilha principal e não autoriza sua execução enquanto a missão ativa de continuidade estiver sendo trabalhada.

Produção não está autorizada e a rotação permanece adiada por decisão humana.
