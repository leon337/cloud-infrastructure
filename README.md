# Cloud Infrastructure

<!-- CANONICAL_EXECUTIVE_PANEL_IMPLEMENTACAO_DA_VPS -->

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Este README é o painel executivo canônico da missão. O
> [`ROADMAP-CHECKLIST.md`](ROADMAP-CHECKLIST.md) é o checklist operacional detalhado,
> subordinado a este painel. Para continuidade, leia também [`CONTEXT.md`](CONTEXT.md),
> [`CHECKPOINT.md`](CHECKPOINT.md) e [`state/current.yaml`](state/current.yaml).
> Fatos mutáveis verificados no GitHub/provider/VPS prevalecem sobre narrativa histórica.

## Estado executivo reconciliado — 05/09/2026

A reconciliação desta projeção parte de `main@34248311116e2282950fe560639873c8e5d2f81c`,
dos receipts live F1.2c/Network P2 preservados da PR #41 e de uma nova leitura read-only
do NODE-01. Nenhuma mudança na VPS pertence a esta reconciliação.

**Estado documental:** `LIVE_STATE_RECONCILED_OPEN_GOVERNANCE_DEBT`.

| Área | Estado atual | Evidência/limite |
|---|---|---|
| VPS / NODE-01 | `OPERATIONAL_WITH_VERIFIED_NETWORK_AND_REBOOT_PENDING` | kernel `6.8.0-138-generic`; reboot requerido para `6.8.0-139-generic`; F1.2c/eth0/runner ativos |
| F1.2c Network Services | `COMPLETE_LIVE_VERIFIED` | candidato `baaf8390...`; serviço `active+enabled`; postverify PASS |
| Network Convergence P2 | `COMPLETE_LIVE_VERIFIED` | candidato `682c3e55...`; `eth0` `routable (configured)`; gateway `/32 scope link`; wait-online ativo |
| Runner isolation | `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED` | run `33998487949`; STARTED/COMPLETED e prova cross-job PASS; `next_exact_step=NONE` |
| SSH key governance | `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED` | preservar fluxo notebook→VPS e `authorized_keys` |
| G2-B Task 8 | `TECHNICAL_PASS_DRAFT_UNINTEGRATED` | PR #21 Draft, head `f91c836e...`; 373/373 testes e 13/13 marcadores; não integrado |
| SentinelX direto | `INTERMITTENT_NOT_CLOSED` | serviço ativo; conexão ao hub oscilou; causa atual `NOT_VERIFIED` |
| Pre-reboot checkpoint | `HISTORICAL_VERIFIED_REFRESH_REQUIRED` | checkpoint V2 de 29/08 é evidência válida, mas antecede o kernel atual e não vale como checkpoint corrente |
| Update/reboot | `HUMAN_GATE_AND_EXTERNAL_SERVICE_COORDINATION_REQUIRED` | checkpoint fresco + coordenação externa + autorização humana antes de qualquer reboot |
| Produção externa | `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` | nenhuma promoção autorizada |

## Próxima ação exata

```text
PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE
```

Antes de qualquer update/reboot:

1. gerar um checkpoint pré-reboot fresco do estado atual;
2. validar backup/recovery off-host aplicável ao checkpoint fresco;
3. coordenar a janela com os responsáveis externos por DeepSeek Harness e 9router;
4. obter autorização humana explícita para updates/reboot;
5. somente então executar manutenção e a validação pós-reboot.

DeepSeek Harness e 9router permanecem `EXTERNALLY_MANAGED_OBSERVE_ONLY`. Esta PR não
os modifica, reinicia, usa como executor ou muda seu ownership. Um reboot do host os
interromperia inevitavelmente, por isso a coordenação externa é requisito de gate.

## F1.2c — fechado live

O rollout F1.2c foi aplicado e verificado no NODE-01. O estado atual não é mais
`REQUIRES_REVIEW` nem aguarda `F1_2C_NODE01_ROLLOUT_HUMAN_GATE`.

