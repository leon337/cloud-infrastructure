# CHECKPOINT — Continuidade da missão IMPLEMENTAÇÃO DA VPS

Atualizado em **28/08/2026** após validação do `RUNNER_ISOLATION_P1`.

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
- Próxima prioridade: `SSH_KEY_GOVERNANCE_P1`.
- Governança da chave `dsh-tunnel...`: pendente e agora é a próxima frente exata.
- F1.2c no NODE-01: rollout pendente e `REQUIRES_REVIEW`.
- Network convergence: pendente antes de reboot.
- Reboot/kernel: bloqueado por precondições.
- Full-image/provider disaster recovery: NÃO VERIFICADO.

## State canônico

`state/current.yaml` agora reconhece `ROADMAP-CHECKLIST.md` como `ADOPTED`.
Subseções legadas ainda são preservadas enquanto a reconciliação histórica completa não
for concluída; por isso `DOCUMENTATION_AND_INTEGRATION_DRIFT` permanece como marcador
de dívida documental, não como negação da adoção do checklist.

Marcadores históricos ainda preservados até reconciliação específica:

- F1.2c: `REQUIRES_REVIEW`;
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
- adoção do checklist não autoriza produção, sudo, Docker write ou reapply F1.2c;
- mudanças materiais no NODE-01 continuam sujeitas aos gates aplicáveis;
- secrets nunca são versionados.

## Próximo passo

Executar `SSH_KEY_GOVERNANCE_P1` conforme `ROADMAP-CHECKLIST.md`; manter a ativação do hook global do runner como hardening pendente sujeito a restart autorizado.
