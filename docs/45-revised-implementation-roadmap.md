# 45 — REVISED_IMPLEMENTATION_ROADMAP

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `LEANDRO / Q40-D`
Scope: `DEV/LAB ONLY`
Status: `BASELINE_V1`

## 1. Execution model

The mission advances through small slices. Every slice must satisfy the mission contract:

1. state the goal and affected components;
2. inspect current state;
3. record technology selection and rationale;
4. define preconditions and rollback;
5. implement the smallest coherent change;
6. run functional/security/recovery checks;
7. capture evidence;
8. update canonical documentation/state;
9. checkpoint before the next slice.

Production promotion is outside this roadmap unless LEANDRO later grants a specific HUMAN_GATE.

## 2. Slice 000 — Recovery, architecture baseline and execution branch

**Status:** `IN_PROGRESS_REPOSITORY_PORTION_COMPLETE_HOST_RECOVERY_BLOCKED`

Deliverables:

- mission acceptance + recovery report;
- isolated mission branch;
- consolidated requirements;
- target architecture;
- threat/autonomy model;
- infrastructure blueprint;
- revised roadmap;
- foundation technology mapping;
- structured mission state;
- read-only host precheck.

Exit criteria:

- GitHub state reconciled;
- no secret committed;
- current NODE-01 state authenticated/read-only verified;
- drift recorded;
- recovery access validated before mutation.

Current blocker: `HG-EXECUTION-ACCESS-001` — this executor does not currently possess a secure authenticated SSH execution channel. Repository-only work continues safely.

Rollback: delete/revert mission branch commits; zero NODE-01 changes exist before the gate is cleared.

## 3. Slice 001 — Private Management Network foundation

**Selected direction:** Tailscale management overlay, retaining current hardened OpenSSH as independent fallback.

Goals:

- establish private management reachability for approved LEANDRO user/device identities;
- keep management services non-public;
- define deny-by-default management access policy using Tailscale Grants;
- preserve provider VNC/Rescue and current SSH recovery.

Preconditions:

- Slice 000 live precheck PASS;
- current SSH host fingerprint validated;
- enrollment identity/device action completed securely when required;
- pre-change network/firewall/service evidence captured.

Implementation constraints:

- do not enable Tailscale SSH in the first slice;
- do not disable public OpenSSH fallback yet;
- do not expose any new administrative service publicly;
- no agent/project workload joins the Management Plane.

Validation:

- approved device reaches management overlay;
- unapproved paths remain denied;
- SSH fallback still works;
- reboot/reconnect behavior passes;
- audit/revocation path documented.

Rollback:

- disable/down Tailscale;
- restore pre-slice network state if changed;
- preserve unchanged OpenSSH/VNC/Rescue recovery paths.

## 4. Slice 002 — Docker/Compose runtime foundation

**Binding technology:** Docker Engine + Docker Compose plugin.

Goals:

- install the protected container runtime;
- establish platform filesystem/ownership conventions;
- verify runtime resource limits and health/restart behavior;
- establish explicit firewall/listener safety before any public container exposure.

Preconditions:

- management/recovery paths validated;
- official package source/version recorded and pinned;
- filesystem/network/firewall baseline captured.

Implementation constraints:

- agents are not added to the `docker` group;
- Docker socket is not exposed to agent/project containers;
- no project/sandbox public host ports;
- no database/admin/runtime listener becomes public;
- no persistent data is deleted during rollback.

Validation:

- Docker/Compose health/version checks;
- constrained no-public-port test container;
- CPU/RAM/PID limit test;
- inspect `ss`, UFW and effective nftables/iptables rules;
- reboot/restart test;
- second desired-state reconciliation produces no unexpected changes.

Rollback:

- stop/disable runtime if necessary;
- restore affected firewall/network configuration;
- retain Docker data/volumes unless separately authorized to remove them;
- restore versioned host configuration.

## 5. Slice 003 — Observability and evidence baseline

Goals:

- host/container metrics;
- centralized platform logs;
- structured platform events/audit channel;
- health/status endpoints;
- evidence convention implemented before higher autonomy.

Technology mapping occurs immediately before implementation and must optimize for single-node resource cost, durability needs and future portability.

Exit criteria:

- NODE-01 health/resource visibility;
- Docker/container visibility;
- evidence linked to mission/slice/repository SHA;
- observability survives service restart/reboot as appropriate;
- admin interfaces remain private.

## 6. Slice 004 — Capability Core + policy enforcement skeleton

**Policy engine selected:** OPA.

Goals:

- create headless Capability Core service skeleton;
- normalize identity/scope model `tenant/project/mission/sandbox/capability`;
- integrate OPA with default-deny policies;
- expose private health/status and test API only;
- implement audit trail for authorization decisions.

Initial capabilities are intentionally non-destructive/read-only, for example node/project status and policy introspection allowed by scope.

Exit criteria:

- cross-scope requests denied;
- no executor-provided text can self-authorize HUMAN_GATE operations;
- service restart/reboot passes;
- policy/config state versioned and reproducible.

