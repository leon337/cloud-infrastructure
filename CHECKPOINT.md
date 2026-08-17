# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-17 após a conclusão real do
`SLICE-002B — Docker runtime boundary`.

## Estado durável

- Repositório canônico: `leon337/cloud-infrastructure`, branch `main`.
- Base recuperada: `987c5359ea948d1903355e98177ae1eb2f1849d5`.
- Branch do slice: `codex/mission-001-foundations-f1-2b-preparation`.
- F0, F1 e F2 Cloud Workstation: `DONE`.
- Mission Acceptance + Recovery: `DONE`.
- Q1–Q39: requisitos arquitetônicos vinculantes.
- Q40-D: Technology Mapping + implementação incremental DEV/lab autorizados.
- Produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- Rotação: `DEFERRED_BY_HUMAN_DECISION`.
- F1.1: commit de implementação
  `edd2497d657cc9bc35952f5dfc71090a18dade53` aprovado no GitHub Actions run
  `31972460567`, inclusive VM descartável privilegiada; slice `DONE`; check
  mode, backup off-host, apply `changed=7`, idempotência
  `changed=0` e invariância real passaram em `2026-08-17`.
- F1.2b: apply/rollback, pin APT, preflight, helper de árvore e harness
  concluídos a partir do desired-state commit `7015c80759a797bcb141773b79cd9b95f6fbecf1`;
  commit testado `fa66f1049bac5540a5b12219186a421cc39dcbc0` e GitHub run
  `31996516019` `PASS`; correções passaram nos runs `32004951916` e
  `32007871491`; preview NODE-01 sem mutação, backup off-host, apply
  `changed=13`, idempotência e pós-restart `changed=0` e invariância `PASS`.

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
- suíte estática endurecida, 37 testes unitários/negativos, três syntax-checks
  Ansible e ShellCheck nos quatro scripts passaram no job `validate` vinculado ao
  commit `edd2497d`;
- os resultados anteriores da fixture (`changed=7`, depois `changed=0` e cleanup)
  permanecem históricos e não são a prova usada para o delta revisado;
- a revisão encontrou gaps de provenance/TOCTOU no rollback, adoção de objetos,
  check mode e proteção do target; eles foram corrigidos no desired state e
  passaram revisão, suíte estática e integração na VM descartável;
- o preflight sem sudo passou no NODE-01 com `changed=0`, e o inventário de teste
  foi recusado corretamente na Workstation física;
- o job `disposable-integration` passou em 1m59: check mode sem mutação real da
  fixture, partial-marker check, primeiro apply `changed=7`, segunda reconciliação
  `changed=0`, postconditions, quatro recusas de rollback fail-closed, rollback
  limpo e cleanup de container/imagem de teste nomeada/bundle;
