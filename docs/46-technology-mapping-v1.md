# 46 — TECHNOLOGY MAPPING V1

Status: **PARTIAL SELECTION — F1.2B REPO-READY/CI PENDING; F1.2C CONTRACT STARTED**
Research cut: 2026-08-16
Contract checkpoint: 2026-08-17
Authority: Q40-D

`SELECTED` significa escolha arquitetônica, não instalação. `CONDITIONAL` exige
teste ou gate indicado. `CANDIDATE` ainda pode ser substituído. Versão/digest é
confirmado novamente no precheck do slice e registrado em `state/components.yaml`.

## Critérios

As comparações consideram aderência Q1–Q39, RAM/CPU/disk, privilégio, maturidade,
manutenção, licença/custo, operação, backup/rebuild, portabilidade, multi-node,
API/CLI friendliness, auditabilidade, lock-in e migração/rollback.

Uma linha `SELECTED` congela o contrato arquitetônico, mas não dispensa o record
do slice. Antes de instalar, o checkpoint deve registrar para a versão/digest:

1. licença/feature split, custo e dependência externa;
2. RAM/CPU/disk medidos no envelope real, não estimados como `PASS`;
3. conta, capabilities, listeners, sockets e privilégios necessários;
4. health, logs, audit, backup/restore/rebuild e comportamento de reboot;
5. portabilidade/multi-node, lock-in, migração e rollback testável.

Ausência de uma dessas evidências mantém o deployment `CONDITIONAL`/`PARTIAL`.
Links mutáveis abaixo servem à pesquisa; o slice deve fixar tag/commit/digest,
data de consulta e texto de licença no decision record sem copiar secrets.

## Matriz consolidada

