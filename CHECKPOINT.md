# CHECKPOINT — State + Toolchain canônicos

Atualizado em 22/08/2026 após autorização explícita de LEANDRO para uma extração mainline-neutral de state + validação.

## Estado da frente

- Repositório: `leon337/cloud-infrastructure`.
- Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
- Branch isolada: `team/canonical-state-toolchain-20260822`.
- PR: `#22`, draft, sem autorização de merge final.
- Resultado anterior C: resolvido pelo HUMAN_GATE de LEANDRO com autorização da extração neutra.
- Estado atual da implementação: `CANONICAL_NEUTRAL_EXTRACTION_AUTHORIZED_PENDING_VALIDATION`.

## State canônico

`state/current.yaml` foi reconciliado a partir de evidência ao vivo e agora separa estado atual de snapshots históricos.

Fatos principais:

- integração de `main`: `DOCUMENTATION_AND_INTEGRATION_DRIFT`;
- F1.2c: `REQUIRES_REVIEW`, recovery candidate estático verde, KVM acceptance não executado por falha externa pré-step, NODE-01 sem reapply autorizado;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: `FAILED_ATTEMPT_3_NOT_ACCEPTED`, causa `NOT_VERIFIED`, diagnóstico isolado `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: não autorizada;
- Repository Hygiene: `REPOSITORY_HYGIENE_BLOCKED` até a suíte canônica obter evidência verde e a integração ser auditada.

## Toolchain canônica

Entry point: `scripts/test.sh`.

Origem comprovada do contrato: commit `edd2497d657cc9bc35952f5dfc71090a18dade53`, lineage `codex/mission-001-foundations-f1-1`, PR #2.

A implementação desta branch não copia o pacote F1.1. Ela mantém o entrypoint e extrai apenas validações mainline-neutral:

- current-tree secret patterns de alta confiança;
- YAML;
- state;
- consistência documental;
- unit tests do contrato;
- sintaxe shell;
- ShellCheck no CI.

## Decisões negativas explícitas

- `state/active-mission.yaml`: **NÃO ADOTADO**; modelo single-active não comprovado para as frentes paralelas atuais.
- `ROADMAP-CHECKLIST.md`: **NÃO ADOTADO**; origem específica G2-B Task 8.
- código funcional G2-B: não importado.
- código funcional F1.2c: não importado.
- operação privilegiada NODE-01: não executada.
- produção: não promovida.
- branch cleanup: não executado.

## Gate de validação

Para concluir esta frente com PASS ainda é obrigatório:

1. `git diff --check` contra a base do PR;
2. `./scripts/test.sh` em SHA exato;
3. state validator e unit tests verdes;
4. consistência README/CONTEXT/CHECKPOINT/state;
5. compare contra `main` sem caminhos funcionais G2-B/F1.2c;
6. registrar run/job/SHA de evidência.

Próximo passo: **EXECUTE_CANONICAL_VALIDATION_ON_EXACT_HEAD**.
