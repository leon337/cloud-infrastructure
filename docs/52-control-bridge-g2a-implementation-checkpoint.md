# 52 — CONTROL BRIDGE G2-A IMPLEMENTATION CHECKPOINT

Data: 2026-08-19
Status: **TASKS_1_9_COMPLETE — WAITING_HUMAN_GATE_TASK_10**
Missão: `CODEX-EXECUTION-MISSION-001` / MCF VPS Control Plane
Branch: `mcf/mission-001-control-bridge-g1`
Base deliberada: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED
Autoridade humana: LEANDRO

## Objetivo deste checkpoint

Congelar o estado material do G2-A após a implementação e validação das Tasks 1–9, para que outra sessão, agente ou Codex consiga retomar a missão sem depender da memória do chat.

Este checkpoint é a fonte de continuidade específica do Control Bridge G2-A. O `CHECKPOINT.md` principal continua descrevendo a trilha de implementação da plataforma/VPS (F1.2c); este documento descreve a capability transversal de control plane.

## Estado testado e comprovado

Implementação G2-A testada no commit:

```text
e36065268f609cbbfc64c6644d4c943f169756c9
```

Último commit material desse HEAD:

```text
test(g2a): document disposable integration fixtures
```

CI commit-bound desse SHA exato:

```text
foundation-ci #145
run_id=32198917421
COMPLETED / SUCCESS

docker-boundary-ci #140
run_id=32198917456
COMPLETED / SUCCESS
```

O `foundation-ci #145` executou a suíte estática/unitária e a integração descartável. O `docker-boundary-ci #140` também concluiu `SUCCESS` no mesmo HEAD.

## Estado por Task

```text
Task 1  Manifest catalog reutilizável ............ DONE
Task 2  Protocolo Core transport-neutral ......... DONE
Task 3  ProjectResolver por manifests ............. DONE
Task 4  Workspace read-only confinado ............. DONE
Task 5  Git inspection bounded .................... DONE
Task 6  Core dispatcher explícito ................. DONE
Task 7  GitHub adapter dormente ................... DONE
Task 8  Integração multi-project descartável ...... DONE
Task 9  CI exato + reconciliação .................. DONE
Task 10 Primeiro roundtrip G2-A real NODE-01 ...... WAITING_HUMAN_GATE
```

## Capacidades implementadas

G2-A permanece estritamente read-only e implementa somente:

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

O Core permanece transport-neutral. GitHub Issue/run/event metadata fica no adapter e não entra no Core Request.

## Project source of truth

Não existe registry paralelo.

Identidade e desired state de Project continuam vindo de:

```text
platform/manifests/**/*.yaml
platform/schemas/project.schema.json
scripts/validate_manifests.py
```

O G2-A somente resolve e observa o workspace local.

## Workspace root transitório

Mapeamento aprovado para bootstrap:

```text
/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>
```

O G2-A não cria, clona, materializa ou remove workspaces.

## Segurança e confinamento implementados

- path absoluto recusado;
- `~` recusado;
- traversal `..` recusado antes de tocar o filesystem;
- symlink root recusado;
- symlink/cross-project escape recusado;
- Git directory externo ao workspace recusado;
- arquivos/paths sensíveis recusados;
- conteúdo com padrão de segredo recusado;
- leitura UTF-8 bounded;
- listagem bounded;
- Git subprocess com argv fixo, `shell=False`, timeout e limites de saída;
- nenhuma capability recebe shell/argv arbitrário do request.

## Prova de integração

A integração G2-A executada nas Tasks 1–8 foi somente em fixtures/diretórios temporários do CI.

Ela comprovou, entre outros:

- resolução de múltiplos Projects;
- isolamento A/B;
- traversal recusado;
- symlink escape recusado;
- leitura bounded;
- inspeção Git local;
- diff grande tratado como attachment bounded;
- gitdir externo recusado.

Esses testes NÃO usaram o NODE-01 como workspace real.

## Gate real preservado

O arquivo abaixo continua deliberadamente AUSENTE:

```text
control/dispatch/g2a.json
```

A presença desse arquivo é o gatilho do primeiro workflow G2-A real. Sua criação pertence exclusivamente à Task 10 e exige HUMAN_GATE separado de LEANDRO.

Portanto:

```text
G2A_LIVE_DISPATCH=NO
G2A_REAL_NODE01_ROUNDTRIP=NO
G2A_REAL_WORKSPACE_MUTATION=NO
TASK_10_AUTHORIZED=NO
```

## Fronteiras que permanecem intactas

Não foram autorizados nem executados pelo G2-A:

```text
workspace.write/mkdir/delete
Git fetch/pull/checkout/commit/push
clone/materialização
shell arbitrário
sudo automático
root direto
Docker socket
grupo docker
docker exec/compose
systemctl mutante
UFW/SSH/rede
APT/packages
secrets
deploy
produção
backup/rollback privilegiado
```

## Relação com G1

G1 continua comprovado pelo checkpoint:

```text
docs/50-control-bridge-g1-handshake-checkpoint.md
```

G1 provou o transporte:

```text
ChatGPT -> GitHub -> Actions -> self-hosted runner -> VPS -> GitHub -> ChatGPT
```

G2-A adiciona o Core read-only multi-project, mas o primeiro roundtrip real desse Core ainda está bloqueado por HUMAN_GATE.

## Relação com documentos anteriores

- `docs/51-control-bridge-g2a-design.md` registra a arquitetura aprovada antes da implementação;
- `docs/superpowers/plans/2026-08-18-control-bridge-g2a-read-only.md` registra o plano TDD aprovado antes da execução;
- os campos de status pré-implementação desses documentos são históricos e são **SUPERSEDED para estado de execução** por este checkpoint;
- para arquitetura, eles continuam válidos;
- para estado atual de execução, usar este checkpoint + GitHub live + CI do SHA aplicável.

## Regras de retomada

Uma nova IA/agente deve:

1. ler `README.md`;
2. ler este checkpoint;
3. conferir o PR #3 e o HEAD live;
4. conferir o CI do HEAD aplicável;
5. confirmar que `control/dispatch/g2a.json` continua ausente;
6. não executar Task 10 sem autorização explícita de LEANDRO.

## Próximo passo exato

```text
NEXT_CONTROL_BRIDGE_STEP=HUMAN_GATE_TASK_10_FIRST_REAL_G2A_NODE01_ROUNDTRIP
```

Nenhuma autorização para Task 10 é inferida deste checkpoint ou da implementação das Tasks 1–9.
