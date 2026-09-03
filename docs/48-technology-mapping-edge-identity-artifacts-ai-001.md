# 48 — Technology Mapping Edge + Identity + Artifacts + AI 001

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `Q13/Q18/Q21/Q22/Q32/Q37/Q40-D`
Scope: `DEV/LAB ONLY`
Status: `SELECTED_FOR_INCREMENTAL_VALIDATION`

## 1. Decisions

| Capability | Selected technology | V1 role |
|---|---|---|
| public HTTP(S) edge / Preview Gateway | Traefik v3 | TLS termination + explicit file-provider routing |
| public identity provider | Keycloak 26.x | OIDC/OAuth2 human + service identity |
| Capability Core / Agent Gateway implementation | Node.js 24 LTS + TypeScript + Fastify v5 | policy-enforcing API services |
| MCP adapter | official MCP TypeScript SDK | Streamable HTTP adapter over Capability Core |
| canonical OCI registry | GitHub Container Registry (GHCR) | independent canonical OCI artifacts |
| local OCI pull-through cache | zot | disposable local OCI cache/sync |
| AI / Model Gateway | LiteLLM Proxy | provider abstraction, routing, budgets, fallback |
| public DEV DNS | wildcard record in an operator-owned domain | stable DEV namespace without per-preview DNS mutation |
| automatic TLS | Traefik ACME | per-host HTTPS; staging CA before production CA |

Exact versions/digests are revalidated and pinned immediately before deployment. No `latest` image tag is accepted as canonical desired state.

## 2. Traefik v3 — public edge and Preview Gateway

### Selection

Use **Traefik v3** as the only platform component that publishes HTTP(S) application ingress on NODE-01.

The critical implementation choice is to use Traefik's **file provider**, not the Docker provider/socket. Dynamic route files are reconciled by a privileged platform component after Capability Core authorization.

This preserves Q17's Docker authority boundary:

```text
Capability Core
  -> authorize preview
  -> reconcile versioned/generated route data
  -> Traefik file provider reload
  -> edge-preview network
  -> authorized workload
```

Traefik therefore does not need `/var/run/docker.sock` merely to discover services.

### Public listener policy

Only the edge stack may publish the platform's HTTP(S) ports:

- TCP/80 for redirect and ACME HTTP-01 when enabled;
- TCP/443 for HTTPS.

Project/sandbox stacks do not publish arbitrary host ports.

Before any public listener is enabled, the Docker/UFW/nftables validation from the foundation mapping must pass.

### Preview isolation

Traefik joins only an `edge-preview` network plus its own control dependencies. A workload becomes reachable by Traefik only after the authorized preview attachment/reconciliation step. Traefik does not join every private project network by default.

Preview routes have explicit lifecycle metadata and are removed when the associated sandbox/preview expires.

## 3. DEV DNS and ACME

### Wildcard DNS instead of per-preview DNS mutation

V1 does not require a DNS API call for every sandbox. One operator-controlled wildcard record can resolve the DEV namespace to NODE-01:

```text
*.dev.<operator-domain> -> NODE-01 public IPv4
```

The platform can then allocate names such as:

```text
<preview-id>.dev.<operator-domain>
<project>-<sandbox>.dev.<operator-domain>
```

without giving agents DNS-provider credentials.

### TLS

Traefik ACME obtains per-host certificates using HTTP-01 once the wildcard DNS record exists. This avoids a DNS-provider token in the first public-preview implementation.

Rules:

- Let's Encrypt/ACME staging CA first;
- certificate storage is persistent and protected;
- route creation is rate-limited/admission-controlled to avoid certificate issuance abuse;
- public certificate issuance happens only for an authorized preview hostname;
- a future wildcard certificate may use DNS-01 only after a provider-specific scoped credential path is designed.

### Deferred external fact / HUMAN_GATE

The repository does not contain a verified operator-owned DEV domain/DNS provider. Public preview activation therefore has a future gate:

`HG-DEV-DNS-001`

LEANDRO must designate an owned domain/subdomain and arrange the wildcard A/AAAA policy or authorize a provider-specific DNS integration. No DNS credential should be pasted into chat or committed.

