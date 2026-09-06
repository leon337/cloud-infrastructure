# Cloud Infrastructure

<!-- CANONICAL_EXECUTIVE_PANEL_IMPLEMENTACAO_DA_VPS -->

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Este README é o painel executivo canônico da missão. O
> [`ROADMAP-CHECKLIST.md`](ROADMAP-CHECKLIST.md) é o checklist operacional detalhado,
> subordinado a este painel. Para continuidade, leia também [`CONTEXT.md`](CONTEXT.md),
> [`CHECKPOINT.md`](CHECKPOINT.md) e [`state/current.yaml`](state/current.yaml).
> Fatos mutáveis verificados no GitHub/provider/VPS prevalecem sobre narrativa histórica.

## Estado executivo reconciliado — 06/09/2026

A projeção atual parte de `main@c7315e43e86beedae5a921e39b1ab7103f4da276`, do checkpoint
pré-reboot de 06/09/2026 e da validação live pós-reboot registrada no mesmo dia.

**Estado documental:** `POST_REBOOT_PR51_PR50_INTEGRATED_CLOSEOUT_MERGE_PENDING`.

| Área | Estado atual | Evidência/limite |
|---|---|---|
| VPS / NODE-01 | `POST_REBOOT_LIVE_VERIFIED` | boot `0d8df458...`; kernel `6.8.0-139-generic`; system `running`; 0 failed units; DSH/9Router acessíveis |
| F1.2c Network Services | `COMPLETE_LIVE_VERIFIED` | candidato `baaf8390...`; serviço `active+enabled`; postverify PASS |
| Network Convergence P2 | `COMPLETE_LIVE_VERIFIED` | candidato live `682c3e55...`; checker corrigido integrado pela PR #51 em `fix/f1-2c-systemd-runtime-lock@d5508e1...` |
| Runner isolation | `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED` | run `33998487949`; STARTED/COMPLETED e prova cross-job PASS; `next_exact_step=NONE` |
| SSH key governance | `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED` | preservar fluxo notebook→VPS e `authorized_keys` |
| G2-B Task 8 | `TECHNICAL_PASS_DRAFT_UNINTEGRATED` | PR #21 Draft, head `f91c836e...`; 373/373 testes e 13/13 marcadores; não integrado |
| SentinelX direto | `INTERMITTENT_NOT_CLOSED` | serviço ativo; conexão ao hub oscilou; causa atual `NOT_VERIFIED` |
| Pre-reboot checkpoint | `FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH` | live/on-host frescos em 06/09; recovery `20260906T185928Z` com 6/6 SHA, secret/path/link safety e restore smoke PASS |
| Update/reboot | `PASS_POST_REBOOT_LIVE_VERIFIED` | autorização B consumida; upgrade RC=0; reboot concluído; P2 check corrigido PASS; nenhuma nova autorização permanece ativa |
| Produção externa | `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` | nenhuma promoção autorizada |

## Próxima ação exata

```text
HUMAN_GATE_POST_REBOOT_CLOSEOUT_MERGE
```

A manutenção autorizada por LEANDRO foi concluída:

1. checkpoint e recovery off-host: **PASS**;
2. consumidores ativos DSH/9Router coordenados: **PASS**;
3. autorização B (`updates + reboot`): **consumida**;
4. upgrade: **PASS**, `APT_UPGRADE_RC=0`, zero pacotes atualizáveis após a transação;
5. reboot: **PASS**, boot ID alterado e kernel `6.8.0-139-generic` ativo;
6. F1.2c e P2 pós-reboot: **PASS**, incluindo `NETWORK_CONVERGENCE_CHECK=PASS` no candidato corrigido `9070c24...`;
7. pós-verificação independente: **PASS**;
8. PR #51: **MERGED** em `fix/f1-2c-systemd-runtime-lock@d5508e1...`; validação pós-merge 166/166, shell 21 e Ansible 6 PASS.
9. PR #50: **MERGED** em `main@c7315e43...`; CI pós-merge `34065344230` SUCCESS e suíte isolada 35/35 PASS.

A correção operacional e a reconciliação canônica já estão integradas. O próximo gate é somente o merge do closeout documental desta manutenção.

DeepSeek Harness e 9router permanecem `EXTERNALLY_MANAGED_OBSERVE_ONLY` como boundary de mutação.
Esta PR não os modifica, reinicia, usa como executor ou muda seu ownership. Um reboot do host os
interromperia inevitavelmente; por isso os consumidores ativos precisavam chegar a checkpoint seguro.

A primeira busca por owner/canal externo não encontrou destinatário verificável. Depois, LEANDRO
clarificou que a coordenação operacional deveria ocorrer diretamente com os dois chats ativos que
consumiam DSH/9Router pela GUI. Ambos foram avisados e drenados: `hy4 teste]` respondeu
`READY_FOR_NODE01_MAINTENANCE`; `Dsh Gpt` declarou a missão pausada em checkpoint seguro e sem
novas execuções DSH/9Router até o retorno do NODE-01.

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

## Pre-reboot — checkpoint fresco com gap off-host

O checkpoint read-only de 06/09 está documentado em
[`evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260906.md`](evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260906.md).

Ele confirmou kernel `6.8.0-138-generic`, alvo `6.8.0-139.139`, `reboot-required=YES`,
zero units failed, rede/F1.2c/runner/serviços críticos ativos, 2 CoreDNS + 2 Squid em Docker
e backup on-host `cloud-infrastructure-config-20260906T030657Z.tar.gz` com integridade PASS.

Na coleta inicial não havia recovery off-host de 06/09; essa ausência permanece como observação
histórica com causa `NOT_VERIFIED`. O gate autorizado produziu depois `20260906T185928Z`, com
`SHA256SUMS` 6/6, secret/path/link safety e restore smoke PASS. O checkpoint/recovery foi então
consumido pela manutenção autorizada e concluída no mesmo dia.

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
- as autorizações one-shot de update/reboot foram consumidas; nenhuma nova manutenção, produção, escrita real G2-B ou reapply F1.2c/Network P2 está autorizada;
- secrets nunca são versionados.
