# RUNNER-ISOLATION-P1 — evidência sanitizada

Data: 2026-08-28

## Escopo

Eliminar o PoC persistente `mcf-mission2-terminal.py`, preservar sua provenance e impedir que workflows canônicos voltem a desabilitar o cleanup do GitHub Actions runner.

## Evidência pré-limpeza

- host: `vmi3506102`;
- runner: `actions.runner.leon337-cloud-infrastructure.node--1-mcf-control.service`;
- runner version observada: `2.336.0`;
- job activity no instante da coleta: `Runner.Listener` ativo; nenhum `Runner.Worker` observado;
- processo legado: PID `783478`, usuário `ubuntu`, PPID `1`, iniciado em 2026-08-22 10:31:36 -03;
- cgroup: `/system.slice/actions.runner.leon337-cloud-infrastructure.node--1-mcf-control.service`;
- socket: `/run/user/1000/mcf-mission2-terminal.sock`, modo `0600`, owner `ubuntu:ubuntu`;
- source: `/home/ubuntu/.local/bin/mcf-mission2-terminal.py`, modo `0700`;
- SHA-256 do source live: `055157d22bfcd1aafe84be0e9403a5267cffe8f1cd2551422b8fe34f24c0359d`;
- checkout VPS no instante da coleta: `codex/control-bridge-g2b@fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`, clean.

## Provenance GitHub

- workflow: `.github/workflows/control-bridge-g1.yml`;
- branch: `mcf/mission-001-control-bridge-g1`;
- workflow SHA: `025a3f784e4f984e10c9cbf087682c43304394d8`;
- run que materializou a persistência: `32576011235`;
- worker log local correspondente: `Worker_20260822-133132-utc.log`.

O workflow histórico executou explicitamente `unset RUNNER_TRACKING_ID` e iniciou o terminal com `nohup setsid`. O processo live preservado não continha `RUNNER_TRACKING_ID` entre os nomes de variáveis de ambiente observados. A branch atual `mcf/mission-001-control-bridge-g1` já não contém o passo persistente.

## Boundary do serviço

A unit do runner observada usa `KillMode=process`. Essa configuração não é alterada por esta missão. A prevenção implementada nesta frente usa: (1) policy check versionado contra manipulação de `RUNNER_TRACKING_ID`; e (2) guard de pre/post-job para o artefato legado, preparado para os hooks oficiais do runner.

## Classificação

- causa raiz: **CONFIRMADA** — exclusão explícita do tracking de processo do runner no PoC histórico;
- exposição de rede do socket: **não observada** — Unix socket local;
- vazamento de segredo: **NÃO PROVADO**; valores de ambiente não foram coletados nesta missão;
- comprometimento externo: **NÃO PROVADO**;
- risco: isolamento cross-job violado pelo PoC, exigindo retirada e prevenção.

## Pós-limpeza

- precheck confirmou PID `783478`, owner `ubuntu` e SHA-256 esperado antes do sinal;
- processo terminou com `SIGTERM`; não houve escalonamento para `SIGKILL`;
- processo `mcf-mission2-terminal.py`: ausente;
- socket: ausente;
- PID file: ausente;
- source executável live: removido;
- `Runner.Listener`: permaneceu ativo;
- checkout VPS permaneceu clean no mesmo SHA;
- legacy user unit: ausente;
- marcador live: `RUNNER_ISOLATION_LIVE_CLEANUP=PASS`.

## Recovery regression

O allowlist RECOVERY-P2 foi alterado para não preservar automaticamente `mcf-mission2-terminal.py` caso reapareça. Execução real do candidato em 28/08 produziu:

- `RESTORE_SMOKE=PASS`;
- `RECOVERY_P2=PASS`;
- `SHA256SUMS`: 6/6 PASS quando validado no diretório correto;
- runtime overlay: 11 membros;
- legacy terminal no overlay: `False`;
- temp residue: `0`.

## Hook host-level

O guard foi instalado em `/home/ubuntu/.local/libexec/cloud-infrastructure-runner-isolation-guard` e executado manualmente com PASS. `~/actions-runner/.env` foi configurado com `ACTIONS_RUNNER_HOOK_JOB_STARTED` e `ACTIONS_RUNNER_HOOK_JOB_COMPLETED`.

A ativação global está **BLOCKED_PRIVILEGE** até um restart autorizado do runner: `systemctl --no-ask-password restart ...` retornou `Interactive authentication required`; o serviço permaneceu `active`. Nenhum bypass de sudo/systemd foi tentado. Até a ativação global, workflows self-hosted canônicos executam o guard explicitamente e o CI proíbe workflows self-hosted sem o guard.

## Prova cross-job real

No candidato funcional `cf96f258f517ea1e520f989ca321e7c24e4aaf24`, três gates independentes passaram:

- `canonical-validation` run `33170001586`: SUCCESS;
- `canonical-validation-maintenance-proof` run `33170001656`: SUCCESS no NODE-01;
- `runner-isolation-proof` run `33170001699`: SUCCESS.

A prova cross-job executou dois jobs sequenciais no mesmo runner `node--1-mcf-control`. O job `seed` lançou um processo benigno desacoplado com `nohup + setsid`, sem remover o tracking do runner. O job `verify` confirmou `RUNNER_ISOLATION_CROSS_JOB=PASS`, seguido de `RUNNER_ISOLATION_GUARD_PASS`.

Classificação operacional: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING`. O hook global permanece `CONFIGURED_NOT_ACTIVE_BLOCKED_PRIVILEGE` até restart autorizado do serviço.
