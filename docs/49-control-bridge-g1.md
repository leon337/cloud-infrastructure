# 49 — CONTROL BRIDGE G1

Status: **HANDSHAKE_PASS — RUNNER_ACTIVE — PR_DRAFT**
Data: 2026-08-18
Missão: `CODEX-EXECUTION-MISSION-001` / continuidade MCF
Branch: `mcf/mission-001-control-bridge-g1`
Base: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED

## Objetivo

Criar a ponte mínima para que ChatGPT/agentes possam solicitar execução na VPS por GitHub sem depender de LEANDRO como transportador manual de comandos, preservando o trabalho já implementado na Mission 001.

G1 não substitui o Capability Core, Node Agent, F5.0 runner isolation ou MCP final. Ele é o bootstrap operacional que permite construir e validar essas camadas com acesso remoto observável.

## Descobertas reconciliadas

A branch F1.2c já contém Foundations, Docker boundary, Network Enforcement, manifests, Ansible, testes e um runner privilegiado temporário da Mission 001. Esse runner permanece a fronteira temporária para as seis operações fixas `check`, `apply`, `test`, `reconcile`, `rollback` e `status`; ele não aceita shell arbitrário.

O GitHub self-hosted runner tem papel diferente: é o transporte de jobs GitHub para o usuário Linux `ubuntu`. Ele não recebeu acesso direto ao Docker socket, root direto ou sudo sem senha.

## Arquitetura G1 comprovada

```text
ChatGPT / GitHub connector
          |
          v
cloud-infrastructure
          |
          +-- push controlado em control/dispatch/probe.json
          |
          v
GitHub Actions
          |
          v
self-hosted runner NODE-01
ubuntu / no Docker socket / no passwordless sudo
          |
          v
probe bounded
          |
          v
resultado estruturado
          |
          v
GitHub Issue #4
          |
          v
ChatGPT
```

## Bootstrap em duas fases

### G1-A — push bootstrap — COMPROVADO

Antes do workflow existir na branch padrão, um push controlado em `control/dispatch/probe.json` dispara o workflow presente na própria branch G1. O request referencia uma Issue de retorno.

O mecanismo foi comprovado em ambiente real em 2026-08-18.

### G1-B — Issue command bus — AINDA NÃO ATIVADO COMO TRIGGER

Depois que a ponte estiver validada e o workflow chegar à branch padrão, Issues com título `[VPS-CMD] PROBE ...` poderão disparar diretamente a mesma prova. O corpo da Issue conterá o request JSON validado.

No G1 atual, a Issue #4 é o sink de resultado; o trigger ativo continua sendo `push` controlado.

## Protocolo de probe V1

```json
{
  "protocol": "MCF_CONTROL_BRIDGE_PROBE_V1",
  "request_id": "CB-PROBE-000001",
  "issue_number": 123
}
```

O primeiro slice executa somente probes fixos e não fornecidos pelo chamador: hostname, identidade do runner, kernel, Python, disco, memória e estado de serviços essenciais. Se o `codex-mission-001-runner` já existir, o probe tenta somente sua operação `status`.

O executor genérico de escrita continua sendo objetivo posterior do Control Plane; ele não será declarado implementado até existir um mecanismo aceito, testado e auditável.

## Protocolo de result V1

Todo resultado contém:

```json
{
  "protocol": "MCF_CONTROL_BRIDGE_PROBE_RESULT_V1",
  "request_id": "CB-PROBE-000001",
  "issue_number": 123,
  "status": "PASS",
  "generated_at": "...",
  "probes": []
}
```

Cada probe preserva `argv`, `exit_code`, `stdout`, `stderr`, `started_at` e `finished_at`. Erro ou timeout não pode ser convertido em sucesso.

## Runner real

Runner registrado no repositório em 2026-08-18 como serviço systemd associado ao usuário `ubuntu`.

Nome observado no GitHub:

```text
node--1-mcf-control
```

O nome contém uma divergência de nomenclatura em relação ao nome planejado `node-01-mcf-control`, mas não participa do roteamento do job e não bloqueou o handshake.

Labels efetivas após correção:

