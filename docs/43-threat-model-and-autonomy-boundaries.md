# 43 — THREAT_MODEL_AND_AUTONOMY_BOUNDARIES

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Status: `BASELINE_V1`

## 1. Protected assets

Highest-value assets include:

- LEANDRO authority/HUMAN_GATE decisions;
- host administrative access and recovery channels;
- Capability Core policies and signing/authentication material;
- secret-store state and provider credentials;
- workflow/event durable state;
- project persistent databases/object data;
- canonical source repositories and immutable artifacts;
- backup/recovery material and evidence;
- tenant/project isolation boundaries.

## 2. Principal classes

- `HUMAN_AUTHORITY`: LEANDRO;
- `PLATFORM_ADMIN`: approved human/device administrative session;
- `GOVERNANCE_SYSTEM`: MCF;
- `PLATFORM_SERVICE`: Capability Core, policy engine, workflow/event services;
- `EXECUTOR`: Hermes, Codex and future replaceable executors;
- `PIPELINE_JOB`: build/test/deploy job identity;
- `PROJECT_WORKLOAD`: DEV application/service;
- `SANDBOX_WORKLOAD`: temporary mission/test/agent workload;
- `EXTERNAL_CALLER`: authenticated caller at Agent Gateway;
- `UNTRUSTED_INTERNET`: unauthenticated/public network origin.

## 3. Trust boundaries

```text
Internet
  |
  | TB-1 public ingress
  v
Agent/Preview Gateways
  |
  | TB-2 capability authorization
  v
Capability Core + OPA
  |
  | TB-3 durable execution
  v
Workflow/Workers
  |
  | TB-4 runtime/network/data isolation
  v
Project/Sandbox resources

Approved device
  |
  | TB-M private management overlay
  v
Management Plane
  |
  | TB-H host/admin boundary
  v
NODE-01
```

## 4. Core autonomy rule

**Autonomy is granted by scope/capability, never by possession of broad infrastructure credentials.**

An executor can be highly autonomous inside a mission and still be technically unable to:

- change host firewall/SSH;
- inspect another tenant/project;
- access provider credentials;
- retrieve global secrets;
- attach itself to the Management Plane;
- publish arbitrary public ports;
- promote to production;
- obtain unrestricted Docker daemon access.

## 5. Allowed autonomous DEV/lab actions

When policy permits the specific mission/project scope, agents may eventually:

- create/destroy disposable sandboxes;
- request bounded compute/network resources;
- run builds/tests;
- deploy approved DEV revisions;
- create/revoke authorized previews;
- request project-scoped database/storage resources;
- read their scoped logs/metrics/status/evidence;
- trigger safe rollback to known DEV artifacts;
- execute durable workflows;
- request model/API capabilities under quota/policy.

## 6. HUMAN_GATE protected actions

At minimum:

- production promotion or production mutation;
- scope expansion outside the approved tenant/project/mission;
- external paid resource creation when not pre-authorized;
- provider-control actions;
- credential rotation currently marked deferred;
- destructive restore/delete of important persistent data when outside pre-approved recovery policy;
- critical host/security changes whose risk exceeds the mission's authorized slice;
- disabling/removing the last validated recovery path.

The Workflow Engine may wait for authorization but cannot create it.

## 7. Threats and required controls

### T-01 — executor escapes capability scope

Threat: prompt/tool compromise causes an executor to attempt host/admin actions.

Controls:

- no root/Docker socket/provider credential in executor environment;
- Capability Core validates scope;
- OPA default deny;
- project/sandbox networks exclude Management Plane;
- scoped short-lived credentials;
- audit every capability call.

### T-02 — Docker socket/root-equivalent compromise

Threat: workload obtains control of Docker daemon and therefore host-level authority.

Controls:

- socket never exposed to project/sandbox containers;
- agents not added to `docker` group;
- root-owned runtime broker/Capability Core mediates operations;
- least-privilege Compose definitions;
- later security testing verifies absence of socket/mount/device escape paths.

