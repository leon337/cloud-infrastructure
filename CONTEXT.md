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

## Mapa atual — reconciliação de 05/09/2026

Base de reconciliação: `main@34248311116e2282950fe560639873c8e5d2f81c`.

- F1.2c: `COMPLETE_LIVE_VERIFIED`; candidato `baaf83908e8e83264baafc032434a4df1952450b` aplicado e pós-verificado.
- Network P2: `COMPLETE_LIVE_VERIFIED`; candidato `682c3e55d835ebea4bcc2edd297a8b819b2df434`; `eth0` configurado/online e gateway `/32 scope link` presente.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`; run `33998487949`; nenhuma ação pendente na trilha.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; preservar fluxo notebook→VPS.
- G2-B Task 8: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`; PR #21 Draft/unmerged; Tasks 9/10 `NOT_STARTED`.
- SentinelX direto: `INTERMITTENT_NOT_CLOSED`; serviço live ativo, causa da intermitência `NOT_VERIFIED`.
- Pre-reboot checkpoint de 29/08: `HISTORICAL_VERIFIED_REFRESH_REQUIRED` porque foi produzido com kernel `6.8.0-137-generic` e o host está agora em `6.8.0-138-generic` com `6.8.0-139-generic` pendente.
- Produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.

**Estado documental:** `LIVE_STATE_RECONCILED_OPEN_GOVERNANCE_DEBT`.

## Próximo passo exato

`PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE`

Não executar diretamente update/reboot. Primeiro:

- gerar checkpoint fresco;
- validar recovery/off-host associado;
- coordenar janela com owners externos dos serviços que seriam interrompidos;
- obter autorização humana explícita.

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

O receipt `PRE-REBOOT-CHECKPOINT-NODE01-20260829.md` continua válido como evidência de
uma baseline histórica. Ele **não** deve ser usado como autorização nem como checkpoint corrente.

Estado atual observado:

- kernel `6.8.0-138-generic`;
- `reboot-required=YES`;
- alvo `linux-image-6.8.0-139-generic` + `linux-base`;
- F1.2c, network wait-online, runner e SentinelX ativos;
- backup on-host recente `cloud-infrastructure-config-20260905T030614Z.tar.gz`.

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
