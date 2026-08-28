# CHECKPOINT — Estado operacional canônico

Atualizado em **28/08/2026** após a adoção formal do checklist operacional canônico.

## Fonte operacional atual

- Checklist canônico: `ROADMAP-CHECKLIST.md`.
- Baseline de reconciliação: `main@bbdc7b2a3874af75424680c49aed3cbcb8d63bcb`.
- Última integração material antes desta governança: PR #28 / RECOVERY-P2.
- Entry point de validação: `scripts/test.sh`.
- Produção continua fechada e exige `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED` quando aplicável.

O checklist deve ser atualizado em toda missão que altere o estado operacional. GitHub/live
evidence continua tendo precedência sobre snapshots documentais para fatos mutáveis.

## Estado atual resumido

- Inventário/base: concluído.
- RECOVERY-P1: concluído.
- RECOVERY-P2: concluído, off-host automático + restore smoke verificados.
- Próxima prioridade: `RUNNER_ISOLATION_P1`.
- Governança da chave `dsh-tunnel...`: pendente.
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
- ShellCheck no CI hospedado.

O contrato agora também exige que, quando
`continuity.roadmap_checklist.status == ADOPTED`, `ROADMAP-CHECKLIST.md` exista e
contenha o marcador `CANONICAL_OPERATIONAL_CHECKLIST`.

## Boundaries

- `state/active-mission.yaml` continua `NOT_ADOPTED`.
- adoção do checklist não autoriza produção, sudo, Docker write ou reapply F1.2c;
- mudanças materiais no NODE-01 continuam sujeitas aos gates aplicáveis;
- secrets nunca são versionados.

## Próximo passo

Executar `RUNNER_ISOLATION_P1` conforme `ROADMAP-CHECKLIST.md`.
