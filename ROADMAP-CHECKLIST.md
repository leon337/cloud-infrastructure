# ROADMAP-CHECKLIST — Checklist operacional da missão IMPLEMENTAÇÃO DA VPS

<!-- IMPLEMENTACAO_DA_VPS_OPERATIONAL_CHECKLIST -->

Atualizado em **05/09/2026** pela reconciliação read-only da realidade live.

Este arquivo é o checklist operacional detalhado da missão **IMPLEMENTAÇÃO DA VPS** no
repositório `leon337/cloud-infrastructure`. Ele é **subordinado ao `README.md`**, que
permanece o painel executivo canônico. Não é autoridade paralela e não se aplica ao MCF
como projeto separado.

Precedência para fatos mutáveis:

1. instrução explícita atual de LEANDRO;
2. GitHub/provider/infraestrutura verificável ao vivo;
3. evidência executável vinculada a SHA/estado;
4. `README.md`;
5. este checklist;
6. `state/current.yaml`, `CHECKPOINT.md` e `CONTEXT.md`;
7. histórico.

Legenda: `[x]` concluído com evidência; `[ ]` pendente; `[!]` gate/bloqueio;
`NÃO VERIFICADO` = evidência insuficiente.

## 1. Inventário e baseline

- [x] NODE-01 identificado como `vmi3506102`, Ubuntu 24.04.4 LTS.
- [x] CPU/RAM/disco/rede/listeners/serviços inventariados.
- [x] Docker/containerd, runner, SentinelX e workstation identificados.
- [x] Auditoria de backups, reboot-required e superfície Git concluída.

**Estado:** `INVENTORY_BASELINE_COMPLETE`.

## 2. Recovery / backup — RECOVERY-P1 + RECOVERY-P2

- [x] Backup local diário com SHA-256.
- [x] Off-host recovery e restore smoke comprovados para componentes cobertos.
- [x] Path/link safety e secret scan fail-closed.
- [x] Execução automatizada de recovery validada.
- [x] Backup on-host mais recente observado nesta reconciliação: `cloud-infrastructure-config-20260905T030614Z.tar.gz`.
- [ ] Snapshot/bare-metal recovery do provider Contabo.
- [ ] Restore integral de imagem da VPS.

**Estado:** `RECOVERY_COVERED_COMPONENTS_VERIFIED`; full-image DR `NÃO VERIFICADO`.

## 3. Runner isolation — P1

- [x] PoC persistente legado identificado e retirado.
- [x] Policy canônica bloqueia `RUNNER_TRACKING_ID` bypass e exige guard em self-hosted.
- [x] Wrapper administrativo `.sh` ativado no runner real.
- [x] Run `33998487949`: STARTED/COMPLETED `RUNNER_ISOLATION_GUARD_PASS`.
- [x] Run `33998487949`: `RUNNER_ISOLATION_CROSS_JOB=PASS`.
- [x] PR #47 integrada; PR #48 fechou o gate residual.
- [x] `runner_isolation.next_exact_step=NONE`.

**Estado:** `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`.

## 4. Governança de chaves SSH — P1

- [x] `authorized_keys` inventariado e provenance relevante preservada.
- [x] LEANDRO confirmou dependência do fluxo notebook→VPS.
- [x] Fallback independente comprovado.
- [x] Decisão: manter a chave requerida pelo fluxo atual; `authorized_keys` inalterado.
- [!] Hardening futuro deve preservar acesso interativo notebook→VPS.

**Estado:** `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`.

## 5. F1.2c / Cloud Platform Network Services — P1

- [x] Falha histórica de runtime lock sob `ProtectSystem=strict` reproduzida/classificada.
- [x] Recovery fail-closed validado em CI estática + KVM.
- [x] Variantes de baseline parcial `ABSENT`/`EXACT_PRESENT` tratadas fail-closed.
- [x] Candidato live aplicado: `baaf83908e8e83264baafc032434a4df1952450b`.
- [x] Pós-validação root independente: recovery/check/base/helper PASS.
- [x] Serviço final `active+enabled`, não failed.
- [x] Releitura de 05/09: serviço ainda `active+enabled`, zero units failed.
- [x] Hash helper live `b69f41cd1c66000da239f39c09a46681afd5098a311065adf76b3c7aae35b9a3`.
- [x] Hash unit live `c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b`.
- [!] Autorização one-shot consumida; qualquer novo reapply exige novo gate.

