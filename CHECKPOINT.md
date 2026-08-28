# CHECKPOINT — Continuidade da missão IMPLEMENTAÇÃO DA VPS

Atualizado em **28/08/2026** após rollout live autorizado e pós-validação independente do `F1_2C` no NODE-01.

## Hierarquia documental

- Painel executivo canônico da missão: `README.md`.
- Checklist operacional detalhado da missão: `ROADMAP-CHECKLIST.md` (subordinado ao README).
- Estado estruturado: `state/current.yaml`.
- Contexto narrativo/entrada: `CONTEXT.md`.
- Entry point de validação: `scripts/test.sh`.
- Produção continua fechada e exige `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` quando aplicável.

Este arquivo é um **checkpoint de continuidade**. Ele não substitui o painel executivo do
README nem transforma o checklist em autoridade concorrente. GitHub/provider/live evidence
continua tendo precedência para fatos mutáveis.

## Estado atual resumido

- Inventário/base: concluído.
- RECOVERY-P1: concluído.
- RECOVERY-P2: concluído, off-host automático + restore smoke verificados.
- RUNNER-ISOLATION-P1: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING`; PoC legado retirado; hook global configurado e aguardando restart privilegiado autorizado.
- SSH_KEY_GOVERNANCE_P1: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; LEANDRO confirmou uso notebook→VPS, chave preservada e `authorized_keys` inalterado.
- Próxima prioridade: `NETWORK_CONVERGENCE_P2`.
- Qualquer hardening futuro da `dsh-tunnel...` deve preservar o acesso interativo atual.
- F1.2c no NODE-01: `COMPLETE_LIVE_VERIFIED`; diagnóstico root corrigiu a classificação para baseline `EXACT_PRESENT`, PRs #39/#40 fecharam os gaps do recovery, candidato `baaf839...` passou static/ShellCheck + KVM nas duas variantes e o rollout autorizado concluiu `RECOVERY_CHECK=PASS` + `F1_2C_POSTVERIFY=PASS`. Checkpoint/backup pré-apply e state `RECOVERED` foram verificados. A autorização one-shot foi consumida.
- Network convergence: pendente antes de reboot.
- Reboot/kernel: bloqueado por precondições.
- Full-image/provider disaster recovery: NÃO VERIFICADO.

## State canônico

`state/current.yaml` agora reconhece `ROADMAP-CHECKLIST.md` como `ADOPTED`.
Subseções legadas ainda são preservadas enquanto a reconciliação histórica completa não
for concluída; por isso `DOCUMENTATION_AND_INTEGRATION_DRIFT` permanece como marcador
de dívida documental, não como negação da adoção do checklist.

Marcadores históricos ainda preservados até reconciliação específica:

- F1.2c: `COMPLETE_LIVE_VERIFIED`; candidato aplicado `baaf839...`, lineage `2408aed4...`, evidência em `evidence/f1-2c/F1-2C-NODE01-LIVE-RECOVERY-20260828.md`;
- G2-B legado: `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- Repository Hygiene histórico: `REPOSITORY_HYGIENE_REVALIDATED`.

Esses marcadores não devem sobrepor o estado operacional mais recente registrado no
checklist e confirmado por evidência live/GitHub.

## Toolchain canônica

A validação continua em `scripts/test.sh`, incluindo:

- `git diff --check`;
- scanner de secrets da árvore e histórico alcançável;
- links Markdown;
- YAML estrito;
- state/consistência;
- unit tests;
- sintaxe Python/shell;
- ShellCheck no CI hospedado;
- policy de isolamento do runner (`scripts/check_runner_isolation.py`).

O contrato agora também exige que, quando
`continuity.roadmap_checklist.status == ADOPTED`, `ROADMAP-CHECKLIST.md` exista e
contenha o marcador `IMPLEMENTACAO_DA_VPS_OPERATIONAL_CHECKLIST` e permaneça subordinado ao README.

## Boundaries

- `state/active-mission.yaml` continua `NOT_ADOPTED`.
- conclusão F1.2c não autoriza produção, G2-B, reboot ou novo reapply; qualquer nova mutação privilegiada segue seu gate específico;
- mudanças materiais no NODE-01 continuam sujeitas aos gates aplicáveis;
- secrets nunca são versionados.

## Próximo passo

Executar `NETWORK_CONVERGENCE_P2` inicialmente read-only conforme `ROADMAP-CHECKLIST.md`; manter a `dsh-tunnel...` para o fluxo atual notebook→VPS e preservar a ativação do hook global do runner como hardening pendente. Não rebootar antes da convergência de rede e de um checkpoint pré-reboot.