```text
self-hosted
Linux
X64
node-01
mcf-control
```

O job G1 exige cumulativamente `self-hosted`, `linux`, `x64`, `node-01` e `mcf-control`.

## Evidência real do handshake

Issue de retorno:

- `#4` — `[VPS-CMD] PROBE — G1 first handshake`

Resultados automáticos publicados por `github-actions[bot]`:

1. `VPS-PROBE-20260818-001` — `PASS` — `2026-08-18T21:09:34Z`;
2. `VPS-PROBE-20260818-002` — `PASS` — `2026-08-18T21:09:49Z`.

Ambos retornaram sem relay manual de stdout por LEANDRO.

Observações retornadas pelo probe:

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

A tentativa read-only de consultar `codex-mission-001-runner status` retornou `exit 1` com `sudo: a password is required`. Isso confirma que o GitHub runner não recebeu sudo sem senha. Esse resultado não invalida o handshake porque o critério core de PASS considera os seis probes base, todos com `exit_code=0`.

## Invariantes G1 preservados

- nenhuma promoção para produção;
- nenhuma rotação de credencial;
- nenhuma senha/chave/token persistida no Git ou resultado;
- nenhuma concessão de Docker socket ao runner;
- nenhuma alteração do SSH/UFW/XRDP pelo probe;
- probe usa argv fixos e `shell=False`;
- o runner privilegiado existente continua separado do GitHub runner;
- G1 não declara escrita arbitrária, F5.0, Capability Core, Node Agent ou MCP como DONE;
- PR #3 continua draft e não foi mergeado.

## Critério de PASS observado

```text
RUNNER_REGISTERED=YES
RUNNER_SERVICE_ACTIVE=YES
RUNNER_GITHUB_CONNECTED=YES
FIRST_JOB_ROUTE=node-01+mcf-control=PASS
PROBE_CORE_EXIT_CODES=0
RESULT_RETURNED_TO_GITHUB=YES
RESULT_READ_BY_MESTRE=YES
LEANDRO_MANUAL_STDOUT_RELAY=NO
PASSWORDLESS_SUDO=NO
ROOT_ACCESS=NO
ARBITRARY_WRITE=NO
```

`VPS_UNRELATED_SERVICES_CHANGED=NO` não é declarado como prova completa de invariância pelo handshake; o probe apenas observou os serviços consultados e não executou comandos mutantes.

## Validação e CI

O gate anterior ao bootstrap estava verde no HEAD `b40deaabc1b7068fb923ae42e408505d67b5a51a`.

Os commits de dispatch posteriores moveram o HEAD do PR. Portanto, cada HEAD posterior continua sujeito à CI commit-bound antes de qualquer avanço estrutural ou merge.

## Relação com o roadmap existente

G1 é uma capability bootstrap de execução, não a conclusão de `F5.0 Runner/build isolation`. O roadmap final continua exigindo runner/builder isolado, Capability Core, Node Agent e adapters MCP/API/CLI. G1 deve ser reaproveitado ou substituído por essas camadas, nunca virar uma arquitetura paralela permanente.

## Estado atual

```text
G1_BRANCH=ACTIVE
G1_REPO_CONTRACT=IMPLEMENTED
G1_BOUNDED_PROBE=IMPLEMENTED
G1_WORKFLOW=IMPLEMENTED
G1_SELF_HOSTED_RUNNER=REGISTERED_AND_SERVICE_ACTIVE
G1_ROUTING_LABELS=CORRECTED
G1_FIRST_HANDSHAKE=PASS
G1_SECOND_HANDSHAKE=PASS
G1_RESULT_SINK=ISSUE_4
G1_MANUAL_STDOUT_RELAY=NO
G1_PRIVILEGED_EXECUTION=NOT_GRANTED
G1_ARBITRARY_WRITE=NOT_IMPLEMENTED
G1_MCP=NOT_IMPLEMENTED
G1_PR3=OPEN_DRAFT_NOT_MERGED
NEXT=FREEZE_HANDSHAKE_EVIDENCE_AND_DESIGN_NEXT_BOUNDED_SLICE
```
