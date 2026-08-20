# CODEX-EXECUTION-MISSION-001

Data: 2026-08-16
Status: **AUTHORIZED_BY_LEANDRO**
Autoridade humana final: **LEANDRO**
Repositório canônico: `leon337/cloud-infrastructure`

## Missão

Assuma a seleção tecnológica e a implementação incremental da plataforma privada de desenvolvimento, laboratório e execução de agentes definida pela Platform Discovery Q1–Q40.

Você não está recebendo liberdade para redesenhar a missão. Q1–Q39 são requisitos arquitetônicos vinculantes. Q40-D delega a você a escolha das tecnologias concretas e a implementação.

## Primeira obrigação: recuperar o estado real

Antes de alterar qualquer coisa:

1. leia o repositório canônico inteiro o suficiente para recuperar contexto, decisões, findings, runbooks, recovery e estado;
2. leia `state/platform-discovery.yaml` e todos os checkpoints da Platform Discovery;
3. confirme HEAD/branch e ausência de mudanças concorrentes relevantes;
4. inspecione o estado real da VPS antes de assumir versões, serviços, portas, usuários, firewall, runtime ou recursos;
5. registre discrepâncias entre GitHub e VPS como findings, sem mascará-las.

Não dependa de memória de chat como fonte de verdade.

## Arquitetura vinculante

Preserve, no mínimo, os seguintes princípios decididos por LEANDRO:

- plataforma privada de compute/desenvolvimento/execução de agentes;
- own-infrastructure-first para DEV/lab, com serviços externos por escolha deliberada;
- isolamento por workspace/tenant → project → mission → sandbox;
- autonomia apenas dentro de escopo previamente autorizado; HUMAN_GATE fora dele;
- Capability Core como camada de capacidades/políticas, acessível progressivamente por API/MCP/CLI;
- compute descartável e estado importante explicitamente persistente;
- manifest declarativo por projeto e reconciliação idempotente de drift;
- bancos DEV persistentes por projeto e bancos de sandbox temporários;
- armazenamento híbrido: Git + temporário + object storage + volumes persistentes quando necessário;
- secret store central com credenciais temporárias/escopadas e runtime injection;
- private-by-default, Preview Gateway controlado e HTTPS automático;
- pipeline build/test/deploy DEV automatizado, rastreável e rollback-capable;
- observabilidade central: logs, métricas, eventos, auditoria e evidence-before-DONE;
- infraestrutura reconstruível, backup off-host automatizado e restore testado;
- container-first, Docker/Compose inicialmente, mediado por Capability Core; sem Docker daemon direto para agentes;
- OCI registry canônico independente + cache local; build once/deploy many; artefatos imutáveis e provenance;
- pipeline híbrido com runners/jobs isolados e descartáveis;
- egress controlado por política; tráfego útil permitido; lateral/admin/private denied by default;
- Management Plane privado + Agent Gateway público mínimo e fortemente escopado;
- identidade individual + autoridade temporária escopada por tenant/project/mission/capability;
- autonomia para DEV/staging; promoção para produção exige HUMAN_GATE de LEANDRO;
- quotas hierárquicas, reserva da plataforma, limites de workload, burst controlado e fila sob pressão;
- single-node first, mas execution-node abstraction e future multi-node/provider portability;
- workflow engine durável e distributed-capable desde o primeiro release;
- MCF governa; Capability Core autoriza; Workflow Engine executa duravelmente;
- ecossistema modular: TriView = cockpit humano; OpenClaw = canais/front door; Hermes/Codex/outros = executores substituíveis; Freebuff = coding interativo;
- plataforma headless independente da Cloud Workstation;
- AI/Model Gateway com routing por política, secrets centralizados, quotas/custos, fallback e backends substituíveis externos ou locais;
- scanning contínuo de segurança, classificação de risco, updates por política, teste/rollback e gate quando o escopo for excedido;
- redes isoladas por tenant/project/sandbox + service discovery por identidade/nome + acesso explícito a shared services;
- classes de criticidade com RPO/RTO, backup/retention e restore testado;
- comandos síncronos via Capability Core + Event Backbone assíncrono durável com identidade/correlação/entrega confiável;
- DNS namespace administrado pela plataforma + Preview Gateway + URLs/TLS automáticos + DEV/PROD rigidamente separados;
- Data Service Plane compartilhado com isolamento lógico por tenant/projeto, recursos descartáveis de sandbox e instância dedicada apenas quando requisito justificar;
- Management Plane acessível por rede privada administrativa com identidade de dispositivo/usuário; SSH fallback; VNC/Rescue break-glass.