| Capability | Seleção/status | Alternativas avaliadas | Motivo e rollback |
|---|---|---|---|
| Desired state | **Ansible Core 2.21.3 — SELECTED** | shell, Nix, OpenTofu | Agentless, idempotente e adequado ao host existente. Shell é frágil para drift; Nix exigiria redesenho do OS; OpenTofu fica para recursos de provedor. Rollback explícito por objeto/backup. |
| Manifest | **YAML + JSON Schema 2020-12 — SELECTED** | schema ad hoc, CUE | Compatível com OpenAPI 3.1, tooling amplo e rejeição de campos desconhecidos. Evolução por `apiVersion`. |
| Management Network | **Tailscale — CONDITIONAL/HUMAN_GATE** | Headscale, WireGuard puro | Cliente Linux é open source, mas coordination server é proprietário/gerenciado e o plano limita recursos/audit features. A vantagem deliberada Q2 é identidade/dispositivo/policy com menor operação; plano, termos, IdP, logs e migração devem ser aprovados. Headscale no único nó cria dependência circular; WireGuard não entrega sozinho IdP/policy/audit. SSH público é rollback transitório no onboarding. |
| Runtime | **Docker CE 29.7.2 + containerd.io 2.3.3 + Buildx 0.36.1 + Compose 5.4.0 — SELECTED/IMPLEMENTING por Q17** | `docker.io`, convenience script, Podman, Kubernetes, Docker rootless | DEC-007 fixa pacotes oficiais Noble `amd64`, socket root-only, grupo vazio e runtime sem bridge/workload. Desired state/harness passaram local-static; uninstall usa provenance/baseline/manifesto fail-closed. CI dinâmica e VPS ainda não provadas. |
| Resource isolation | **cgroup v2 + systemd + AppArmor/seccomp — SELECTED** | apenas limites Compose, VM/nested virt, gVisor | Nativo e econômico. gVisor permanece candidato para código hostil; containers não são declarados equivalentes a VM. |
| Network/egress/service discovery | **CONDITIONAL — REPO CONTRACT PASS; ADR antes do primeiro workload** | nftables/`DOCKER-USER` + DNS proxy, egress proxy, firewall dedicado/execution node | O contrato F1.2c fixa v4/v6, host/metadata/Management/control/lateral deny, shared grants, Internet por perfil, identidade e evidência. Nenhum candidato foi selecionado ou implementado; instalar daemon sem workload não satisfaz Q20/Q34. |
| Disk isolation | **DECISION PENDING** | project quota/XFS, volume/bloco limitado, execution node dedicado | cgroup e ext4/overlay2 não impõem quota rígida do writable layer. Monitoramento/admission sozinho não satisfaz Q8/Q25; sandbox permanece `PARTIAL` até teste de uma alternativa. |
| Capability Core | **Go 1.26.x + OpenAPI 3.1.2 — SELECTED** | Python/FastAPI, OpenAPI 3.2 | Binário pequeno e portável; 3.1 possui compatibilidade madura com JSON Schema. Contratos separam executores e permitem reimplementação. |
| Policy | **OPA/Rego v1 embutido — SELECTED** | OpenFGA, Cedar, OPA sidecar | Rego cobre contexto, risco, tempo e ambiente. OpenFGA é forte em relações, mas não substitui policy contextual. Adapter permite sidecar posterior. |
| Identity | **Keycloak 26.x — SELECTED; DEPENDS ON POSTGRESQL + OPERATIONAL SECRET STORE** | ZITADEL | Apache-2.0, PostgreSQL suportado e ecossistema maduro. ZITADEL exigiria revisão de licença/feature split; somente plano/termos/custo externos criariam HUMAN_GATE. OIDC mantém caminho de migração. H2/dev mode não é deployment de saída. |
| Secret store | **OpenBao 2.6.x/Raft/Shamir — SELECTED; INIT GATED** | Vault, SOPS/age | MPL-2.0, leases/policy e storage integrado. SOPS ajuda bootstrap, mas não emite credencial temporária. Snapshot/export e interface Vault-compatible reduzem lock-in; shares ficam sob custódia humana. Root token inicial é revogado após bootstrap; emergência usa geração por quorum. |
| Workflow | **Temporal 1.31.x + PostgreSQL — SELECTED** | Restate, fila ad hoc | Satisfaz Q28 com retry, timers, cancelamento e evolução distribuída. Fila ad hoc não fornece histórico/replay. Schemas/migrations explícitos e workflows versionados são rollback. |
| Event Backbone | **NATS JetStream 2.14.x — SELECTED** | RabbitMQ, Kafka, Redis Streams | Footprint baixo, durability, accounts e cluster futuro. Kafka é desproporcional no nó; Redis mistura cache/eventos. Contrato de eventos permite migração. |
| Application messaging | **NATS REUSE CONDITIONAL** | RabbitMQ, JetStream cluster/account separado, broker futuro | Q38 exige queues/topics de projeto e Q36 define eventos internos. Reuso só congela após provar accounts/subjects/quotas/retention separados e que consumidores de aplicação não acessam o Event Backbone. |
| Relational data | **PostgreSQL 18.x — CONDITIONAL; 17.x fallback** | databases independentes por serviço | Um servidor compartilhado reduz operação; databases/owners/runtime roles separam domínios. PG18 só congela após Keycloak, Temporal, migrations, pgBackRest/replay/restore tests. SQL/pgBackRest preservam portabilidade. |
| Cache | **Valkey 9.x — SELECTED WHEN CONSUMER EXISTS** | Redis, cache in-process | BSD e protocolo conhecido. Apenas cache/coordenação descartável, memory cap e TTL; pode ser eliminado/reconstruído. |
| Object storage | **DECISION PENDING; Garage 2.3 candidato** | MinIO CE, serviço S3 externo | MinIO CE foi rejeitado por linha oficial arquivada. Garage é ativo, mas exige compliance review e teste das lacunas S3; HUMAN_GATE só se uma opção externa exigir termos/custo/credencial. Serviço externo pode vencer por durability/off-host. |
| OCI registry/cache | **GHCR canônico — SELECTED; CACHE LOCAL — DECISION PENDING** | CNCF Distribution pull-through, Harbor, somente content store do runtime | GHCR é independente da perda da VPS e suporta OCI/deploy por digest, mas não resolve sozinho o cache local exigido por Q18. O cache deve ser descartável, validar digest, não virar fonte canônica e permitir bypass/rebuild; a tecnologia congela após teste de autenticação, eviction, indisponibilidade e footprint. Harbor no mesmo nó não pode ser registry canônico. OCI preserva migração/export. |
| Pipeline/runner | **DECISION PENDING; GitHub/Temporal dispatcher + isolated runner** | GitHub runner persistente, runner efêmero, executor interno | BuildKit não é runner/control plane. O slice deve selecionar identity/bootstrap, queue, timeout, network, cleanup e evidence; runner nunca recebe Docker ou Node Agent socket. |
| Builder | **BuildKit — SELECTED; isolation CONDITIONAL** | daemon Docker direto, builder remoto/dedicado | BuildKit fornece OCI/cache, mas rootless em Noble tem trade-off AppArmor. Jobs devem ser efêmeros e sem socket; rootful worker só atrás de fronteira dedicada e capability revalidada. |
| Preview Gateway | **Caddy — SELECTED** | Traefik, Nginx manual | HTTPS automático, config API e admin em Unix socket. Não precisa ler Docker socket. Config/PKI são backupáveis e Caddy pode ser substituído pelo contrato de rotas. |
| DNS automation | **CONDITIONAL/HUMAN_GATE** | provider API plugin, delegação de subdomínio, DNS externo manual | Domínio/zona/credential e plugin dependem do provedor. Depois do bootstrap, rotas DEV no namespace/grant aprovado são autônomas; novo domínio, custo ou produção voltam ao gate. |
| Telemetria | **OTLP + Alloy — SELECTED** | OTel Collector e Alloy juntos | Alloy já inclui pipelines OTel/Prometheus/Loki; operar dois coletores desperdiça RAM. OTLP preserva portabilidade. |
| Metrics/logs/UI | **Prometheus SELECTED; Loki + Grafana CONDITIONAL/AGPL REVIEW** | VictoriaMetrics, Grafana alternatives, stack distribuída | Prometheus é Apache-2.0; Loki/Grafana são AGPL-3.0 e exigem compliance review antes de instalar. Isso não cria sozinho HUMAN_GATE sob Q40-D; termos/custo/aceite externo, se houver, criam. Permanecem candidatos adequados ao single-node se aprovados e se retention/cardinality/footprint medidos; provisioning/export preserva migração. |
| Audit ledger | **DECISION PENDING** | PostgreSQL append-only + export, object/WORM externo, JetStream consumer materializado | Loki e JetStream sozinhos não são declarados ledger canônico. Seleção deve provar correlação, tenant scope, retention, integridade, backup/off-host e consulta por agentes autorizados. |
| File backup | **Restic off-host — SELECTED/HUMAN destination gate** | Borg, tar local | Criptografia/dedup/S3 e checks. Writer append-only e prune separado. Restore é para filesystem isolado; senha/chave permanece custódia humana. |
| PostgreSQL backup | **pgBackRest — SELECTED WITH MAINTENANCE WATCH** | restic de PGDATA, dump-only, pg_basebackup manual | Full/diff/incremental, WAL/PITR e verify. Restic de PGDATA ativo é inconsistente. Manutenção upstream será monitorada e formatos PostgreSQL permitem saída. |
| Supply chain | **Syft + Trivy + Cosign — SELECTED** | scanner único, tags mutáveis | SBOM, scan direto e assinatura/attestation por digest. Verificação fixa issuer+identity; ações/binários são pinados. |
| Model Gateway | **LiteLLM — CONDITIONAL CANDIDATE** | proxy mínimo no Core, acesso direto a providers | Cobertura de providers/quotas é boa, mas footprint, cadência de patch, advisories e funções Enterprise exigem spike. Nunca endpoint público ou raiz de identidade. |

