# Runbook — GitHub Self-Hosted Runner Bootstrap para NODE-01

Status: EXECUTED — HANDSHAKE PASS
Missão: CODEX-EXECUTION-MISSION-001 / G1 Control Bridge
Branch: mcf/mission-001-control-bridge-g1
Data de execução: 2026-08-18

## Objetivo

Registrar um GitHub Actions self-hosted runner no NODE-01 apenas para o bootstrap do Control Bridge G1. O runner é o transporte GitHub -> VPS para o primeiro handshake remoto read-only.

Este runbook não autoriza merge, produção, rotação de credenciais, Docker socket, sudo irrestrito ou operações mutantes na VPS.

## Pré-condições usadas

1. PR #3 permaneceu draft.
2. Os workflows de validação do HEAD anterior ao bootstrap estavam verdes.
3. Operador conectado como `ubuntu` no NODE-01.
4. Runner não foi executado como `root`.
5. `ubuntu` não foi adicionado ao grupo `docker` pelo G1.
6. Registration token não foi versionado no repositório.

## Registro executado

No repositório `leon337/cloud-infrastructure` foi usado:

Settings -> Actions -> Runners -> New self-hosted runner

Arquitetura selecionada: Linux / x64.

Diretório usado no NODE-01:

```text
/home/ubuntu/actions-runner
```

O pacote oficial GitHub Actions Runner 2.336.0 foi baixado e o checksum exibido pelo GitHub foi validado antes da extração.

Configuração pretendida:

```text
runner name: node-01-mcf-control
additional labels: node-01,mcf-control
work folder: _work
```

Configuração efetivamente observada no GitHub após o bootstrap:

```text
runner name: node--1-mcf-control
labels: self-hosted, Linux, X64, node-01, mcf-control
work folder: _work
```

O nome contém uma divergência de nomenclatura não bloqueante (`node--1` em vez de `node-01`). O roteamento depende das labels, e `node-01` + `mcf-control` estão corretas.

Durante o bootstrap a label adicional foi inicialmente digitada como `mfc-control`; ela foi corrigida no GitHub para `mcf-control` antes do handshake comprovado.

## Serviço 24/7

O runner foi instalado como serviço systemd usando `svc.sh`, associado ao usuário `ubuntu`.

Evidência visual/terminal observada:

```text
Active: active (running)
Connected to GitHub
```

O GitHub mostrou o runner online antes do primeiro probe.

## Invariantes pós-bootstrap preservados

O bootstrap G1 não foi usado para:

- alterar SSH/UFW/XRDP/fail2ban;
- publicar nova porta TCP/UDP;
- adicionar acesso ao Docker socket;
- adicionar `ubuntu` ao grupo `docker`;
- criar senha/token permanente;
- promover produção;
- executar `apply`, `reconcile` ou `rollback` da Mission 001.

## Primeiro handshake

O primeiro job aceito pelo runner executou somente o probe bounded versionado em `scripts/control_bridge_probe.py`.

Issue de retorno:

```text
#4 — [VPS-CMD] PROBE — G1 first handshake
```

Resultados publicados automaticamente por `github-actions[bot]`:

```text
VPS-PROBE-20260818-001 = PASS @ 2026-08-18T21:09:34Z
VPS-PROBE-20260818-002 = PASS @ 2026-08-18T21:09:49Z
```

O resultado retornou pelo GitHub e foi lido pelo MESTRE sem transporte manual de stdout por LEANDRO.

## Resultado observado

```text
hostname=vmi3506102
identity=ubuntu uid=1000
kernel=6.8.0-137-generic x86_64
python=3.12.3
root_fs=290G total / 15G used / 275G available
memory=23Gi total / ~15Gi available
ssh=active
ufw=active
docker=active
containerd=active
```

A consulta opcional ao `codex-mission-001-runner status` retornou:

```text
exit=1
sudo: a password is required
```

Isso confirma que o GitHub runner não recebeu sudo sem senha. O handshake permaneceu `PASS` porque os probes core retornaram exit code 0.

## Critério de PASS — fechamento

```text
RUNNER_REGISTERED=YES
RUNNER_SERVICE=ACTIVE
RUNNER_GITHUB_CONNECTED=YES
FIRST_JOB_ROUTE=node-01+mcf-control=PASS
PROBE_CORE_EXIT_CODE=0
RESULT_RETURNED_TO_GITHUB=YES
RESULT_READ_BY_MESTRE=YES
LEANDRO_MANUAL_STDOUT_RELAY=NO
PASSWORDLESS_SUDO=NO
ARBITRARY_WRITE=NO
```

`VPS_UNRELATED_SERVICES_CHANGED=NO` não é declarado como prova completa de invariância por este runbook; o probe foi read-only e observou somente o conjunto previsto de serviços/recursos.

## Falha / recuperação futura

Se o runner deixar de registrar ou receber jobs:

1. não ampliar permissões;
2. coletar somente estado do serviço/runner;
3. preservar logs do runner;
4. remover/reconfigurar somente o bootstrap G1 se necessário;
5. não tocar na implementação F1.1/F1.2b/F1.2c para forçar o bridge a funcionar.

## Próxima evolução após PASS

O handshake PASS libera apenas o planejamento/implementação do próximo slice do Control Bridge: operações não privilegiadas explícitas em workspaces de projeto, com testes unitários e de integração e retorno estruturado.

Capability Core, Node Agent, MCP, acesso privilegiado amplo, Docker socket, root direto e shell arbitrário continuam fora do G1 inicial.
