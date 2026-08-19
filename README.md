# Cloud Infrastructure

<!-- PROJECT_STATUS:START -->
## STATUS ATUAL

- **Status geral:** `IMPLEMENTATION_IN_PROGRESS`
- **Progresso:** 3/32 slices `DONE`; slice atual `PARTIAL`
- **Slice atual:** `F1.2c` — Network Enforcement
- **Concluídos:** S0, F1.1, F1.2b
- **Próximos:** F1.3, F1.4, F1.5
- **HUMAN_GATEs no roadmap:** 4 (F1.2a, F1.5, F1.6, F5.4)
- **Próximo passo exato:** `SLICE_002C_VERIFY_RUNNER_AND_APPLY_NODE_01_NETWORK_SERVICES`
- **Último checkpoint:** `F1_2C_NODE_01_SERVICES_COMMIT_BOUND_CI_PASS`
- **Último commit relevante:** [`f771cfd`](https://github.com/leon337/cloud-infrastructure/commit/f771cfd09f1824562ddfdaea507fb3cb0781f6ac)
- **Última CI material:** [run `32131461110`](https://github.com/leon337/cloud-infrastructure/actions/runs/32131461110) — `PASS`
- **GitHub Project:** `BLOCKED_EXTERNAL_MISSING_READ_PROJECT_AND_PROJECT_SCOPES`
- **Produção:** `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`
- **Rotação de credenciais:** `DEFERRED_BY_HUMAN_DECISION`
- **Atualizado em:** `2026-08-18`

> Esta seção é gerada das fontes canônicas; não edite manualmente.
<!-- PROJECT_STATUS:END -->

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Nova IA/agente? Comece por [`CONTEXT.md`](CONTEXT.md). Para a capability transversal MCF VPS Control Plane, leia também [`docs/52-control-bridge-g2a-implementation-checkpoint.md`](docs/52-control-bridge-g2a-implementation-checkpoint.md) e [`state/control-bridge-g2a.yaml`](state/control-bridge-g2a.yaml).

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO aprende a administrar, diagnosticar, recuperar e reconstruir o ambiente com mínima dependência de IA. O projeto é separado do MCF; a VPS poderá hospedar o framework e outros sistemas, mas a infraestrutura não pertence estruturalmente a ele.

## Continuidade

O repositório implementa o PUC v1.0. `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml` são as portas de entrada da trilha principal da plataforma; `docs/`, `decisions/`, `findings/`, `history/`, `runbooks/`, `recovery/`, `assets/` e `governance/` preservam o contexto por tipo. Chats são temporários; o GitHub é a memória canônica após validação e publicação.

A capability transversal **MCF VPS Control Plane / Control Bridge** possui continuidade própria para não sobrescrever o estado da trilha F1.2c. O estado atual dessa capability está em `docs/52-control-bridge-g2a-implementation-checkpoint.md` e `state/control-bridge-g2a.yaml`. GitHub live, código, testes e CI do SHA aplicável prevalecem sobre status históricos em documentos anteriores.

## Control Bridge — estado transversal reconciliado

- **G1:** handshake real `ChatGPT -> GitHub -> Actions -> self-hosted runner -> VPS -> GitHub -> ChatGPT` comprovado.
- **G2-A:** Tasks 1–9 concluídas; implementação read-only multi-project validada no HEAD material `e36065268f609cbbfc64c6644d4c943f169756c9`.
- **CI desse HEAD:** `foundation-ci #145` (`32198917421`) `SUCCESS`; `docker-boundary-ci #140` (`32198917456`) `SUCCESS`.
- **Task 10:** `WAITING_HUMAN_GATE` — primeiro roundtrip G2-A real no NODE-01 ainda não autorizado.
- **Live dispatch:** `control/dispatch/g2a.json` deve permanecer ausente até autorização explícita de LEANDRO.
- **Mutação real de workspace pelo G2-A:** não executada.
- **Produção / sudo automático / root direto / Docker socket:** não autorizados pelo G2-A.
- **Checkpoint canônico do G2-A:** `docs/52-control-bridge-g2a-implementation-checkpoint.md`.
- **Estado machine-readable do G2-A:** `state/control-bridge-g2a.yaml`.

Os cabeçalhos pré-implementação em `docs/51-control-bridge-g2a-design.md` e no plano TDD permanecem como registro histórico do gate anterior; para estado executivo atual do G2-A, o checkpoint 52 + estado live prevalecem.

## Estado operacional — baseline reconciliada em 16/08/2026

- FASE 0, FASE 1 e FASE 2: **DONE**.
- `ubuntu`/publickey é o único login SSH permitido; root e autenticação SSH por senha estão desabilitados pela política efetiva.
- UFW está ativo com `deny incoming` e somente OpenSSH em TCP 22; fail2ban protege o SSH.
- sudo exige senha; não existe regra `NOPASSWD`; `ubuntu` saiu do grupo `lxd` e o LXD está desabilitado/inativo.
- VNC do provedor foi revalidado como console out-of-band; Rescue está disponível, snapshots não estão configurados, backup do provedor não está contratado e firewall do provedor não está configurado.
- backup diário sanitizado de configurações está ativo; a primeira cópia off-host teve hash validado e o archive passou em teste de extração, não em restore funcional.
- zero atualizações APT pendentes após upgrade e reboot final.

## Cloud Workstation

A Cloud Workstation está **FUNCTIONAL_AND_VALIDATED**: XFCE + LightDM, XRDP restrito a `127.0.0.1:3389` e acesso somente por túnel SSH. Firefox oficial em pacote DEB, VS Code, terminal, Thunar, múltiplas janelas, clipboard bidirecional, resolução dinâmica, logout/login, desconexão/reconexão, persistência e reboot foram testados.

Recursos são fatos voláteis. A recuperação da missão observou 8 CPUs, 23 GiB de
RAM total, sem swap e raiz de 290 GiB; uso atual deve ser medido antes de cada
slice. Os números de ~2,2 GiB RAM/~7,5 GiB disco pertencem ao snapshot histórico
da validação final da Workstation.

## Implementação atual

Q1–Q39 definem a arquitetura vinculante e Q40-D autoriza o Codex a selecionar as
tecnologias e implementar incrementalmente a plataforma DEV/lab. A missão está em
[`docs/CODEX-EXECUTION-MISSION-001.md`](docs/CODEX-EXECUTION-MISSION-001.md) e o
roadmap corrente em
[`docs/45-revised-implementation-roadmap.md`](docs/45-revised-implementation-roadmap.md).
A camada de acompanhamento está documentada em
[`docs/48-status-layer-v1.md`](docs/48-status-layer-v1.md).

F1.1 e F1.2b estão concluídos no NODE-01. A base F1.2c também está ativa no host,
e a matriz de redes/DNS/proxy/grants passou em VM descartável. O estado e o
próximo passo exatos da trilha principal são projetados automaticamente na seção `STATUS ATUAL`.
Produção não está autorizada e a rotação permanece adiada por decisão humana.

A trilha transversal Control Bridge não altera o próximo passo F1.2c. Seu estado é recuperado separadamente pelo checkpoint 52 e por `state/control-bridge-g2a.yaml`.
