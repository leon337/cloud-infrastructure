# 44 — INFRASTRUCTURE_BLUEPRINT_V1

Status: **EXECUTABLE BASELINE — CONDITIONAL GAPS BLOCK CAPABILITY DONE**
Node inicial: `node-01`
Desired state: Git + Ansible + manifests/schema

## Regras de implantação

1. um slice altera uma fronteira coerente por vez;
2. precheck e rollback são escritos antes do apply;
3. versões são resolvidas em fonte oficial e fixadas no inventário;
4. nenhum serviço inicia com default público ou credencial de exemplo;
5. estado persistente recebe classe, owner, backup e restore antes de dados reais;
6. segunda reconciliação deve resultar em `changed=0`;
7. listener, ruleset, grupos privilegiados e Workstation são comparados após apply;
8. produção permanece `false` em manifests e policy.

## Layout do host

| Caminho | Função | Owner inicial | Persistência |
|---|---|---|---|
| `/etc/cloud-platform` | configuração não secreta reconciliada | `root:cloud-platform 0750` | Git/rebuildable |
| `/var/lib/cloud-platform` | raiz de estado declarado | `root:cloud-platform 0750` | por subdiretório/classe |
| `/var/log/cloud-platform` | fallback local de logs | `root:cloud-platform 0750` | retenção limitada |
| `/var/cache/cloud-platform` | caches reconstruíveis | `root:cloud-platform 0750` | disposable |
| `/run/cloud-platform` | sockets/runtime state | `root:cloud-platform 0750` | tmpfs/reboot |
| `/run/cloud-platform/credentials` | transporte runtime temporário | `root:root 0700` | nunca backup |

Diretórios folha de serviços devem usar `RuntimeDirectory=`, `StateDirectory=`,
`CacheDirectory=` e `LogsDirectory=` quando as units existirem. `tmpfiles.d` cria
somente namespaces independentes; não usa tipos destrutivos `D`, `R` ou `r`.

## Identidades e privilégio

- `ubuntu`: operador humano, sudo autenticado, nunca membro de `docker`/`lxd`;
- `cloud-platform`: grupo de leitura/IPC estritamente permissionado;
- `platform-core`: conta bloqueada, sem home, sudo, lxd ou docker;
- novas contas são service-specific e criadas no slice do serviço;
- Node Agent privilegiado será root-owned, com API por Unix socket, verbs e
  argumentos allowlisted; o frontend do Core continua não privilegiado;
- a API/socket do Node Agent não é montada em worker, runner ou sandbox; o Agent
  revalida peer e capability assinada/curta emitida pelo Core;
- runners e sandboxes nunca montam `/var/run/docker.sock`.

## Slices cgroup

`cloud-platform.slice` e `cloud-workloads.slice` começam apenas com accounting e
pesos 200/100. Não há `Delegate=`, `MemoryMax=` ou `CPUQuota=` em F1.1.

Depois de baseline medido:

- control plane usa `MemoryHigh` como pressão principal e `MemoryMax` apenas como
  última defesa;
- workload/sandbox sempre declara CPU, memória, PIDs e limite de disco;
- admission considera RAM disponível, load, espaço, inode e concorrência;
- jobs de backup, compaction, migration e scan não rodam simultaneamente sem
  orçamento explícito.

## Componentes e implantação física inicial

| Capability | Componente V1 | Deployment inicial | Estado |
|---|---|---|---|
| Desired state | Ansible Core 2.21.3 + JSON Schema | controller → SSH/sudo humano | `F1_1_PARTIAL_AWAITING_DISPOSABLE_VM_REVALIDATION` |
| Management Network | Tailscale com grants explícitos | serviço host | `WAITING_HUMAN_GATE` |
| Container runtime | Docker Engine + Compose plugin | serviço host, grupo vazio, sem workload/porta | `PLANNED_F1_2B` |
| Network/egress | nftables/`DOCKER-USER` + DNS/egress mechanism a selecionar | host + bridges segregadas | `DECISION_PENDING_BEFORE_FIRST_WORKLOAD` |
| Disk isolation | project quota/XFS, volume/bloco limitado ou execution node a testar | por sandbox/workload | `DECISION_PENDING; Q8_NOT_YET_PROVEN` |
| Capability Core | Go + OpenAPI 3.1.2 + OPA/Rego v1 | container/unix socket | `PLANNED_F2` |
| PostgreSQL foundation | major após Keycloak/Temporal/pgBackRest compat test | container/volume sem dado real antes de backup/cofre | `PLANNED_F2_2; DEPENDS_F1_5_F1_6_FOR_REAL_STATE` |
| Identity | Keycloak | container privado + PostgreSQL foundation | `PLANNED_F2_3; DEPENDS_F1_6_F2_2` |
| Secrets | OpenBao/Raft/Shamir | container/volume privado | `F1_4_INSTALL_SEALED; F1_6_INIT_GATED_AFTER_F1_5` |
| Workflow | Temporal + PostgreSQL visibility | containers privados | `PLANNED_F3` |
| Events | NATS JetStream file/R1 | container privado | `PLANNED_F3` |
| Application messaging | NATS segregado ou alternativa após teste | accounts/subjects separados do Event Backbone | `CONDITIONAL_Q38` |
| Cache | Valkey | privado, memory limit, disposable | `DEFERRED_UNTIL_CONSUMER` |
| Object storage | Garage candidato | privado/volume | `DECISION_PENDING` |
| OCI registry/cache | GHCR canônico + cache local a selecionar | externo + cache descartável no node | `PARTIAL_SELECTION; LOCAL_CACHE_DECISION_PENDING` |
| Preview | Caddy | privado inicialmente, sem Docker socket | `PLANNED_F5` |
| Observability | Alloy, Prometheus; Loki/Grafana condicionais | containers privados/volumes | `CONDITIONAL_LICENSE_COMPLIANCE_REVIEW_BEFORE_LOKI_GRAFANA` |
| Audit ledger | storage/retention a selecionar | append-only/correlated, off-host conforme classe | `DECISION_PENDING` |
| Backup | Restic + pgBackRest | off-host | `WAITING_DESTINATION_GATE` |
| Supply chain | Syft, Trivy, Cosign | runners efêmeros | `PLANNED_F5` |
| Pipeline/runner | control plane + runner/builder isolado a selecionar | efêmero, sem Docker/Node Agent socket | `DECISION_PENDING_BEFORE_F5` |
| Model Gateway | LiteLLM candidato condicional | privado atrás do Core | `DEFERRED_SECURITY_SPIKE` |