Evidência: `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`.

**Estado:** `COMPLETE_LIVE_VERIFIED`.

## 6. Rede / systemd-networkd — NETWORK_CONVERGENCE_P2

- [x] Assinatura `eth0 configuring` + wait-online timeout reproduzida em KVM.
- [x] Causa funcional: ausência da rota IPv4 conectada reproduzida; agente que a removeu permanece `NOT_VERIFIED`.
- [x] Correção mínima: `169.58.128.1/32 scope link`, sem restaurar o `/17` conectado.
- [x] Candidato live aplicado: `682c3e55d835ebea4bcc2edd297a8b819b2df434`.
- [x] Postverify live: `AdministrativeState=configured` e wait-online PASS.
- [x] Releitura de 05/09: `eth0` `routable (configured)`, online, gateway `/32` presente.
- [x] `systemd-networkd-wait-online.service` observado active.
- [!] Autorização one-shot consumida; qualquer novo reapply exige novo gate.

Evidência: `evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`.

**Estado:** `COMPLETE_LIVE_VERIFIED`.

## 7. Kernel / checkpoint / update / reboot — P2

- [x] Checkpoint histórico V2 de 29/08 preservado como evidência.
- [x] Checkpoint pré-reboot read-only fresco coletado em 06/09.
- [x] Kernel atual `6.8.0-138-generic`; alvo `6.8.0-139.139` instalado.
- [x] `reboot-required=YES` para `linux-image-6.8.0-139-generic` + `linux-base`.
- [x] Zero units failed; F1.2c/rede/runner/serviços críticos ativos no checkpoint.
- [x] Backup on-host 06/09 `cloud-infrastructure-config-20260906T030657Z.tar.gz`: integridade PASS.
- [x] Recovery off-host de 05/09 revalidado: `SHA256SUMS` 6/6 PASS.
- [!] Recovery off-host de 06/09 ausente no momento da coleta; causa `NOT_VERIFIED`.
- [ ] Produzir/revalidar recovery off-host fresco para fechar o gate atual.
- [!] Depois, revalidar frescor mínimo do checkpoint conforme necessário.
- [!] Coordenar janela com owners externos de DeepSeek Harness e 9router.
- [!] Obter autorização humana explícita para updates/reboot.
- [ ] Executar update/reboot controlado somente após todos os gates.
- [ ] Executar validação pós-reboot completa.

**Estado:** `FRESH_READ_ONLY_VERIFIED_OFFHOST_FRESHNESS_GAP` + `BLOCKED_OFFHOST_RECOVERY_FRESHNESS_THEN_EXTERNAL_COORDINATION`.

**Próximo passo exato:** `PRE_REBOOT_OFFHOST_RECOVERY_FRESHNESS_GATE`.

## 8. SentinelX direto NODE-01 → hub

- [x] `sentinelx-cloud-core` observado active + enabled no NODE-01.
- [x] Conexões diretas ao hub observadas.
- [x] Oscilações recentes observadas: WebSocket `1006`, hub `1012`, HTTP `502`, seguidas de reconexão.
- [ ] Provar uma janela de conectividade persistente suficiente para o critério operacional.
- [ ] Identificar causa atual se a intermitência persistir; hoje `NOT_VERIFIED`.
- [!] Não reiniciar/patchar SentinelX como atalho nesta frente enquanto puder interferir em workloads externos.

**Estado:** `INTERMITTENT_NOT_CLOSED`.

## 9. Control Bridge G2-B

- [x] G1: `PASS_REAL_NODE_01_ROUNDTRIP`.
- [x] G2-A: `PASS_REAL_NODE_01_READ_ONLY`.
- [x] G2-B Tasks 1–7: `COMPLETE`.
- [x] Task 8 head `f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8`: 373/373 testes PASS.
- [x] Task 8: 13/13 marcadores de lifecycle comprovados; cleanup sem resíduos.
- [!] PR #21 permanece Draft e não integrada ao mainline aplicável.
- [ ] Task 9: não iniciada.
- [ ] Task 10: não iniciada.
- [!] Escrita G2-B real no NODE-01 continua `NOT_AUTHORIZED`.