- o run [`31972460567`](https://github.com/leon337/cloud-infrastructure/actions/runs/31972460567)
  valida o commit `edd2497d`; esta atualização posterior de evidência/state não é
  apresentada como CI do commit final.
- o checkpoint `da7df70` passou novamente no run
  [`31973125852`](https://github.com/leon337/cloud-infrastructure/actions/runs/31973125852):
  job estático em 22 s e integração descartável em 2m25;
- o baseline read-only de `2026-08-16T21:23:21Z` confirmou identidade, mesmo boot,
  zero units falhas, mesmos listeners/serviços, LXD inativo, Docker ausente, zero
  concorrência e todos os objetos/lock F1.1 ausentes, sem sudo ou mutação;
- timer de backup ativo e último serviço `success`; checksum/archive e cópia
  off-host devem ser revalidados antes do apply, não deste preview sem mutação.

A prova na fixture não substituiu a VPS real. Depois dela, check mode, backup,
apply, idempotência, restart e invariância também passaram no NODE-01.

## Baseline real da VPS antes do apply

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
- conta/grupo/paths/units F1.1 aplicados e validados;
- múltiplas sessões Firefox/VS Code/Codex ativas;
- `sudo -n` negado conforme política.

O preview F1.2b revalidou o host sem mutação. Docker/containerd, marker, lock e
listeners 2375/2376 permaneceram ausentes; serviços essenciais ficaram ativos.

## SLICE-002B — estado concluído

- branch recuperado limpo em `d849caa0eafdc231d2782be602be1a2263758b7b`;
- role/playbooks de apply e rollback versionados com target/allowlist imutáveis;
- chave/source/pin/config/drop-ins versionados e verificados por SHA-256;
- install exige versão/path/digest do índice APT autenticado e suprime autostart;
- helper de rollback compara baseline, usa `find -xdev` nos dois roots literais,
  congela device/inode e recusa symlink, hardlink, mount, open path e drift;
- harness GitHub-hosted executou check sem mutação, apply `changed=13`,
  reconciliação/restart `changed=0`, invariância, sete recusas, rollback e cleanup
  no run `31996516019` para o commit `fa66f10`;
- suíte local/CI: 66 unitários/negativos, 34 YAML, dois manifests, seis scripts com
  sintaxe/ShellCheck e seis syntax-checks Ansible, todos `PASS`;
- CI GitHub, lifecycle descartável, check mode, backup, apply, idempotência,
  restart e invariância real estão `PASS`; o runtime está vazio e o primeiro
  workload permanece `BLOCKED` por F1.2c.

## SLICE-002C — contrato repo-only

- contrato machine-readable versionado em
  `platform/network/f1-2c-contract.yaml`, commit
  `b4cbeb066605754d538ff5abe2d294f0759d6f59`;
- preserva Q20/Q34, TM-02/TM-03/TM-10, IPv4/IPv6, deny de
  host/Management/metadata/control/lateral, sharing por grant e egress por
  profile;
- DEC-008 seleciona `DOCKER-USER`, bridges internas, DNS por escopo e egress
  proxy-only; compilador fail-closed passou localmente apenas com input de
  exemplo, enquanto apply e prova descartável continuam pendentes;
- quatro testes específicos e suíte integrada de 60 testes/34 YAML passaram;
- não há ruleset executável, harness dinâmico, network namespace, probe ou
  mutação real; implementação/integração permanecem `PENDING` e NODE-01
  `NOT_EXECUTED`;
- evidência sanitizada: `evidence/SLICE-002C/`.

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

- F1.1 real está concluído com apply, idempotência e invariância comprovados;
- LEANDRO digita sudo diretamente nas operações humanas; senha nunca é
  enviada/registrada;
- manter segunda sessão SSH e revalidar concorrência antes de futuras mutações;
- usar `runbooks/platform-foundation.md`;
- F1.1 não instala pacote/runtime, não cria listener e não toca
  SSH/UFW/XRDP/Workstation/credenciais;
- abortar diante de objeto preexistente sem marker ou estado concorrente;
- depois do apply exigir segunda execução `changed=0`, negações, modes e
  invariância de listeners/SSH/UFW/fail2ban/XRDP/LXD/units;
- rollback só quando os namespaces persistentes estiverem vazios.
- F1.2b está concluído; não repetir o apply fora de reconciliação controlada e
  nenhum workload é permitido antes de F1.2c.
- F1.2c repo-only não autoriza workload: ADR, implementation e matriz dinâmica
  completa em IPv4/IPv6 continuam bloqueantes.

## Próximo passo exato

**SLICE_002C_IMPLEMENTATION_AND_DISPOSABLE_NETWORK_ENFORCEMENT**

Implementar a DEC-008 e provar a matriz dinâmica IPv4/IPv6 em ambiente
descartável. Não aplicar no
NODE-01 nem iniciar container/workload antes dessa prova. Management Network,
produção e rotação permanecem fora desse passo.

## Architecture/Technology Mapping — gaps condicionais

- worker não chama Node Agent diretamente; toda capability privilegiada volta ao
  Core e é revalidada localmente;
- PostgreSQL foundation precede Keycloak;
- o contrato de network/egress/service discovery existe, mas ADR/prova dinâmica
  e quota de disco ainda bloqueiam o primeiro workload;
- dados Critical/Important dependem de backup off-host e restore por classe;
- Loki/Grafana dependem de review AGPL; runner, cache OCI local, audit ledger,
  mensageria Q38, DNS, object storage e Model Gateway final continuam
  `CONDITIONAL`;
- previews DEV no namespace/grant aprovado são autônomos após bootstrap DNS;
- produção continua não autorizada e rotação continua adiada.
