# 41 — CONSOLIDATED_REQUIREMENTS

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `LEANDRO / Q1–Q40`
Status: `BASELINE_V1`

## 1. Mission boundary

Build a private DEV/lab compute, development and agent-execution platform on the current single Contabo node, incrementally and reversibly.

This document consolidates Q1–Q39 without changing their meaning. Q40-D authorizes technology selection and implementation; it does not authorize production promotion or credential rotation.

## 2. Hard authority requirements

- LEANDRO is the final human authority.
- MCF owns mission/governance/HUMAN_GATE semantics.
- Capability Core is the technical capability/policy enforcement boundary.
- Workflow Engine executes authorized work durably.
- Executor statements do not create technical authority.
- Production promotion always requires a new LEANDRO HUMAN_GATE.
- Current credential rotation remains `DEFERRED_BY_HUMAN_DECISION`.

## 3. Scope hierarchy and isolation

Canonical resource scope:

```text
platform
  -> workspace/tenant
      -> project
          -> mission
              -> sandbox/workload
```

Requirements:

- ownership exists above project;
- network, data, secrets, artifacts, logs, quotas and authorization follow scope;
- lateral access between tenants/projects/sandboxes is denied by default;
- temporary work is disposable unless persistence is explicitly declared;
- an agent cannot consume the protected platform reserve through normal workload authority.

## 4. Capability and interface model

- Capability Core exposes controlled capabilities progressively through API, MCP and CLI.
- API/MCP/CLI are interfaces to the same authorization domain, not separate privilege paths.
- Agents receive capabilities, not raw host authority.
- Agents must not receive root, provider credentials, global secrets or unrestricted Docker daemon access.
- Capability requests must be attributable to identity, tenant/workspace, project, mission and requested capability.

## 5. Compute/runtime

- container-first;
- Docker Engine + Compose initially;
- no Kubernetes requirement in V1;
- host Ubuntu remains protected platform foundation;
- project/sandbox stacks are isolated;
- CPU, RAM, PID/process, disk and network controls must be enforceable;
- runtime is hidden behind platform capabilities;
- `node-01` is the first execution node, not the platform identity;
- architecture remains future multi-node/provider portable.

## 6. Desired state and reconciliation

- versioned desired state is canonical for rebuildable configuration;
- host/platform reconciliation must be idempotent where technically applicable;
- drift must be detectable;
- protected changes still require applicable policy/gates;
- project manifests declare desired capabilities without embedding real secrets;
- a new node must be reconstructible from versioned configuration plus protected persistent state/backups.

## 7. Data and storage

- persistent DEV database per project when required;
- temporary isolated database/resources per sandbox when needed;
- shared Data Service Plane by default with logical tenant/project isolation;
- dedicated instances only when version, extension, load, sensitivity or client requirements justify them;
- hybrid storage: Git + temporary filesystem + object storage + persistent volumes only when required;
- storage credentials and namespaces are scoped;
- backup is separate from storage availability.

## 8. Secrets and identity

- central secret store is required;
- real secrets never enter Git/manifests/logs/evidence;
- temporary/scoped credentials are preferred;
- runtime injection is preferred over static distribution;
- identities are distinguishable; authority is temporary and scoped;
- compromised credentials should have bounded blast radius;
- future workload identity/mTLS/PKI must remain possible.

## 9. Networking and exposure

- services private by default;
- isolated networks by tenant/project/sandbox;
- service discovery by name/identity rather than fixed IP dependency;
- useful Internet egress may be allowed by policy;
- lateral/admin/private access denied by default;
- Management Plane private;
- Agent Gateway public only when minimal/scoped/authenticated/audited;
- Preview Gateway is distinct from Agent Gateway;
- DEV/previews use platform-managed names and automatic TLS;
- production namespace/authority remains separate.

## 10. Delivery and artifacts

- Git/revision is the source of build provenance;
- build/test/deploy DEV is automatable within authorized scope;
- canonical OCI artifacts live in an independent registry;
- local image cache is disposable;
- deploy by immutable digest/version where possible;
- rollback prefers a known prior artifact instead of ad-hoc rebuild;
- CI/build/test jobs run as isolated disposable workloads.

## 11. Durable execution and events

- V1 requires a durable, distributed-capable Workflow Engine even though physical deployment is single-node;
- durable workflow state survives worker/process restarts;
- retries, timeouts, scheduling, cancel, dependent steps and idempotency are first-class requirements;
- command path: API/MCP/CLI -> Capability Core -> authorized execution;
- event path: durable Event Backbone with identity, correlation and reliable consumption;
- event payloads include versioned context such as event, tenant/project/mission/source/time/correlation identifiers;
- Event Backbone does not imply full event sourcing.

## 12. Observability and evidence

Central capability must provide:

- logs;
- metrics;
- events;
- audit trail;
- health/status;
- resource usage;
- correlation/provenance.

`DONE` requires evidence when applicable, not merely a successful command return.

## 13. Capacity management

- reserve resources for OS, SSH/recovery, control plane, observability and backup;
- enforce workload limits;
- support hierarchical quota/accounting;
- controlled burst may use otherwise idle capacity without consuming protected reserve;
- insufficient safe capacity yields queue/admission denial rather than uncontrolled oversubscription.

## 14. AI/model access

- model providers sit behind an AI/Model Gateway;
- agents request model capability rather than receive provider-wide secrets;
- routing may consider capability, cost, latency, availability, quota and policy;
- external and future local backends remain replaceable;
- consumption must be attributable/auditable by scope.

## 15. Security lifecycle and supply chain

- continuous scanning for host/dependencies/images/artifacts;
- vulnerability classification before remediation;
- routine reversible updates may be automated under policy;
- critical host/control-plane changes require impact analysis, checkpoint and rollback;
- source -> dependency -> build -> artifact -> deploy provenance is retained at an appropriate V1 level;
- production changes are never implied by DEV automation.

## 16. Recovery and criticality

State classes:

- `CRITICAL` — governance, platform recovery and key control-plane state;
- `IMPORTANT` — project persistent data and important evidence;
- `REBUILDABLE` — components recoverable from desired state/registry/configuration;
- `DISPOSABLE` — sandboxes, previews, temporary filesystems/workers.

Requirements:

- differentiated RPO/RTO/retention by class;
- off-host backup for protected persistent state;
- restore testing with evidence;
- full-host loss must not require reconstruction from human memory;
- provider portability remains a recovery objective.

## 17. Human cockpit and ecosystem

- Cloud Workstation is optional and must not host authoritative permanent platform state;
- TriView is a human cockpit/view over canonical systems;
- OpenClaw is a channel/front-door layer, not authority;
- Hermes/Codex/other executors remain substitutable;
- Freebuff remains human-interactive rather than required backend.

## 18. Definition of Done for any capability

When applicable, DONE requires:

1. desired state versioned;
2. reproducible/idempotent reconcile path;
3. health/status check;
4. logs/metrics/events/audit visibility;
5. scoped access policy verified;
6. isolation verified;
7. restart/reboot behavior verified;
8. backup/restore or rebuild behavior verified according to criticality;
9. evidence stored;
10. checkpoint/documentation updated.

## 19. Current execution blocker

Repository-only work can proceed.

Host mutation remains blocked until an authenticated live read-only reconciliation of NODE-01 is possible through the existing authorized access path. No private key, password or token may be committed or pasted into project artifacts.
