# 45 — REVISED_IMPLEMENTATION_ROADMAP

Status: **ACTIVE — Q40-D**
Substitui como roadmap corrente as antigas fases provisórias F3–F10.

## Estados

- `PLANNED`: desired state ainda não implementado;
- `IMPLEMENTING`: trabalho em branch/slice, não validado no node;
- `WAITING_HUMAN_GATE`: depende de interação/decisão humana explícita;
- `CONDITIONAL`: tecnologia/contrato depende de ADR, teste ou compatibilidade ainda
  não provados;
- `PARTIAL`: parte validada, critérios de DONE faltam;
- `DONE`: todos os critérios aplicáveis e evidence-before-DONE satisfeitos.

## Roadmap por slice

| Slice | Resultado | Estado | Gate/dependência de saída |
|---|---|---|---|
| S0 Recovery | GitHub/VPS/Q1–Q40 reconciliados | `DONE` | report canônico e drift registrado |
| F1.1 Foundations declarativas | Ansible/schema/namespaces/contas/slices accounting | `DONE` | check mode sem mutação, backup off-host, apply real `changed=7`, idempotência `changed=0` e invariância passaram em `2026-08-17` |
| F1.2a Management Network | administração privada por identidade/dispositivo | `WAITING_HUMAN_GATE` | conta/plano/policy/onboarding e recovery testados |
| F1.2b Docker boundary | Docker CE/Compose pinados, root-only, bridge default ausente, sem porta/workload | `DONE` | CI descartável; preview; backup off-host; apply `changed=13`; idempotência e pós-restart `changed=0`; invariância passaram; não satisfaz Q20/Q34 e não libera workload |
| F1.2c Network enforcement | isolamento/egress/service discovery v4/v6 | `PARTIAL` | base `DOCKER-USER` v4/v6 está no NODE-01; desired state de redes, DNS e proxy passou 123 testes e lifecycle commit-bound no run `32131461110`; apply real dos serviços e gates restantes ainda bloqueiam workload |
| F1.3 Observability baseline | host/runtime logs, métricas, audit envelope | `CONDITIONAL` | compliance review de Loki/Grafana AGPL ou alternativa; HUMAN_GATE somente se termos/custo/aceite externo exigirem; limites/retention e interfaces privadas |
| F1.4 Secret bootstrap foundation | OpenBao instalado, não inicializado/selado | `PLANNED` | nenhum dado real; init/unseal/custódia e revogação do root token inicial permanecem gate humano |
| F1.5 Off-host recovery foundation | destino Restic, policy, keys e restore fixture | `WAITING_HUMAN_GATE` | destino/custo/custódia, targets provisórios e restore cronometrado; bloqueia dado Critical/Important real |
| F1.6 Secrets operational | OpenBao inicializado, auth/policies/audit/recovery e runtime injection | `WAITING_HUMAN_GATE` | F1.5; Shamir/recovery custody, bootstrap limitado, revogação imediata do root token inicial e snapshot/restore Raft |
| F2.1 Capability Core skeleton | API/CLI, correlation, deny-default e audit | `PLANNED` | contratos OpenAPI/policy e testes negativos |
| F2.2 PostgreSQL foundation | databases/roles/migrations/pgBackRest harness | `CONDITIONAL` | F1.5 e F1.6 antes de credencial/dado real; Keycloak/Temporal/PG-major compatibility e restore fixture |
| F2.3 Identity/scope | Keycloak, grants temporários e tenant/project/mission model | `PLANNED` | Management Network, Core, F1.6 e PostgreSQL F2.2; H2/dev mode não é saída |
| F2.4 Node Agent/resources | Core → API local revalidada, quotas/admission e network model | `CONDITIONAL` | Docker/Core/F1.2c; ADR e teste de quota de disco; worker direto negado |
| F3.1 Durable Workflow | Temporal + worker + retry/idempotency | `PLANNED` | PostgreSQL compatibility/replay/restore, F1.5 e F1.6 |
| F3.2 Event Backbone | JetStream, accounts, correlation e recovery | `PLANNED` | storage/limits/off-host snapshot drill, F1.5 e F1.6 |
| F3.3 Application messaging | queues/topics segregados por tenant/project | `CONDITIONAL` | provar NATS accounts separados do Event Backbone ou selecionar alternativa |
| F4.1 Data Service Plane | PostgreSQL/Valkey/object/messaging resources isolados | `CONDITIONAL` | F1.6, object store e messaging decisions, quota e backup/restore por classe |
| F4.2 Artifact Plane | GHCR/digest/cache/SBOM/signature | `CONDITIONAL` | HUMAN_GATE de registry auth/permissions/retention e decisão/teste do cache OCI local descartável |
| F5.0 Runner/build isolation | control plane e runner/builder efêmero sem sockets privilegiados | `CONDITIONAL` | ADR GitHub/Temporal/BuildKit, F1.2c/F2.4 e testes de escape/cleanup |
| F5.1 DEV pipeline | build/test/scan/sign/deploy/rollback | `PLANNED` | Core/Workflow/Artifact Plane/F5.0 |
| F5.2 Sandboxes | disposable compute/network/db/disk e cleanup | `CONDITIONAL` | Node Agent, quota de disco provada, admission e egress |
| F5.3 Preview Gateway | Caddy privado e rota autorizada | `PLANNED` | Core/sandboxes; nenhum DNS público ainda |
| F5.4 DNS/TLS DEV | namespace/URL/ACME para previews | `WAITING_HUMAN_GATE` | domínio/DNS credential escopada |
| F6.1 Agent Gateway | endpoint público mínimo e capability-only | `PLANNED` | threat model, IdP/Core, abuse tests |
| F6.2 MCP/API/CLI adapters | interfaces substituíveis para executores | `PLANNED` | Core stable contracts |
| F6.3a Model Gateway spike | comparar LiteLLM/Core proxy, quota/redaction/security | `PLANNED` | medição, licença/feature split, advisories e patch policy |
| F6.3b Model Gateway operational | gateway privado mediado pelo Core, routing/fallback/cost audit | `CONDITIONAL` | decisão F6.3a, backends substituíveis e testes de exfiltração/failover |
| F6.4 Ecosystem adapters | OpenClaw/Hermes/Codex/Freebuff/TriView boundaries | `PLANNED` | gateways e identity scopes |
| F7.1 Continuous security/update lifecycle | scan host/deps/IaC/image, classificar, remediar, testar, atualizar por policy e rollback | `PLANNED` | pipeline, remediation workflows, exception lifecycle e gate por risco |
| F7.2 Recovery integrado | Restic/pgBackRest/Raft/JetStream/object restore por classe | `PLANNED` | F1.5 e todos os slices persistentes; provar RPO/RTO/retention, não iniciar backups tardiamente |
| F7.3 Rebuild drill | novo node a partir de Git + backups | `PLANNED` | todos estados importantes classificados |
| F7.4 Findings closure | findings reavaliados com evidência | `PLANNED` | drills e hardening completos |