## Autoridade e limites

### AUTORIZADO

Você está autorizado a:

- pesquisar e comparar tecnologias adequadas;
- selecionar tecnologias concretas para cada capability;
- criar ADRs/technology decision records no repositório;
- produzir Target Architecture, Threat/Autonomy Model, Infrastructure Blueprint v1 e roadmap revisado;
- instalar, configurar, integrar e testar componentes na VPS para DEV/lab;
- criar containers, redes, volumes, serviços e automações necessários dentro dos guardrails;
- criar scripts idempotentes, manifests, compose files, policies, runbooks e testes;
- realizar mudanças reversíveis no host quando necessárias para a plataforma, com precheck, backup/checkpoint e rollback;
- atualizar documentação e checkpoints a cada incremento verificável.

### NÃO AUTORIZADO

Você NÃO está autorizado a:

- promover workloads para produção externa sem novo HUMAN_GATE de LEANDRO;
- versionar ou imprimir secrets reais em Git, logs ou relatórios;
- rotacionar credenciais marcadas `DEFERRED_BY_HUMAN_DECISION`;
- habilitar acesso administrativo público ao Management Plane;
- conceder root ou Docker daemon irrestrito a agentes;
- remover mecanismos de recovery existentes sem substituição comprovadamente superior e reversível;
- reabrir silenciosamente decisões Q1–Q39;
- apagar dados persistentes, repositórios, backups ou configuração crítica sem plano de recuperação e autorização aplicável;
- tratar “funcionou uma vez” como DONE sem evidência verificável.

## Critérios para seleção tecnológica

Para cada capability, compare candidatos com evidência e registre a decisão considerando:

1. aderência às decisões Q1–Q39;
2. consumo de RAM/CPU/disk no single-node atual;
3. segurança e modelo de privilégios;
4. maturidade e manutenção ativa;
5. licença e custo;
6. simplicidade operacional;
7. capacidade de backup/restore/rebuild;
8. portabilidade entre provedores;
9. capacidade de evoluir para multi-node;
10. API/CLI/MCP friendliness para agentes;
11. observabilidade e auditabilidade;
12. risco de lock-in;
13. caminho de migração/rollback.

Não escolha ferramentas apenas por popularidade.

## Entregáveis obrigatórios antes ou durante a implementação

Crie e mantenha no repositório, em formato canônico:

- `CONSOLIDATED_REQUIREMENTS`;
- `TARGET_ARCHITECTURE`;
- `THREAT_MODEL_AND_AUTONOMY_BOUNDARIES`;
- `INFRASTRUCTURE_BLUEPRINT_V1`;
- `REVISED_IMPLEMENTATION_ROADMAP`;
- registros de Technology Mapping/ADRs;
- inventário de componentes e versões;
- runbooks de operação/recovery;
- evidências de testes e validação.

Esses artefatos não precisam bloquear todo o trabalho até ficarem perfeitos, mas devem evoluir junto com a implementação e jamais ficar atrás do estado real.

## Ordem de execução recomendada

Você pode ajustar a ordem com justificativa, mas preserve dependências e recovery.

### Fase 0 — Reconciliação e baseline

- recuperar estado GitHub + VPS;
- identificar drift;
- confirmar backup/recovery atual;
- confirmar recursos do NODE-01;
- estabelecer branch/commit/checkpoint de trabalho.

### Fase 1 — Foundations

- private management network;
- container runtime boundaries;
- filesystem/directories/ownership;
- secret handling foundation;
- declarative configuration and idempotent bootstrap;
- observability baseline.

### Fase 2 — Platform Core