Versões posteriores a F1.1 permanecem inventory candidates até o precheck do seu
slice; `docs/46-technology-mapping-v1.md` é a fonte de trade-offs.

## Redes Docker planejadas

| Padrão | Uso | Comunicação padrão |
|---|---|---|
| `cp-mgmt` | Core/IdP/cofre/workflow/observabilidade admin | Management Network somente |
| `cp-core` | APIs internas do control plane | explicitamente allowlisted |
| `shared-data` | PostgreSQL/Valkey/object/event | consumers com identity/grant |
| `project-<id>` | serviços persistentes de projeto | mesmo projeto + shared grants |
| `sandbox-<mission>` | ambiente descartável | sem lateral; egress profile |
| `preview` | Caddy → workload alvo | somente rota publicada |

F1.2b instala Docker sem publicar porta ou workload. Antes de qualquer container:

- capturar UFW, iptables/nftables, sysctls, routes e listeners;
- não configurar `iptables=false`;
- grupo `docker` deve continuar vazio;
- daemon usa socket local root-owned; TCP daemon é proibido;
- validar que uma porta de fixture não fica pública por acidente em IPv4/IPv6;
- aceitar um ADR que selecione e atribua ownership ao enforcement da cadeia
  suportada pelo Docker, DNS/egress, IPv6 e service discovery;
- testar allow/deny lateral, host, Management, metadata, shared services e Internet
  conforme perfil, com rollback do ruleset.

Instalar o daemon sem workload não satisfaz Q20/Q34. O primeiro container de
plataforma ou projeto depende de F1.2c Network Enforcement validado.

## Manifests e reconciliation

O schema `platform.leandro.dev/v1alpha1` possui inicialmente:

- `ExecutionNode`: capacidade, reserva, sandbox defaults, Management exposure e
  production gate;
- `Project`: tenant/project/environment, capabilities, persistence, sandbox,
  egress/shared services, preview, `secretRefs` e production gate.

Campos desconhecidos são rejeitados. Secret literal não é um campo válido.
Mudança crítica detectada por drift gera relatório; não é auto-reconciliada sem a
policy de risco e rollback apropriados.

## Estado e recovery por classe

| Classe | Exemplos | Meta inicial | Recovery |
|---|---|---|---|
| Critical | OpenBao, grants/audit, futuro release record | alvo provisório RPO ≤4h, RTO ≤8h; `UNVALIDATED` | backup off-host on-change/periódico, 30 diários + 12 mensais, restore isolado |
| Important | PostgreSQL DEV, Temporal, JetStream, object storage/evidências | alvo provisório RPO ≤24h, RTO ≤24h; `UNVALIDATED` | pgBackRest/snapshot/export off-host, 14 diários + 8 semanais, drill |
| Rebuildable | config, imagens por digest, provisioning | RPO = Git/registry aprovado; alvo RTO ≤24h `UNVALIDATED` | reprovision idempotente |
| Disposable | sandbox, cache, build cache, tmpfs | sem backup; alvo de recriação ≤1h `UNVALIDATED` | recriar e provar cleanup |

Esses valores são objetivos de policy selecionados para DEV/lab, não evidência de
atingimento. Exigem destino off-host, capacidade medida e restore cronometrado;
até então capacidades persistentes permanecem `PARTIAL` e não recebem dados reais
fora de fixture. Qualquer mudança futura desses alvos é ADR, não ajuste silencioso.

## Sequência técnica

```text
F1.1 desired state/namespaces/accounting
  -> F1.2a Management Network
  -> F1.2b Docker boundary sem portas/workloads
  -> F1.2c network/egress/service-discovery enforcement
  -> F1.3 observabilidade mínima (Loki/Grafana após compliance review)
  -> F1.4 OpenBao instalado, selado e sem estado inicializado
  -> F1.5 fundação off-host + restore de fixture
  -> F1.6 OpenBao inicializado, root bootstrap revogado e recovery provado
  -> F2.1 Capability Core skeleton
  -> F2.2 PostgreSQL foundation + backup/restore fixture/off-host gate
  -> F2.3 identity/policy
  -> F2.4 Node Agent/resource model + disk-isolation decision
  -> F3 Temporal + NATS + workers
  -> F4 data/artifact plane; backup por classe antes de dado real
  -> F5 runner/pipeline/sandboxes/preview/DNS/TLS
  -> F6 gateways/adapters/model routing
  -> F7 restore/rebuild agregado/security and update lifecycle
```

Cada seta é dependency, não autorização para executar o próximo slice sem o
checkpoint do anterior.