## Component record do slice corrente — F1.1

Este record torna explícitos os treze critérios da missão para a única seleção já
em implementação. A prova na fixture descartável não substitui a prova na VPS.

| Critério | Registro F1.1 | Estado |
|---|---|---|
| Aderência Q1–Q39 | Ansible/Schema implementam Q9/Q27; accounting prepara Q25 sem aplicar hard limits cegos | `SATISFIED_BY_DESIGN` |
| RAM/CPU/disk | nenhum daemon Ansible é instalado no node; custo transitório do apply e delta final ainda serão medidos na VPS | `PARTIAL_NOT_MEASURED_REMOTE` |
| Segurança/privilégio | SSH por identidade do controller, sudo humano, target/machine guard, marker root-only e rollback fail-closed passaram na fixture commit-bound; preview/apply privilegiados no NODE-01 não ocorreram | `SATISFIED_DISPOSABLE_CI_REMOTE_NOT_APPLIED` |
| Maturidade/manutenção | Ansible Core 2.21.3 e Python 3.12 são fixados; lifecycle/release vêm das fontes oficiais abaixo | `SELECTED` |
| Licença/custo | Ansible GPL-3.0-or-later; PyYAML/jsonschema MIT; nenhum plano comercial selecionado | `RECORDED` |
| Simplicidade operacional | agentless, módulos builtin, um inventory e playbooks separados de preflight/apply/rollback | `SELECTED` |
| Backup/restore/rebuild | desired state está no Git e F1.1 não contém dado de aplicação; rollback vazio e reconstrução da fixture passaram, enquanto recovery real continua condicionado ao apply | `SATISFIED_DISPOSABLE_CI_REMOTE_NOT_APPLIED` |
| Portabilidade | inventory e role separam controller/node; F1.1 pressupõe Ubuntu 24.04 + systemd/cgroup v2 declarados | `SELECTED_WITH_OS_CONSTRAINT` |
| Evolução multi-node | grupos de inventory e `ExecutionNode` preservam expansão; este slice só autoriza exatamente `node-01` | `DESIGNED_NOT_TESTED_MULTI_NODE` |
| API/CLI/MCP | CLI Ansible é interface do controller; agentes futuros só poderão acioná-la por capability, nunca receber sudo/inventory secreto | `CLI_SELECTED_FUTURE_MEDIATION_REQUIRED` |
| Observabilidade/auditoria | output sanitizado, correlation/evidence contract e invariance checks definidos; execução remota não ocorreu | `PARTIAL_NOT_APPLIED` |
| Lock-in | YAML/JSON Schema e arquivos systemd são abertos; dependência de módulos builtin torna migração possível, porém não gratuita | `ACCEPTED_MODERATE` |
| Migração/rollback | remoção por proveniência/diretório vazio, quatro recusas fail-closed e rollback limpo passaram no CI; rollback real permanece inaplicável antes do apply | `SATISFIED_DISPOSABLE_CI_REMOTE_NOT_APPLIED` |