**Estado Task 8:** `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.

## 10. Segurança / firewall

- [x] Baseline anterior: UFW/Fail2ban/AppArmor ativos; INPUT/FORWARD DROP; SSH key-only.
- [x] Nenhuma evidência de comprometimento confirmada na auditoria.
- [ ] Bans/jails Fail2ban com visibilidade privilegiada atual.
- [ ] Firewall/snapshot/recovery nativo do provider Contabo.
- [ ] Auditoria privilegiada final após os gates de manutenção.

**Estado:** `SECURITY_BASELINE_GOOD_WITH_PRIVILEGED_VISIBILITY_GAPS`.

## 11. Docker / workloads

- [x] Docker/containerd ativos na auditoria.
- [x] Quatro processos live confirmados em cgroups Docker: 2 CoreDNS + 2 Squid.
- [ ] Inventário semântico completo de containers/images/volumes/restart policies/owners.
- [ ] Definir recovery por workload.
- [!] DeepSeek Harness e 9router são `EXTERNALLY_MANAGED_OBSERVE_ONLY`; não modificar/reiniciar nesta missão.

**Estado:** `DOCKER_DEEP_INVENTORY_PENDING`.

## 12. Workstation / XRDP / desktop

- [x] XRDP/LightDM e RDP loopback-only inventariados.
- [x] Acúmulo de sessões e erros históricos quantificados.
- [ ] Classificar sessões ativas vs órfãs.
- [ ] Implementar lifecycle/cleanup em gate próprio.
- [ ] Revisar estabilidade Firefox/desktop após manutenção futura.

**Estado:** `XRDP_SESSION_LIFECYCLE_DEBT`.

## 13. Estado canônico / PR e branch hygiene

- [x] `README.md` permanece painel executivo canônico.
- [x] Este checklist permanece subordinado ao `README.md`.
- [x] Runner foi reconciliado e fechado em PRs #47/#48.
- [x] F1.2c e Network P2 agora projetados como live verified.
- [x] PR #23 classificada operacionalmente como histórica/sucedida por lineage posterior.
- [x] PR #41 tratada como fonte de evidência, não como merge candidate atual.
- [ ] Classificar/fechar PRs legadas comprovadamente superseded sem apagar evidência.
- [ ] Revisar branches históricas após classificação.
- [ ] Atualizar Capsule/Capability Registry quando a reconciliação cross-repo for retomada.

**Estado:** `PRE_REBOOT_CHECKPOINT_RECONCILED_OFFHOST_FRESHNESS_GAP`.

## Ordem operacional vigente

```text
INVENTORY                           DONE
RECOVERY_P1                         DONE
RECOVERY_P2                         DONE
RUNNER_ISOLATION_P1                 DONE / ACTIVE_VERIFIED
SSH_KEY_GOVERNANCE_P1               DONE / KEEP_CURRENT_USER_WORKFLOW
F1_2C_NODE01_ROLLOUT                DONE / LIVE_VERIFIED
NETWORK_CONVERGENCE_P2              DONE / LIVE_VERIFIED
PRE_REBOOT_CHECKPOINT               FRESH_READ_ONLY / OFFHOST_FRESHNESS_GAP
SENTINELX_DIRECT                    INTERMITTENT / NOT_CLOSED
G2B_TASK8                           TECHNICAL_PASS / DRAFT_UNINTEGRATED
PRE_REBOOT_OFFHOST_RECOVERY         NEXT / FRESHNESS_GATE
UPDATE_AND_CONTROLLED_REBOOT        NOT_AUTHORIZED
POST_REBOOT_VALIDATION              PENDING
CANONICAL_PR_BRANCH_HYGIENE         PENDING
FINAL_TRANSVERSAL_AUDIT             PENDING
```

## Regra de closeout

Toda sub-missão que mude o estado de um item deste checklist deve atualizar a projeção e
vincular evidência antes do closeout. Não promover `NÃO VERIFICADO` para PASS e não
transformar autorização one-shot em autorização permanente.
