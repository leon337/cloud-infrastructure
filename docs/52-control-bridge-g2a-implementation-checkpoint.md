# 52 — CONTROL BRIDGE G2-A IMPLEMENTATION CHECKPOINT

Data: 2026-08-19
Status: **TASK_10_LIVE_PROOF_PASS — CHECKPOINT_CI_PENDING**
Missão: `CODEX-EXECUTION-MISSION-001` / MCF VPS Control Plane
Branch: `mcf/mission-001-control-bridge-g1`
Base deliberada: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED
Autoridade humana: LEANDRO

## Objetivo deste checkpoint

Congelar o estado material e a evidência real do G2-A após o primeiro roundtrip read-only no NODE-01. Este documento é a fonte de continuidade específica do Control Bridge G2-A; GitHub live e CI do SHA aplicável continuam prevalecendo para estado operacional.

## Estado por Task

```text
Task 1  Manifest catalog reutilizável ............ DONE
Task 2  Protocolo Core transport-neutral ......... DONE
Task 3  ProjectResolver por manifests ............. DONE
Task 4  Workspace read-only confinado ............. DONE
Task 5  Git inspection bounded .................... DONE
Task 6  Core dispatcher explícito ................. DONE
Task 7  GitHub adapter ............................ DONE
Task 8  Integração multi-project descartável ...... DONE
Task 9  CI exato + reconciliação .................. DONE
Task 10 Primeiro roundtrip G2-A real NODE-01 ...... PASS
```

## CI de implementação comprovado antes do roundtrip

O fix de execução direta do adapter foi validado no SHA:

```text
204967b5748273615eb20ce4d6e2020839233f72
```

CI commit-bound desse SHA:

```text
foundation-ci #157
run_id=32249250284
COMPLETED / SUCCESS

docker-boundary-ci #152
run_id=32249250290
COMPLETED / SUCCESS
```

Durante o primeiro live dispatch foram identificadas duas incompatibilidades de runtime e corrigidas por TDD:

1. execução direta de `scripts/control_bridge_g2a.py` não resolvia o pacote `control_plane`;
2. NODE-01 possui `jsonschema` e `PyYAML`, mas não possui `venv/ensurepip/pip`; o workflow foi ajustado para usar o Python 3.12 do sistema sem instalar pacotes, sem sudo e sem ampliar privilégios.

O adapter corrigido teve `8/8` testes direcionados executados com sucesso no próprio NODE-01 antes do roundtrip final.

## Fixture real usada

Project lógico:

```text
leon337/g2a-smoke/dev
```

Workspace transitório:

```text
/home/ubuntu/mcf-workspaces/leon337/g2a-smoke/dev
```

A fixture é DEV, não crítica, rebuildable e sem autorização de produção.

## Issue de evidência

```text
Issue #5 — G2-A — NODE-01 read-only roundtrip evidence
```

Todos os resultados abaixo retornaram automaticamente do self-hosted runner para essa Issue.

## Roundtrip positivo real

```text
G2A-NODE01-20260819-003  project.list      PASS
G2A-NODE01-20260819-004  project.get       PASS
G2A-NODE01-20260819-005  workspace.stat    PASS
G2A-NODE01-20260819-006  workspace.list    PASS
G2A-NODE01-20260819-007  workspace.read    PASS
G2A-NODE01-20260819-008  git.status        PASS
G2A-NODE01-20260819-009  git.branch        PASS
G2A-NODE01-20260819-010  git.head          PASS
G2A-NODE01-20260819-011  git.diff          PASS
```

Leitura adicional usada na prova de não mutação:

```text
G2A-NODE01-20260819-013  workspace.read    PASS
```

## Prova negativa de confinamento

Request:

```text
G2A-NODE01-20260819-012
operation=workspace.read
path=../README.md
```

Resultado obrigatório observado:

```text
status=REFUSED
error=path_escape_refused
```

Nenhum segredo real do host foi usado como leitura positiva.

## Prova de não mutação

Antes e depois de uma leitura G2-A final, a fixture permaneceu idêntica:

```text
sha256=f9238cd615de9637c8df196a6e2f5592e43d40f68847b9a0bce2236ff2b360c0
size=705
mtime_ns=1787138952926672279
```

Git local antes/depois:

```text
HEAD=f8d97e6a20888f455a377c4c296ab9267a7fde9d
status_porcelain=<empty>
```

Boundary de privilégio reconfirmado:

```text
sudo -n true = REFUSED / password required
Docker socket read+write access = REFUSED
runner user = ubuntu
```

Portanto não houve mudança de conteúdo, HEAD Git, dirty state, sudo automático ou acesso ao Docker socket causada pelo G2-A.

## Capacidades comprovadas no NODE-01

```text
project.list
project.get
workspace.stat
workspace.list
workspace.read
git.status
git.branch
git.head
git.diff
```

O Core permanece transport-neutral e não aceita shell/argv arbitrário pelo request.

## Estado canônico do gate

```text
G2A_READ_ONLY=PASS
G2B_WRITE=NOT_IMPLEMENTED
SHELL=NOT_IMPLEMENTED
SUDO=NOT_GRANTED
DOCKER_SOCKET=NOT_GRANTED
PRODUCTION=NOT_AUTHORIZED
```

## Limites que continuam intactos

Não estão autorizados por este checkpoint:

```text
workspace.write/mkdir/delete
Git fetch/pull/checkout/commit/push
shell arbitrário
sudo automático/root direto
Docker socket/grupo docker
docker exec/compose
systemctl mutante
UFW/SSH/rede
APT/packages
secrets
deploy
produção
```

## CI final do checkpoint

Este checkpoint deve passar `foundation-ci` e `docker-boundary-ci` no HEAD que o contém antes de qualquer discussão de merge ou declaração de fechamento total do G2-A.

Enquanto esse CI final não estiver verde:

```text
LIVE_NODE01_PROOF=PASS
CHECKPOINT_CI=PENDING
MERGE=NO
```

## Próximo passo após CI verde

G2-B é um design e uma autorização separados. A próxima capability pretendida é escrita limitada, inicialmente somente em workspace DEV descartável, com precondition, evidência e rollback, sem shell/root/Docker/produção.

```text
NEXT_CONTROL_BRIDGE_STEP=DESIGN_G2B_BOUNDED_WRITE
```
