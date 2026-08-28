# CHECKPOINT — Continuidade da missão IMPLEMENTAÇÃO DA VPS

Atualizado em **28/08/2026** após validação exact-head, integração do recovery parcial `F1_2C` e preflight live não privilegiado.

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
- Próxima prioridade: `F1_2C_NODE01_ROLLOUT_HUMAN_GATE`.
- Qualquer hardening futuro da `dsh-tunnel...` deve preservar o acesso interativo atual.
- F1.2c no NODE-01: `REQUIRES_REVIEW`; recovery do estado `PARTIAL_FIRST_APPLY` validado/integrado e preflight live não privilegiado PASS em `2026-08-28T17:11:31Z`; conteúdo dos markers `0600`, `zero_docker_state`, staging root-owned e precheck privilegiado permanecem pendentes do HUMAN_GATE; nenhum write live foi executado.
- Network convergence: pendente antes de reboot.
- Reboot/kernel: bloqueado por precondições.
- Full-image/provider disaster recovery: NÃO VERIFICADO.

## State canônico

`state/current.yaml` agora reconhece `ROADMAP-CHECKLIST.md` como `ADOPTED`.
Subseções legadas ainda são preservadas enquanto a reconciliação histórica completa não
for concluída; por isso `DOCUMENTATION_AND_INTEGRATION_DRIFT` permanece como marcador
de dívida documental, não como negação da adoção do checklist.

Marcadores históricos ainda preservados até reconciliação específica:

- F1.2c: `REQUIRES_REVIEW` até o rollout live; recovery técnico exact-head já validado e integrado;
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
- adoção do checklist e validação do recovery não autorizam produção, sudo, Docker write ou reapply F1.2c;
- mudanças materiais no NODE-01 continuam sujeitas aos gates aplicáveis;
- secrets nunca são versionados.

## Próximo passo

Resolver `F1_2C_NODE01_ROLLOUT_HUMAN_GATE` conforme `ROADMAP-CHECKLIST.md`; após autorização, executar staging root-owned + precheck privilegiado fail-closed antes de qualquer apply; manter a `dsh-tunnel...` para o fluxo atual notebook→VPS e preservar a ativação do hook global do runner como hardening pendente.