- Capability Core skeleton/API;
- identity/scope/policy enforcement;
- project/mission/sandbox resource model;
- network isolation/service discovery;
- quotas/resource control.

### Fase 3 — Durable Execution

- workflow engine;
- worker model;
- Event Backbone;
- durable state/retry/idempotency;
- evidence/correlation/audit integration.

### Fase 4 — Data and Artifact Plane

- PostgreSQL/data plane;
- object storage;
- cache/KV;
- messaging/event dependencies when separate from backbone;
- OCI registry/cache;
- backup/restore by criticality.

### Fase 5 — Developer Experience

- project manifest;
- build/test/deploy DEV pipeline;
- temporary sandboxes;
- Preview Gateway;
- platform DNS/TLS automation;
- logs/metrics/status interfaces.

### Fase 6 — Agent Ecosystem

- Agent Gateway;
- MCP/API/CLI interfaces;
- AI/Model Gateway;
- executor adapters for Hermes/Codex/others;
- OpenClaw channel boundary when applicable;
- TriView integration boundary;
- preserve Cloud Workstation as optional human cockpit.

### Fase 7 — Security, Recovery and Hardening

- continuous scanning;
- update policy/rollback;
- supply-chain checks/provenance appropriate to v1;
- tested disaster recovery;
- off-host backup automation;
- rebuild drill from desired state + backups;
- close or update findings with evidence.

## Incremental execution contract

Do not perform a giant opaque installation.

For each slice:

1. declare goal and affected components;
2. inspect current state;
3. state selected technology and rationale;
4. define preconditions and rollback;
5. implement the smallest coherent slice;
6. run functional/security/recovery checks as applicable;
7. capture evidence;
8. update GitHub documentation/state;
9. checkpoint before the next slice.

When a step requires LEANDRO interaction that cannot be eliminated by the platform — for example provider dashboard action, purchase, external production promotion, secret input or credential rotation — stop that path at `WAITING_FOR_HUMAN_GATE` and continue independent work where safe.

## Definition of DONE

A capability is not DONE merely because the process is running.

DONE requires, when applicable:

- desired state versioned;
- idempotent reprovision/reconcile path;
- health/status check;
- logs/metrics/events visible;
- scoped access policy verified;
- isolation verified;
- restart/reboot behavior verified;
- backup/restore or rebuild behavior verified according to its criticality class;
- evidence stored;
- documentation/checkpoint updated.

## Control Bridge — continuidade reconciliada em 2026-08-20

```text
CONTROL_BRIDGE_G2B=P0_DESIGN_APPROVED_IMPLEMENTATION_PENDING
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
G2B_REAL_WRITE=NOT_EXECUTED
CODEX=AVAILABLE_PARALLEL_EXECUTOR
MESTRE_MCF=ORCHESTRATOR
LEANDRO=FINAL_HUMAN_AUTHORITY
F1_2C_SYSTEMD_RUNTIME_LOCK=FROZEN_FOR_CODEX_OWNED_BY_MESTRE_MCF_AND_LEANDRO
GITHUB_HOSTED_CI=BLOCKED_EXTERNAL_BILLING
SELF_HOSTED_NODE_01_RUNNER=ONLINE_OBSERVED_2026_08_20
```

O status online é da GitHub API, não observação VPS fresca. Codex trabalha
somente em `codex/control-bridge-g2b`; F1.2c preserva fatos/timestamps e sua
branch permanece congelada. G2-B permanece fail-closed em
`state/control-bridge-g2b.yaml`.

## Primeira resposta esperada do Codex

Antes de executar alterações destrutivas ou amplas, retorne um **MISSION ACCEPTANCE + RECOVERY REPORT** contendo:

- HEAD/branch/SHA do repositório;
- checkpoint/state recuperado;
- resumo das decisões Q1–Q40 entendidas;
- estado real da VPS verificado;
- divergências GitHub ↔ VPS;
- riscos imediatos;
- plano de Technology Mapping;
- primeiro incremento que pretende executar;
- rollback desse primeiro incremento;
- itens que já exigem HUMAN_GATE, se houver.

Depois disso, prossiga com a missão autorizada dentro dos guardrails acima.
