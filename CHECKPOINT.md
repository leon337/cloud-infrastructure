# CHECKPOINT — Continuidade da missão IMPLEMENTAÇÃO DA VPS

Atualizado em **05/09/2026** após reconciliação read-only do GitHub e do NODE-01.

## Hierarquia documental

- Painel executivo canônico: `README.md`.
- Checklist operacional detalhado: `ROADMAP-CHECKLIST.md`, subordinado ao README.
- Estado estruturado: `state/current.yaml`.
- Porta de entrada: `CONTEXT.md`.
- Validação canônica: `scripts/test.sh`.

Fatos mutáveis verificados ao vivo prevalecem sobre narrativa histórica. Este checkpoint
não autoriza mudança material por si só.

## Estado atual resumido

- Inventário/base: concluído.
- RECOVERY-P1/P2: concluídos para os componentes cobertos; full-image/provider DR segue `NÃO VERIFICADO`.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`; run `33998487949` PASS; `runner_isolation.next_exact_step=NONE`.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; preservar acesso notebook→VPS.
- F1.2c: `COMPLETE_LIVE_VERIFIED`; candidato aplicado `baaf83908e8e83264baafc032434a4df1952450b`; serviço relido `active+enabled` em 05/09.
- Network P2: `COMPLETE_LIVE_VERIFIED`; candidato aplicado `682c3e55d835ebea4bcc2edd297a8b819b2df434`; `eth0` relido `routable (configured)` e online.
- G2-B Task 8: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`; PR #21 permanece Draft e não integrada; Tasks 9/10 não iniciadas.
- SentinelX direto: `INTERMITTENT_NOT_CLOSED`; serviço ativo, mas aceite persistente ao hub não comprovado; causa atual `NOT_VERIFIED`.
- Pre-reboot V2 de 29/08: evidência histórica válida, mas `HISTORICAL_VERIFIED_REFRESH_REQUIRED` para o host atual.
- Kernel atual: `6.8.0-138-generic`; alvo pendente: `6.8.0-139-generic`; `reboot-required=YES`.

## Próxima ação exata

`PRE_REBOOT_CHECKPOINT_REFRESH_AND_EXTERNAL_SERVICE_COORDINATION_GATE`

Esse gate exige, nesta ordem:

1. checkpoint pré-reboot fresco do estado atual;
2. validação do backup/recovery off-host aplicável ao checkpoint fresco;
3. coordenação de janela com os responsáveis externos por DeepSeek Harness e 9router;
4. autorização humana explícita para update/reboot;
5. manutenção controlada e pós-validação completa.

## Boundaries

- DeepSeek Harness: `EXTERNALLY_MANAGED_OBSERVE_ONLY`.
- 9router: `EXTERNALLY_MANAGED_OBSERVE_ONLY`.
- Esta reconciliação não faz deploy, restart, package update, firewall change ou write na VPS.
- Reboot do host interromperia os serviços externos acima; portanto coordenação externa é obrigatória.
- F1.2c e Network P2 tiveram autorizações one-shot consumidas; nenhum reapply está autorizado.
- G2-B real write permanece `NOT_AUTHORIZED`.
- Produção permanece `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- Secrets nunca são versionados.

## Evidências principais

- F1.2c: `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`.
- Network P2: `evidence/network-convergence/NETWORK-CONVERGENCE-P2-NODE01-LIVE-20260829.md`.
- Checkpoint histórico: `evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260829.md`.
- Reconciliação atual: `evidence/vps/LIVE-STATE-RECONCILIATION-20260905.md`.

## Toolchain canônica

`scripts/test.sh` continua sendo o entrypoint e deve manter:

- `git diff --check`;
- scanner de secrets na árvore e histórico alcançável;
- links Markdown locais;
- YAML estrito;
- validação/consistência do estado;
- unit tests;
- sintaxe Python/shell;
- ShellCheck no CI hospedado;
- policy de isolamento do runner.

**Estado documental:** `LIVE_STATE_RECONCILED_OPEN_GOVERNANCE_DEBT`.