This gate blocks public preview activation only; private platform implementation continues independently.

## 4. Keycloak — human/service identity provider

### Selection

Use **Keycloak** for platform human and service identity.

Reasons:

- mature OIDC/OAuth2 provider;
- built-in service accounts for machine-to-machine clients;
- PostgreSQL 18 is currently a supported/tested database;
- Apache-2.0 licensing avoids the AGPL server licensing boundary identified in the ZITADEL alternative;
- current Keycloak supports explicit frontend/admin hostname separation and reverse-proxy filtering patterns.

### Role in the architecture

Keycloak authenticates principals and issues tokens. It does **not** replace Capability Core/OPA authorization or MCF mission authority.

```text
Keycloak
  -> authenticated identity / claims
  -> Capability Core
  -> OPA evaluates scope/capability/environment/mission context
  -> allow / deny / HUMAN_GATE-required
```

### Public vs administrative surface

When browser/OIDC login is required publicly, expose only the Keycloak paths required for OIDC/login/resource delivery. Keycloak documentation explicitly recommends keeping `/admin/`, the administrative realm, health and metrics off the public surface.

The Keycloak admin hostname/API remains reachable only from the private Management Plane. Reverse-proxy policy, not merely Keycloak's generated `hostname-admin`, enforces this network separation.

### Database and criticality

Use a dedicated PostgreSQL database/role in the shared Data Service Plane. Identity state is `CRITICAL` and must have off-host backup + tested restore before this capability reaches DONE.

### Bootstrap HUMAN_GATE

Creation/receipt of the first platform administrator credential/recovery material is a future HUMAN_GATE. Bootstrap secrets are not committed, echoed into evidence or reused as general platform credentials.

## 5. Capability Core + Agent Gateway — Node.js 24 LTS, TypeScript, Fastify v5

### Runtime selection

Use **Node.js 24 LTS** for platform TypeScript services. At mapping time Node.js 24 is an LTS line, while Node.js 26 is still Current; the platform intentionally chooses the LTS line.

### HTTP framework

Use **Fastify v5** because its schema-first request validation and response serialization align with a capability API whose inputs/outputs must be explicit, testable and resistant to accidental data disclosure.

Rules:

- JSON Schema is platform-authored code; never accept arbitrary caller-supplied validation schemas;
- validation runs before business logic;
- async authorization/resource checks run in hooks/handlers, not expensive async schema validation;
- response schemas are used to prevent accidental secret/internal-field disclosure;
- identity/token verification occurs before capability execution;
- every state-changing request carries correlation and idempotency metadata where applicable.

### Capability Core and Agent Gateway are separate deployable concerns

`Capability Core` is the internal authorization/enforcement service.

`Agent Gateway` is the minimal external API surface that authenticates callers, rate-limits them and forwards normalized authorized capability requests inward.

They may share TypeScript packages/contracts but do not collapse into one trust boundary.

### MCP

Use the **official MCP TypeScript SDK** as an adapter over the same Capability Core contracts. For remote MCP, use Streamable HTTP; deprecated HTTP+SSE is not the canonical V1 transport.

MCP tools expose scoped platform capabilities, never raw shell/root/Docker/provider authority.

## 6. Canonical OCI registry — GHCR

### Selection

Use **GitHub Container Registry (`ghcr.io`)** as the canonical independent OCI registry for platform/project images.

Reasons:

- source repository is already on GitHub;
- GHCR supports OCI images;
- repository-linked GitHub Actions can publish with narrowly scoped `GITHUB_TOKEN` permissions instead of a standing broad registry secret;
- images can be pulled by digest;
- GitHub Actions supports artifact attestations/provenance for container images;
- losing NODE-01/local cache does not lose canonical artifacts.

### Supply-chain rules

- CI actions are pinned to commit SHAs, not floating tags, when the pipeline is created;
- image output records source repository/revision;
- canonical deployment references immutable digest;
- build provenance/attestation is generated where supported;
- package visibility/access is explicitly configured;
- NODE-01 receives only the minimum package-read credential required for private images, later sourced from OpenBao.

No GitHub token is committed.

## 7. Local OCI cache — zot

### Selection

Use **zot** as a local OCI-native registry/cache layer.

