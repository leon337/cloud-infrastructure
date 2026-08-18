# 51 — CONTROL BRIDGE G2-A DESIGN

Status: **ARCHITECTURE_APPROVED — IMPLEMENTATION_NOT_AUTHORIZED**
Data: 2026-08-18
Missão: `CODEX-EXECUTION-MISSION-001` / MCF VPS Control Plane
Branch: `mcf/mission-001-control-bridge-g1`
Base: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED
Autoridade de aprovação arquitetônica: LEANDRO

## 1. Objetivo

G2-A transforma o G1, já comprovado como transporte `ChatGPT -> GitHub -> Actions -> runner -> VPS -> GitHub -> ChatGPT`, em uma primeira capability operacional multi-project **somente leitura**.

O objetivo é permitir que agentes consultem estado **local/observado** de workspaces registrados na VPS sem shell arbitrário, sem sudo, sem Docker e sem escrita.

G2-A não substitui o Capability Core, Node Agent, MCF, PermissionEngine, HUMAN_GATE ou workflow engine. Ele é um bootstrap transport-neutral de inspeção de workspace que deve sobreviver à futura troca do backend.

## 2. Decisões arquitetônicas aprovadas

A auditoria independente do G2 foi aceita com quatro alterações obrigatórias:

1. separar `G2-A = READ-ONLY` de `G2-B = BOUNDED WRITE`;
2. não criar segunda fonte de verdade para Project Registry;
3. tornar o Workspace Core transport-neutral;
4. separar source state remoto/canônico de workspace state local/observado.

Consequências:

- nenhum SQLite/dedupe persistente em G2-A;
- nenhum mutation ledger;
- nenhum lock manager local;
- nenhuma precondition de escrita;
- nenhuma operação Git mutante;
- nenhum provisioning/clone de workspace;
- nenhum registry paralelo ao manifest `Project` existente.

## 3. Arquitetura

```text
GitHub Adapter
      |
      v
GitHub Actions
      |
      v
Self-Hosted Runner NODE-01
      |
      v
Workspace Core
  |-- ManifestLoader
  |-- ProjectResolver
  |-- WorkspaceResolver
  |-- PathConfinement
  |-- ReadOperations
  `-- GitInspection
      |
      v
Core Result
      |
      v
GitHub Adapter
      |
      +-- Issue comment / Job Summary
      `-- Artifact quando necessário
```

O Core não depende de Issue, workflow run, GitHub token ou outro conceito de transporte.

## 4. Transporte versus Core

### GitHub Transport Envelope

Dados específicos do transporte permanecem fora do Core, por exemplo:

```json
{
  "issue_number": 123,
  "workflow_run_id": 456,
  "event_name": "push"
}
```

Esse envelope existe apenas no adapter GitHub.

### Core Request

```json
{
  "protocol": "MCF_WORKSPACE_CONTROL_V1",
  "request_id": "G2A-000001",
  "project": {
    "tenant": "potiguar",
    "name": "controle-de-ponto",
    "environment": "dev"
  },
  "operation": "git.status",
  "arguments": {}
}
```

Campos obrigatórios do Core:

- `protocol`;
- `request_id`;
- `project.tenant`;
- `project.name`;
- `project.environment`;
- `operation`;
- `arguments` objeto.

O request não aceita `cwd` absoluto, `argv`, comando shell ou workspace absoluto.

## 5. Core Result

```json
{
  "protocol": "MCF_WORKSPACE_CONTROL_RESULT_V1",
  "request_id": "G2A-000001",
  "project": {
    "tenant": "potiguar",
    "name": "controle-de-ponto",
    "environment": "dev"
  },
  "operation": "git.status",
  "status": "PASS",
  "started_at": "...",
  "finished_at": "...",
  "result": {},
  "error": null,
  "evidence": {
    "workspace_state": "PRESENT",
    "git_head": "..."
  }
}
```

Estados G2-A:

- `PASS`;
- `REFUSED`;
- `NOT_FOUND`;
- `FAILED`;
- `TIMEOUT`.

`CONFLICT` fica reservado para capacidades mutantes futuras e não é requisito do G2-A.

