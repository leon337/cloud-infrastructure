# 49 — CONTROL BRIDGE G1

Status: **REPO_ONLY_PREPARED — VPS_NOT_MUTATED**
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
          +-- exec.argv / exec.script não privilegiado
          |
          +-- mission001.runner para operações fixas permitidas
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

Antes do workflow existir na branch padrão, um push controlado em `control/dispatch/request.json` pode disparar o workflow presente na própria branch G1. O request referencia uma Issue de retorno. Isso permite provar o ciclo sem merge prematuro.

### G1-B — Issue command bus

Depois que a ponte estiver validada e o workflow chegar à branch padrão, Issues com título `[VPS-CMD] ...` poderão disparar diretamente a execução. O corpo da Issue conterá o request JSON validado.

## Protocolo de request V1

```json
{
  "protocol": "MCF_CONTROL_BRIDGE_V1",
  "request_id": "CB-000001",
  "issue_number": 123,
  "action": "exec.argv",
  "argv": ["hostname"],
  "cwd": "/home/ubuntu",
  "timeout_seconds": 30
}
```

Ações G1:

- `exec.argv`: executa uma lista argv diretamente, sem shell intermediário, como o usuário do self-hosted runner;
- `exec.script`: executa um script versionado no repositório com argumentos explícitos;
- `mission001.runner`: chama somente operações da fronteira temporária já existente. No G1 inicial, somente `status`, `check` e `test` são liberadas pelo dispatcher; operações mutantes permanecem fora até gate próprio.

## Protocolo de result V1

Todo resultado deve conter pelo menos:

```json
{
  "protocol": "MCF_CONTROL_BRIDGE_RESULT_V1",
  "request_id": "CB-000001",
  "status": "completed",
  "exit_code": 0,
  "started_at": "...",
  "finished_at": "...",
  "stdout": "...",
  "stderr": "..."
}
```

Timeout, validação recusada e falha de execução devem produzir estado explícito em vez de serem convertidos em sucesso.

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
- `exec.argv` não usa `shell=True`, `eval`, `bash -c` ou `sh -c`;
- o runner privilegiado existente continua separado do GitHub runner;
- G1 não declara F5.0, Capability Core, Node Agent ou MCP como DONE.

## Validação antes do bootstrap na VPS

1. testes unitários do protocolo/dispatcher;
2. sintaxe Python e YAML;
3. regressão da suíte `scripts/test.sh`;
4. revisão do workflow para confirmar labels, permissions e timeout;
5. PR draft/checks sem merge;
6. somente depois: HUMAN interaction de registro do self-hosted runner;
7. primeiro handshake deve ser read-only (`hostname`, `id`, `uname`, `status`);
8. somente após handshake PASS liberar operações não privilegiadas de escrita no workspace.

## Relação com o roadmap existente

G1 é uma capability bootstrap de execução, não a conclusão de `F5.0 Runner/build isolation`. O roadmap final continua exigindo runner/builder isolado, Capability Core, Node Agent e adapters MCP/API/CLI. G1 deve ser reaproveitado ou substituído por essas camadas, nunca virar uma arquitetura paralela permanente.

## Estado de saída esperado

```text
G1_REPO_CONTRACT=PASS
G1_UNIT_TESTS=PASS
G1_PR_CHECKS=PASS
G1_SELF_HOSTED_RUNNER=NOT_INSTALLED
G1_VPS_MUTATION=NO
NEXT=G1_BOOTSTRAP_HUMAN_INTERACTION
```
