# PRF — G2-B Task 8

Estado: `PASS_TECHNICAL_READY_FOR_CENTRAL_AUDIT`

Este diretório contém o pacote de rastreabilidade da frente isolada G2-B Task 8.

Ordem recomendada:
1. `PHASE-G2B-TASK-8-PLAN.md`
2. `PHASE-G2B-TASK-8-REPORT.md`
3. `PHASE-G2B-TASK-8-VALIDATION.txt`
4. `PHASE-G2B-TASK-8-VALIDATION-FULL.txt`
5. `PHASE-G2B-TASK-8-SMOKE.txt`
6. `PHASE-G2B-TASK-8-DECISIONS.md`
7. `PHASE-G2B-TASK-8-CHECKPOINT.yaml`
8. `MISSION-TRACE.md`
9. `PHASE-G2B-TASK-8-ARTIFACT-MANIFEST.sha256`

Evidência histórica:
- `evidence/CONTROL-BRIDGE-G2B/TASK-8-ATTEMPT-3.md`
- `evidence/CONTROL-BRIDGE-G2B/TASK-8-FINALIZATION-20260823.md`

Resultado técnico:
- candidato funcional validado: `ac3e2f8a52b881bcd2b40acab0d723d547b90e81`;
- 373/373 unit tests PASS;
- 9/9 Ansible syntax PASS;
- lifecycle descartável exit 0;
- 13/13 marcadores obrigatórios, uma vez cada, em ordem;
- bounded cleanup PASS;
- nenhum write G2-B real no NODE-01;
- Tasks 9/10 não iniciadas;
- merge final não executado.

GitHub-hosted CI está bloqueado antes da execução por billing/spending limit da conta. Os jobs afetados têm runner_id=0 e steps=[]; isso não é classificado como falha funcional do candidato.
