# ROADMAP-CHECKLIST — Checklist operacional da missão IMPLEMENTAÇÃO DA VPS

<!-- IMPLEMENTACAO_DA_VPS_OPERATIONAL_CHECKLIST -->

Atualizado em **28/08/2026 14:14 -03:00**.

Este arquivo é o checklist operacional detalhado da missão **IMPLEMENTAÇÃO DA VPS** no
repositório `leon337/cloud-infrastructure`. Ele é **subordinado ao `README.md`**, que
permanece o painel executivo canônico e consolidado da missão. Este checklist não cria
uma autoridade paralela e não se aplica ao MCF como projeto separado.

Ele substitui apenas, para acompanhamento operacional detalhado desta missão, o antigo
checklist específico da lineage G2-B. Documentos históricos continuam preservados como
evidência.

## Hierarquia e atualização

Para decisões e fatos mutáveis, aplicar esta precedência:

1. instrução atual explícita de LEANDRO;
2. GitHub/provider/infraestrutura verificável ao vivo;
3. evidência executável vinculada ao estado/SHA aplicável;
4. `README.md` como painel executivo da missão;
5. este checklist para detalhamento operacional da mesma missão;
6. `state/current.yaml`, `CHECKPOINT.md` e `CONTEXT.md` como projeções de apoio;
7. documentos históricos.

**Regra de closeout:** toda sub-missão da IMPLEMENTAÇÃO DA VPS que mudar o estado de
um item deste checklist deve atualizar o item e sua evidência antes do closeout. Mudanças
fora desta missão não devem ser inseridas aqui automaticamente.

Legenda:

- `[x]` concluído e com evidência compatível;
- `[ ]` pendente;
- `[!]` bloqueado ou requer gate;
- `NÃO VERIFICADO` significa que não há evidência suficiente para afirmar o estado.

