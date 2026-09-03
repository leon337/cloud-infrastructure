# 44 — INFRASTRUCTURE_BLUEPRINT_V1

Data: 2026-08-16
Mission: `CODEX-EXECUTION-MISSION-001`
Status: `BASELINE_V1_INCREMENTAL`
Physical topology: `single NODE-01`

## 1. Node baseline

Canonical last-verified snapshot before this mission:

- Ubuntu 24.04.4 LTS;
- kernel 6.8.0-137-generic;
- 8 logical CPUs;
- ~23 GiB RAM;
- no swap;
- ~290 GiB root filesystem;
- UFW active/default deny incoming;
- public OpenSSH TCP/22 only;
- XRDP loopback only;
- fail2ban/sshd active;
- `ubuntu` key-only SSH, sudo with password;
- LXD disabled/inactive;
- provider VNC validated; Rescue available.

This is a historical canonical snapshot, not permission to skip live revalidation before host mutation.

## 2. Host filesystem layout

Target layout after live validation:

```text
/etc/cloud-platform/              root:root, platform configuration generated from desired state
/etc/cloud-platform/policies/     authorization/network policy material
/etc/cloud-platform/env/          references/templates only; no committed real secrets

/opt/cloud-platform/              versioned/runtime-independent platform assets
/opt/cloud-platform/compose/      Compose project definitions
/opt/cloud-platform/bin/          root-owned operational wrappers

/var/lib/cloud-platform/          platform persistent state root
/var/lib/cloud-platform/data/     service-specific protected persistent data
/var/lib/cloud-platform/evidence/ retained operational evidence according to policy
/var/lib/cloud-platform/work/     rebuildable/disposable work area

/var/backups/cloud-infrastructure/ existing sanitized config backup path preserved
```

Exact ownership/service accounts are assigned in the slice that installs each service. No broad shared writable group is created for agents.

## 3. Desired-state repository layout

Planned repository additions:

```text
infra/
  ansible/
    inventory/
    playbooks/
    roles/
  compose/
    platform/
    observability/
    data/
  policy/
  schemas/
  tests/
  evidence/
```

Secrets are referenced by logical names; no real value is committed.

## 4. Foundation technology map

Selected in `docs/40-technology-mapping-foundations-001.md`:

- reconciliation/bootstrap: Ansible;
- runtime: Docker Engine + Docker Compose plugin;
- private management overlay: Tailscale;
- host firewall: retain UFW;
- authorization decision engine: OPA.

Exact package versions will be recorded only after the live package/source precheck and then pinned before apply.

## 5. Network blueprint

### 5.1 Host interfaces

- public provider interface: existing `eth0`;
- private management overlay: future `tailscale0` after enrollment;
- Docker bridges: platform/project/sandbox scoped and not assumed trusted.

### 5.2 Listener policy

Public host listeners allowed in V1 only by explicit capability and review:

- OpenSSH fallback: existing TCP/22 while recovery policy requires it;
- future Agent Gateway: explicit public HTTPS listener;
- future Preview Gateway: explicit public HTTPS listener.

Forbidden by default on public interfaces:

- Docker API/socket;
- databases/cache/object-store admin interfaces;
- workflow administration;
- observability administration;
- secret-store administration;
- Capability Core management endpoints;
- XRDP;
- arbitrary project container ports.

### 5.3 Docker firewall rule

No project/sandbox Compose file may publish a host port directly. Public exposure is owned by gateway stacks only. Effective UFW + nftables/iptables policy is part of the post-Docker security test.

### 5.4 Logical Docker networks

Planned classes:

```text
platform-control      internal control-plane service communication
platform-data         scoped shared Data Service Plane access
platform-observe      telemetry ingestion/collection
project-<id>          persistent DEV project network
sandbox-<id>          disposable mission/job network
edge-preview          only gateway + explicitly exposed service attachment
edge-agent            Agent Gateway boundary
```

Networks are attached only where required; there is no universal workload network.

## 6. Capacity blueprint

Final quotas require live measurement and service benchmarks. Initial policy before core services are installed:

