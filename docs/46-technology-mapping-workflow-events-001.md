# 46 — Technology Mapping Workflow + Events 001

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `Q28-D + Q29-C + Q36-C + Q40-D`
Scope: `DEV/LAB ONLY`
Status: `SELECTED_FOR_INCREMENTAL_VALIDATION`

## 1. Decisions

| Capability | Selected technology | Initial topology |
|---|---|---|
| Durable Workflow Engine | Temporal, self-hosted | single NODE-01 service deployment backed by PostgreSQL; distributed-capable contracts preserved |
| Durable Event Backbone | NATS + JetStream | single NODE-01 JetStream server initially; account/subject isolation; future clustered replication |

Exact image versions/digests are not frozen until the implementation slice performs a current upstream release/security check. The selected major products and contracts are frozen by this mapping unless validation exposes a blocking defect.

## 2. Workflow Engine — Temporal

### Why Temporal

Q28 requires durable/distributed-capable execution from V1, including retries, scheduling, timeouts, cancellation, dependent steps and recovery after worker/process failure. Temporal is purpose-built for durable workflow execution and has a long-lived, mature server/SDK ecosystem.

The self-hosted Temporal server is MIT-licensed. The project has established server releases and supports PostgreSQL persistence, which fits the shared Data Service Plane direction rather than adding a second mandatory database technology.

### Architectural boundary

Temporal is **not** the mission/governance authority.

```text
MCF
  = mission state, authority, HUMAN_GATE

Capability Core + OPA
  = technical authorization / capability enforcement

Temporal
  = durable operational execution after authorization
```

A workflow may enter an application-defined waiting state for authorization, but only MCF/LEANDRO can create the approval. Temporal receives the resulting scoped authorization context through Capability Core and continues the already-authorized workflow.

### Initial topology

V1 physical deployment is single-node, but workflow contracts must not embed NODE-01 addresses or assume one worker.

Conceptually:

```text
Capability Core
    |
    v
Temporal service
    |
    +-- PostgreSQL persistence
    |
    +-- worker task queues
          +-- platform worker
          +-- build/test worker
          +-- future scoped workers
```

Workers remain isolated workloads and do not receive unrestricted Docker socket/root authority.

### PostgreSQL dependency

Temporal persistence will use a dedicated logical database/user in the shared PostgreSQL service plane. Its credentials are platform secrets and are never committed.

The Temporal database is classified `CRITICAL` because losing its durable execution state can invalidate in-progress workflows and operational continuity. It therefore requires off-host backup and restore testing before the workflow capability reaches DONE.

### Required V1 validation

- start workflow and complete normal path;
- kill/restart a worker during an in-progress workflow and verify resume/retry semantics;
- restart Temporal service and verify durable workflow state remains consistent;
- exercise timeout, retry, cancellation and scheduled/delayed execution;
- exercise an application-level wait-for-authorization flow without allowing Temporal to self-authorize it;
- verify workflow metadata carries tenant/project/mission/correlation identifiers;
- verify cross-scope workers cannot read/operate outside allowed task queues/capabilities;
- PostgreSQL backup + isolated restore test;
- reboot NODE-01 and verify service/workflow recovery.

### Operational risk

Temporal is heavier operationally than newer single-binary workflow runtimes. The deployment must therefore be benchmarked on NODE-01 before enabling broad concurrency. If measured overhead violates the protected platform reserve, worker concurrency and service sizing are reduced before considering architectural replacement.

## 3. Alternatives evaluated for workflow execution

### Restate

Strengths:

- lightweight single-binary server path;
- durable execution, workflows, timers, signals, state and retries;
- architecture supports distributed/replicated deployment.

Not selected for the canonical V1 workflow engine because its current server license is Business Source License 1.1 rather than an OSI open-source license. The current additional use grant permits internal deployments and certain abstraction-layer public uses, but introduces a future licensing boundary that the platform would need to continuously preserve as it evolves toward customer/tenant use.

Restate remains a technically credible contingency if Temporal resource/operational measurements are unacceptable and the license boundary is explicitly accepted.

### Hatchet

Strengths:

- durable task/workflow orchestration;
- Postgres-backed architecture;
- retries/scheduling/observability and multiple SDKs;
- comparatively straightforward self-hosting.

Not selected because the project is moving rapidly and, at mapping time, current release/version evolution and recent architecture transitions create more migration uncertainty than Temporal for the platform's core durable execution source of operational truth.

Hatchet remains a contingency for a future task-oriented execution plane if requirements diverge from the canonical workflow engine.

## 4. Event Backbone — NATS JetStream

### Why NATS JetStream

Q36 requires durable asynchronous events with identity, correlation, reliable delivery and recovery of events for temporarily unavailable consumers.

JetStream provides:

