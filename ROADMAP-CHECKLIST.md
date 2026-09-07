# ROADMAP CHECKLIST — ESTADO CANÔNICO ATUAL

Atualizado em: **2026-09-07**
Repositório: `leon337/cloud-infrastructure`
Branch de trabalho G2-B: `team/g2b-task9-prebootstrap-gate-20260907`
PR: `#56 DRAFT / DO NOT MERGE`
Fonte machine-readable: `state/current.yaml` + `state/control-bridge-g2b.yaml`

> Regra: um item só recebe `[x]` quando sua evidência aplicável sustenta conclusão. `BLOCKED_EXTERNAL`, `WAITING_HUMAN_GATE`, `PARTIAL`, `CONDITIONAL` e `PLANNED` permanecem `[ ]`.

## Continuidade e recuperação

- [x] R1 — preservar/publicar G2-B recuperado — `COMPLETE`
- [x] R2 — reconciliar entrypoints canônicos — `COMPLETE`
- [x] R3 — protocolo obrigatório startup/recovery — `COMPLETE`
- [x] R4 — persistência de missões longas — `COMPLETE`
- [x] R5 — memória institucional — `COMPLETE`
- [x] R6 — controles de consistência/drift — `COMPLETE`
- [x] R7 — cold-start recovery validation — `COMPLETE`
- [x] R8 — concluir G2-B Task 7 — `COMPLETE`

## Control Bridge

- [x] G1 — roundtrip real NODE-01 histórico — `PASS_REAL_NODE_01_ROUNDTRIP_HISTORIC_LIVE_REQUIRED`
- [x] G2-A — leitura real NODE-01 histórica — `PASS_REAL_NODE_01_READ_ONLY_HISTORIC_LIVE_REQUIRED`
- [x] G2-B Tasks 1–6 — `COMPLETE_MATERIALLY_REVIEWED`
- [x] G2-B Task 7 — `COMPLETE_7_PASS_0_FAIL`; Ansible `3/3 PASS`
- [x] G2-B Task 8 — `COMPLETE_PASS_DISPOSABLE_HOSTED_AND_LAB_13_OF_13` — laboratório histórico 13/13 + CI hospedada pós-merge no `f1be00b...`
- [ ] G2-B lifecycle — `LAB_VALIDATED_INACTIVE` — ativação não autorizada
- [ ] G2-B Task 9 — `WAITING_HUMAN_GATE` — PR #56 Draft publicada; parada obrigatória antes do bootstrap NODE-01
- [ ] G2-B Task 10 — `NOT_STARTED` — nenhuma operação real autorizada; exige HUMAN_GATE explícito
- [ ] G2-B merge — `CLOSED_NOT_AUTHORIZED_TASK9_DRAFT`

### Evidência atual e plano histórico

- `docs/56-g2b-task8-vps-qemu-tcg-disposable-boundary-plan.md`
- o plano QEMU/TCG permanece histórico; o gate de pacotes está fechado e não é necessário após o PASS local descartável.
- evidência atual: `evidence/CONTROL-BRIDGE-G2B/TASK-8-RECONCILED-LAB-20260823.md`.

### Limite G2-B atual

Task 8 preserva o laboratório `570779b...` como evidência histórica e adiciona a prova hospedada pós-merge de `f1be00b...`. O transporte seletivo sobre a base MCF atual resultou no pre-checkpoint `da78a16...`, validado localmente com 400 testes, e foi publicado na PR Draft #56. Task 9 está parada no gate humano; Task 10, NODE-01, grant, write, produção e merge permanecem não autorizados.

Próximo passo exato:

```text
HUMAN_REVIEW_AND_NODE01_G2B_BOOTSTRAP
```

## Roadmap principal da plataforma

- [x] S0 Recovery — `DONE`
- [x] F1.1 Foundations declarativas — `DONE`
- [ ] F1.2a Management Network — `WAITING_HUMAN_GATE`
- [x] F1.2b Docker boundary — `DONE`
- [ ] F1.2c Network enforcement — `PARTIAL`
- [ ] F1.3 Observability baseline — `CONDITIONAL`
- [ ] F1.4 Secret bootstrap foundation — `PLANNED`
- [ ] F1.5 Off-host recovery foundation — `WAITING_HUMAN_GATE`
- [ ] F1.6 Secrets operational — `WAITING_HUMAN_GATE`
- [ ] F2.1 Capability Core skeleton — `PLANNED`
- [ ] F2.2 PostgreSQL foundation — `CONDITIONAL`
- [ ] F2.3 Identity/scope — `PLANNED`
- [ ] F2.4 Node Agent/resources — `CONDITIONAL`
- [ ] F3.1 Durable Workflow — `PLANNED`
- [ ] F3.2 Event Backbone — `PLANNED`
- [ ] F3.3 Application messaging — `CONDITIONAL`
- [ ] F4.1 Data Service Plane — `CONDITIONAL`
- [ ] F4.2 Artifact Plane — `CONDITIONAL`
- [ ] F5.0 Runner/build isolation — `CONDITIONAL`
- [ ] F5.1 DEV pipeline — `PLANNED`
- [ ] F5.2 Sandboxes — `CONDITIONAL`
- [ ] F5.3 Preview Gateway — `PLANNED`
- [ ] F5.4 DNS/TLS DEV — `WAITING_HUMAN_GATE`
- [ ] F6.1 Agent Gateway — `PLANNED`
- [ ] F6.2 MCP/API/CLI adapters — `PLANNED`
- [ ] F6.3a Model Gateway spike — `PLANNED`
- [ ] F6.3b Model Gateway operational — `CONDITIONAL`
- [ ] F6.4 Ecosystem adapters — `PLANNED`
- [ ] F7.1 Continuous security/update lifecycle — `PLANNED`
- [ ] F7.2 Recovery integrado — `PLANNED`
- [ ] F7.3 Rebuild drill — `PLANNED`
- [ ] F7.4 Findings closure — `PLANNED`

## Gates atuais

- NODE-01 G2-B bootstrap: `CLOSED_NOT_AUTHORIZED_WAITING_HUMAN_REVIEW`
- grant real G2-B: `CLOSED_NOT_AUTHORIZED`
- bounded write real: `CLOSED_NOT_AUTHORIZED`
- produção: `CLOSED_NOT_AUTHORIZED`
- publicação G2-B: `EXECUTED_DRAFT_PR56_NO_MERGE`
- merge G2-B: `CLOSED_NOT_AUTHORIZED_TASK9_DRAFT`
- F1.2c parallel branch: `ISOLATED_DO_NOT_MODIFY`
