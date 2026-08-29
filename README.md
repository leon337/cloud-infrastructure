# Cloud Infrastructure

<!-- CANONICAL_EXECUTIVE_PANEL_IMPLEMENTACAO_DA_VPS -->

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Este README é o **painel executivo canônico e consolidado da missão IMPLEMENTAÇÃO DA VPS**.
> Ele define a visão executiva, o escopo e a hierarquia documental da missão. O
> [`ROADMAP-CHECKLIST.md`](ROADMAP-CHECKLIST.md) é um checklist operacional detalhado
> subordinado a este painel — não uma fonte executiva concorrente. Para recuperar o
> contexto completo, leia também [`CONTEXT.md`](CONTEXT.md), [`CHECKPOINT.md`](CHECKPOINT.md)
> e [`state/current.yaml`](state/current.yaml). Evidência GitHub/provider/live continua
> prevalecendo sobre documentação quando fatos mutáveis divergirem.

## Painel consolidado

Reconciliação-base executada em **22/08/2026, 11:09 BRT (14:09 UTC)** a partir do
GitHub, worktrees locais, evidências do Control Bridge e uma auditoria curta e
somente leitura no NODE-01.

**Atualização operacional de 28/08/2026:** RECOVERY-P1/P2 concluídos e
`RUNNER_ISOLATION_P1` comprovado no NODE-01. O PoC persistente foi retirado e a
prova real entre dois jobs passou; o hook global do runner está configurado, mas
permanece `CONFIGURED_NOT_ACTIVE_BLOCKED_PRIVILEGE` até restart autorizado do serviço.

**SSH key governance em 28/08/2026:** a provenance da `dsh-tunnel...` foi confirmada
por histórico do `ubuntu` e auth log. LEANDRO confirmou que essa chave é usada no fluxo
real de abertura/acesso à VPS pelo notebook. O fallback independente permanece apenas
como contingência; `authorized_keys` segue inalterado e a chave deve ser preservada.

**F1.2c live recovery em 28/08/2026:** a classificação parcial foi refinada após diagnóstico
root: a árvore `/etc/cloud-platform/network-services` já existia e era byte-exata (`EXACT_PRESENT`);
a ausência reportada no preflight não privilegiado era falso negativo de traversal permission. As PRs
#39/#40 corrigiram o contrato de markers e modelaram rollback simétrico para `ABSENT`/`EXACT_PRESENT`.
O candidato exato `baaf83908e8e83264baafc032434a4df1952450b` passou static/ShellCheck run
`33217692498` e KVM run `33217692536` nas duas variantes.

Com autorização humana one-shot, o precheck live retornou `KNOWN_PARTIAL baseline_config=EXACT_PRESENT`;
checkpoint e backup pré-apply foram verificados; `apply` + `check` concluíram e a pós-validação root
confirmou `state=RECOVERED`, serviço `active+enabled`, helper/base checks `PASS`, forwarding IPv4/IPv6
`1/0` e ausência de listeners públicos gerenciados. A autorização foi consumida; novo reapply exige
novo gate. Evidência: [`evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`](evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md).

**NETWORK_CONVERGENCE_P2 live em 29/08/2026:** a causa funcional do `wait-online` foi reproduzida em KVM como ausência da rota conectada IPv4 `/17`; o agente exato que a removeu permanece `NÃO VERIFICADO`. O fix preservou o `staticroute` do cloud-init/provedor e adicionou somente `169.58.128.1/32 scope link`. Após PRs #42/#43, static + KVM hospedados `SUCCESS`, precheck live `KNOWN_BROKEN`, backup/checkpoint e apply/check autorizados, `eth0` convergiu para `configured` e ambos os predicates `wait-online` passaram. O `systemd-networkd` não foi reiniciado. Evidência: [`evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`](evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md).