## 7. Slice 005 — Durable Workflow Engine + Event Backbone

Q28/Q36 require both durable execution and durable asynchronous events.

Before implementation, record a dedicated technology mapping comparing at least:

- workflow durability/retries/idempotency/scheduling/distribution;
- event durability/replay/consumer model/correlation;
- RAM/CPU/disk cost on NODE-01;
- operational complexity and recovery;
- license/maintenance;
- migration/rollback path.

Goals:

- workflow survives worker/process restart;
- retries and idempotency verified;
- tenant/project/mission/correlation metadata propagated;
- events can be consumed after temporary consumer unavailability;
- MCF authority remains outside the engine.

## 8. Slice 006 — Shared Data Service Plane

Technology mapping immediately precedes implementation for:

- PostgreSQL;
- cache/KV when justified;
- object storage;
- secret store;
- dependencies required by workflow/event components.

Goals:

- shared engines with logical tenant/project isolation;
- persistent DEV data and disposable sandbox resources;
- scoped credentials/runtime injection;
- quotas/criticality classification;
- backup and isolated restore test for `CRITICAL`/`IMPORTANT` state.

No existing credential is rotated merely to complete this slice.

## 9. Slice 007 — Artifact plane and isolated CI jobs

Goals:

- independent canonical OCI registry selection/integration;
- local disposable cache;
- immutable digest/provenance;
- isolated disposable build/test job model;
- source → build → scan → artifact → deployment traceability;
- security/secret scanning appropriate to V1.

Agents/pipelines request jobs through platform capabilities; they do not receive administrative host authority.

## 10. Slice 008 — Project manifest, sandbox lifecycle and quotas

Goals:

- versioned project manifest schema;
- project DEV stack reconciliation;
- mission/job sandbox creation/destruction;
- per-workload CPU/RAM/PID/network/storage limits;
- platform reserve and admission control;
- service discovery by name/identity;
- cross-project isolation tests.

## 11. Slice 009 — Preview Gateway, DEV DNS and automatic TLS

Technology mapping precedes implementation.

Goals:

- private-by-default services;
- controlled `INTERNAL`, `PROTECTED_PREVIEW`, `PUBLIC_PREVIEW` classes;
- platform-managed DEV/preview naming;
- automatic TLS;
- automatic route revocation for disposable sandboxes;
- no arbitrary project host-port publication.

Production domains are explicitly excluded.

## 12. Slice 010 — Agent Gateway and API/MCP/CLI interfaces

Goals:

- minimal authenticated public Agent Gateway;
- capability-scoped external access;
- per-identity/project/mission authorization;
- audit/correlation end to end;
- MCP/API/CLI operate over the same Capability Core contracts;
- rate/quota enforcement.

Management endpoints remain private and separate from the Agent Gateway.

## 13. Slice 011 — AI/Model Gateway

Goals:

- model/backend catalog;
- policy routing by capability/cost/quota/availability;
- centralized provider-secret handling;
- scoped accounting/audit;
- backend substitution/fallback;
- no global provider key delivered to executors.

External provider onboarding that requires a new secret/input can pause only that path at HUMAN_GATE while independent work continues.

## 14. Slice 012 — Security lifecycle and supply-chain hardening

Goals:

- continuous host/dependency/image/artifact scanning;
- SBOM/provenance policy appropriate to V1;
- update classification and safe automated remediation paths;
- rollback-tested critical update workflow;
- policy tests for Docker/socket/network/secret boundaries;
- review `FND-CPU-001` and `FND-CLOUDINIT-001` with current provider/kernel evidence.

Critical host/control-plane updates remain gated when their risk exceeds authorized scope.

## 15. Slice 013 — Backup, restore and full rebuild drill

Goals:

- automate off-host backup for all `CRITICAL`/`IMPORTANT` state;
- define concrete RPO/RTO/retention per class;
- restore into an isolated target;
- verify integrity/application function;
- execute documented rebuild drill from desired state + canonical artifacts + backups;
- preserve provider portability.

`FND-BACKUP-001` can close only after evidence satisfies its remaining requirements.

## 16. Slice 014 — Ecosystem adapters and cockpit integration

Goals:

- executor adapter contracts for Hermes/Codex/others;
- TriView reads canonical state rather than becoming source of truth;
- OpenClaw remains channel/front-door adapter;
- Cloud Workstation/Freebuff remain optional human tooling;
- validate platform operation with graphical session stopped/disconnected.

## 17. Mission completion gate

`CODEX-EXECUTION-MISSION-001` is not complete because components are merely running.

Completion requires:

- versioned desired state;
- idempotent reconcile/rebuild;
- access/isolation/policy tests;
- health/observability/evidence;
- restart/reboot behavior;
- backup/restore/rebuild appropriate to criticality;
- current state/checkpoints synchronized with reality;
- unresolved findings accurately retained;
- no production promotion performed without explicit LEANDRO HUMAN_GATE.
