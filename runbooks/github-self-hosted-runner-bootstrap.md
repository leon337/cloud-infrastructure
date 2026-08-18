# Runbook — GitHub Self-Hosted Runner Bootstrap para NODE-01

Status: PREPARED — NOT EXECUTED
Missão: CODEX-EXECUTION-MISSION-001 / G1 Control Bridge
Branch: mcf/mission-001-control-bridge-g1

## Objetivo

Registrar um GitHub Actions self-hosted runner no NODE-01 apenas para o bootstrap do Control Bridge G1. O runner será o transporte GitHub -> VPS para o primeiro handshake remoto read-only.

Este runbook não autoriza merge, produção, rotação de credenciais, Docker socket, sudo irrestrito ou operações mutantes na VPS.

## Pré-condições obrigatórias

1. PR #3 continua draft.
2. Os workflows de validação do HEAD G1 devem estar verdes antes da instalação.
3. Operador conectado como `ubuntu` no NODE-01.
4. Não usar `root` para executar o runner.
5. Não adicionar `ubuntu` ao grupo `docker` por causa do G1.
6. Não persistir registration token, PAT, senha ou chave no repositório, terminal history deliberado, Issue ou documentação.

## Registro no GitHub

No repositório `leon337/cloud-infrastructure`, abrir:

Settings -> Actions -> Runners -> New self-hosted runner

Selecionar Linux / x64 e usar os comandos que o próprio GitHub gerar naquele momento. Não copiar comandos versionados deste runbook porque versão do runner e registration token são temporários.

Diretório recomendado no NODE-01 para este bootstrap:

```text
/home/ubuntu/actions-runner-mcf-control
```

Executar download, verificação de hash e `config.sh` exatamente conforme a página do GitHub.

Ao configurar o runner:

```text
runner name: node-01-mcf-control
additional labels: node-01,mcf-control
work folder: _work
```

As labels padrão esperadas do GitHub são `self-hosted`, `Linux` e `X64`; o workflow G1 adiciona `node-01` e `mcf-control` ao roteamento.

## Serviço 24/7

Depois que o runner aparecer como conectado no GitHub, instalar o runner como serviço usando o mecanismo `svc.sh` incluído no pacote oficial, mantendo o serviço associado ao usuário `ubuntu`.

Validar no GitHub que o runner aparece `Idle` antes de qualquer probe.

## Invariantes pós-bootstrap

O bootstrap G1 NÃO deve:

- alterar SSH/UFW/XRDP/fail2ban;
- publicar nova porta TCP/UDP;
- adicionar acesso ao Docker socket;
- adicionar `ubuntu` ao grupo `docker`;
- criar senha/token permanente;
- promover produção;
- executar `apply`, `reconcile` ou `rollback` da Mission 001.

## Primeiro handshake

O primeiro job aceito pelo runner deve executar somente o probe bounded versionado em `scripts/control_bridge_probe.py`.

Resultado mínimo esperado:

```text
hostname
identity
kernel
python
disk
memory
service state
mission-001 runner status, se disponível
```

O resultado deve retornar pelo GitHub e ser observável pelo MESTRE sem transporte manual de stdout por LEANDRO.

## Critério de PASS

```text
RUNNER_REGISTERED=YES
RUNNER_SERVICE=ACTIVE
RUNNER_GITHUB_STATE=IDLE_BEFORE_JOB
FIRST_JOB_ROUTE=node-01+mcf-control
PROBE_EXIT_CODE=0
RESULT_RETURNED_TO_GITHUB=YES
LEANDRO_MANUAL_STDOUT_RELAY=NO
VPS_UNRELATED_SERVICES_CHANGED=NO
```

## Falha / recuperação

Se o runner não registrar ou não receber job:

1. não ampliar permissões;
2. coletar somente estado do serviço/runner;
3. preservar logs do runner;
4. remover/reconfigurar somente o bootstrap G1 se necessário;
5. não tocar na implementação F1.1/F1.2b/F1.2c para forçar o bridge a funcionar.

## Próxima evolução após PASS

O handshake PASS libera apenas o planejamento/implementação do próximo slice do Control Bridge: operações não privilegiadas explícitas em workspaces de projeto. Capability Core, Node Agent, MCP e acesso privilegiado amplo continuam fora do G1 inicial.