## 6. Operações G2-A

Único conjunto de operações aprovado para o primeiro slice:

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

### Semântica

`project.list`
: lista Projects válidos encontrados nos manifests existentes.

`project.get`
: retorna identidade e desired state não secreto do Project selecionado.

`workspace.stat`
: informa se o workspace esperado está `PRESENT`, `ABSENT` ou inválido e retorna metadados seguros.

`workspace.list`
: lista entradas locais dentro de path confinado ao workspace.

`workspace.read`
: lê conteúdo local de arquivo permitido, sujeito a limites de tamanho/encoding e confinamento.

`git.status`
: retorna status local estruturado/porcelain ou equivalente parseável.

`git.branch`
: retorna branch local observada, inclusive detached state quando aplicável.

`git.head`
: retorna commit HEAD local observado.

`git.diff`
: retorna diff local bounded, com limite de saída; saída grande usa Artifact via adapter.

## 7. Operações explicitamente fora do G2-A

```text
workspace.write
workspace.mkdir
workspace.delete
git.fetch
git.pull
git.checkout
git.commit
git.push
clone
workspace provisioning
workspace materialization
shell
sudo
Docker
docker exec
docker compose
systemctl mutante
UFW/SSH/rede
APT/packages
secrets
deploy
produção
backup/rollback privilegiado
```

Essas operações não podem entrar por argumento genérico nem por fallback de shell.

## 8. Fonte de verdade de Project

G2-A não cria `registry.json`, SQLite ou banco próprio de projetos.

A identidade/desired state vem da linha existente:

```text
platform/manifests/**/*.yaml
        |
        v
scripts/validate_manifests.py
        |
        v
Project manifests válidos
```

O `ProjectResolver` é somente um resolver dos manifests existentes.

Modelo:

```text
MANIFEST = identidade + desired state
GITHUB   = source remoto/canônico
WORKSPACE = estado local/observado
```

`spec.capabilities` do Project não é usado como ACL do Control Plane em G2-A.

## 9. Identidade multi-project

Chave lógica:

```text
tenant / project / environment
```

Exemplos:

```text
potiguar/controle-de-ponto/dev
potiguar/almoxarifado/dev
potiguar/rastreamento-frota/dev
```

O request fornece somente essa identidade lógica. O workspace físico é resolvido internamente.

## 10. Workspace root transitório

Para o bootstrap G2-A, o root aprovado é:

```text
/home/ubuntu/mcf-workspaces/<tenant>/<project>/<environment>
```

Classificação:

```text
TRANSITIONAL_G2_WORKSPACE_ROOT
```

Razões:

- runner atual opera como `ubuntu`;
- não exige sudo nem mudança de ownership da árvore gerenciada da plataforma;
- separa workspace de projeto do `_work` interno do GitHub Actions;
- permite migração futura para `/var/lib/cloud-platform/...` atrás do mesmo contrato externo.

G2-A não cria, clona, corrige, materializa ou reconcilia workspaces. Ele apenas observa o path esperado.

## 11. Source state versus workspace state

G2-A não deve usar runner quando o GitHub já responde melhor sobre o source remoto/canônico.

Exemplos de source state — consultar GitHub diretamente:

- conteúdo publicado no repositório;
- commit remoto;
- arquivos da branch remota;
- PRs/issues/checks.

Exemplos de workspace state — consultar G2-A:

- workspace existe localmente?;
- qual HEAD está checkoutado?;
- está dirty?;
- há diff local?;
- qual conteúdo local ainda não foi commitado?;
- o arquivo local diverge do source remoto?

Essa separação reduz tráfego no runner e evita duplicação de capabilities do GitHub connector.

## 12. Path confinement

Todo acesso filesystem é relativo ao workspace resolvido internamente.

Recusas obrigatórias:

```text
/path/absoluto
../escape
~/atalho
symlink -> fora do workspace
resolução real fora do root permitido
```

Fluxo lógico:

```text
request path
   |
   v
workspace canônico
   |
   v
normalização + resolução real
   |
   v
continua dentro do workspace?
   |                |
   | não            | sim
   v                v
REFUSED          operação read-only
```

