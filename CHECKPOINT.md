# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-16 após Mission Acceptance, revisão arquitetônica e revisão
de safety do `SLICE-001 — Foundations F1.1`.

## Estado durável

- Repositório canônico: `leon337/cloud-infrastructure`, branch `main`.
- Base recuperada: `987c5359ea948d1903355e98177ae1eb2f1849d5`.
- Branch do slice: `codex/mission-001-foundations-f1-1`.
- F0, F1 e F2 Cloud Workstation: `DONE`.
- Mission Acceptance + Recovery: `DONE`.
- Q1–Q39: requisitos arquitetônicos vinculantes.
- Q40-D: Technology Mapping + implementação incremental DEV/lab autorizados.
- Produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- Rotação: `DEFERRED_BY_HUMAN_DECISION`.
- F1.1: remediação candidata materializada e suíte estática local aprovada no
  worktree; comportamento em VM descartável requer nova validação; VPS real
  **NOT_APPLIED**.

## Artefatos canônicos criados

- `docs/40-mission-acceptance-recovery-report.md`;
- `docs/41-consolidated-requirements.md`;
- `docs/42-target-architecture.md`;
- `docs/43-threat-model-and-autonomy-boundaries.md`;
- `docs/44-infrastructure-blueprint-v1.md`;
- `docs/45-revised-implementation-roadmap.md`;
- `docs/46-technology-mapping-v1.md`;
- `decisions/DEC-005-*`, `decisions/DEC-006-*`;
- `state/components.yaml`;
- `automation/ansible/`, `platform/`, `scripts/`, `tests/`;
- `runbooks/platform-foundation.md`;
- `evidence/SLICE-001/`.

## SLICE-001 — estado de evidência

- Ansible Core 2.21.3 e dependências estão fixados em ambiente local isolado;
- manifests `ExecutionNode`/`Project` validados por JSON Schema 2020-12;
- produção `false`, ingress público arbitrário e secret literal rejeitados;
- secret/path policy passou;
- suíte estática endurecida, testes unitários e syntax-checks Ansible passaram no
  worktree local, ainda sem vínculo a commit; as contagens ficam no test report;
- ShellCheck 0.9 passou nos quatro scripts no worktree local;
- os resultados anteriores da fixture (`changed=7`, depois `changed=0` e cleanup)
  permanecem históricos, não prova atual;
- a revisão encontrou gaps de provenance/TOCTOU no rollback, adoção de objetos,
  check mode e proteção do target; eles foram corrigidos no desired state e
  passaram revisão/suíte estática, mas ainda exigem integração na VM descartável
  antes de qualquer apply/rollback na VPS;
- o preflight sem sudo passou no NODE-01 com `changed=0`, e o inventário de teste
  foi recusado corretamente na Workstation física.

Check mode, primeiro apply, segunda reconciliação e rollback da fixture precisam
de rerun em VM GitHub descartável. O resultado histórico nunca substitui
apply/idempotência/invariância na VPS real.

## Estado real da VPS antes do apply

Snapshot read-only: `2026-08-16T19:46:14Z`.

- Ubuntu 24.04.4, kernel `6.8.0-137-generic`, KVM, 8 CPUs;
- ~23,5 GiB RAM, ~17,2 GiB disponível; sem swap;
- raiz ~289,6 GiB, ~279 GiB disponível;
- cgroup v2, AppArmor ativo, Python 3.12.3;
- zero units falhas;
- público somente SSH TCP 22;
- XRDP `127.0.0.1:3389`, sesman `[::1]:3350`;
- SSH/UFW/fail2ban/XRDP/LightDM ativos;
- `ubuntu` fora de `lxd`; LXD daemon/socket inativos;
- Docker/containerd ausentes;
- conta/grupo/paths/units F1.1 ausentes, sem conflito;
- múltiplas sessões Firefox/VS Code/Codex ativas;
- `sudo -n` negado conforme política.

## Backup/recovery

- timer sanitizado ativo e último resultado de serviço `success`;
- dois archives remotos passaram checksum e leitura do tar;
- primeira cópia off-host observada confere; a mais recente não foi observada
  off-host;
- houve extração histórica, não restore/rebuild funcional;
- archives atuais normalizam modes para `0640` e não são restore drop-in;
- VNC/Rescue/provedor não foram reabertos nesta coleta guest-only;
- `FND-BACKUP-001` permanece `MITIGATED — OPEN`.

## Guardrails do próximo passo

- não executar check mode, apply ou rollback na VPS antes de a VM GitHub
  descartável provar a remediação de safety do F1.1 e existir novo checkpoint;
- quando chegar ao apply, LEANDRO digita sudo diretamente; senha nunca é
  enviada/registrada;
- manter segunda sessão SSH e revalidar concorrência antes do apply;
- usar `runbooks/platform-foundation.md`;
- F1.1 não instala pacote/runtime, não cria listener e não toca
  SSH/UFW/XRDP/Workstation/credenciais;
- abortar diante de objeto preexistente sem marker ou estado concorrente;
- depois do apply exigir segunda execução `changed=0`, negações, modes e
  invariância de listeners/SSH/UFW/fail2ban/XRDP/LXD/units;
- rollback só quando os namespaces persistentes estiverem vazios.

## Próximo passo exato

**SLICE_001_REVALIDATE_IN_DISPOSABLE_GITHUB_VM_AFTER_SAFETY_REMEDIATION**

Somente depois de a nova suíte provar prechecks, idempotência e rollback
fail-closed o próximo checkpoint poderá autorizar check mode/apply interativo. Até
que apply, segunda reconciliação e invariance checks passem na VPS, F1.1 permanece
`PARTIAL/NOT_APPLIED`, nunca `DONE`. Docker F1.2, Management Network, produção e
rotação não fazem parte desse passo.

## Architecture/Technology Mapping — gaps condicionais

- worker não chama Node Agent diretamente; toda capability privilegiada volta ao
  Core e é revalidada localmente;
- PostgreSQL foundation precede Keycloak;
- network/egress/service discovery e quota de disco bloqueiam o primeiro workload;
- dados Critical/Important dependem de backup off-host e restore por classe;
- Loki/Grafana dependem de review AGPL; runner, cache OCI local, audit ledger,
  mensageria Q38, DNS, object storage e Model Gateway final continuam
  `CONDITIONAL`;
- previews DEV no namespace/grant aprovado são autônomos após bootstrap DNS;
- produção continua não autorizada e rotação continua adiada.