zot is vendor-neutral, implements the OCI Distribution model and provides sync/on-demand upstream retrieval. In this architecture it is **not** the canonical registry.

```text
build -> GHCR canonical digest
          |
          v
      zot local cache
          |
          v
       NODE-01 pulls
```

The zot cache is `REBUILDABLE`. Cache loss must not affect artifact provenance or recoverability. Upstream registry credentials, if needed, come from the secret plane and are scoped read-only.

## 8. LiteLLM Proxy — AI / Model Gateway

### Selection

Use **LiteLLM Proxy** behind Capability Core as the initial AI/Model Gateway.

It provides a common model interface across many providers plus routing/retry/fallback, per-project/user cost tracking, budgets/rate limits and a centralized proxy model suitable for Q32.

### Authority boundary

Agents do not call a provider with a global provider API key.

```text
agent/workflow
 -> Capability Core authorization
 -> LiteLLM virtual/scoped identity or internal gateway credential
 -> policy-selected model alias
 -> provider backend
```

Provider credentials are injected from OpenBao into LiteLLM only. They are never returned to the calling agent.

### Model catalog

Platform-owned aliases hide provider coupling, for example conceptually:

```text
coding.fast
reasoning.general
vision.general
embedding.general
local.general
```

Routing policy may consider capability, allowed data class, tenant/project quota, cost, latency and availability.

### Supply-chain guardrail

LiteLLM publishes signed container releases. The implementation slice must select a stable release, verify its image signature/provenance and pin the digest rather than tracking `latest`/dev tags.

### Database/state

If LiteLLM features require persistent database state, use a dedicated PostgreSQL logical database/role; secrets remain in OpenBao. Usage/accounting data inherits the applicable tenant/project and retention policy.

## 9. Public edge separation

One Traefik edge process may terminate public TLS on ports 80/443, but the exposed surfaces remain strictly separated by hostname, router configuration, middleware/policy and backend trust boundary:

```text
agent.<domain>
  -> Agent Gateway only

id.<domain>
  -> allowed Keycloak public OIDC/login paths only

*.dev.<domain>
  -> authorized Preview routes only
```

Management endpoints, Keycloak admin, Grafana admin, OpenBao, Temporal admin, NATS admin, PostgreSQL and Docker never receive public routes.

## 10. Required validation before public activation

- Docker/UFW/nftables effective-policy test PASS;
- no project container publishes host ports directly;
- Traefik has no Docker socket;
- unauthorized route-file changes cannot be made by project/agent identities;
- public scanner/inventory shows only explicitly intended listeners/routes;
- Keycloak public paths exclude admin/master realm/health/metrics according to policy;
- OIDC issuer/audience/signature validation tests PASS;
- cross-tenant capability calls denied;
- MCP and REST produce identical authorization outcomes for equivalent capability requests;
- GHCR build -> digest -> attestation -> pull path verified;
- zot cache removal/rebuild verified;
- LiteLLM provider keys absent from agent environment/logs;
- ACME staging issuance/renewal/restart test PASS;
- preview creation/revocation lifecycle PASS;
- restart/reboot tests PASS.

## 11. Source evidence reviewed

Primary upstream documentation reviewed on 2026-08-16:

- Traefik v3 file provider and ACME certificate resolver documentation;
- Keycloak 26.x database, reverse proxy, hostname, OIDC and service-account documentation;
- Node.js release/LTS documentation;
- Fastify v5 validation/serialization documentation;
- official MCP TypeScript SDK server/transport documentation;
- GitHub Container Registry and artifact-attestation documentation;
- zot upstream repository/sync examples;
- LiteLLM official proxy documentation/repository/release signature guidance;
- ZITADEL current licensing and self-hosting documentation as an evaluated alternative.

## 12. No activation yet

This mapping does not:

- publish TCP/80 or TCP/443;
- change DNS;
- request a certificate;
- create Keycloak users/passwords;
- create/publish a container image;
- install zot/LiteLLM;
- create a provider API key;
- expose an Agent Gateway;
- promote anything to production;
- rotate any credential.

All NODE-01 activation remains downstream of the authenticated live recovery gate and the slice-specific prechecks/rollback plans.
