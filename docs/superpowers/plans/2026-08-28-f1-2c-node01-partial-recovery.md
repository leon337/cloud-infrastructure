# F1.2c NODE-01 Partial Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a fail-closed recovery path for the exact partial F1.2c network-services state observed on NODE-01, validate it in disposable KVM, and stop before live privileged mutation.

**Architecture:** Preserve the existing KVM-validated normal `apply` and `rollback` entrypoints unchanged. Add a dedicated partial-recovery operation that recognizes only the known old helper/unit hashes, existing service marker, absent service configuration tree, zero managed runtime state, healthy base enforcement, and exact source artifacts. It checkpoints the old installed surfaces before replacement; a successful recovery can be rolled back to a bounded safe partial baseline, while unclassified mid-apply failures preserve evidence instead of attempting broad cleanup.

**Tech Stack:** Bash, systemd, Docker/Compose, iptables/ip6tables, Python unittest contracts, QEMU/KVM Ubuntu 24.04 disposable guest.

**Spec:** `history/F1-2C-NETWORK-RECOVERY-2026-08-22.md` plus fresh 2026-08-28 NODE-01 read-only evidence.

## Global Constraints

- Exact validated parent lineage: `80a1579bf6525029be8085fa1d1cbdec602ddfbd`.
- Never run privileged recovery on `vmi3506102` without an explicit LEANDRO HUMAN_GATE.
- Do not weaken `ProtectSystem=strict`, firewall policy, project isolation, proxy/DNS policy, SSH, UFW, Docker socket mode, or sudo boundaries.
- Preserve `cloud-platform-network-enforcement` and previous mission layers.
- Normal `automation/mission-001/operations/apply` and `rollback` remain unchanged.
- Any unexpected hash, marker, Docker object, managed link, route collision, service state, or source drift aborts before mutation.
- Mid-apply state that is not provably healthy must not trigger destructive best-effort cleanup.

---

### Task 1: Contract for exact partial-state recovery

**Files:**
- Create: `tests/test_f1_2c_partial_recovery_contract.py`
- Create: `automation/mission-001/operations/recover-network-services-partial`

**Interfaces:**
- Consumes: exact old and candidate SHA-256 inventories plus NODE-01/KVM identity.
- Produces: operations `precheck`, `apply`, `check`, `rollback` and explicit PASS/REFUSED markers.

- [ ] Write tests requiring exact old/candidate hashes, host identity, source validation, zero-runtime guards, checkpointing, and no automatic destructive cleanup on unclassified apply failure.
- [ ] Run the focused test and verify RED because the recovery entrypoint does not exist.
- [ ] Implement the minimal fail-closed entrypoint.
- [ ] Run focused tests and verify GREEN.

### Task 2: Disposable partial-state lifecycle harness

**Files:**
- Create: `scripts/test_node_network_services_partial_recovery_vm.sh`
- Modify: `scripts/run_f1_2c_kvm_lab.sh`

**Interfaces:**
- Consumes: the new recovery operation and historical old surfaces reachable at commit `c9f909945b544d22dbabc619252456f7190f7ae9`.
- Produces: `NODE_NETWORK_SERVICES_PARTIAL_RECOVERY_VM_PASS` after exact old failure → recovery → check → rollback.

- [ ] Add a contract test requiring the KVM runner to execute the partial-recovery harness.
- [ ] Verify RED before wiring the harness.
- [ ] Build the exact historical partial state in the disposable guest using old helper/unit blobs, marker present, configs absent and no managed Docker/network objects.
- [ ] Prove the old unit fails with the historical read-only lock error.
- [ ] Run recovery `precheck`, `apply`, `check`, idempotent `apply`, then `rollback` and verify bounded restoration.
- [ ] Wire the harness after the existing full lifecycle test.

### Task 3: Operational runbook and evidence boundary

**Files:**
- Modify: `runbooks/network-services-node-01.md`
- Create: `history/F1-2C-NODE01-PARTIAL-RECOVERY-PREP-2026-08-28.md`

**Interfaces:**
- Produces: exact pre-gate procedure, source staging requirements, checkpoint/rollback semantics, and explicit stop before live apply.

- [ ] Document fresh live state and candidate lineage.
- [ ] Document root-owned exact candidate staging and `precheck` before any apply.
- [ ] Document that an unclassified apply failure is a HUMAN recovery gate, not an automatic cleanup trigger.
- [ ] Record the live mutation as NOT AUTHORIZED until LEANDRO approves the gate.

### Task 4: Verification and publication

**Files:**
- All files changed above.

**Interfaces:**
- Produces: exact candidate SHA plus local/full/KVM evidence suitable for the HUMAN_GATE.

- [ ] Run focused contracts.
- [ ] Run the full 142+ unittest suite with locked dependencies.
- [ ] Run shell syntax and ShellCheck when available.
- [ ] Run `scripts/run_f1_2c_kvm_lab.sh <exact-head>` on the laptop KVM boundary.
- [ ] Confirm KVM evidence includes both normal lifecycle PASS and partial-recovery PASS, rollback and cleanup.
- [ ] Commit/push the candidate and attach GitHub-hosted/static CI evidence where applicable.
- [ ] Stop at `F1_2C_NODE01_ROLLOUT_HUMAN_GATE`; do not mutate NODE-01.
