# Evidence Inheritance for Non-Executable Delta — Design

Status: APPROVED_FOR_IMPLEMENTATION
Date: 2026-08-19
Scope: F1.2c validation policy only
Authority: LEANDRO approved the written specification in project conversation on 2026-08-19

## Goal

Allow a candidate HEAD to reuse previously successful disposable/integration evidence only when the delta from the fully tested anchor commit is proven not to alter executable behavior, operational desired state, security guards, test semantics, dependency resolution or privileged execution semantics.

This policy exists to keep evidence-before-DONE meaningful when GitHub-hosted runners are unavailable for billing/quota reasons. It does not downgrade tests and does not authorize NODE-01 mutation by itself.

## Safety model

Analogy: a vehicle that already passed a destructive crash test does not need another crash test because the owner corrected the manual, but it does need a new crash test if anyone changes the chassis, brakes, airbag controller, test procedure or safety switches.

Therefore inheritance is deny-by-default. A changed file or changed state field is considered material unless an explicit rule proves otherwise.

## Evidence anchor

For the current F1.2c lineage, the initial disposable/integration anchor is:

- commit: `f771cfd09f1824562ddfdaea507fb3cb0781f6ac`;
- hosted lifecycle evidence: run `32131461110` and the companion foundation run recorded by the checkpoint;
- covered behavior: repository validation, Docker/runtime/network-policy lifecycle, NODE-01 network-services desired-state lifecycle, apply/idempotence, DNS/proxy behavior, direct-egress denial, restart and bounded rollback.

The anchor may be replaced later only by a newer commit that itself has full required evidence.

## Classification rules

### Always material — inheritance refused

Any change under these categories requires fresh full integration/disposable evidence:

- `.github/workflows/**` or other CI execution definitions;
- `automation/**`;
- `scripts/**`;
- `tests/**`;
- `platform/**`;
- `config/**` when consumed by runtime/automation;
- dependency locks/manifests such as `requirements*.lock`, package manifests or image/digest inventories;
- Dockerfiles, Compose files, systemd units, tmpfiles, firewall/network policy, schema or manifest definitions used by execution;
- operational runbooks or generated artifacts that are directly consumed by an executor;
- any file newly made executable or any symlink/path-type change on a managed surface;
- any unknown path not explicitly classified as non-material.

### Documentation/evidence candidates — inheritance may be allowed

Changes limited to human-facing documentation, historical session records and sanitized evidence can be non-material only if fresh static validation passes and no executable/operational references are modified indirectly.

Typical candidates include:

- `history/**`;
- narrative sections of `docs/**`;
- sanitized evidence records under `evidence/**`;
- `CHECKPOINT.md`, `CONTEXT.md`, and `README.md` when they only describe already-proven facts and remain consistent with canonical state.

These paths are candidates, not blanket exemptions.

### State files are policy-sensitive, not automatically safe

`state/**` is never accepted merely because it is YAML. Some state fields are read by operational guard code.

In particular, `state/current.yaml` participates in the temporary privileged runner's safety checks. Inheritance is refused if protected safety semantics change, including at minimum:

- `platform_discovery.production_promotion_authorized` must remain `false`;
- `authorization.production_promotion` must remain `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`;
- credential rotation must remain `DEFERRED_BY_HUMAN_DECISION` wherever required by the runner/mission contract;
- branch/mission identity and any field consumed by privileged guard logic must preserve the tested safety meaning.

A state change may inherit evidence only when a semantic comparison proves that all changed fields are observational/progress metadata and all protected operational values remain unchanged.

## Required gate for inheritance

Evidence inheritance is valid only when all of the following are true:

1. The anchor commit is an ancestor of the candidate HEAD.
2. The anchor has recorded full disposable/integration evidence for the behavior being inherited.
3. A machine-readable delta classifier returns no material executable/operational change.
4. Protected state/security guard values are semantically unchanged.
5. Fresh static validation runs on the candidate HEAD and passes.
6. Secret policy, YAML/manifest validation, state cross-checks, unit tests, shell syntax and ShellCheck applicable to the current repository all pass.
7. The candidate checkout remains unprivileged: no passwordless sudo and no Docker socket access are granted to the CI runner.
8. The inheritance decision records anchor SHA, candidate SHA, changed paths, classification result and fresh static-CI evidence.
9. Any ambiguity causes `REFUSED` and requires fresh full integration evidence.

## Current F1.2c application

The F1.2c lineage from `f771cfd09f1824562ddfdaea507fb3cb0781f6ac` through the pre-policy checkpoint `0fb5214ff8e823c971160eccd436893b5bed7330` contains documentation, evidence, history and state-projection updates; no `automation/**`, `scripts/**`, `tests/**`, `platform/**`, workflow or dependency file changed in that delta.

The policy/spec commits themselves are documentation changes and must also be included in the eventual candidate comparison before inheritance is accepted.

Because state files changed, implementation must not rely on path names alone. It must prove that the changed state fields are evidence/progress projections and that production/credential/mission safety guards retain their tested values.

Fresh self-hosted static validation on NODE-01 has already demonstrated that the unprivileged validation path is viable without granting sudo or Docker access. That evidence supports the design but does not itself implement this policy.

## Failure behavior

The classifier is fail-closed:

- unknown path -> `REFUSED_UNKNOWN_PATH`;
- executable or operational file changed -> `REFUSED_MATERIAL_DELTA`;
- protected state field changed -> `REFUSED_PROTECTED_STATE_CHANGE`;
- static CI missing/failing -> `REFUSED_STATIC_EVIDENCE_MISSING`;
- anchor not ancestor or evidence missing -> `REFUSED_INVALID_ANCHOR`.

No refusal may be overridden automatically.

## Non-goals

This design does not:

- make fresh full disposable integration optional for future material implementation changes; the execution venue may be GitHub-hosted or a future isolated self-hosted environment, but the isolation/evidence requirement remains;
- authorize destructive tests on NODE-01;
- grant Docker socket, root, unrestricted sudo or arbitrary shell;
- authorize production;
- authorize credential rotation;
- alter F1.2a/F1.5/F1.6/F5.4 HUMAN_GATEs;
- replace future F5.0 isolated runner/build architecture.

## Implementation outline

Implementation should add a small deterministic classifier plus tests, then wire the result into the F1.2c checkpoint/evidence flow. The classifier should compare an explicit anchor SHA to an explicit candidate SHA, classify changed paths, semantically inspect protected state, and emit a machine-readable PASS/REFUSED record suitable for evidence storage.

The implementation must be developed test-first and must not mutate NODE-01 while being built or validated.

## Acceptance criteria

The policy is complete when:

- material changes are demonstrably refused;
- harmless documentation/history changes are accepted only with fresh static validation;
- protected state changes are refused;
- the real `f771cfd...` -> current F1.2c candidate delta is evaluated with recorded evidence;
- checkpoint/state language distinguishes inherited integration evidence from fresh static evidence;
- no claim says the current HEAD itself ran destructive integration tests when it did not.