## Critério de checkpoint por slice

Cada slice encerra com:

1. objetivo, componentes e riscos;
2. versão/digest/licença e decisão tecnológica;
3. precheck e evidência antes;
4. desired state e rollback versionados;
5. functional, security, negative e recovery checks aplicáveis;
6. segunda reconciliação idempotente;
7. evidência e inventário de componentes;
8. runbook, history, state, CONTEXT e CHECKPOINT reconciliados;
9. branch/commit publicado sem secret;
10. próximo passo exato.
11. status executivo do README reconciliado;
12. GitHub Project reconciliado ou explicitamente `BLOCKED_EXTERNAL`;
13. GitHub Actions Job Summary gerado e validado.

Estado canônico inconsistente bloqueia `DONE`. Falha apenas cosmética de
renderização deve ser registrada e corrigida, mas não bloqueia operação técnica
independente já segura. Indisponibilidade externa do GitHub Project é
`BLOCKED_EXTERNAL`, não bloqueio da missão principal.

## Gates externos já conhecidos

- autenticação sudo é entrada humana, nunca secret transmitido ao agente;
- Management Network: identidade, plano, termos e policy;
- domínio/DNS e credencial de zona;
- GHCR privado e permissão/token/OIDC;
- destino/custo de backup e custódia de chaves;
- inicialização/unseal/recovery do cofre;
- termos/licença/custo que exijam aceite humano ou serviço externo; a revisão de
  compliance AGPL por si só permanece trabalho técnico sob Q40-D;
- painel Contabo e toda promoção para produção.

Trabalho independente continua enquanto um caminho aguarda gate. Depois do gate
inicial de domínio/DNS, criar/revogar preview DEV dentro do namespace, quota e
grant aprovados é autônomo; novo domínio, custo ou produção volta ao gate. Rotação
de credenciais não faz parte deste roadmap enquanto permanecer adiada por LEANDRO.

F1.2b concluiu código, validação descartável e lifecycle real do runtime vazio.
O primeiro container permanece bloqueado por F1.2c, mesmo que não publique
portas.

F1.2c possui contrato machine-readable, tecnologia selecionada pela DEC-008,
base fail-closed ativa e matriz de serviços aprovada em VM descartável. O
desired state NODE-01 agora está preparado com quatro serviços privados por
digest, quatro redes exatas, forwarding fail-closed, lifecycle systemd e
rollback por camada. CI commit-bound passou no run `32131461110`; apply/rollback real e gates de workload
permanecem necessários.

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

O status do runner é observado na GitHub API, não uma observação nova da VPS.
F1.2c preserva seus fatos/timestamps e a branch paralela permanece congelada
para Codex. O estado fail-closed de G2-B é `state/control-bridge-g2b.yaml`.
