# 50 — CONTROL BRIDGE G1 HANDSHAKE CHECKPOINT

Data: 2026-08-18
Status: **PASS — REAL VPS ROUNDTRIP PROVEN**
Missão: `CODEX-EXECUTION-MISSION-001` / G1 MCF VPS Control Bridge
Branch: `mcf/mission-001-control-bridge-g1`
Base deliberada: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED

## Objetivo deste checkpoint

Congelar o primeiro marco operacional comprovado do MCF VPS Control Bridge para que outra sessão, agente ou Codex possa recuperar o estado sem depender do contexto do chat.

## Estado antes do bootstrap

- gate de CI anterior ao bootstrap: verde no HEAD `b40deaabc1b7068fb923ae42e408505d67b5a51a`;
- self-hosted runner: ainda não instalado;
- VPS não havia sido alterada pelo G1;
- primeiro slice autorizado: somente handshake read-only;
- shell arbitrário, root direto, Docker socket, escrita arbitrária, deploy e produção: fora do escopo.

## Bootstrap executado

GitHub Actions self-hosted runner instalado no NODE-01 em 2026-08-18.

Runner observado:

```text
name=node--1-mcf-control
user=ubuntu
service=systemd active/running
GitHub connection=connected
```

Labels efetivas após correção:

```text
self-hosted
Linux
X64
node-01
mcf-control
```

Finding de nomenclatura:

- nome planejado: `node-01-mcf-control`;
- nome registrado: `node--1-mcf-control`;
- impacto operacional observado: nenhum, porque o workflow roteia por labels;
- correção do nome: adiada; não justificar reinstalação apenas por estética.

Finding de label durante bootstrap:

- label inicialmente digitada: `mfc-control`;
- label exigida pelo workflow: `mcf-control`;
- correção: realizada no GitHub antes do handshake comprovado;
- estado final: `mcf-control` atribuída e roteamento funcional.

## Handshake comprovado

Issue sink:

```text
#4 — [VPS-CMD] PROBE — G1 first handshake
```

Dispatches:

```text
VPS-PROBE-20260818-001
VPS-PROBE-20260818-002
```

Resultados automáticos publicados por `github-actions[bot]`:

```text
VPS-PROBE-20260818-001 = PASS @ 2026-08-18T21:09:34Z
VPS-PROBE-20260818-002 = PASS @ 2026-08-18T21:09:49Z
```

A segunda execução confirmou a primeira após a correção das labels.

## Dados lidos diretamente da VPS

```text
hostname=vmi3506102
uid=1000(ubuntu)
kernel=Linux 6.8.0-137-generic x86_64
python=3.12.3
root filesystem=290G total, 15G used, 275G available
memory=23Gi total, ~15Gi available
ssh=active
ufw=active
docker=active
containerd=active
```

Esses dados foram produzidos pelo runner na VPS, publicados automaticamente na Issue #4 e lidos pelo MESTRE pelo GitHub, sem relay manual de stdout por LEANDRO.

## Fronteira privilegiada observada

Probe opcional:

```text
mission001_runner_status
```

Resultado:

```text
exit_code=1
sudo: a password is required
```

Interpretação:

- o GitHub runner não recebeu `NOPASSWD`;
- não há evidência de root direto;
- a fronteira privilegiada continua separada;
- o resultado não invalida o handshake core, que permaneceu `PASS`.

## Critérios comprovados

```text
RUNNER_REGISTERED=YES
RUNNER_SERVICE_ACTIVE=YES
RUNNER_GITHUB_CONNECTED=YES
ROUTING_NODE_01=PASS
ROUTING_MCF_CONTROL=PASS
PROBE_CORE=PASS
RESULT_RETURNED_TO_GITHUB=YES
RESULT_READ_BY_MESTRE=YES
LEANDRO_MANUAL_STDOUT_RELAY=NO
PASSWORDLESS_SUDO=NO
ARBITRARY_WRITE=NO
PR3_MERGED=NO
PRODUCTION_PROMOTION=NO
```

## O que NÃO está comprovado

Este checkpoint não declara:

- shell arbitrário;
- escrita arbitrária;
- acesso privilegiado pelo GitHub runner;
- Docker socket concedido ao runner;
- Capability Core concluído;
- Node Agent concluído;
- MCP concluído;
- F5.0 Runner/build isolation concluído;
- invariância total da VPS além do conjunto observado pelo probe;
- produção autorizada;
- PR #3 pronto para merge.

## CI após os dispatches

Os commits de dispatch moveram o HEAD do PR depois do gate verde usado para liberar o bootstrap. Cada novo HEAD continua sujeito a CI commit-bound.

Não usar o PASS do handshake como substituto de CI do repositório.

## Relação com o checkpoint principal

`CHECKPOINT.md` continua descrevendo a sequência canônica da implementação da VPS e o slice F1.2c. Este documento registra uma capability transversal paralela — o Control Bridge — sem reescrever o próximo passo da Network Enforcement.

Para recuperar G1, ler em conjunto:

1. `docs/49-control-bridge-g1.md`;
2. `runbooks/github-self-hosted-runner-bootstrap.md`;
3. este checkpoint;
4. Issue #4;
5. PR #3;
6. `control/dispatch/probe.json`;
7. `scripts/control_bridge_probe.py`;
8. `scripts/control_bridge_publish.py`.

## Próximo passo G1

```text
G1_HANDSHAKE=PASS
NEXT_G1=DESIGN_AND_VALIDATE_NEXT_BOUNDED_NON_PRIVILEGED_SLICE
```

O próximo slice deve priorizar operações não privilegiadas explícitas em workspaces de projeto, com request schema, resultado estruturado, idempotência quando aplicável, testes unitários e de integração e sem duplicar Capability Core / Node Agent.

## Continuidade reconciliada em 2026-08-20

```text
CONTROL_BRIDGE_G2B=P0_DESIGN_APPROVED_IMPLEMENTATION_PENDING
G1=PASS_REAL_NODE_01_ROUNDTRIP
G2A=PASS_REAL_NODE_01_READ_ONLY
G2B_REAL_WRITE=NOT_EXECUTED
CODEX=AVAILABLE_PARALLEL_EXECUTOR
MESTRE_MCF=ORCHESTRATOR
LEANDRO=FINAL_HUMAN_AUTHORITY
F1_2C_SYSTEMD_RUNTIME_LOCK=FROZEN_FOR_CODEX_OWNED_BY_MESTRE_MCF_AND_LEANDRO
GITHUB_HOSTED_CI=BLOCKED_EXTERNAL_BILLING
SELF_HOSTED_NODE_01_RUNNER=ONLINE_OBSERVED_2026_08_20
```

O status online é da GitHub API, não observação VPS fresca. F1.2c mantém seus
fatos/timestamps e sua branch está congelada para Codex; G2-B é fail-closed em
`state/control-bridge-g2b.yaml`.
