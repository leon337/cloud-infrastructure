# 47 — Technology Mapping Data + Secrets + Observability 001

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `Q10/Q11/Q12/Q15/Q35/Q38/Q40-D`
Scope: `DEV/LAB ONLY`
Status: `SELECTED_FOR_INCREMENTAL_VALIDATION`

## 1. Decisions

| Capability | Selected technology | V1 role |
|---|---|---|
| relational Data Service Plane | PostgreSQL 18 | shared engine, logical DB/role isolation |
| central secrets / PKI foundation | OpenBao | KV, dynamic DB credentials later, PKI later, audit |
| object storage | Garage | private S3-compatible object store |
| cache/KV | Valkey | cache/ephemeral coordination only, not canonical durable state |
| telemetry collection | OpenTelemetry Collector | receive/process/export telemetry |
| metrics | Prometheus | host/platform/workload metrics |
| logs | Grafana Loki | centralized log store/query |
| observability UI | Grafana | private dashboards/query/alert cockpit |
| durable platform events | NATS JetStream | selected separately in doc 46 |

Exact container tags/digests are pinned immediately before each implementation slice after current release/security verification.

## 2. PostgreSQL 18 — relational Data Service Plane

### Selection

Use **PostgreSQL major 18**, current supported minor at deployment time, as the shared relational engine.

At mapping time PostgreSQL 18 is the current stable major and 18.4 is the current minor; PostgreSQL recommends keeping a supported major on its current minor release.

### V1 tenancy model

One PostgreSQL engine may host multiple logical platform/project databases, but no application receives a global superuser credential.

Example logical ownership:

```text
postgres engine
  |
  +-- temporal / temporal_role
  +-- capability_core / capability_core_role
  +-- project_<id>_dev / project_<id>_role
  +-- future service-specific DBs/roles
```

Rules:

- separate database/role when isolation or lifecycle requires it;
- project roles cannot enumerate/read other project data by default;
- administrative role is platform-only;
- sandbox databases/roles are temporary and carry expiry/mission metadata;
- credentials come from OpenBao once the secret plane is initialized;
- connection strings never enter Git/evidence.

### Temporal compatibility gate

Temporal uses PostgreSQL persistence, but the actual PostgreSQL 18 + selected Temporal release pair must pass a compatibility/schema smoke test before becoming canonical. If upstream compatibility blocks PostgreSQL 18, the fallback is PostgreSQL 17 current minor under a recorded ADR rather than forcing an unverified combination.

### Criticality

- Temporal DB: `CRITICAL`.
- Capability Core durable policy/config data if stored here: `CRITICAL`.
- project DEV DB: normally `IMPORTANT`.
- temporary sandbox DB: normally `DISPOSABLE` unless mission explicitly promotes its state.

### Validation

- authentication and least-privilege role tests;
- cross-project denial test;
- connection/resource limits;
- restart/reboot;
- logical backup and isolated restore;
- schema migration rollback/forward procedure;
- resource metrics;
- Temporal compatibility before workflow slice DONE.

## 3. OpenBao — central secrets and identity-adjacent cryptographic services

### Selection

Use **OpenBao** with Integrated Storage (Raft) for V1.

OpenBao provides identity-based secret management, auditable API access, dynamic database credentials and PKI capabilities. Its documentation recommends Integrated Storage for most use cases because it avoids an additional external storage dependency and supports HA/backup workflows.

### V1 topology

Single NODE-01 instance first:

```text
OpenBao
  |
  +-- integrated Raft storage on protected persistent volume
  +-- KV secrets
  +-- audit device
  +-- future database secrets engine
  +-- future PKI/workload identity
```

Its API/admin listener is Management/Control Plane only and must never become a public Internet endpoint.

### Bootstrap boundary

OpenBao initialization creates recovery/unseal material. That material is **not** stored in Git, chat, normal Ansible vars, project logs or on the same unprotected path as the only OpenBao data copy.

The initialization/recovery-material handling step is a HUMAN_GATE because it requires LEANDRO to securely receive/store protected recovery material.

This does not rotate existing VPS/provider credentials. Existing credentials remain unchanged until separately authorized.

### Secret namespace direction

```text
kv/platform/...
kv/tenants/<tenant>/projects/<project>/...
```

Actual policy uses authenticated identity and scoped paths; naming alone is not an authorization boundary.

### Future dynamic credentials

After PostgreSQL integration is proven, the database secrets engine may issue leased project/service credentials. Static credentials can coexist during migration; no forced rotation is implied by installing OpenBao.

### Criticality and recovery

OpenBao state is `CRITICAL`.

DONE requires:

- encrypted persistent storage and restrictive filesystem ownership;
- initialization/recovery material handled outside Git;
- audit enabled;
- snapshot/off-host backup procedure;
- isolated restore/unseal test;
- reboot/recovery test;
- documented break-glass path.

## 4. Garage — private S3-compatible object storage

### Selection

Use **Garage 2.x** as the V1 self-hosted object store.

Reasons:

- S3-compatible API;
- explicitly designed for lightweight small-to-medium self-hosted deployments;
- supports a single-node bootstrap path and future multi-node replication;
- avoids coupling object storage to a hyperscaler;
- provides a clean portability boundary for clients that speak S3.

Garage is AGPLv3; this is acceptable for self-hosted platform use and must be retained in license inventory.

### Initial topology

