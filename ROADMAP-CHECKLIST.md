# ROADMAP CHECKLIST — ESTADO CANÔNICO ATUAL

Atualizado em: **2026-08-23**
Repositório: `leon337/cloud-infrastructure`
Branch de trabalho G2-B: `codex/context-bridge-reconcile-20260823`
PR: `NONE_LOCAL_ONLY_NO_PUSH`
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
- [x] G2-B Task 8 — `PASS_DISPOSABLE_NOTEBOOK_DOCKER_13_OF_13` — laboratório local Ubuntu 24.04/systemd, `--network none`, cleanup completo
- [ ] G2-B lifecycle — `LAB_VALIDATED_INACTIVE` — ativação não autorizada
- [ ] G2-B Task 9 — `NOT_STARTED` — exige revisão/publicação separada e não é autorizada pelo PASS da Task 8
- [ ] G2-B Task 10 — `NOT_STARTED` — exige HUMAN_GATE explícito para NODE-01 bootstrap/grant/write
- [ ] G2-B merge — `CLOSED_NOT_AUTHORIZED_LOCAL_CANDIDATE_REVIEW_REQUIRED`

### Evidência atual e plano histórico

- `docs/56-g2b-task8-vps-qemu-tcg-disposable-boundary-plan.md`
- o plano QEMU/TCG permanece histórico; o gate de pacotes está fechado e não é necessário após o PASS local descartável.
- evidência atual: `evidence/CONTROL-BRIDGE-G2B/TASK-8-RECONCILED-LAB-20260823.md`.

### Limite G2-B atual

Task 8 passou no candidato local `570779b...`; Tasks 9/10, ativação, transporte mutante pelo Context, NODE-01, staging, produção, publicação e merge permanecem não executados/não autorizados. O resultado hosted anterior (`steps=0`, `BlobNotFound`) continua evidência histórica inconclusiva e não é reescrito.

Próximo passo exato:

```text
REVIEW_LOCAL_RECONCILED_CANDIDATE_BEFORE_PUBLICATION_OR_TASK_9
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

- NODE-01 G2-B bootstrap: `CLOSED_NOT_AUTHORIZED`
- grant real G2-B: `CLOSED_NOT_AUTHORIZED`
- bounded write real: `CLOSED_NOT_AUTHORIZED`
- produção: `CLOSED_NOT_AUTHORIZED`
- publicação G2-B: `CLOSED_NOT_AUTHORIZED`
- merge G2-B: `CLOSED_NOT_AUTHORIZED_LOCAL_CANDIDATE_REVIEW_REQUIRED`
- F1.2c parallel branch: `ISOLATED_DO_NOT_MODIFY`