**PRE_REBOOT_CHECKPOINT em 29/08/2026:** baseline pré-reboot verificada com serviços críticos ativos, `eth0=configured`, wait-online PASS e recovery F1.2c/P2 saudável. O V1 foi rejeitado por self-hash inválido de `SHA256SUMS`; o V2 `pre-reboot-checkpoint-20260829T203736Z.tar.gz` passou SHA externo, segurança de archive, todos os hashes internos e cópia off-host. Backup canônico associado `cloud-infrastructure-config-20260829T203734Z.tar.gz` também foi verificado off-host com `RECOVERY_P2=PASS`. Reboot/updates continuam não autorizados. Evidência: [`evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md`](evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md).

| Área | Estado reconciliado | Resumo |
|---|---|---|
| VPS / NODE-01 | `OPERATIONAL_WITH_OPEN_INCIDENTS` | F1.2c, network convergence P2 e checkpoint pré-reboot verificados; reboot e outros débitos permanecem abertos |
| Plataforma privada | `IMPLEMENTATION_IN_PROGRESS` | S0, F1.1, F1.2b, F1.2c, network convergence P2 e checkpoint pré-reboot concluídos; próximo gate é update/reboot controlado |
| Control Bridge G1 | `PASS_REAL_NODE_01_ROUNDTRIP` | transporte curto pelo runner comprovado |
| Control Bridge G2-A | `PASS_REAL_NODE_01_READ_ONLY` | leitura confinada e recusa de escape comprovadas |
| Control Bridge G2-B | `TASK_8_FAILED_ATTEMPT_3` | Tasks 1–7 concluídas; prova descartável completa ainda não passou |
| Runner isolation | `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING` | PoC persistente retirado; policy + guard canônicos e prova cross-job real passaram; hook global aguarda restart autorizado |
| SSH key governance | `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED` | `dsh-tunnel...` é usada no acesso notebook→VPS; manter a chave e preservar esse fluxo em qualquer hardening futuro |
| GitHub `main` | `DOCUMENTATION_AND_INTEGRATION_DRIFT` | não contém ainda as linhagens completas da plataforma e do bridge |
| Produção externa | `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` | nenhuma promoção para produção está autorizada |
| Credenciais | `ROTATION_DEFERRED_BY_HUMAN_DECISION` | política anterior permanece vigente |

### Próxima ação exata

```text
UPDATE_AND_CONTROLLED_REBOOT
```

Hardening pendente separado: ativar os hooks globais STARTED/COMPLETED do runner
somente em uma janela de restart autorizada do serviço. Não contornar o boundary de
`systemd`/sudo para isso. F1.2c e network convergence P2 estão concluídos; reboot continua em gate separado.

## Estado observado da VPS

