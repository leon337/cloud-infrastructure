# DEC-006 — Technology Mapping V1 e implantação por lifecycle

Status: **ACCEPTED FOR F1.1 — PARTIAL/CONDITIONAL FOR LATER CAPABILITIES**

## Contexto

Q40-D delegou seleção tecnológica, mas a VPS single-node não suporta instalar
toda a arquitetura opacamente. Uma escolha de ferramenta também não prova que a
capability está pronta.

## Decisão

Adotar `docs/46-technology-mapping-v1.md` como baseline tecnológico evolutivo. Ele
é suficiente para F1.1; gaps explicitamente `CONDITIONAL` impedem instalar ou
declarar pronta a capability posterior correspondente. Toda entrada possui
lifecycle independente:

- `SELECTED`: tecnologia escolhida, ainda não necessariamente instalada;
- `CONDITIONAL`: depende de teste, compatibilidade ou HUMAN_GATE;
- `CANDIDATE`: decisão permanece aberta;
- `PLANNED/ABSENT`: inventário prova ausência no node;
- `VALIDATED`: somente após critérios de DONE aplicáveis.

As seleções centrais são Ansible/JSON Schema, Docker/Compose mediado, Go/OpenAPI,
OPA, Keycloak, OpenBao, Temporal, NATS, PostgreSQL, Valkey, GHCR, Caddy,
OTLP/Alloy/Prometheus, Restic/pgBackRest e Syft/Trivy/Cosign. Loki/Grafana são
condicionais ao review AGPL; isso corrige a seleção anteriormente tratada como
incondicional.

Tailscale é condicional ao gate humano e à aceitação deliberada do coordination
server proprietário; Garage continua candidato; LiteLLM exige spike de segurança
e depois slice operacional. MinIO Community não será usado em novo deployment
porque o repositório oficial está arquivado.

Permanecem decisões bloqueantes: enforcement de rede/egress/service discovery,
quota de disco, pipeline/runner isolation, mensageria Q38, audit ledger, DNS,
object storage, cache OCI local e Model Gateway final. PostgreSQL foundation
precede Keycloak; o secret store operacional precede credenciais reais de
PostgreSQL, Keycloak e Temporal.

## Consequências

- versões são fixadas no precheck de cada slice, não antecipadamente para
  software ausente;
- APIs/protocolos abertos e adapters preservam substituição e portabilidade;
- compliance AGPL permanece revisão técnica sob Q40-D; licença/termos comerciais,
  conta externa, custo, aceite humano ou custódia de chave criam gate quando
  aplicáveis;
- o root token inicial do OpenBao é revogado após bootstrap; custódia rotineira é
  das shares, e root emergencial é gerado por quorum;
- Docker, rede administrativa, cofre, dados e observabilidade são instalados em
  slices separados;
- cada component record registra licença/custo, recursos medidos, privilégios,
  recovery, portabilidade, auditabilidade, lock-in e rollback; ausência mantém
  `PARTIAL`;
- `state/components.yaml` distingue seleção de estado observado.

## Rollback e migração

Cada component record aponta para o caminho de saída: OCI por digest, SQL/PITR,
OpenAPI/OIDC/OTLP/S3, snapshots/export e desired state. Uma tecnologia só pode ser
substituída quando o teste provar preservação das exigências Q1–Q39.

## Revisão

Reavaliar antes de cada major upgrade, diante de abandono/licença/advisory crítico,
ou quando medição real violar o envelope do node. Mudança de ferramenta é ADR;
redução de requisito exige decisão humana explícita.

Nenhuma condição desta ADR autoriza promoção para produção ou rotação das
credenciais marcadas `DEFERRED_BY_HUMAN_DECISION`.
