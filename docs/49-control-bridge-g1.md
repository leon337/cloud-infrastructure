# 49 — CONTROL BRIDGE G1

Status: **REPO_ONLY_IMPLEMENTING — VPS_NOT_MUTATED**
Data: 2026-08-18
Missão: `CODEX-EXECUTION-MISSION-001` / continuidade MCF
Branch: `mcf/mission-001-control-bridge-g1`
Base: `codex/mission-001-f1-2c-network-enforcement`

## Objetivo

Criar a ponte mínima para que ChatGPT/agentes possam solicitar execução na VPS por GitHub sem depender de LEANDRO como transportador manual de comandos, preservando o trabalho já implementado na Mission 001.

G1 não substitui o Capability Core, Node Agent, F5.0 runner isolation ou MCP final. Ele é o bootstrap operacional que permite construir e validar essas camadas com acesso remoto observável.

## Descobertas reconciliadas

A branch F1.2c já contém Foundations, Docker boundary, Network Enforcement, manifests, Ansible, testes e um runner privilegiado temporário da Mission 001. Esse runner permanece a fronteira temporária para as seis operações fixas `check`, `apply`, `test`, `reconcile`, `rollback` e `status`; ele não aceita shell arbitrário.

O novo GitHub self-hosted runner terá papel diferente: será o transporte de jobs GitHub para o usuário Linux `ubuntu`. Ele não deve receber acesso direto ao Docker socket nem substituir o futuro Node Agent.

## Arquitetura G1

```text
ChatGPT / GitHub connector
          |
          v
cloud-infrastructure
          |
          +-- bootstrap: push controlado
          |
          +-- estado estável: Issue command bus
          |
          v
GitHub Actions
          |
          v
self-hosted runner NODE-01
ubuntu / no Docker socket
          |
          v
probe bounded / adapters futuros
          |
          v
resultado estruturado
          |
          v
GitHub Issue + workflow logs
          |
          v
ChatGPT
```

## Bootstrap em duas fases

### G1-A — push bootstrap

Antes do workflow existir na branch padrão, um push controlado em `control/dispatch/probe.json` pode disparar o workflow presente na própria branch G1. O request referencia uma Issue de retorno. Isso permite provar o ciclo sem merge prematuro.

### G1-B — Issue command bus

Depois que a ponte estiver validada e o workflow chegar à branch padrão, Issues com título `[VPS-CMD] PROBE ...` poderão disparar diretamente a mesma prova. O corpo da Issue conterá o request JSON validado.

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

## Labels do runner

O job G1 exige cumulativamente:

```text
self-hosted
linux
x64
node-01
mcf-control
```

## Invariantes G1

- nenhuma mudança de produção;
- nenhuma rotação de credencial;
- nenhuma senha/chave/token persistida no Git ou resultado;
- nenhuma concessão de Docker socket ao runner;
- nenhuma alteração do SSH/UFW/XRDP pelo bootstrap G1;
- probe usa argv fixos e `shell=False`;
- o runner privilegiado existente continua separado do GitHub runner;
- G1 não declara escrita arbitrária, F5.0, Capability Core, Node Agent ou MCP como DONE.

## Validação antes do bootstrap na VPS

1. testes unitários do protocolo/probe;
2. sintaxe Python e YAML;
3. regressão da suíte `scripts/test.sh`;
4. revisão do workflow para confirmar labels, permissions e timeout;
5. PR draft/checks sem merge;
6. somente depois: interação humana de registro do self-hosted runner;
7. primeiro handshake deve ser somente leitura;
8. depois do handshake PASS, desenhar o próximo slice de capacidades de leitura/escrita sem duplicar o futuro Capability Core/Node Agent.

## Relação com o roadmap existente

G1 é uma capability bootstrap de execução, não a conclusão de `F5.0 Runner/build isolation`. O roadmap final continua exigindo runner/builder isolado, Capability Core, Node Agent e adapters MCP/API/CLI. G1 deve ser reaproveitado ou substituído por essas camadas, nunca virar uma arquitetura paralela permanente.

## Estado atual

```text
G1_BRANCH=CREATED
G1_REPO_CONTRACT=IMPLEMENTING
G1_BOUNDED_PROBE=IMPLEMENTED_REPO_ONLY
G1_WORKFLOW=IMPLEMENTED_REPO_ONLY
G1_UNIT_TESTS=NOT_YET_VERIFIED_BY_CI
G1_PR_CHECKS=NOT_YET_RUN
G1_SELF_HOSTED_RUNNER=NOT_INSTALLED
G1_VPS_MUTATION=NO
NEXT=OPEN_DRAFT_PR_AND_RUN_REPOSITORY_VALIDATION
```