- persisted streams;
- replay by sequence/time/policy;
- durable consumers that persist delivery progress;
- acknowledgments and redelivery;
- at-least-once delivery by default;
- message de-duplication / stronger exactly-once mechanisms when explicitly used;
- retention and storage limits;
- account and subject-level authorization;
- future clustered replication based on RAFT.

NATS Server is Apache-2.0 licensed and is operationally compact enough to be a reasonable single-node V1 event backbone.

### Event contract

Canonical platform events contain, as applicable:

```text
event_id
event_type
schema_version
timestamp
source
identity_id
tenant_id
project_id
mission_id
sandbox_or_workload_id
correlation_id
causation_id
payload
```

Events are immutable facts. Commands do not become events merely to avoid the Capability Core authorization path.

### Subject model

Initial subject convention:

```text
platform.events.<domain>.<event_type>
```

Examples:

```text
platform.events.workflow.started
platform.events.workflow.completed
platform.events.sandbox.created
platform.events.sandbox.destroyed
platform.events.deployment.completed
platform.events.authorization.denied
```

Tenant/project context stays in the authenticated identity and event envelope. Where stronger message-plane isolation is needed, NATS Accounts and scoped subject permissions are used rather than relying only on naming conventions.

### Delivery model

Default consumer semantics are **at least once**. Consumers must therefore be idempotent using `event_id`/domain identifiers.

Durable pull consumers are preferred for platform consumers that need backpressure, horizontal scale or controlled retries.

### Single-node durability caveat

JetStream documentation notes that file storage can acknowledge writes before the operating system has performed an `fsync`, depending on `sync_interval`; a sudden OS loss on a non-replicated single node can therefore lose recently acknowledged messages.

For the initial low-throughput platform event streams, the implementation slice must explicitly evaluate a strict disk-sync setting. The starting safety preference is `sync_interval: always` for critical platform-event persistence, accepting the performance cost until measurement shows whether a different bounded interval is necessary.

This does not replace off-host backup/recovery for retained critical event/audit state.

### Initial topology

```text
NATS / JetStream NODE-01
  |
  +-- platform event streams (file storage)
  +-- durable consumers
       +-- MCF integration
       +-- TriView integration
       +-- observability/audit processor
       +-- future notification/integration consumers
```

V1 uses replication factor 1 because Q26 is single-node first. The stream/consumer configuration must remain compatible with a future three-node JetStream cluster; NATS documentation recommends 3 or 5 JetStream-enabled servers for clustered HA.

### Security boundary

- NATS client/admin ports are private platform services, never public Internet endpoints;
- accounts/users/subject permissions apply least privilege;
- project/sandbox workloads do not receive general platform-event publish/subscribe authority;
- platform producers publish only allowed subjects;
- consumers receive only authorized subject sets;
- credentials come from the central secret/identity layer once implemented.

### Required V1 validation

- publish while consumer is offline, restart consumer, verify replay;
- negative/timeout acknowledgment causes controlled redelivery;
- duplicate event handling remains idempotent;
- retention/size limits are enforced;
- unauthorized subject publish/subscribe is denied;
- NATS restart and NODE-01 reboot preserve durable stream/consumer state;
- backup/restore or rebuild procedure appropriate to event criticality is tested;
- resource use is measured before increasing retention/concurrency.

## 5. Temporal and NATS separation

Temporal history is the durable operational record for Temporal workflows. NATS is the platform event backbone for facts emitted to decoupled consumers.

Do not duplicate every internal Temporal history event into NATS. Emit only stable platform-domain events at explicit boundaries, for example:

```text
workflow requested
workflow authorized
workflow started
workflow waiting_for_authorization
workflow completed
workflow failed
```

This prevents two competing workflow state stores while satisfying Q36's decoupled event requirement.

## 6. Rollback/migration strategy

### Temporal

- Capability Core calls a workflow adapter, not Temporal-specific APIs from every caller;
- workflow/domain IDs remain platform-owned;
- no production workloads are introduced in this mission;
- before removal/replacement, complete/cancel/migrate in-flight DEV workflows and preserve required evidence;
- PostgreSQL backup precedes schema/version changes.

### NATS

- event envelope/schema is platform-owned;
- publishers/consumers use an event-bus adapter where practical;
- stream configuration is declarative/versioned;
- replacement can replay retained platform events or start from a documented checkpoint according to criticality/retention policy.

## 7. Source evidence reviewed

Primary upstream documentation/repositories reviewed on 2026-08-16:

- Temporal official documentation and `temporalio/temporal` repository/release/license information;
- Restate official documentation, architecture and current server license;
- Hatchet official repository/current release information;
- NATS official JetStream, consumer, clustering, authentication/accounts/authorization and server release/license documentation.

## 8. Implementation gate

No Temporal or NATS service is installed by this mapping.

Implementation remains behind:

1. authenticated NODE-01 live precheck;
2. Docker runtime foundation PASS;
3. current version/security check and digest pinning;
4. resource budget based on measured NODE-01 headroom;
5. service-specific backup/rollback definitions.