Fonte da fotografia atual: execução read-only
[`32577551012`](https://github.com/leon337/cloud-infrastructure/actions/runs/32577551012)
e inspeção confinada do guest nas execuções
[`32577659953`](https://github.com/leon337/cloud-infrastructure/actions/runs/32577659953)
e
[`32577815107`](https://github.com/leon337/cloud-infrastructure/actions/runs/32577815107).
Os probes temporários foram removidos imediatamente depois da coleta.

Atualização live de **28/08/2026**: o PID `783478`, socket, PID file e source do PoC foram removidos de forma controlada. O runner permaneceu ativo. A prova `runner-isolation-proof` no mesmo `node--1-mcf-control` produziu `RUNNER_ISOLATION_CROSS_JOB=PASS`; evidência sanitizada em [`evidence/runner-isolation/RUNNER-ISOLATION-P1-20260828.md`](evidence/runner-isolation/RUNNER-ISOLATION-P1-20260828.md).

| Item | Estado em 22/08/2026 14:09 UTC |
|---|---|
| Host | `vmi3506102`, Ubuntu 24.04.4, kernel `6.8.0-137-generic`, 8 CPUs |
| Uptime | 6 dias e 12 horas |
| Memória | 23 GiB total, 9,5 GiB usada, 13 GiB disponível, sem swap |
| Disco raiz | 290 GiB total, 23 GiB usado, 268 GiB disponível |
| SSH, UFW, Docker, containerd | `active` |
| Self-hosted runner | `active/running`, identidade `node--1-mcf-control` |
| Units falhas | `cloud-platform-network-services.service` |
| Repositório da VPS | `/home/ubuntu/cloud-infrastructure`, limpo e sincronizado |
| Branch/HEAD da VPS | `codex/control-bridge-g2b` em `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a` |
| Repositório MCF na VPS | ausente em `/home/ubuntu/multiagent-collaboration-framework` |
| QEMU host | `qemu-system-x86`, `qemu-utils` e `cloud-image-utils` instalados |
| VM descartável G2-B | ainda ligada como `g2b-disposable-task8-vm3`, 6 vCPU/12 GiB, SSH local `127.0.0.1:22284` |
| PTY persistente experimental | **histórico em 22/08:** PID `783478`, processo vivo, socket modo `0600`; retirado em 28/08 |

### Incidentes e pendências

#### INC-001 — RESOLVIDO em 28/08 — F1.2c network services

- causa histórica: helper/unit antigos tentavam lock em `/run/lock` sob filesystem protegido;
- o preflight não privilegiado inferiu incorretamente config ausente; diagnóstico root confirmou baseline `EXACT_PRESENT` byte-exata;
- PRs #39/#40 corrigiram marker equivalence e preservação da baseline parcial;
- candidato `baaf83908e8e83264baafc032434a4df1952450b` passou static/ShellCheck e KVM `ABSENT` + `EXACT_PRESENT`;
- rollout autorizado concluiu `RECOVERY_CHECK=PASS` e pós-validação `F1_2C_POSTVERIFY=PASS`;
- qualquer novo reapply requer nova autorização humana; a autorização usada foi consumida.

#### INC-002 — G2-B tentativa descartável 3 encerrada, guest ainda ligado

- candidate exato: `fbef3d4`;
- o cloud-init do guest concluiu e Docker ficou ativo;
- o limitador de recursos do container foi aplicado: 5 CPUs e 8 GiB;
- o harness terminou com status `2` em `apply_g2b`;
- último marcador: `G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0`;
- nenhum dos 13 marcadores de aceite foi comprovado nesta tentativa;
- não existe processo de harness/Ansible ainda executando;
- a VM e seu diretório efêmero devem ser removidos somente depois de preservar a
  evidência sanitizada e identificar a causa do `EXIT_2`.

#### INC-003 — SSH direto local sem identidade carregada

O alias `contabo-vps` está configurado, mas o `ssh-agent` local não possui a
chave dedicada carregada. O teste direto retorna `Permission denied
(publickey)`. Isso é um bloqueio do cliente local, não indisponibilidade da VPS.
Nunca registrar nem enviar a passphrase; quando o acesso direto for necessário,
LEANDRO carrega a chave localmente com `ssh-add`.

#### INC-004 — RESOLVIDO em 29/08 — systemd-networkd convergence

- causa funcional comprovada: ausência da rota conectada `169.58.128.0/17` mantinha `eth0` em `configuring` e `wait-online` em timeout;
- agente exato que removeu a rota conectada: `NÃO VERIFICADO`;
- `staticroute` originado em NoCloud/cloud-init foi preservado e não foi provado como causa única;
- correção mínima: host-route `169.58.128.1/32 scope link`, sem restaurar o `/17` inteiro;
- candidato `682c3e55d835ebea4bcc2edd297a8b819b2df434`, PRs #42/#43, static/KVM hospedados PASS;
- rollout live autorizado concluiu `RECOVERED`, `AdministrativeState=configured` e wait-online PASS sem restart do networkd;
- autorização P2 one-shot consumida; reboot continua não autorizado.

## Onde está cada parte do trabalho

Esta tabela é o inventário de reconciliação. Nenhum item listado como local ou
experimental deve ser apagado, resetado ou mesclado sem classificação prévia.

| Local/ref | Estado | Conteúdo e decisão |
|---|---|---|
| GitHub `main` — `3621a6d` antes desta reconciliação | limpo, porém incompleto | baseline histórica, Cloud Workstation e provas temporárias; não contém a implementação integral das branches abaixo |
| `fix/f1-2c-systemd-runtime-lock` — GitHub | lineage funcional em `badad65` | F1.2c (`baaf839...`) + NETWORK_CONVERGENCE_P2 (`682c3e55...`) integrados via PRs #39/#40/#42/#43; `main` ainda não importa código funcional |
| `codex/mission-001-f1-2c-network-enforcement` — GitHub | branch de implementação | F1.1/F1.2b e desired state F1.2c; base da PR #9 |
| `mcf/mission-001-control-bridge-g1` — GitHub | G1/G2-A comprovados | roundtrip e leitura real do NODE-01; [PR #3](https://github.com/leon337/cloud-infrastructure/pull/3) aberta |
| `codex/control-bridge-g2b` — VPS/GitHub | limpo em `fbef3d4` | G2-B Tasks 1–7, continuidade R1–R8 e correções das tentativas 1–3; [PR #11](https://github.com/leon337/cloud-infrastructure/pull/11) draft |
| worktree local `cloud-infrastructure-control-bridge-g2b` | divergente e staged | 1 commit local exclusivo, 87 commits atrás do remoto e 1.337 linhas staged do adaptador SSH; não rebasear nem descartar antes de extrair/salvar o delta |
| clone local `/home/leo/cloud-infrastructure` | obsoleto | `main` em `160edc7`, cinco screenshots não rastreados; tratar como arquivo histórico, não como fonte de verdade |
| clone local `implementacao_vps` | antigo e limpo | branch F1.2c em `b4cdc9d`; substituído pelos worktrees mais novos |
| MCF local principal | desatualizado | branch de intake em `162c25c`, relatório não rastreado; `main` remoto observado em `87c7f24` |
| worktree `multiagent-collaboration-framework-vps-continuity` | 39 entradas não commitadas | PostgreSQL/fila/worker Codex experimental; arquitetura rejeitada porque substituiria o MESTRE/ChatGPT; **não implantar** |
| container local `mcf-continuity-pg-20260822` | artefato de teste | PostgreSQL descartável do experimento rejeitado; não existe prova de implantação na VPS |

### Problema local adicional do MCF

O fetch do clone MCF local falha por uma referência Git malformada em
`refs/codex/turn-diffs/.../base`. Nenhuma referência foi removida durante esta
reconciliação. Corrigir esse metadata em uma tarefa separada, depois de fazer
backup/inspeção do ref, para não perder trabalho do usuário.

## Arquitetura e ownership atuais

| Frente | Autoridade | Coordenação atual | Regra |
|---|---|---|---|
| Segurança, produção e HUMAN_GATE | LEANDRO | LEANDRO | decisão humana final |
| Sequenciamento da implementação da VPS | LEANDRO | Codex nesta retomada | auditar, preservar e consolidar antes de mutar |
| F1.2c | LEANDRO | MESTRE | rollout live verificado; lineage funcional permanece isolada até integração mainline revisada |
| Control Bridge G2-B | LEANDRO | Codex retomando a execução técnica | VPS/GitHub `fbef3d4` é a linha remota mais avançada |
| MESTRE/ChatGPT e equipe MCF | LEANDRO | MESTRE | agentes consumidores do bridge; não recebem root/shell arbitrário |
| Experimento MCF com worker Codex autônomo | nenhum rollout autorizado | nenhum | rejeitado para esta missão; Codex não substitui o MESTRE |

## Capacidades do Control Bridge

| Gate | Estado | Evidência/limite |
|---|---|---|
| G1 — transporte | `[x] PASS` | runner real executa probes curtos e publica resultado |
| G2-A — leitura | `[x] PASS` | list/read/stat e Git read-only; escape de path recusado |
| G2-B Tasks 1–6 | `[x] COMPLETE` | contratos, escrita atômica confinada, lock, dedupe, auditoria, rollback, revogação e boundary sudo |
| G2-B Task 7 | `[x] COMPLETE` | bootstrap idempotente; 7 testes focados e 3 syntax checks Ansible passaram |
| G2-B Task 8 | `[ ] FAILED_ATTEMPT_3` | prova descartável integral ainda não passou |
| G2-B Task 9 | `[ ] NOT_STARTED` | publicar candidato revisado e parar no gate real do NODE-01 |
| G2-B Task 10 | `[ ] NOT_STARTED` | piloto real: write → audit → rollback → revoke → refusal |
| Uso efetivo pelo MCF | `[ ] NOT_PROVEN` | leitura existe; escrita real e retomada pelo MESTRE não foram aceitas |
| Merge do G2-B | `[ ] NOT_ELIGIBLE` | somente após Tasks 8–10 e evidência de aceite |

O G2-B atual é deliberadamente limitado ao piloto
`leon337/g2a-smoke/dev/G2B-PILOT.txt`, com grant de 24 horas e uma única mutação
ativa. Ele não fornece shell arbitrário, Docker socket, sudo genérico, root,
administração de host nem escrita Git.

## Checklist cronológico

Um `[x]` significa que o marco possui evidência compatível com a afirmação. Um
item parcial ou bloqueado permanece `[ ]`, mesmo quando existe código.

- [x] **14/08 — Fundação documental e inventário:** repositório isolado, PUC v1,
  histórico, findings e primeira baseline da VPS.
- [x] **15/08 — Acesso e recuperação:** chave dedicada, SSH publickey-only,
  root/password desabilitados, UFW/fail2ban, sudo autenticado, LXD removido da
  superfície root-equivalent e backup sanitizado.
- [x] **15/08 — Cloud Workstation:** XFCE/LightDM/XRDP em loopback, túnel SSH,
  Firefox, VS Code, reconexão, persistência e reboot validados.
- [x] **16/08 — Platform Discovery:** Q1–Q39 consolidadas; Q40-D autorizou
  seleção tecnológica e implementação incremental DEV/lab.
- [x] **16/08 — Mission Acceptance/Recovery:** baseline, arquitetura, threat
  model, blueprint, roadmap e Technology Mapping produzidos nas branches de
  implementação.
- [x] **17/08 — F1.1 Foundations:** apply real, idempotência e invariância
  comprovados no NODE-01.
- [x] **17/08 — F1.2b Docker boundary:** Docker/containerd aplicados, reiniciados
  e reconciliados com runtime vazio.
- [x] **17–28/08 — F1.2c Network Enforcement:** falha histórica reproduzida e recovery
  fail-closed corrigido; rollout live autorizado do candidato `baaf839...` terminou
  `RECOVERED`, com serviço/helper/base/rede privada pós-apply verificados.
- [x] **18/08 — Control Bridge G1:** primeiro handshake e roundtrip real pelo
  self-hosted runner.
- [x] **19/08 — Control Bridge G2-A:** leitura real do workspace, Git read-only,
  isolamento e recusa de path escape comprovados.
- [x] **20–22/08 — G2-B Tasks 1–7:** implementação confinada, recovery de crash,
  bootstrap idempotente e validações focadas concluídos.
- [x] **20–22/08 — Continuidade R1–R8:** protocolo de retomada, checkpoints
  remotos, memória institucional, drift checker e cold-start repository-only
  documentados na branch G2-B.
- [ ] **22/08 — G2-B Task 8 tentativa 1:** `EXIT_9`; fixture não tolerava usuário
  `ubuntu` preexistente; correção commitada.
- [ ] **22/08 — G2-B Task 8 tentativa 2:** `EXIT_2`; `/usr/local/libexec`
  ausente no guest limpo; correção commitada.
- [ ] **22/08 — G2-B Task 8 tentativa 3:** `EXIT_2` em `apply_g2b`; causa ainda
  não classificada; guest descartável permanece ligado para preservação.
- [x] **22/08 — PTY persistente experimental:** `Hello World` e o mesmo
  PID/socket foram observados por jobs independentes; prova de processo
  desacoplado, não de orquestração autônoma do ChatGPT.
- [x] **22/08 — Incidente do runner:** removidos workflows de espera longa que
  ocupavam o único runner e criavam latência artificial.
- [x] **22/08 — Reconciliação atual:** GitHub, computador local e VPS auditados;
  worktrees divergentes e incidentes abertos registrados neste painel.
- [x] **28/08 — RECOVERY-P1:** backup sanitizado atual sincronizado off-host para o
  notebook com SHA-256 origem/destino idêntico; path/link safety e restore smoke `PASS`.
  O escopo cobre os artefatos definidos, não restore integral/bare-metal da VPS.
- [x] **28/08 — RECOVERY-P2:** pull off-host diário, runtime overlay allowlisted,
  manifest, hashes, secret scan e restore smoke automatizados; execução real pelo
  `systemd --user` validada e PR #28 integrada. Full-image/provider DR permanece
  `NÃO VERIFICADO`.
- [x] **28/08 — Governança documental:** `README.md` preservado como painel executivo
  canônico da missão IMPLEMENTAÇÃO DA VPS; `ROADMAP-CHECKLIST.md` adotado como checklist
  operacional subordinado, com contratos de CI contra inversão da hierarquia; PRs #29/#30
  integradas.
- [x] **28/08 — RUNNER-ISOLATION-P1:** causa raiz confirmada (`unset RUNNER_TRACKING_ID`
  + `nohup setsid` na lineage histórica), PoC live retirado, recovery ajustado, policy/guard
  canônicos adicionados e prova real cross-job `PASS`. Hook global configurado, mas ainda
  não carregado por restart privilegiado pendente.
- [x] **28/08 — SSH_KEY_GOVERNANCE_P1:** provenance e uso histórico confirmados; LEANDRO
  confirmou dependência atual no fluxo notebook→VPS. A chave será mantida, `authorized_keys`
  permanece inalterado e o fallback independente fica apenas como contingência. Hardening
  futuro deve preservar o acesso interativo atual.

## Roadmap operacional

### P0-A — Conter e fechar o estado vivo atual

- [ ] preservar evidência sanitizada da tentativa G2-B 3;
- [ ] diagnosticar a causa exata de `apply_g2b exit=2` sem repetir a mutação;
- [ ] encerrar a QEMU `g2b-disposable-task8-vm3` e remover somente o diretório
  efêmero validado, após preservar a evidência;
- [ ] confirmar que CPU/RAM e porta local `22284` foram liberadas;
- [x] coletar diagnóstico read-only/root da unit e classificar o estado parcial F1.2c;
- [x] corrigir o recovery F1.2c em lineage isolada sem sobrescrever trabalho local; PRs #39/#40 integradas na lineage.

### P0-B — Concluir as chaves controladas do prédio

- [ ] criar teste de regressão para a causa da tentativa 3;
- [ ] executar nova VM Ubuntu 24.04/systemd descartável com candidate limpo;
- [ ] exigir os 13 marcadores G2-B, em ordem e uma única vez;
- [ ] comprovar write, replay idempotente, conflito de request ID, exclusão
  mútua, auditoria, rollback, estado final, revogação e recusa pós-revogação;
- [ ] concluir Task 9 e publicar candidato revisado sem bootstrap real;
- [ ] parar no HUMAN_GATE da Task 10;
- [ ] após autorização específica, executar o piloto real no NODE-01;
- [ ] comprovar o uso efetivo do canal por MESTRE/MCF;
- [ ] somente então tornar a PR #11 elegível para merge.

### P0-C — Tornar `main` realmente canônica

- [ ] salvar/classificar o delta staged do worktree G2-B local;
- [ ] reconciliar o commit local exclusivo com os 87 commits remotos;
- [ ] fechar ou arquivar clones antigos sem apagar screenshots/relatórios;
- [ ] integrar em ordem revisada F1.1/F1.2b/F1.2c, G1/G2-A e G2-B;
- [ ] atualizar `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml` no mesmo
  merge que alterar o estado aceito;
- [ ] executar verificação de links, secrets, estado e suíte aplicável;
- [ ] remover branches temporárias somente após confirmar ancestry e evidência.

### P1 — Finalizar a fundação da plataforma DEV/lab

- [x] **F1.2c:** network services recuperados no NODE-01; precheck, backup/checkpoint, apply/check, KVM/idempotência e pós-validação live comprovados;
- [x] **NETWORK_CONVERGENCE_P2:** `eth0` convergiu para `configured`, gateway `/32` materializado e wait-online validado sem restart;
- [ ] **F1.2a:** Management Network — `WAITING_HUMAN_GATE`;
- [ ] **F1.3:** observabilidade mínima e accounting;
- [ ] **F1.4:** secret bootstrap foundation;
- [ ] **F1.5:** recuperação off-host — `WAITING_HUMAN_GATE`;
- [ ] **F1.6:** secrets operacionais — `WAITING_HUMAN_GATE`.

### P2 — Capability Core e execução durável

- [ ] F2.1 Capability Core skeleton;
- [ ] F2.2 PostgreSQL foundation;
- [ ] F2.3 identidade/escopo;
- [ ] F2.4 Node Agent e recursos;
- [ ] F3.1 Durable Workflow;
- [ ] F3.2 Event Backbone;
- [ ] F3.3 mensageria de aplicação.

### P3 — Dados, entrega, agentes e recovery

- [ ] F4 Data/Artifact Plane;
- [ ] F5 runner/build isolation, pipeline DEV, sandboxes, preview e DNS/TLS;
- [ ] F6 Agent Gateway, MCP/API/CLI e Model Gateway;
- [ ] F7 segurança contínua, recovery integrado, rebuild drill e fechamento de
  findings.

O detalhamento operacional da missão **IMPLEMENTAÇÃO DA VPS** é acompanhado em
[`ROADMAP-CHECKLIST.md`](ROADMAP-CHECKLIST.md), subordinado a este painel executivo.
O roadmap técnico detalhado histórico continua disponível na lineage de implementação,
mas não deve ser usado como fonte de estado atual quando divergir deste README, do
checklist da missão ou de evidência GitHub/provider/live.

## HUMAN_GATEs vigentes

- carregar a chave SSH local quando o acesso direto for necessário;
- qualquer bootstrap/grant/write real da G2-B no NODE-01;
- promoção para produção externa;
- rotação de credenciais, enquanto a decisão de adiamento permanecer;
- Management Network, full-image/provider recovery e DNS/TLS conforme o
  roadmap detalhado;
- qualquer descarte de trabalho local que não esteja preservado por commit,
  patch ou backup verificável.

A limpeza da VM descartável da tentativa 3 não é promoção nem implantação: ela
faz parte do containment previsto no teste. Mesmo assim, deve ocorrer somente
depois da preservação da evidência e com alvo exato validado.

## Regras operacionais

- nunca versionar passwords, passphrases, chaves privadas, tokens, API keys,
  2FA, connection strings reais ou credenciais do provedor;
- não conceder shell root, sudo genérico, Docker socket ou credenciais
  administrativas permanentes a agentes;
- não usar o self-hosted runner para `sleep`, polling ou espera prolongada;
- processos longos devem rodar desacoplados na VPS, com estado e logs
  persistidos; o runner executa somente comandos curtos;
- antes de mutar: verificar identidade, branch/HEAD, worktree limpo ou delta
  preservado, lock, rollback e critério de aceite;
- não marcar `DONE` apenas porque o código existe;
- diferenciar sempre `observado agora`, `evidência histórica`, `parcial`,
  `bloqueado` e `não iniciado`.

## Finalidade permanente

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO
mantém autoridade humana final e aprende a administrar, diagnosticar, recuperar
e reconstruir o ambiente. A Cloud Workstation continua funcional como cockpit
humano opcional. O MCF poderá usar a infraestrutura, mas o repositório
`cloud-infrastructure` permanece separado do framework.