A implementação deverá usar resolução real de paths e verificar ancestry após resolução de symlinks, não apenas sanitização textual de `..`.

## 13. Limites de leitura

Antes da implementação, o plano deverá definir valores explícitos e testáveis para:

- tamanho máximo de arquivo lido inline;
- profundidade/quantidade máxima em `workspace.list`;
- tamanho máximo de `git.diff` inline;
- timeout por operação;
- política de encoding binário/texto;
- redaction/recusa de paths sensíveis quando necessário.

Esses limites são parâmetros de implementação, não autorização para ampliar o escopo.

## 14. Concorrência

G2-A é read-only e não exige lock manager local ou mutation queue.

GitHub Actions `concurrency` pode continuar sendo usado como proteção operacional do transporte, mas não faz parte do contrato do Core.

Para G2-B futuro:

```text
GitHub concurrency
       +
lock local defensivo por workspace
```

será reavaliado para cobrir também MCP/API/CLI que não passam por GitHub Actions.

## 15. Idempotência

Operações G2-A são observacionais e repetíveis.

`request_id` permanece obrigatório para correlação/evidência, mas G2-A não cria persistent dedupe store.

Dedupe persistente, expected state, preconditions e `CONFLICT` entram apenas quando capacidades mutantes forem projetadas em G2-B.

## 16. Resultados e evidência

Separação obrigatória:

```text
TRANSPORTE OPERACIONAL
Issue / Job Summary / Artifact

MEMÓRIA CANÔNICA
Git / manifests / checkpoints / ADRs somente para decisões/estado material
```

Política:

- resultado pequeno: Issue comment e/ou Job Summary;
- resultado grande: Artifact + referência resumida;
- Artifact não é fonte de verdade durável;
- não criar histórico Git `control/results/*` para cada request;
- não criar commit documental para cada leitura.

## 17. Relação com `vpsctl`

`vpsctl` permanece nome conceitual do Execution Core transport-neutral.

Ele deve ser estreito:

```text
request validado
→ resolve Project
→ resolve workspace
→ aplica confinamento
→ executa capability conhecida
→ retorna resultado estruturado
```

Ele não implementa:

- PermissionEngine;
- HUMAN_GATE;
- MCF mission engine;
- workflow engine;
- policy global;
- evidence ledger completo.

GitHub, MCP, API, CLI, Codex ou Hermes devem convergir para o mesmo Core em vez de implementar executores divergentes.

## 18. Relação com executor privilegiado do Codex

G2-A não usa `codex-mission-001-runner` para operações normais de workspace/Git.

O executor anterior do Codex permanece separado com seus verbos fixos e fronteira privilegiada própria.

G2-A:

```text
runner ubuntu
→ workspace core
→ filesystem/Git read-only
```

sem sudo.

Operações privilegiadas futuras devem passar pela fronteira Capability Core / Node Agent ou por mecanismo transitório explicitamente autorizado, nunca por sudo genérico no G2-A.

## 19. Evolução futura

Hoje:

```text
GitHub Adapter
→ Actions
→ runner
→ Workspace Core
```

Futuro:

```text
GitHub / MCP / API / CLI
          |
          v
    Capability Core
      /          \
     v            v
Workspace Core   Node Agent
não privilegiado privilegiado
```

O contrato do Workspace Core deve sobreviver à introdução futura de GitHub App, OIDC, MCP/API/CLI e Capability Core.

GitHub App e OIDC têm papéis distintos:

- GitHub App: Control Plane acessando GitHub/cross-repository;
- OIDC: GitHub Actions autenticando no futuro Capability Core.

Nenhum dos dois é requisito do primeiro G2-A.

## 20. Testes obrigatórios antes do teste real

### Unitários

- Core request válido/inválido;
- operação desconhecida recusada;
- manifest loading;
- Project resolution;
- Project inexistente;
- workspace `PRESENT`/`ABSENT`;
- path absoluto recusado;
- `../` recusado;
- symlink escape recusado;
- cross-project escape recusado;
- `workspace.stat`;
- `workspace.list`;
- `workspace.read`;
- limite de tamanho;
- encoding/binário;
- `git.status`;
- `git.branch`;
- `git.head`;
- `git.diff`;
- result serialization;
- timeout.

