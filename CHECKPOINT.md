# CHECKPOINT — Continuidade da missão IMPLEMENTAÇÃO DA VPS

Atualizado em **06/09/2026** após checkpoint pré-reboot read-only do NODE-01 e recovery off-host.

## Hierarquia documental

- Painel executivo canônico: `README.md`.
- Checklist operacional detalhado: `ROADMAP-CHECKLIST.md`, subordinado ao README.
- Estado estruturado: `state/current.yaml`.
- Porta de entrada: `CONTEXT.md`.
- Validação canônica: `scripts/test.sh`.

Fatos mutáveis verificados ao vivo prevalecem sobre narrativa histórica. Este checkpoint
não autoriza mudança material por si só.

## Estado atual resumido

- F1.2c/Network P2: `COMPLETE_LIVE_VERIFIED`.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_ACTIVE_VERIFIED`; `next_exact_step=NONE`.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; preservar fluxo notebook→VPS.
- G2-B Task 8: `TECHNICAL_PASS_DRAFT_UNINTEGRATED`.
- SentinelX direto: `INTERMITTENT_NOT_CLOSED`; causa `NOT_VERIFIED`.
- Kernel atual: `6.8.0-138-generic`; alvo instalado: `6.8.0-139.139`; reboot requerido.
- Checkpoint live 06/09: `FRESH_READ_ONLY_VERIFIED_OFFHOST_FRESHNESS_GAP`.
- Backup on-host 06/09: `cloud-infrastructure-config-20260906T030657Z.tar.gz`, SHA `ec5d83dd...5816f4`, integridade PASS.
- Recovery off-host: último completo `20260905T033111Z`, `SHA256SUMS` 6/6 PASS; recovery 06/09 ausente no check.
- Causa da ausência do recovery 06/09: `NOT_VERIFIED`.

## Próxima ação exata

`PRE_REBOOT_OFFHOST_RECOVERY_FRESHNESS_GATE`

Esse gate exige primeiro um recovery off-host fresco. Depois disso ainda são obrigatórios
recheck mínimo do checkpoint, coordenação externa de DSH/9router e autorização humana para reboot.

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
- Checkpoint fresco: `evidence/pre-reboot/PRE-REBOOT-CHECKPOINT-NODE01-20260906.md`.
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

**Estado documental:** `PRE_REBOOT_CHECKPOINT_RECONCILED_OFFHOST_FRESHNESS_GAP`.