- candidato aplicado: `baaf83908e8e83264baafc032434a4df1952450b`;
- helper instalado SHA-256: `b69f41cd1c66000da239f39c09a46681afd5098a311065adf76b3c7aae35b9a3`;
- unit instalada SHA-256: `c8297e4e88572a9fee9393960f7896e1ba27d9650f5643d595388878f059a57b`;
- `cloud-platform-network-services.service`: `active+enabled` na releitura de 05/09;
- `systemctl --failed`: zero units na mesma releitura.

Evidência: [`evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`](evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md).

## Network Convergence P2 — fechado live

A convergência de `systemd-networkd` foi recuperada sem restaurar a rota conectada `/17`.
O fix materializa apenas `169.58.128.1/32 scope link` para o gateway.

- candidato aplicado: `682c3e55d835ebea4bcc2edd297a8b819b2df434`;
- `eth0`: `routable (configured)` e online na releitura de 05/09;
- gateway: `169.58.128.1`;
- host-route `/32 scope link`: presente;
- `systemd-networkd-wait-online.service`: ativo na releitura de 05/09.

Evidência: [`evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`](evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md).

## Runner isolation — fechado

O hardening do runner está concluído e não deve voltar ao checklist como pendência:

- estado: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`;
- wrapper administrativo `.sh` validado e ativo;
- run `33998487949`: STARTED/COMPLETED `RUNNER_ISOLATION_GUARD_PASS`;
- `RUNNER_ISOLATION_CROSS_JOB=PASS`;
- PR #47 integrada e PR #48 fechou `runner_isolation.next_exact_step=NONE`.

## G2-B — separar PASS técnico de integração

A PR #21 continua aberta e Draft. O head `f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8`
registra PASS técnico da Task 8: 373/373 testes, 13/13 marcadores de lifecycle,
cleanup sem resíduos e nenhuma escrita G2-B real no NODE-01. Isso substitui a narrativa
antiga `TASK_8_FAILED_ATTEMPT_3` como estado técnico, mas **não** significa integração
canônica nem autorização para Tasks 9/10.

Classificação atual: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.

## SentinelX direto — ainda aberto

`sentinelx-cloud-core` está ativo e enabled no NODE-01, porém a conexão direta ao hub
não atingiu aceite persistente nesta reconciliação. O journal recente mostrou ciclos de
`connected`, WebSocket `1006`, hub restart `1012`, HTTP `502` e reconexão.

Classificação: `INTERMITTENT_NOT_CLOSED`; causa atual: `NOT_VERIFIED`.

Não reiniciar ou patchar SentinelX como atalho nesta frente enquanto isso puder interferir
com workloads externos em execução. Diagnóstico material exige missão/gate próprio.

## Pre-reboot: evidência histórica ≠ checkpoint corrente

O checkpoint V2 de 29/08 permanece válido como evidência histórica e está documentado em
[`evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md`](evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md).

Ele foi criado com kernel `6.8.0-137-generic`. A releitura de 05/09 mostrou kernel
`6.8.0-138-generic`, `reboot-required=YES` e alvo `6.8.0-139-generic`. Portanto o V2
não é aceito como checkpoint corrente para o próximo reboot. Um refresh é obrigatório.

## Dívidas ainda abertas

- full-image/bare-metal disaster recovery do provider: `NÃO VERIFICADO`;
- gaps privilegiados finais de segurança/Fail2ban/provider firewall;
- inventário semântico profundo de Docker/workloads;
- lifecycle/cleanup XRDP;
- SentinelX direto persistente;
- G2-B Task 8 ainda não integrada; Tasks 9/10 não iniciadas;
- classificação/fechamento de PRs e branches históricas;
- auditoria transversal final após os gates de manutenção.

## Regra de execução

- LEANDRO é a autoridade humana final;
- `scripts/test.sh` é o entrypoint de validação canônico;
- esta reconciliação é documental/estado: `vps_mutation_by_this_reconciliation=false`;
- nenhuma conclusão aqui autoriza produção, update, reboot, escrita real G2-B ou reapply F1.2c/Network P2;
- secrets nunca são versionados.
