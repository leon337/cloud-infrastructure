# 42 — TARGET_ARCHITECTURE

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Status: `BASELINE_V1`
Deployment target: `NODE-01 / DEV-LAB`

## 1. Architectural intent

The platform separates governance, authorization, durable execution and workload runtime so no executor or runtime becomes an implicit source of authority.

```text
                           LEANDRO
                              |
                           TriView
                              |
                              v
                             MCF
                   mission / HUMAN_GATE
                              |
                              v
                    +------------------+
                    | CAPABILITY CORE  |
                    | API / MCP / CLI  |
                    | authz enforcement|
                    +--------+---------+
                             |
                policy ------+------ audit
                 OPA         |       evidence
                             v
                    +------------------+
                    | WORKFLOW ENGINE  |
                    | durable state    |
                    +----+--------+----+
                         |        |
                         |        +-------> Durable Event Backbone
                         |                        |
                         v                        +--> MCF/TriView/Observability
                  isolated workers
                         |
                    runtime broker
                         |
                    Docker/Compose
                         |
              project/mission sandboxes
```

## 2. Network planes

```text
INTERNET
   |
   +--> Agent Gateway ---------> Capability Core
   |
   +--> Preview Gateway -------> explicitly exposed DEV services

LEANDRO APPROVED DEVICE
   |
   v
PRIVATE MANAGEMENT OVERLAY
   |
   +--> management APIs/dashboards
   +--> host maintenance interfaces
   +--> OpenSSH fallback path remains separate/recoverable

PROJECT / SANDBOX NETWORKS
   |
   +--> own project services
   +--> explicitly authorized shared Data/Platform services
   +--> policy-controlled Internet egress
   X--> other projects / host admin / Management Plane
```

Initial management-overlay implementation: Tailscale with deny-by-default Grants. Application-layer authentication remains required; network membership alone is not authorization.

## 3. NODE-01 physical deployment

V1 runs on one execution node but keeps a node abstraction in platform data/contracts.

```text
NODE-01
Ubuntu 24.04 LTS
|
+-- Recovery / access
|   +-- OpenSSH public-key fallback
|   +-- UFW + fail2ban
|   +-- Tailscale management overlay
|   +-- provider VNC / Rescue break-glass
|
+-- Host reconciliation
|   +-- Ansible-managed desired state
|
+-- Container runtime
|   +-- Docker Engine
|   +-- Compose plugin
|   +-- platform networks
|   +-- per-project networks
|   +-- per-sandbox networks
|
+-- Control plane, headless
|   +-- Capability Core
|   +-- OPA
|   +-- Workflow Engine
|   +-- Event Backbone
|   +-- Agent Gateway
|   +-- Preview Gateway
|
+-- Shared service plane
|   +-- PostgreSQL
|   +-- object storage
|   +-- cache/KV
|   +-- registry cache
|
+-- Observability
|   +-- logs
|   +-- metrics
|   +-- events
|   +-- audit/evidence
|
+-- Workers / projects / sandboxes
|   +-- isolated disposable jobs
|   +-- DEV project stacks
|   +-- mission sandboxes
|
+-- Cloud Workstation
    +-- optional human cockpit only
```

## 4. Authority flow

A normal operation follows:

```text
request
 -> authenticated identity
 -> mission/scope context
 -> Capability Core
 -> OPA/policy decision
 -> synchronous service action OR durable workflow start
 -> isolated execution
 -> result + events + evidence
```

A protected operation follows:

```text
request
 -> policy identifies HUMAN_GATE
 -> mission state WAITING_FOR_AUTHORIZATION
 -> LEANDRO decision through MCF/governance
 -> short-lived scoped authorization
 -> Capability Core validates approved scope
 -> workflow resumes
 -> authorization expires/revokes after operation
```

No workflow engine or executor can self-approve the gate.

## 5. Resource model

Every managed workload resource carries at least:

```text
workspace_or_tenant_id
project_id
mission_id (optional for persistent DEV resources)
sandbox_or_workload_id
execution_node_id
resource_class
criticality
owner_identity
created_at
expiry/retention when disposable
```

Resource classes include compute, network, database, storage, secret binding, deployment, preview, job and evidence.

## 6. Persistence model

### CRITICAL

- desired-state repositories/configuration needed for governance/rebuild;
- Capability Core policy/configuration state;
- workflow/event state needed for durable recovery;
- secret-store durable state and protected recovery material.

### IMPORTANT

- project DEV databases;
- important object data;
- retained evidence/audit according to policy.

### REBUILDABLE

- application containers;
- control-plane service containers when configuration/state lives elsewhere;
- registry cache;
- package/build caches.

### DISPOSABLE

- mission/job sandboxes;
- temporary databases/storage;
- preview instances;
- build workspaces.

## 7. Runtime boundary

Docker is a protected platform mechanism.

- Docker socket is never mounted into agent/project containers by default.
- `docker` group membership is not an agent capability.
- Capability Core/runtime broker validates scope before runtime operations.
- Compose/project definitions use explicit networks and resource limits.
- public port publishing is forbidden except through explicitly reviewed gateway stacks.
- Docker/UFW interaction is treated as a security-critical networking concern.

## 8. Service discovery

V1 uses container/network DNS names inside authorized networks. Clients depend on service names/contracts, not fixed container IP addresses.

Shared services are reached through dedicated authorized attachment/proxy patterns rather than attaching every project to a universal flat network.

## 9. Desired-state layers

```text
Git
|
+-- host desired state (Ansible)
+-- platform Compose/manifests
+-- policy bundles/config
+-- project manifests/schemas
+-- runbooks/tests/evidence metadata
```

Runtime state is observed and reconciled against desired state; Git changes alone do not bypass policy or protected gates.

## 10. Deployment sequence

1. recover/verify access and baseline;
2. private management overlay;
3. Docker runtime with zero public project ports;
4. filesystem/ownership and platform reserve controls;
5. observability baseline;
6. Capability Core + OPA skeleton;
7. durable workflow + Event Backbone;
8. Data Service Plane;
9. artifact/registry flow;
10. sandbox/job model;
11. Preview Gateway/DNS/TLS;
12. Agent Gateway + model gateway;
13. full recovery/rebuild drills and hardening.

## 11. Explicit non-goals for V1

- production hosting/promotion without HUMAN_GATE;
- Kubernetes;
- multi-node HA;
- commercial SaaS billing/tenant portal;
- full service mesh;
- direct executor/root/Docker authority;
- dependency on the graphical Cloud Workstation for platform uptime.