### Integração

Usar fixtures isoladas `project-a` e `project-b` para provar:

- A não lê B;
- B não lê A;
- traversal falha;
- symlink escape falha;
- workspace read funciona;
- Git status/head/diff funcionam;
- resultado volta pelo GitHub adapter;
- output grande segue a política de Artifact definida no plano.

### Teste real

Somente depois dos testes unitários e de integração:

- registrar/usar um workspace fixture não crítico já materializado;
- executar `workspace.stat`;
- executar `workspace.list`;
- executar `workspace.read`;
- executar `git.status`;
- executar `git.branch`;
- executar `git.head`;
- executar `git.diff` quando houver fixture apropriada.

Nenhuma escrita é autorizada por esse teste.

## 21. Critério de conclusão do G2-A

G2-A só poderá ser declarado concluído quando houver evidência de:

```text
PROJECT_RESOLUTION_MULTI_PROJECT=PASS
WORKSPACE_RESOLUTION=PASS
PATH_TRAVERSAL_REFUSAL=PASS
SYMLINK_ESCAPE_REFUSAL=PASS
CROSS_PROJECT_ISOLATION=PASS
WORKSPACE_READ=PASS
GIT_STATUS=PASS
GIT_BRANCH=PASS
GIT_HEAD=PASS
GIT_DIFF=PASS
CORE_TRANSPORT_NEUTRAL=PASS
GITHUB_ROUNDTRIP=PASS
NO_SUDO=PASS
NO_MUTATION=PASS
UNIT_TESTS=PASS
INTEGRATION_TESTS=PASS
```

CI do repositório continua commit-bound e não pode ser substituído por uma mensagem de sucesso do bridge.

## 22. G2-B explicitamente adiado

G2-B será um design separado e não herda autorização automática desta aprovação.

Assuntos exclusivos de G2-B:

- `workspace.write` / `mkdir` / `delete`;
- preconditions e expected state;
- persistent dedupe;
- lock local;
- mutation evidence;
- rollback de arquivo;
- operações Git mutantes;
- concorrência entre múltiplos transports.

G2-B exigirá nova auditoria arquitetônica e HUMAN_GATE apropriado antes de implementação.

## 23. Itens deliberadamente adiados

Não são necessários para provar G2-A:

- GitHub App;
- OIDC;
- `workflow_dispatch` como command API;
- `repository_dispatch`;
- reusable workflows;
- runner hooks;
- Runner Groups;
- JIT/ephemeral runners;
- MCP adapter;
- API externa;
- CLI pública;
- Capability Core;
- Node Agent.

Podem ser reavaliados quando reduzirem complexidade real de um slice posterior.

## 24. Arquivos previstos para a implementação futura

Nenhum dos arquivos abaixo está autorizado por este documento; são apenas fronteiras previstas para o plano posterior:

```text
scripts/ ou control-plane/
  workspace core / adapter GitHub

tests/
  unitários e integração G2-A

.github/workflows/
  evolução do Control Bridge para G2-A

platform/manifests/ e platform/schemas/
  somente se necessário para reutilizar/estender contrato existente sem criar registry paralelo
```

A implementação deve seguir os padrões já existentes do repositório e evitar estrutura paralela desnecessária.

## 25. Estado de aprovação

```text
G1_HANDSHAKE=PASS
G1_CURRENT_HEAD_CI=GREEN_BEFORE_THIS_DESIGN_COMMIT
G1_PR3=OPEN_DRAFT_NOT_MERGED

G2_A_ARCHITECTURE=APPROVED_BY_LEANDRO
G2_A_IMPLEMENTATION=NOT_AUTHORIZED
G2_A_VPS_MUTATION=NO
G2_A_GITHUB_CODE_IMPLEMENTATION=NO

G2_B=DEFERRED_SEPARATE_DESIGN_REQUIRED
G3=FUTURE
```

Próximo gate: revisão humana deste documento versionado. Somente depois de sua aprovação explícita como especificação escrita deve ser criado o plano de implementação detalhado.
