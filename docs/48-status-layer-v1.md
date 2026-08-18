# 48 — STATUS LAYER V1

Status: **IMPLEMENTED — GITHUB PROJECT BLOCKED_EXTERNAL**

## Objetivo e precedência

A camada oferece três projeções leves da missão: README executivo, GitHub
Actions Job Summary e GitHub Project privado. Ela não é fonte de verdade.

```text
state/*.yaml + CHECKPOINT + roadmap
                  |
                  +--> README / Actions Summary / GitHub Project
```

Em qualquer divergência, as fontes canônicas prevalecem. Nenhum componente
desta camada consulta a VPS ou modifica estado canônico.

## Gerador

`scripts/generate_project_status.py` valida `state/current.yaml`,
`state/components.yaml` e a tabela de `docs/45-revised-implementation-roadmap.md`.
Ele atualiza somente a região `PROJECT_STATUS` do README.

```bash
python scripts/generate_project_status.py --write-readme
python scripts/generate_project_status.py --check-readme
python scripts/generate_project_status.py --project-json /tmp/project.json
```

A geração é determinística e idempotente. Produção autorizada, rotação fora do
estado adiado, campo obrigatório ausente, estado desconhecido ou README stale
causam falha fechada.

## GitHub Actions

Os jobs `validate` das workflows Foundation e Docker executam o check do README
e publicam no `$GITHUB_STEP_SUMMARY`: slice, estado, resultado dos testes,
HUMAN_GATEs, próximo passo, SHA e timestamp. Não há segunda suíte nem polling.

## GitHub Project

A conta GitHub está autenticada, o repositório é privado, mas o token corrente
possui somente `repo`, `read:org` e `gist`. `gh project list --owner leon337`
recusou acesso por falta de `read:project`. Portanto:

- estado: `BLOCKED_EXTERNAL_MISSING_READ_PROJECT_AND_PROJECT_SCOPES`;
- nenhuma credencial foi solicitada, persistida ou exposta;
- o gerador já produz o modelo normalizado para sincronização;
- HUMAN_GATE futuro: LEANDRO autorizar o escopo GitHub Project na CLI; depois
  criar o Project privado `IMPLEMENTAÇÃO DA VPS` e sincronizar os 32 slices.

O mapeamento visual preparado é: `PLANNED/CONDITIONAL -> TODO`,
`IMPLEMENTING -> IN PROGRESS`, `WAITING_HUMAN_GATE -> HUMAN GATE`,
`PARTIAL -> VALIDATING`, `DONE -> DONE`.

## Custo e segurança

O custo ocorre somente durante commit/CI e é medido em segundos. Não existe
serviço systemd, daemon, container, banco, cron, listener, polling ou consumo
residente na VPS. Secrets, credenciais e dados classificados continuam
proibidos nas três projeções.
