# 40 — Technology Mapping Foundations 001

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Authority: `Q40-D / LEANDRO`
Scope: `DEV/LAB ONLY`
Status: `SELECTED_FOR_INCREMENTAL_VALIDATION`

## Purpose

Select the minimum foundation technologies needed to start the private DEV/lab platform without reopening Q1–Q39 and without requiring a giant installation.

Exact package versions are deliberately **not** frozen before the live VPS precheck. The implementation will query the approved upstream repository, record the candidate version, then pin the version in desired state before applying it.

## Decision summary

| Capability | Selected technology | State | Primary reason |
|---|---|---|---|
| host desired-state/bootstrap | Ansible Core / playbooks | SELECTED | agentless SSH model, YAML desired-state automation, check mode, repeatable/idempotent modules |
| container runtime | Docker Engine + Docker Compose plugin | BINDING/SELECTED | Q17 requires Docker/Compose initially; official Ubuntu repository; Compose resource limits support |
| private management overlay | Tailscale | SELECTED | device/user identity, deny-by-default policy model through Grants, low bootstrap/operations cost |
| host ingress firewall | existing UFW retained | PRESERVE | currently validated recovery/security boundary; no reason to replace during bootstrap |
| platform authorization policy engine | Open Policy Agent (OPA) | SELECTED_FOR_CORE | general policy decisions, local REST/SDK integration, policy/data separation, auditable policy bundles |

## TM-FND-001 — Desired-state reconciliation: Ansible

### Selected

**Ansible** is the bootstrap/reconciliation tool for NODE-01 and future execution nodes.

### Alternatives considered

- shell-only provisioning;
- cloud-init as the continuing configuration engine;
- Terraform/OpenTofu for in-guest host configuration;
- bespoke TypeScript/Python bootstrap code.

### Rationale

- Managed nodes normally do not require Ansible to be installed; the control node connects to the managed host.
- Inventory provides a clean abstraction for `node-01` now and additional nodes later.
- Playbooks model desired configuration and can be run repeatedly.
- `--check` supports a pre-apply diff-like validation path.
- Roles separate host foundations from later platform capabilities.
- It does not create a second mission/workflow authority; it is an execution mechanism under the mission and policy boundary.

### Guardrails

- No SSH private key is stored in Git or Ansible variables.
- No `ansible_password`, sudo password or provider credential is versioned.
- Host-critical roles must support precheck, backup/checkpoint, apply and verification.
- `changed=0` on the second safe reconciliation is required evidence for idempotent roles where technically applicable.
- Destructive handlers are forbidden in the initial foundation slice.

### Rollback

Ansible roles must include explicit restoration steps or call a versioned rollback playbook for critical configuration. Removal of an installed package is not automatically equivalent to rollback; previous config and access path must be preserved first.

## TM-FND-002 — Runtime: Docker Engine + Compose

### Selected

**Docker Engine + Docker Compose plugin**, installed from Docker's official Ubuntu apt repository.

This implements Q17 rather than reopening it.

### Runtime authority boundary

- Agents do **not** join the `docker` group.
- Agents do **not** receive `/var/run/docker.sock`.
- Project/sandbox runtime actions will later pass through Capability Core or a narrowly scoped runtime broker.
- Platform containers use explicit networks, resource constraints, health checks and restart policy.
- Project/sandbox containers must use CPU, memory and PID limits appropriate to their class.

### Critical firewall finding

Docker's official Ubuntu documentation warns that published container ports can bypass UFW/firewalld policy. Therefore:

1. installing Docker is **not** combined with public service publication;
2. the first Docker validation publishes no application port to `0.0.0.0`;
3. host port exposure remains deny-by-default;
4. the later Preview/Agent Gateway slice must implement and test an explicit Docker/nftables/`DOCKER-USER` ingress policy before any public listener is accepted;
5. management services bind only to loopback/private-management addresses unless an explicit gateway capability says otherwise.

### Rollback

- preserve pre-install package/network/firewall evidence;
- stop/disable Docker if verification fails;
- restore affected firewall/network state before removing packages;
- do not delete `/var/lib/docker` or persistent volumes as part of a normal rollback.