## Component record do slice repo-only concluído localmente — F1.2b

DEC-007 fixa o pacote e a fronteira. O commit
`7015c80759a797bcb141773b79cd9b95f6fbecf1` passou a validação local estática,
mas este record ainda não possui CI commit-bound nem prova dinâmica/na VPS. F1.1
bloqueia o apply real; F1.2c bloqueia qualquer workload.

| Critério | Registro F1.2b | Estado |
|---|---|---|
| Aderência Q1–Q39 | Docker/Compose atende Q17; socket root-only preserva mediação futura, mas instalar daemon vazio não satisfaz isolamento/egress/discovery Q20/Q34 | `SATISFIED_BY_DESIGN_FOR_Q17_Q20_Q34_BLOCKED_BY_F1_2C` |
| RAM/CPU/disk | runtime vazio e logs limitados foram desenhados; footprint de instalação, idle e restart ainda não foi medido na VM final nem no NODE-01 | `PENDING_MEASUREMENT` |
| Segurança/privilégio | socket `root:root 0600`, grupo vazio, sem TCP/metrics/bridge/workload, config antes do start e package post-install suprimido têm assertions/negativos versionados | `LOCAL_STATIC_PASS_CI_PENDING_REMOTE_NOT_EXECUTED` |
| Maturidade/manutenção | Docker CE 29.7.2, containerd.io 2.3.3, Buildx 0.36.1 e Compose 5.4.0 estão pinados por versão/digest do índice oficial consultado em 2026-08-16 | `SELECTED_UPDATE_POLICY_NOT_YET_OPERATIONAL` |
| Licença/custo | Docker Engine/Moby, CLI, containerd, Buildx e Compose upstream são Apache-2.0; Docker Desktop não é instalado; nenhum plano pago selecionado | `RECORDED` |
| Simplicidade operacional | repositório oficial, cinco pacotes, systemd e daemon config único; custo aceito de pin/upgrade explícito e policy de autostart | `SELECTED_BY_DESIGN` |
| Backup/restore/rebuild | `/var/lib/docker` e `/var/lib/containerd` não recebem estado útil; runtime deve continuar vazio/rebuildable; helper baseline/manifesto passou testes não privilegiados | `LOCAL_HELPER_TEST_PASS_DYNAMIC_ROLLBACK_CI_PENDING` |
| Portabilidade | OCI, Compose e containerd são portáveis; pacote/source atual exige Ubuntu Noble `amd64` e role separa esse constraint | `SELECTED_WITH_OS_ARCH_CONSTRAINT` |
| Evolução multi-node | configuração cgroup/slices preserva node abstraction, mas F1.2b autoriza exatamente `node-01` e não testa cluster/swarm | `DESIGNED_NOT_TESTED_MULTI_NODE` |
| API/CLI/MCP | CLI é somente root operacional; API TCP ausente e socket negado a agentes; Node Agent/Capability Core fará mediação futura | `CLI_ROOT_ONLY_FUTURE_MEDIATION_REQUIRED` |
| Observabilidade/auditoria | logging `local` limitado e snapshots de units/listeners/network/ruleset estão no harness; métricas/listener e stack central não fazem parte do slice | `HARNESS_STATIC_PASS_DYNAMIC_CI_PENDING_REMOTE_NOT_EXECUTED` |
| Lock-in | imagens/Compose usam contratos OCI/abertos; daemon-specific config e networking criam lock-in moderado documentado | `ACCEPTED_MODERATE` |
| Migração/rollback | marker/prestate/lock externos, baseline e manifesto `find -xdev` limitado às duas raízes substituem remoção recursiva; unitários cobrem symlink/hardlink/open-path/drift/remoção exata | `LOCAL_STATIC_AND_HELPER_PASS_DYNAMIC_CI_PENDING_REMOTE_NOT_APPLICABLE` |