Baseline usada nesta correção de hierarquia: `main@f06cebd1998300e2b85126ffc88349b4253ea3b3`
(PR #29 integrada). O HEAD atual de `main` deve sempre ser confirmado no GitHub.

## 1. Inventário e baseline

- [x] VPS identificada como `vmi3506102`, Ubuntu 24.04.4 LTS.
- [x] 8 vCPU, ~23 GiB RAM e ~300 GiB de disco inventariados.
- [x] Rede, IPs, listeners e serviços systemd inventariados.
- [x] Docker/containerd, Cloud Workstation, GitHub Actions Runner e SentinelX detectados.
- [x] Logs, crashes, reboot pendente e backup local inventariados.

**Estado:** `INVENTORY_BASELINE_COMPLETE`.

## 2. Recovery / backup — RECOVERY-P1 + RECOVERY-P2

- [x] Backup local diário da VPS validado por SHA-256.
- [x] Backup atual sincronizado para off-host.
- [x] Restore smoke do archive sanitizado executado com sucesso.
- [x] Path safety e link safety dos archives validados.
- [x] Overlay runtime allowlisted implementado.
- [x] `RECOVERY-MANIFEST.txt`, `runtime-state.txt` e `SHA256SUMS` implementados.
- [x] Secret scan fail-closed implementado.
- [x] Timer off-host `systemd --user` ativo, enabled e waiting.
- [x] Execução real pelo serviço: `Result=success`, `ExecMainStatus=0`.
- [x] GitHub-hosted `canonical-validation` do candidato RECOVERY-P2: SUCCESS.
- [x] PR #28 integrada; merge commit `bbdc7b2a3874af75424680c49aed3cbcb8d63bcb`.
- [ ] Snapshot/bare-metal recovery do provider Contabo.
- [ ] Restore integral de imagem da VPS.

**Estado:** `RECOVERY_COVERED_COMPONENTS_VERIFIED`; full-image DR `NÃO VERIFICADO`.

## 3. Runner isolation — P1

- [x] `mcf-mission2-terminal.py` persistente identificado e provenance exata preservada.
- [x] Causa raiz confirmada: workflow histórico executava `unset RUNNER_TRACKING_ID` + `nohup setsid`.
- [x] Lineage atual do Control Bridge já não contém o passo persistente; runner estava idle antes da limpeza.
- [x] Não foram observados nomes explícitos de tokens sensíveis no ambiente preservado; valores não foram coletados.
- [x] Daemon legado encerrado de forma controlada; socket, PID file e source live removidos.
- [x] `scripts/check_runner_isolation.py` bloqueia manipulação de `RUNNER_TRACKING_ID` e self-hosted workflow sem guard.
- [x] Guard obrigatório aplicado aos workflows self-hosted canônicos.
- [x] Prova real em dois jobs no mesmo `node--1-mcf-control`: `RUNNER_ISOLATION_CROSS_JOB=PASS`.
- [x] Recovery off-host revalidado sem preservar o daemon legado (`RECOVERY_P2=PASS`).
- [ ] Ativar hooks globais `ACTIONS_RUNNER_HOOK_JOB_STARTED/COMPLETED` após restart autorizado do serviço; configuração já instalada, mas ainda não carregada.

**Estado:** `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING`.

**Próximo passo exato da missão:** `SSH_KEY_GOVERNANCE_P1`.

## 4. Governança de chaves SSH — P1

- [x] Quatro entradas em `authorized_keys` inventariadas.
- [x] Duas chaves administrativas históricas reconhecidas.
- [x] `mcf-ox-display10` confirmada com loopback + forced command/restrict.
- [x] `dsh-tunnel-leo-N43SM-to-vmi3506102` identificada e comando de inclusão localizado.
- [x] Owner/origem operacional da `dsh-tunnel...` correlacionados ao caminho administrativo do notebook por histórico do `ubuntu` + fingerprint em auth log.
- [x] LEANDRO confirmou dependência atual: a chave é usada para abrir/acessar a VPS pelo notebook (`CONFIRMED_BY_LEANDRO_USER_WORKFLOW`).
- [x] Fallback independente comprovado com chave administrativa distinta (`PASS_INDEPENDENT_KEY`), classificado apenas como contingência.
- [x] Decisão operacional: manter a `dsh-tunnel...` para preservar o fluxo notebook→VPS; `authorized_keys` permanece inalterado.
- [!] Qualquer hardening/restrição futura deve primeiro provar que preserva o acesso interativo atual.
- [x] Provenance e correção da dependência registradas em `evidence/ssh-key-governance/SSH-KEY-GOVERNANCE-P1-20260828.md`.

**Estado:** `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`.

**Próximo passo exato:** `NETWORK_CONVERGENCE_P2`.

## 5. F1.2c / Cloud Platform Network Services — P1

- [x] Falha histórica de runtime lock sob filesystem protegido reproduzida e classificada.
- [x] Recovery fail-closed específico implementado; PR #35 integrou a primeira versão na lineage.
- [x] Falso `foundation_marker_drift` identificado: recovery/KVM usavam markers simplificados; PR #39 alinhou aos markers canônicos reais.
- [x] `partial_state_mismatch` decomposto predicate-by-predicate; única divergência persistente era a suposta ausência de `/etc/cloud-platform/network-services`.
- [x] Diagnóstico root provou baseline `EXACT_PRESENT`: diretórios/arquivos canônicos, metadata exata, shape exato e sete hashes corretos; o preflight não privilegiado anterior sofreu falso negativo por traversal permission.
- [x] PR #40 adicionou variantes `ABSENT`/`EXACT_PRESENT`, checkpoint da baseline, rollback simétrico, rejeição de extras e não reescrita de config já exata.
- [x] Candidato exato: `baaf83908e8e83264baafc032434a4df1952450b`; lineage após merge da PR #40: `2408aed4ac8dbe692912a8d806852a45d9a97c49`.
- [x] Local: contratos `10/10`, suíte `152/152`, Markdown/YAML/manifests/state/status/compile/shell/diff = PASS.
- [x] GitHub-hosted static + ShellCheck run `33217692498` = SUCCESS.
- [x] GitHub-hosted KVM run `33217692536` = SUCCESS para `baseline_config=absent` e `baseline_config=exact_present`, incluindo historical failure, precheck, apply, check, idempotência, rollback e cleanup.
- [!] `foundation-ci` / `docker-boundary-ci` genéricos continuam `FAIL — PREEXISTING_HISTORY_ONLY_GATE`; nenhum arquivo novo da PR apareceu nos achados históricos.
- [x] LEANDRO autorizou one-shot o rollout do SHA exato `baaf839...`.
- [x] Precheck live em `2026-08-28T22:52:55Z`: `RECOVERY_PRECHECK=PASS state=KNOWN_PARTIAL baseline_config=EXACT_PRESENT`.
- [x] Checkpoint root-owned + backup pré-apply criados em `2026-08-28T22:55:37Z`; sidecar SHA-256 do backup validou `OK`.
- [x] Apply + recovery check concluídos; state root-owned = `RECOVERED`.
- [x] Pós-validação root independente: `F1_2C_POSTVERIFY=PASS`, serviço `active+enabled`, helper/base checks PASS, IPv4/IPv6 forwarding `1/0` e ausência de listeners públicos gerenciados.
- [x] Superfície privada observada: `cp00000001/02/03` + `cpeg0001`, rotas 10.240.1/2/3/254, containers `4`, images `2`, volumes `0`, custom networks `4`.
- [x] Evidência sanitizada: `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`.
- [!] A autorização foi consumida; não existe autorização permanente para novo reapply.

**Estado:** `COMPLETE_LIVE_VERIFIED`; F1.2c aceito tecnicamente no NODE-01. Próxima frente: `NETWORK_CONVERGENCE_P2`.

## 6. Rede / systemd-networkd — P2

- [x] `eth0` operacional/routable observado com `AdministrativeState=configuring`.
- [x] Dois predicates reais de `systemd-networkd-wait-online` reproduzidos em timeout.
- [x] Causa funcional reproduzida em KVM: rota conectada `169.58.128.0/17` ausente; agente que a removeu = `NÃO VERIFICADO`.
- [x] Netplan/networkd efetivo validado; `staticroute` NoCloud/cloud-init preservado.
- [x] Correção mínima validada: `169.58.128.1/32 scope link`, sem restaurar o `/17` inteiro.
- [x] PRs #42/#43, static + KVM hospedados PASS; candidato live `682c3e55d835ebea4bcc2edd297a8b819b2df434`.
- [x] Precheck, backup/checkpoint, apply/check e pós-validação independentes PASS.
- [x] `eth0 AdministrativeState=configured` e ambos `wait-online` PASS; networkd não reiniciado.
- [x] Evidência: `evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`.

**Estado:** `COMPLETE_LIVE_VERIFIED`; próxima etapa: `PRE_REBOOT_CHECKPOINT`.

## 7. Kernel / atualização / reboot — P2

- [x] `reboot-required` confirmado.
- [x] Kernel atual e kernel novo pendente inventariados.
- [x] Pacotes atualizáveis inventariados.
- [x] `Spec rstack overflow` reportado pelo kernel foi registrado.
- [x] F1.2c e `NETWORK_CONVERGENCE_P2` foram fechados com evidência live.
- [x] `PRE_REBOOT_CHECKPOINT` V2 criado, SHA interno/externo e cópia off-host verificados; V1 rejeitado e preservado como evidência.
- [ ] Executar update/reboot controlado somente após gate humano separado.
- [ ] Validar SSH, rede, firewall, Docker, Runner, SentinelX, XRDP e backup pós-reboot.

**Estado:** `WAITING_HUMAN_GATE_FOR_UPDATE_AND_CONTROLLED_REBOOT`.

## 8. Segurança / firewall

- [x] UFW, Fail2ban e AppArmor ativos na auditoria.
- [x] Snapshot efetivo: `INPUT DROP`, `FORWARD DROP`, `OUTPUT ACCEPT`.
- [x] TCP/22 como regra explícita de entrada; RDP loopback-only.
- [x] SSH root/password authentication desabilitados.
- [x] `ubuntu` sem NOPASSWD genérico.
- [x] Boundary `sentinelx -> mcf-hermes-operator` identificado como restrito ao wrapper.
- [ ] Bans/jails Fail2ban live com privilégio.
- [ ] Firewall/snapshot/recovery nativo do provider Contabo.
- [ ] Auditoria privilegiada final após saneamento.

**Estado:** `SECURITY_BASELINE_GOOD_WITH_PRIVILEGED_VISIBILITY_GAPS`.

## 9. Docker / workloads

- [x] Docker e containerd ativos.
- [x] `ubuntu` fora do grupo Docker.
- [!] Post-F1.2c: contagem root verificada em containers `4`, images `2`, volumes `0`, custom networks `4`; isto não substitui inventário semântico por workload.
- [ ] Mapear owner/projeto, restart policies e persistência de cada workload.
- [ ] Definir recovery apropriado por workload.

**Estado:** `DOCKER_DEEP_INVENTORY_PENDING`.

## 10. Cloud Workstation / XRDP

- [x] XRDP e LightDM ativos; RDP restrito a loopback.
- [x] Acúmulo de sessões Xorg/XFCE observado.
- [x] Erros XRDP/sesman quantificados na auditoria.
- [ ] Identificar sessões realmente ativas e órfãs.
- [ ] Implementar lifecycle/cleanup de sessão.
- [ ] Validar novo login/logout limpo e consumo após cleanup.

**Estado:** `XRDP_SESSION_LIFECYCLE_DEBT`.

## 11. Firefox / desktop

- [x] 26 segfaults históricos `libxul.so` identificados.
- [x] Crash file identificado.
- [x] Nenhum novo segfault `libxul` observado nas 48h da auditoria.
- [ ] Revisar estabilidade após atualização/reboot.

**Estado:** `HISTORICAL_CRASH_MONITOR`.

## 12. Estado canônico e documentação

- [x] `README.md` preservado como painel executivo canônico e consolidado da missão **IMPLEMENTAÇÃO DA VPS**.
- [x] `ROADMAP-CHECKLIST.md` adotado somente como checklist operacional detalhado, subordinado ao README e restrito à missão.
- [x] `state/current.yaml` codifica `README.md` como `canonical_executive_panel` e o checklist como `SUBORDINATE_TO_README_EXECUTIVE_PANEL`.
- [x] `CHECKPOINT.md` classificado como checkpoint de continuidade, sem autoridade executiva concorrente.
- [x] CI exige os marcadores distintos de README/checklist, o escopo `IMPLEMENTACAO_DA_VPS_ONLY` e rejeita a antiga autodeclaração `CANONICAL_OPERATIONAL_CHECKLIST`.
- [ ] Reconciliar integralmente subseções históricas de `state/current.yaml` que ainda representam frentes antigas.
- [ ] Atualizar Capsule/Capability Registry quando a reconciliação cross-repo for retomada.
- [ ] Registrar ownership canônico dos runtimes live não pertencentes ao core Cloud.

**Estado:** `MISSION_DOCUMENT_HIERARCHY_RECONCILED_LEGACY_STATE_RECONCILIATION_PENDING`.

## 13. PR / branch hygiene

- [x] Dívida de PRs históricas identificada.
- [ ] Classificar PRs legadas como `ACTIVE`, `SUPERSEDED`, `HISTORICAL` ou `DO_NOT_MERGE`.
- [ ] Fechar somente PRs comprovadamente superseded, sem apagar evidência necessária.
- [ ] Revisar branches antigas após classificação das PRs.

**Estado:** `REPOSITORY_GOVERNANCE_DEBT_PENDING`.

## Ordem operacional vigente

```text
RECOVERY-P1                         DONE
RECOVERY-P2                         DONE
RUNNER_ISOLATION_P1                 DONE_CROSS_JOB / GLOBAL_HOOK_HARDENING_PENDING
SSH_KEY_GOVERNANCE_P1               DONE_KEEP_CURRENT_USER_WORKFLOW
F1_2C_NODE01_ROLLOUT                DONE / LIVE_VERIFIED
NETWORK_CONVERGENCE_P2              DONE / LIVE_VERIFIED
PRE_REBOOT_CHECKPOINT               DONE / VERIFIED_OFFHOST
UPDATE_AND_CONTROLLED_REBOOT        WAITING_HUMAN_GATE
POST_REBOOT_VALIDATION              PENDING
CANONICAL_STATE_AND_PR_HYGIENE      PENDING
FINAL_AUDIT                         PENDING
```

## Evidência de atualização

Ao concluir uma missão, registrar neste arquivo pelo menos:

- status anterior -> status novo;
- data da validação;
- PR/commit ou evidência live aplicável;
- pendências remanescentes;
- `NÃO VERIFICADO` para qualquer ponto sem prova suficiente.
