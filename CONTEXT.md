# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `leon337/cloud-infrastructure`.

## Regra de verdade

Hierarquia documental: `README.md` é o painel executivo canônico; `ROADMAP-CHECKLIST.md`
é o checklist operacional detalhado subordinado; `state/current.yaml` é a projeção estruturada;
`CHECKPOINT.md` preserva continuidade.

Precedência operacional:

1. instrução explícita atual de LEANDRO;
2. GitHub/provider/infraestrutura verificável ao vivo;
3. testes/evidências executáveis vinculados a SHA/estado;
4. `README.md` e `state/current.yaml`;
5. `ROADMAP-CHECKLIST.md` e `CHECKPOINT.md`;
6. histórico.

Nunca transformar estado desejado ou histórico em estado observado atual.

## Mapa atual — checkpoint pré-reboot de 06/09/2026

Base canônica: `main@7ce6fff85f66eaed88c7b6e092c4bc2375f5382d`.

- F1.2c e Network P2: `COMPLETE_LIVE_VERIFIED`.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`; `next_exact_step=NONE`.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; preservar fluxo notebook→VPS.
- G2-B Task 8: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.
- SentinelX direto: `INTERMITTENT_NOT_CLOSED`; causa atual `NOT_VERIFIED`.
- Checkpoint 06/09: `FRESH_READ_ONLY_VERIFIED_OFFHOST_FRESHNESS_GAP`.
- Backup on-host 06/09: `FRESH_INTEGRITY_PASS`.
- Recovery off-host: último completo `20260905T033111Z`, `PASS_6_OF_6`; 06/09 ausente no check; causa `NOT_VERIFIED`.
- Produção/update/reboot: não autorizados.

**Estado documental:** `PRE_REBOOT_CHECKPOINT_RECONCILED_OFFHOST_FRESHNESS_GAP`.

## Próximo passo exato

`PRE_REBOOT_OFFHOST_RECOVERY_FRESHNESS_GATE`

Não executar update/reboot. Primeiro fechar a frescura do recovery off-host; depois revalidar
checkpoint conforme necessário, coordenar a janela com owners externos e obter autorização humana.

## Boundary externo

DeepSeek Harness e 9router são `EXTERNALLY_MANAGED_OBSERVE_ONLY` nesta missão.

Não:

- editar seus arquivos/configurações;
- reiniciar/parar seus processos;
- alterar supervisor/cron/pacotes;
- usá-los como rota de execução;
- realizar reboot do host sem coordenação externa explícita.

O fato de um reboot não editar seus arquivos não elimina o impacto: ele interrompe o host e,
portanto, esses serviços.

## F1.2c e Network P2

O antigo `F1_2C_NODE01_ROLLOUT_HUMAN_GATE` foi consumido por execução posterior comprovada.
Não reaplicar F1.2c nem Network P2 como resposta ao checklist histórico.

Receipts canônicos:

- `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`;
- `evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`.

A releitura read-only de 05/09 confirmou F1.2c `active+enabled`, zero units failed,
`eth0 routable (configured)`, gateway `169.58.128.1`, wait-online ativo e os hashes live
esperados do helper/unit F1.2c.

## G2-B

O estado antigo `FAILED_ATTEMPT_3_NOT_ACCEPTED` não é mais o terminal técnico mais recente.
A PR #21 registra o head `f91c836e92fae1aea1cc2e48ecc4c4bde6df78b8` com 373/373 testes,
13/13 marcadores e cleanup sem resíduos.

Isso é **PASS técnico**, não integração. A classificação corrente é
`TECHNICAL_PASS_DRAFT_UNINTEGRATED`. Escrita real G2-B segue não autorizada.

## SentinelX

`sentinelx-cloud-core` está ativo/enabled, mas a janela observada mostrou conexão ao hub
alternando com WebSocket `1006`, hub restart `1012` e HTTP `502`, seguida de reconexões.
A causa atual permanece `NOT_VERIFIED`. Não inferir automaticamente que o heartbeat histórico
é a causa presente.

## Reboot / checkpoint

O receipt histórico de 29/08 continua válido como baseline histórica, mas o snapshot corrente é
`evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260906.md`.

O checkpoint de 06/09 confirmou:

- kernel `6.8.0-138-generic`; alvo instalado `6.8.0-139.139`;
- `reboot-required=YES` para kernel + `linux-base`;
- zero units failed; F1.2c, wait-online, Docker, UFW, Fail2Ban, Tailscale, Runner e SentinelX ativos;
- backup on-host 06/09 íntegro;
- recovery off-host mais recente ainda 05/09, 6/6 SHA PASS.

A ausência do recovery de 06/09 bloqueia o gate atual. Causa: `NOT_VERIFIED`.

## Toolchain canônica

`scripts/test.sh` é o entrypoint canônico. O CI de integração permanece GitHub-hosted
`ubuntu-24.04`, com secret policy, runner isolation policy, Markdown, YAML estrito,
state/consistency, unit tests, Python/shell syntax e ShellCheck.

## Guardrails

- LEANDRO é a autoridade humana final.
- MESTRE orquestra a missão.
- esta reconciliação é documental/estado e não autoriza mudanças live;
- autorizações one-shot F1.2c/Network P2 foram consumidas;
- nenhuma conclusão autoriza produção, reboot, update, G2-B real write ou reapply;
- secrets nunca são versionados.