- one NODE-01 Garage node;
- replication factor 1 because there is physically one node;
- metadata/data on persistent paths, never `/tmp`;
- S3/admin/RPC endpoints private;
- bucket/key creation mediated by platform administration/Capability Core, not given directly to agents;
- credentials stored/injected through OpenBao after secret plane bootstrap.

### Namespace

Examples:

```text
platform-artifacts-aux
platform-backup-staging
project-<id>-objects
sandbox-<id>-objects
observability-loki
```

Buckets/keys follow lifecycle/criticality. Sandbox buckets are disposable and automatically revocable; project buckets persist according to policy.

### Important limitation

A single-node Garage instance provides an object API, **not independent backup**. Data that requires off-host recovery must be copied to an independent destination. Future additional nodes may add replication, but replication also does not replace backup.

## 5. Valkey — cache only in canonical V1

### Selection

Use **Valkey 9.x** as the shared cache/KV service where caching is justified.

### Boundary

Valkey is not a workflow state store, mission source of truth, secret store, canonical event log or primary project database.

Canonical V1 classification is `REBUILDABLE`/`DISPOSABLE` cache state. Persistence is disabled unless a later capability has an explicit durable use case and ADR.

### Security

- private listener only;
- named ACL users, no anonymous `nopass` default in platform deployment;
- per-service command/key permissions where practical;
- memory limit + eviction policy;
- no dangerous/admin commands for application identities;
- credentials from OpenBao.

This follows Valkey's documented ACL model, which can limit both commands and key patterns.

## 6. Observability architecture

### Selected stack

```text
applications / host / platform services
          |
          v
OpenTelemetry Collector
   |          |          |
   |          |          +--> traces later if justified
   |          +-------------> Loki (logs)
   +------------------------> Prometheus (metrics)

NATS JetStream --------------> structured domain/platform events
OpenBao audit ---------------> protected audit/log pipeline

Prometheus + Loki + event/audit sources
                 |
                 v
              Grafana
          private management UI
```

### Why OpenTelemetry Collector

The Collector provides a vendor-neutral receiver/processor/exporter pipeline so applications are not tightly coupled to one observability backend.

### Prometheus

Use Prometheus for:

- NODE-01 host metrics;
- Docker/container metrics;
- platform service metrics;
- resource reserve/quota signals;
- health/SLO alert inputs.

Admin UI/API stays private. Retention is explicitly size/time bounded before broad workload fan-out.

### Loki

Use Loki for centralized logs.

Initial DEV/lab deployment may use single-binary Loki with a bounded persistent filesystem store to avoid blocking observability on the later object-storage slice. Grafana documents filesystem storage as suitable for low-volume/development single-binary use but not the preferred production/HA storage model.

After Garage is validated, migrate Loki TSDB/chunk storage to the Garage S3 endpoint and test restore/query before deleting old storage.

### Grafana

Grafana is a human observability cockpit only. It does not become the canonical source of mission/policy state.

- bind/private network only;
- provision datasources/dashboards declaratively;
- individual authentication integrated in the identity slice;
- no public anonymous admin mode.

## 7. Observability criticality

- current operational metrics: `REBUILDABLE` unless retention is required for evidence;
- routine DEV logs: `IMPORTANT` or bounded `REBUILDABLE` by project policy;
- security/audit evidence required for governance: `IMPORTANT` or `CRITICAL` according to policy;
- NATS workflow/domain events: classified per stream/retention, independent from Loki;
- OpenBao audit records receive protected handling because they expose security metadata even when secret values are protected.

## 8. Resource guardrails

NODE-01 is finite. Before enabling long retention:

- measure idle and active RAM/CPU for each service;
- set explicit Compose memory/CPU/PID limits where applicable;
- set Prometheus retention size/time;
- set Loki retention and disk-pressure alerting;
- set Garage quotas/capacity reserve;
- set PostgreSQL connection/resource controls;
- set Valkey maxmemory/eviction;
- refuse new disposable work when platform reserve would be violated.

## 9. Incremental deployment order

After the live recovery and Docker foundation gates:

1. OpenTelemetry Collector + minimal host/container metrics/log collection;
2. Prometheus + bounded local storage;
3. Loki single-binary + bounded persistent filesystem storage;
4. Grafana private dashboard;
5. PostgreSQL 18 compatibility/backup validation;
6. OpenBao initialization HUMAN_GATE + protected recovery procedure;
7. Garage S3 + project/bucket isolation tests;
8. migrate Loki to Garage only after Garage restore path passes;
9. Valkey only when an actual cache consumer exists.

This preserves observability before increasing autonomy without installing the full Data Service Plane at once.

## 10. Source evidence reviewed

Primary upstream documentation reviewed on 2026-08-16:

- PostgreSQL 18.4 documentation, release/versioning policy;
- OpenBao 2.6.x documentation for Integrated Storage, database secrets, PKI and audit devices;
- Garage official documentation/repository for S3 compatibility and single-node/multi-node model;
- Valkey documentation for releases, ACLs and persistence;
- OpenTelemetry Collector architecture;
- Prometheus server storage/retention options;
- Grafana Loki storage/deployment documentation;
- Grafana documentation for the observability UI.

## 11. No activation yet

This mapping performs no NODE-01 mutation, creates no external production resource, rotates no credential and publishes no service. Activation remains downstream of `HG-EXECUTION-ACCESS-001` and each slice's own recovery/security gate.
