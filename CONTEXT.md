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

## Mapa atual — pós-reboot live verified de 06/09/2026

Base canônica: `main@c7315e43e86beedae5a921e39b1ab7103f4da276`.

- F1.2c e Network P2: `COMPLETE_LIVE_VERIFIED`.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`; `next_exact_step=NONE`.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; preservar fluxo notebook→VPS.
- G2-B Task 8: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.
- SentinelX direto: `INTERMITTENT_NOT_CLOSED`; causa atual `NOT_VERIFIED`.
- Checkpoint 06/09: `FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH`.
- Backup on-host 06/09: `FRESH_INTEGRITY_PASS`.
- Recovery off-host: `20260906T185928Z`, `RECOVERY-P2-v1`, `PASS_6_OF_6`, restore smoke PASS; causa da ausência anterior segue historicamente `NOT_VERIFIED`.
- Produção: não autorizada; autorizações one-shot de update/reboot já foram consumidas e não permanecem ativas.

**Estado documental:** `POST_REBOOT_INTEGRATION_COMPLETE_BRANCH_HYGIENE_NEXT`.

## Próximo passo exato

`CANONICAL_PR_BRANCH_HYGIENE`

Update/reboot autorizados por LEANDRO já foram executados e consumidos. O NODE-01 voltou no kernel
`6.8.0-139-generic`, zero failed units, DSH/9Router acessíveis e Network P2 formalmente PASS com o
checker corrigido `9070c24...`. A PR #51 foi integrada em `fix/f1-2c-systemd-runtime-lock@d5508e1...`
e passou validação pós-merge 166/166. A PR #50 foi integrada em `main@c7315e43...`, com CI pós-merge SUCCESS e 35/35 testes isolados. A integração pós-reboot está encerrada. O próximo passo operacional é `CANONICAL_PR_BRANCH_HYGIENE`.

## Boundary externo

DeepSeek Harness e 9router são `EXTERNALLY_MANAGED_OBSERVE_ONLY` nesta missão.

Não:

- editar seus arquivos/configurações;
- reiniciar/parar seus processos;
- alterar supervisor/cron/pacotes;
- usá-los como rota de execução;
- executar novo reboot/update sem uma nova autorização humana explícita.

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

O checkpoint pré-reboot de 06/09 confirmou kernel `6.8.0-138-generic` e `reboot-required=YES`.
Depois, o recovery off-host `20260906T185928Z` fechou a lacuna de frescor e a autorização B foi consumida.

O estado pós-reboot confirmado é:

- boot ID `0d8df458-4f6f-4db6-84a4-d51b393d6743`;
- kernel `6.8.0-139-generic`;
- `reboot-required=NO`, zero pacotes atualizáveis e zero failed units;
- F1.2c enforcement/services ativos e check PASS;
- Network P2 `NETWORK_CONVERGENCE_CHECK=PASS state=RECOVERED` no candidato `9070c24...`;
- rota `/17` permitida via gateway e rota `/17 scope link` ausente na tabela IPv4 main;
- DSH HTTP 200 e 9Router HTTP 307.

Receipt: `evidence/post-reboot/POST-REBOOT-LIVE-VERIFICATION-20260906.md`.

## Toolchain canônica

`scripts/test.sh` é o entrypoint canônico. O CI de integração permanece GitHub-hosted
`ubuntu-24.04`, com secret policy, runner isolation policy, Markdown, YAML estrito,
state/consistency, unit tests, Python/shell syntax e ShellCheck.

## Guardrails

- LEANDRO é a autoridade humana final.
- MESTRE orquestra a missão.
- esta reconciliação é documental/estado e não autoriza mudanças live;
- autorizações one-shot F1.2c/Network P2 foram consumidas;
- nenhuma conclusão autoriza nova produção, novo reboot/update, G2-B real write ou reapply;
- secrets nunca são versionados.