## Contract record repo-only — F1.2c

O commit `b4cbeb066605754d538ff5abe2d294f0759d6f59` adiciona somente o
contrato `platform/network/f1-2c-contract.yaml` e quatro testes. Q20/Q34,
TM-02/TM-03/TM-10, IPv4/IPv6, deny-by-default, grants explícitos, profiles de
egress, descoberta identity-aware e evidência mínima estão codificados. A
seleção tecnológica continua `UNRESOLVED`; não há ruleset, playbook, harness
dinâmico ou prova de conectividade.

| Nível | Estado F1.2c |
|---|---|
| Contrato local | `PASS_4_TESTS` |
| ADR/mecanismo | `PENDING` |
| Integração descartável | `PENDING` |
| NODE-01 | `NOT_EXECUTED` |
| Primeiro workload | `BLOCKED` |

## Evidência oficial por domínio

### Foundations e runtime

- Ansible 2.21 lifecycle/requisitos e release:
  [support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html),
  [installation requirements](https://docs.ansible.com/projects/ansible-core/devel/installation_guide/intro_installation.html),
  [2.21.3](https://github.com/ansible/ansible/releases/tag/v2.21.3),
  [GPL-3.0-or-later](https://github.com/ansible/ansible/blob/devel/COPYING).
- JSON Schema/Python validation:
  [JSON Schema 2020-12](https://json-schema.org/draft/2020-12),
  [PyYAML license](https://github.com/yaml/pyyaml/blob/main/LICENSE),
  [python-jsonschema license](https://github.com/python-jsonschema/jsonschema/blob/main/COPYING).
- Docker suporta Ubuntu Noble; `docker compose` é o plugin corrente:
  [Ubuntu install](https://docs.docker.com/engine/install/ubuntu/),
  [Compose plugin](https://docs.docker.com/compose/install/linux/),
  [Engine 29 release notes](https://docs.docker.com/engine/release-notes/29/),
  [pacotes Noble amd64](https://download.docker.com/linux/ubuntu/dists/noble/pool/stable/amd64/)
  e [chave pública](https://download.docker.com/linux/ubuntu/gpg).
- Os pins F1.2b e SHA-256 de cada `.deb` foram lidos do índice oficial Noble
  `amd64`; chave vendorizada é aceita somente com SHA-256
  `1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570`,
  fingerprint primária `9DC858229FC7DD38854AE2D88D81803C0EBFCD88` e subchave
  `D3306A018370199E527AE7997EA0A9C3F273FCD8`.
- Licenças upstream:
  [Moby](https://github.com/moby/moby/blob/master/LICENSE),
  [Docker CLI](https://github.com/docker/cli/blob/master/LICENSE),
  [containerd](https://github.com/containerd/containerd/blob/main/LICENSE),
  [Buildx](https://github.com/docker/buildx/blob/master/LICENSE) e
  [Compose](https://github.com/docker/compose/blob/main/LICENSE).
- Docker documenta que portas publicadas desviam antes das chains do UFW e que
  desativar iptables tende a quebrar networking:
  [packet filtering/firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/).
- A ordem das chains e a cadeia `DOCKER-USER` precisam ser validadas para a versão
  instalada; a documentação não é evidência do ruleset real.
- cgroup v2/systemd driver:
  [Docker runtime metrics](https://docs.docker.com/engine/containers/runmetrics/).
- BuildKit rootless e restrições de AppArmor em Ubuntu 24.04:
  [rootless guide](https://github.com/moby/buildkit/blob/master/docs/rootless.md).
- slices, `MemoryHigh`/`MemoryMax`, tmpfiles e credentials:
  [systemd.slice](https://manpages.ubuntu.com/manpages/noble/man5/systemd.slice.5.html),
  [resource control](https://manpages.ubuntu.com/manpages/noble/man5/systemd.resource-control.5.html),
  [tmpfiles.d](https://manpages.ubuntu.com/manpages/noble/man5/tmpfiles.d.5.html),
  [systemd.exec](https://manpages.ubuntu.com/manpages/noble/man5/systemd.exec.5.html),
  [credentials model](https://systemd.io/CREDENTIALS/).

### Management Network

- Tailscale identity, grants e outage behavior:
  [identity](https://tailscale.com/docs/concepts/tailscale-identity),
  [grants](https://tailscale.com/docs/reference/syntax/grants),
  [coordination outage](https://tailscale.com/docs/reference/coordination-server-down),
  [open-source components](https://tailscale.com/opensource),
  [pricing](https://tailscale.com/pricing).
- Headscale OIDC/policy/backup e escopo do projeto:
  [OIDC](https://headscale.net/stable/ref/oidc/),
  [policy](https://headscale.net/stable/ref/policy/),
  [project](https://github.com/juanfont/headscale),
  [FAQ](https://github.com/juanfont/headscale/blob/main/docs/about/faq.md).
- WireGuard fornece pares/AllowedIPs, não identidade humana central:
  [overview](https://www.wireguard.com/),
  [quick start](https://www.wireguard.com/quickstart/).

### Core, identity, secrets e durable execution

- Go releases: [go.dev](https://go.dev/doc/devel/release).
- OpenAPI 3.1.2 e linha 3.2:
  [spec index](https://spec.openapis.org/oas/),
  [3.1.2](https://spec.openapis.org/oas/v3.1.2.html).
- OPA integration/security/bundles/logs:
  [integration](https://www.openpolicyagent.org/docs/integration),
  [security](https://www.openpolicyagent.org/docs/security),
  [bundles](https://www.openpolicyagent.org/docs/management-bundles),
  [decision logs](https://www.openpolicyagent.org/docs/management-decision-logs).
- OpenBao release/storage/seal/backup:
  [repository](https://github.com/openbao/openbao),
  [2.6 release notes](https://openbao.org/community/release-notes/2-6-0/),
  [storage](https://openbao.org/docs/configuration/storage/),
  [seal](https://openbao.org/docs/next/concepts/seal/),
  [Raft snapshots](https://openbao.org/docs/next/commands/operator/raft/),
  [root tokens](https://openbao.org/docs/2.5.x/concepts/tokens/).
- Keycloak licensing/configuration; ZITADEL licensing:
  [Keycloak](https://github.com/keycloak/keycloak),
  [supported configurations](https://www.keycloak.org/server/supported-configurations),
  [containers](https://www.keycloak.org/server/containers),
  [ZITADEL licensing](https://github.com/zitadel/zitadel/blob/main/LICENSING.md).
- Temporal release/PostgreSQL setup/schema warning:
  [Temporal releases](https://github.com/temporalio/temporal/releases),
  [PostgreSQL setup](https://github.com/temporalio/samples-server/blob/main/compose/scripts/setup-postgres.sh),
  [archived auto-setup examples](https://github.com/temporalio/docker-compose).
- NATS JetStream persistence/security/recovery:
  [JetStream](https://docs.nats.io/nats-concepts/jetstream),
  [security](https://docs.nats.io/nats-concepts/security),
  [disaster recovery](https://docs.nats.io/running-a-nats-service/nats_admin/jetstream_admin/disaster_recovery).

### Data, artifacts e delivery

- PostgreSQL lifecycle, RLS and PITR:
  [versioning](https://www.postgresql.org/support/versioning/),
  [row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html),
  [continuous archiving](https://www.postgresql.org/docs/current/continuous-archiving.html).
- Valkey releases/security/persistence:
  [releases](https://valkey.io/download/releases/),
  [security](https://valkey.io/topics/security/),
  [persistence](https://valkey.io/topics/persistence/).
- Object storage:
  [MinIO archived repository](https://github.com/minio/minio),
  [Garage releases](https://garagehq.deuxfleurs.fr/_releases.html),
  [S3 compatibility](https://garagehq.deuxfleurs.fr/documentation/reference-manual/s3-compatibility/).
- GHCR auth/digest, attestations and lifecycle:
  [container registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry),
  [artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations),
  [delete/restore](https://docs.github.com/en/packages/learn-github-packages/deleting-and-restoring-a-package).
- CNCF Distribution e pull-through cache candidato:
  [repository](https://github.com/distribution/distribution),
  [registry mirror](https://distribution.github.io/distribution/recipes/mirror/).
- Caddy HTTPS/DNS/Admin API:
  [automatic HTTPS](https://caddyserver.com/docs/automatic-https),
  [DNS challenge](https://caddyserver.com/docs/caddyfile/directives/tls),
  [Admin API](https://caddyserver.com/docs/api).

### Observability, recovery e security

- OTel/Alloy:
  [Collector architecture](https://opentelemetry.io/docs/collector/architecture/),
  [Alloy introduction](https://grafana.com/docs/alloy/latest/introduction/).
- Prometheus/Loki retention e licenças:
  [Prometheus storage](https://prometheus.io/docs/prometheus/latest/storage/),
  [Loki storage](https://grafana.com/docs/loki/latest/configure/storage/),
  [Loki retention](https://grafana.com/docs/loki/latest/operations/storage/retention/),
  [Loki AGPL-3.0](https://github.com/grafana/loki/blob/main/LICENSE),
  [Grafana AGPL-3.0](https://github.com/grafana/grafana/blob/main/LICENSE),
  [Alloy Apache-2.0](https://github.com/grafana/alloy/blob/main/LICENSE).
- Restic and pgBackRest:
  [Restic repository](https://github.com/restic/restic),
  [retention](https://restic.readthedocs.io/en/latest/060_forget.html),
  [integrity checks](https://restic.readthedocs.io/en/stable/045_working_with_repos.html),
  [pgBackRest guide](https://pgbackrest.org/user-guide.html),
  [pgBackRest news](https://pgbackrest.org/news.html).
- Supply chain:
  [Syft](https://github.com/anchore/syft),
  [Trivy](https://github.com/aquasecurity/trivy/blob/main/README.md),
  [Cosign keyless](https://docs.sigstore.dev/cosign/signing/overview/),
  [Cosign verification](https://docs.sigstore.dev/cosign/verifying/verify/).
- LiteLLM remains conditional:
  [overview](https://docs.litellm.ai/),
  [license](https://github.com/BerriAI/litellm/blob/main/LICENSE),
  [production guidance](https://docs.litellm.ai/docs/proxy/prod),
  [release cycle](https://docs.litellm.ai/docs/proxy/release_cycle),
  [official advisories](https://github.com/BerriAI/litellm/security).

## Decisions that remain open

1. object storage: Garage versus deliberate external S3 after compatibility,
   legal, cost and recovery evaluation;
2. PostgreSQL 18 versus 17 após Keycloak/Temporal schema, replay, pgBackRest e
   restore fixture;
3. exact management tailnet plan/policy after HUMAN_GATE;
4. network/egress/service-discovery enforcement v4/v6;
5. quota de disco do writable layer/sandbox;
6. pipeline runner e builder isolation sem enfraquecer AppArmor nem montar socket;
7. tecnologia/configuração do cache OCI local descartável;
8. NATS segregado versus broker separado para mensageria Q38;
9. storage/retention do audit ledger;
10. plugin/provedor DNS e namespace DEV após HUMAN_GATE;
11. Loki/Grafana após review AGPL ou alternativa;
12. LiteLLM versus minimal Core proxy após security/resource spike, seguido de
   slice operacional obrigatório;
13. validação dos alvos provisórios de RPO/RTO/retention após destino off-host e
    restore cronometrado.

Open decisions do not block F1.1 and must not be silently resolved during later
installation. Elas bloqueiam o primeiro workload ou capability correspondente e
jamais autorizam produção ou rotação das credenciais adiadas.
