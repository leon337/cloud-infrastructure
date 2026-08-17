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
| F1.2b Docker boundary | Docker CE/Compose pinados, root-only, bridge default ausente, sem porta/workload | `PARTIAL` | desired state `7015c80`; CI descartável completa passou; preview NODE-01 passou sem mutação em `2026-08-17T08:37:46Z`; apply `NOT_EXECUTED`; não satisfaz Q20/Q34 |
| F1.2c Network enforcement | isolamento/egress/service discovery v4/v6 | `CONTRACT_STARTED` | contrato Q20/Q34 local-static `PASS` no commit `b4cbeb0`; tecnologia/ADR, implementation, F1.2b, matriz dinâmica allow/deny e rollback continuam `PENDING`; bloqueia primeiro container |
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

F1.2b concluiu código, validação local e integração descartável commit-bound em
paralelo ao gate F1.1. Isso não autoriza check/apply no NODE-01: a fundação real
continua pendente. O primeiro container permanece bloqueado por F1.2c, mesmo que
não publique portas.

F1.2c avançou somente até um contrato machine-readable repo-only. Isso permite
desenhar a ADR e a fixture sem depender do HUMAN_GATE F1.1, mas não equivale a
network enforcement nem reduz os gates IPv4/IPv6, rollback e evidência dinâmica.