### T-03 — lateral movement between projects/tenants

Controls:

- isolated networks;
- scoped database/storage credentials;
- explicit shared-service access path;
- default-deny policy;
- no universal flat project network.

### T-04 — public ingress exposes administrative service

Controls:

- Management Plane binds only to loopback/private overlay where applicable;
- Agent and Preview gateways are separate stacks/surfaces;
- gateway allowlists/routing generated from authorized desired state;
- automatic inventory/check fails if administrative listeners appear on public interfaces.

### T-05 — Docker port publication bypasses expected UFW boundary

Controls:

- no arbitrary `ports:` publication in project/sandbox manifests;
- inspect Docker-created firewall rules after installation;
- explicit gateway-only host listeners;
- security test compares `ss`, UFW and nftables/iptables effective policy;
- stop deployment if an unintended public listener appears.

### T-06 — secret leakage

Controls:

- no real secrets in Git/manifests/logs/evidence;
- central secret store;
- runtime injection;
- output/log redaction;
- scoped credentials;
- repository and image scanning for secrets.

### T-07 — workflow replay/retry duplicates destructive action

Controls:

- idempotency keys;
- durable workflow semantics;
- operation-class specific retry policy;
- compensations/rollback when applicable;
- destructive operations require stronger authorization and explicit state checks.

### T-08 — event spoofing or cross-scope event consumption

Controls:

- authenticated producers/consumers;
- tenant/project/mission context in events;
- durable event identifiers and correlation IDs;
- consumer authorization;
- schema/version validation.

### T-09 — resource exhaustion

Controls:

- protected platform reserve;
- CPU/RAM/PID/storage limits;
- quota by scope;
- concurrent sandbox/job limits;
- admission/queueing when insufficient capacity;
- resource metrics and alerting.

### T-10 — compromised canonical artifact/supply chain

Controls:

- source/revision provenance;
- immutable OCI digest;
- security scanning/SBOM/signing policy introduced incrementally;
- registry credentials scoped;
- rollback uses previously validated immutable artifact;
- critical platform updates pass checkpoint and health/recovery checks.

### T-11 — loss of NODE-01

Controls:

- desired state in Git;
- canonical artifacts outside local cache;
- off-host backup for CRITICAL/IMPORTANT state;
- tested restore/rebuild;
- provider portability;
- VNC/Rescue retained for incident recovery while node exists.

### T-12 — management overlay/account compromise

Controls:

- Tailscale Grants deny by default;
- approved device/user identities only;
- application-layer auth remains mandatory;
- management membership does not grant project/Capability authority automatically;
- OpenSSH/provider recovery remains independent;
- ability to revoke overlay devices.

## 8. Trust assumptions for V1

- NODE-01/hypervisor are trusted infrastructure boundaries; hypervisor compromise is out of direct guest control.
- Docker containers are not treated as a complete hard multi-tenant security boundary against hostile kernel exploits.
- V1 is a private DEV/lab platform; future hostile/commercial multi-tenancy may require stronger sandboxing (for example microVM or hardened user-space kernel isolation) before broad tenant exposure.
- Third-party control planes/providers are trust dependencies only when deliberately selected and documented.

## 9. Evidence required before increasing autonomy

- runtime socket/privilege isolation test;
- project-to-project network isolation test;
- sandbox-to-Management-Plane denial test;
- quota/resource limit test;
- secret non-exposure test;
- policy default-deny and cross-scope denial tests;
- restart/reboot workflow recovery test;
- backup/restore or rebuild test appropriate to each criticality class;
- audit/correlation evidence linking request -> decision -> execution -> result.

## 10. Current temporary boundary

Until live VPS access is revalidated, the executor may modify only the isolated Git mission branch and perform external research. NODE-01 mutation remains `WAITING_FOR_HUMAN_GATE / HG-EXECUTION-ACCESS-001`.
