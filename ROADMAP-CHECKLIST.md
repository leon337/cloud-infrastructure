# ROADMAP-CHECKLIST — Estado operacional canônico da VPS

<!-- CANONICAL_OPERATIONAL_CHECKLIST -->

Atualizado em **28/08/2026 07:40 -03:00**.

Este arquivo é a projeção operacional canônica do projeto `leon337/cloud-infrastructure`.
Ele substitui, para acompanhamento de estado atual, o antigo checklist específico da
lineage G2-B. Documentos históricos continuam preservados como evidência, mas não
devem sobrescrever este checklist quando houver divergência com GitHub/live evidence.

## Regras de autoridade e atualização

Ordem de precedência para estado mutável:

1. instrução atual explícita de LEANDRO;
2. GitHub/provider/live evidence;
3. este checklist, atualizado contra essa evidência;
4. `state/current.yaml` e `CHECKPOINT.md`;
5. documentos históricos.

**Regra de closeout:** toda missão que mudar o estado de um item deste checklist deve
atualizar o próprio item e sua evidência no mesmo PR de integração ou em follow-up
obrigatório antes de declarar o estado consolidado como atual.

Legenda:

- `[x]` concluído e com evidência compatível;
- `[ ]` pendente;
- `[!]` bloqueado ou requer gate;
- `NÃO VERIFICADO` significa que não há evidência suficiente para afirmar o estado.

Baseline usada nesta reconciliação: `main@bbdc7b2a3874af75424680c49aed3cbcb8d63bcb`
(PR #28 já integrada). O HEAD atual de `main` deve sempre ser confirmado no GitHub.

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

- [x] `mcf-mission2-terminal.py` persistente identificado.
- [x] Shell filho e Unix socket persistentes confirmados.
- [x] Reuso do mesmo workspace por branch posterior confirmado.
- [x] Não foram observados nomes explícitos de tokens sensíveis no ambiente preservado.
- [ ] Confirmar se alguma missão ativa ainda depende do daemon.
- [ ] Encerrar daemon/shell de forma controlada.
- [ ] Remover socket residual.
- [ ] Implementar cleanup obrigatório ao final de jobs.
- [ ] Testar que nenhum processo de job atravessa execuções futuras.

**Próximo passo exato:** `RUNNER_ISOLATION_P1`.

## 4. Governança de chaves SSH — P1

- [x] Quatro entradas em `authorized_keys` inventariadas.
- [x] Duas chaves administrativas históricas reconhecidas.
- [x] `mcf-ox-display10` confirmada com loopback + forced command/restrict.
- [x] `dsh-tunnel-leo-N43SM-to-vmi3506102` identificada e comando de inclusão localizado.
- [ ] Determinar owner/origem operacional definitiva da `dsh-tunnel...`.
- [ ] Confirmar necessidade atual.
- [ ] Restringir o boundary ou remover somente após validar fallback.
- [ ] Registrar provenance/gate.

**Estado:** `SSH_KEY_GOVERNANCE_P1_PENDING`.

## 5. F1.2c / Cloud Platform Network Services — P1

- [x] `cloud-platform-network-services.service` confirmado em FAILED no live audit.
- [x] Falha de runtime lock sob filesystem protegido observada.
- [x] Lineage de correção validada em KVM localizada no GitHub.
- [x] Confirmado que o rollout no NODE-01 permaneceu separado da validação.
- [ ] Fixar SHA exato do rollout autorizado.
- [ ] Executar precheck live e checkpoint/rollback.
- [!] Reapply NODE-01 requer gate próprio antes de alteração privilegiada/material.
- [ ] Validar serviço e `systemctl --failed` pós-apply.

**Estado:** `REQUIRES_REVIEW`; rollout live pendente.

## 6. Rede / systemd-networkd — P2

- [x] `eth0` operacional/routable observado.
- [x] `SetupState=configuring` observado.
- [x] `systemd-networkd-wait-online` com timeouts recorrentes observado.
- [ ] Identificar causa de não convergência.
- [ ] Validar netplan/networkd efetivo.
- [ ] Corrigir somente após diagnóstico.
- [ ] Confirmar `wait-online` saudável antes de reboot.

**Estado:** `NETWORK_CONVERGENCE_P2_PENDING`.

## 7. Kernel / atualização / reboot — P2

- [x] `reboot-required` confirmado.
- [x] Kernel atual e kernel novo pendente inventariados.
- [x] Pacotes atualizáveis inventariados.
- [x] `Spec rstack overflow` reportado pelo kernel foi registrado.
- [!] Não rebootar antes de fechar recovery, F1.2c e network convergence.
- [ ] Criar checkpoint pré-reboot.
- [ ] Executar reboot controlado quando autorizado.
- [ ] Validar SSH, rede, firewall, Docker, Runner, SentinelX, XRDP e backup pós-reboot.

**Estado:** `REBOOT_BLOCKED_BY_PRECONDITIONS`.

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
- [ ] Inventário completo de containers, imagens e volumes.
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

- [x] `ROADMAP-CHECKLIST.md` adotado como projeção operacional canônica.
- [x] `state/current.yaml` atualizado para reconhecer a adoção.
- [x] `CHECKPOINT.md` atualizado para apontar este checklist como fonte operacional.
- [x] CI passa a exigir checklist presente quando status for `ADOPTED`.
- [ ] Reconciliar integralmente subseções históricas de `state/current.yaml` que ainda representam frentes antigas.
- [ ] Atualizar Capsule/Capability Registry quando a reconciliação cross-repo for retomada.
- [ ] Registrar ownership canônico dos runtimes live não pertencentes ao core Cloud.

**Estado:** `CHECKLIST_CANONICALIZED_LEGACY_STATE_RECONCILIATION_PENDING`.

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
RUNNER_ISOLATION_P1                 NEXT
SSH_KEY_GOVERNANCE_P1               PENDING
F1_2C_NODE01_ROLLOUT                PENDING / HUMAN_GATE
NETWORK_CONVERGENCE_P2              PENDING
UPDATE_AND_CONTROLLED_REBOOT        BLOCKED_BY_PRECONDITIONS
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