## TM-FND-003 — Private Management Network: Tailscale

### Selected

**Tailscale** as the initial private management overlay.

### Alternatives considered

- manually managed WireGuard;
- self-hosted Headscale control plane;
- SSH tunnels only.

### Rationale

- Q39 requires a private administrative network with user/device identity; Tailscale directly supplies user/device membership plus policy controls.
- Current Tailscale documentation recommends **Grants** for new policy configurations and documents deny-by-default/least-privilege access control.
- It has materially lower bootstrap and recovery complexity than introducing a self-hosted control plane before the management network itself exists.
- Q2 permits an external service when there is a deliberate operational advantage.
- Provider portability remains: workloads and platform APIs do not depend on Tailscale semantics; it is an access-plane implementation detail.

### Deliberate limitation

Tailscale is an external control-plane dependency for the initial management overlay. This is accepted for V1 bootstrap simplicity and must remain replaceable by WireGuard/Headscale or another overlay without changing Capability Core contracts.

### Policy direction

- use Tailscale Grants, not a permissive default policy;
- only approved LEANDRO devices/users may reach management endpoints;
- agents/project workloads are not management-network members;
- management services remain authenticated at the application layer as well;
- do not enable Tailscale SSH in the first slice; preserve the already-validated OpenSSH key path as fallback until the overlay is independently verified.

### HUMAN_GATE

Enrollment/device approval requires a Tailscale identity or equivalent secure enrollment mechanism. Authentication material is never committed. This gate is independent from the currently blocked SSH execution channel.

### Rollback

- keep public OpenSSH fallback unchanged during first validation;
- `tailscale down` / service disable returns routing to the prior state;
- do not tighten UFW/public SSH until private management connectivity has passed independent reconnect tests.

## TM-FND-004 — Authorization policy: Open Policy Agent

### Selected for Capability Core slice

**Open Policy Agent (OPA)** as the policy decision engine, kept separate from the TypeScript Capability Core business logic.

### Rationale

OPA exposes policy/data/query/health APIs and supports policy bundles, allowing authorization rules to be versioned separately from request handling. This maps well to the Q22 dimensions `identity + tenant + project + mission + capability + environment + validity/risk`.

OPA is a **policy decision point**, not the source of mission authority. MCF remains mission/governance truth and Capability Core remains the technical enforcement point.

### Initial policy model

A capability request will eventually provide normalized input such as:

```text
identity
workspace/tenant
project
mission
sandbox/workload
capability
environment
requested resource
validity/risk context
```

The default decision is deny. HUMAN_GATE-protected actions cannot be converted to allow solely by executor-supplied input.

## Source evidence reviewed

Primary documentation reviewed on 2026-08-16:

- Ansible Community/Core documentation: managed-node/control-node model, inventories, repeatable playbooks and check mode.
- Docker official documentation: Ubuntu apt installation, Docker Compose plugin and Compose resource limits.
- Docker official Ubuntu documentation: warning that published container ports can bypass UFW/firewalld rules.
- Tailscale official documentation: access control, Grants, policy-file syntax and device/user management.
- Open Policy Agent official REST API documentation: policy, data/query, health/status APIs and policy bundles.

## First host apply order after live recovery succeeds

1. authenticated read-only VPS precheck;
2. capture package/network/firewall/SSH/service baseline and backup relevant config;
3. install/enroll Tailscale without changing current SSH fallback;
4. validate private management reachability and reconnect/reboot behavior;
5. install Docker Engine/Compose with no public application ports;
6. verify UFW/SSH state is unchanged and inspect resulting nftables/iptables chains;
7. run a constrained `hello-world`/foundation container with no host listener;
8. rerun Ansible in check/apply mode and capture idempotency evidence;
9. checkpoint state before any Platform Core services are deployed.

## Not selected in this slice

No final choice is made here for:

- workflow engine;
- Event Backbone;
- PostgreSQL packaging/topology;
- cache/KV;
- object storage;
- secret store;
- registry/cache implementation;
- observability stack;
- Preview Gateway/DNS/TLS;
- Agent Gateway;
- AI/Model Gateway.

Those capabilities will receive separate evidence-backed mappings before implementation.