- preserve at least 25% of RAM for OS/control-plane/recovery headroom until measurements justify a different reserve;
- preserve CPU headroom for SSH, monitoring and control-plane operations;
- every sandbox/job receives explicit memory, CPU and PID limits;
- concurrent disposable workloads are admission-controlled;
- persistent storage allocations require quota/criticality metadata;
- disk-pressure thresholds are defined before enabling automated build fan-out.

These are conservative bootstrap policies, not permanent commercial tenant quotas.

## 7. Service deployment classes

### Foundation

- Tailscale client/management overlay;
- Docker Engine/Compose;
- Ansible desired-state/control artifacts;
- base filesystem/ownership;
- host/resource/security prechecks.

### Control Plane

- Capability Core — technology mapping in Platform Core slice;
- OPA — selected policy engine;
- durable Workflow Engine — technology mapping pending;
- durable Event Backbone — technology mapping pending.

### Data Service Plane

Technology mapping pending for:

- PostgreSQL topology/version policy;
- object storage;
- cache/KV;
- workflow/event persistence dependencies.

Logical isolation and scoped credentials are mandatory regardless of implementation.

### Artifact plane

- canonical external/independent OCI registry: provider mapping pending;
- local cache implementation: pending;
- immutable digest/provenance required.

### Edge

- Preview Gateway/DNS/TLS: mapping pending;
- Agent Gateway: mapping pending;
- management endpoints never share the public edge by default.

### Observability

Stack mapping pending, but must cover:

- host/container metrics;
- centralized application/platform logs;
- structured platform events;
- authorization/audit records;
- health/status;
- evidence retention/query.

## 8. Secret lifecycle blueprint

Before a central secret store is deployed:

- existing credentials remain in their current approved locations;
- no migration/rotation is performed;
- new platform services requiring credentials remain blocked or use ephemeral local test credentials generated only at runtime and not committed, when safe and explicitly scoped.

After secret-store selection:

```text
authorized request
 -> Capability Core policy
 -> secret store / credential issuer
 -> runtime-only scoped binding
 -> workload
 -> expiry/revocation when supported
```

## 9. Bootstrap slice gates

### Gate A — live recovery

Required before host changes:

- authenticate to `ubuntu@NODE-01` with existing approved key;
- verify expected host fingerprint;
- collect read-only baseline;
- compare to canonical snapshot;
- record drift.

### Gate B — private management overlay

Before considering Tailscale slice DONE:

- enrollment approved without storing credential in Git;
- device/user policy applied;
- management connectivity validated from approved device;
- existing OpenSSH recovery path remains functional;
- reconnect and reboot behavior validated;
- rollback tested or demonstrated safely.

### Gate C — Docker foundation

Before considering runtime slice DONE:

- pre-install firewall/network/package snapshot stored;
- official packages installed at pinned recorded versions;
- agents/users are not granted Docker group/socket authority;
- no unintended public listener created;
- UFW + effective Docker firewall rules inspected;
- constrained no-public-port test container passes;
- restart/reboot passes;
- Ansible second reconciliation shows no unexpected change.

## 10. Backup/recovery blueprint

Existing sanitized config backup is preserved.

Progressive target:

```text
Git desired state --------------------> rebuild config
OCI canonical registry --------------> rebuild runtime artifacts
CRITICAL/IMPORTANT persistent state -> off-host backup
                                      -> integrity validation
                                      -> isolated restore test
                                      -> evidence
```

No current backup is deleted or replaced until the new path has passed restore testing.

## 11. Evidence convention

Each slice will produce evidence metadata containing at least:

```text
mission
slice
repository_sha
target_node
precheck timestamp
applied desired-state revision
commands/tests performed (sanitized)
PASS/FAIL results
drift/findings
rollback verification
next gate
```

Secrets and sensitive raw authentication data are excluded.

## 12. Current implementation state

- repository mission branch: created;
- foundation technology mapping: created;
- canonical requirements/architecture/threat model/blueprint: created;
- NODE-01 changes: none performed by this mission;
- live host reconciliation: blocked on `HG-EXECUTION-ACCESS-001`.
