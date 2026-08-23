# CHECKPOINT — State + Toolchain canônicos

Atualizado em 22/08/2026 após autorização explícita de LEANDRO para uma extração mainline-neutral de state + validação.

## Estado da frente

- Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
- Branch: `team/canonical-state-toolchain-20260822`.
- PR: `#22`, draft, sem autorização de merge final.
- HUMAN_GATE: resolvido por LEANDRO.
- Estado: `CANONICAL_HOSTED_EXECUTOR_RESTORED_PENDING_EXECUTION`.

## State canônico

`state/current.yaml` foi reconciliado a partir de evidência, sem copiar snapshots branch-local obsoletos.

- `main`: `DOCUMENTATION_AND_INTEGRATION_DRIFT`;
- F1.2c: `REQUIRES_REVIEW`, sem reapply NODE-01 autorizado;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: `FAILED_ATTEMPT_3_NOT_ACCEPTED`, causa `NOT_VERIFIED`, diagnóstico `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: fechada;
- Repository Hygiene: `REPOSITORY_HYGIENE_REVALIDATED`; PR #19 foi validado contra a toolchain canônica, sem credencial literal histórica detectada.

## Toolchain canônica

Entry point: `scripts/test.sh`.
Origem: `edd2497d657cc9bc35952f5dfc71090a18dade53`, F1.1 / PR #2.

Preservado de forma mainline-neutral:

- diff check;
- scanner de secrets da árvore e histórico alcançável;
- links Markdown;
- YAML estrito;
- state/consistência;
- unit tests;
- sintaxe Python/shell;
- ShellCheck.

O caminho de integração canônico é `.github/workflows/canonical-validation.yml` em `ubuntu-24.04`, com Python 3.12 e `requirements-dev.lock`. Isso preserva o executor do workflow F1.1 em vez de acoplar CI ao NODE-01.

Uma prova de manutenção separada pode executar a mesma suíte em NODE-01 apenas para branches `team/canonical-state-toolchain-*`, com boundary não privilegiado obrigatório. Ela não substitui o CI hospedado.

## Evidência anterior

Run `32609819790`, job `97120890824`, candidato `55cbbf0b...` executou no NODE-01 e provou checkout/boundary/ShellCheck/workspace, mas falhou no `git diff --check` por quatro trailing spaces desta frente. Os defeitos foram corrigidos.

Auditoria posterior restaurou o scanner histórico, links Markdown, YAML estrito e o boundary hosted original; por isso o candidato atual deve executar novamente do início.

## Interpretação de falhas

- falha causada pelos arquivos desta extração: esta frente corrige e reroda;
- `SECRET_POLICY_FAIL` em histórico preexistente: blocker real para Repository Hygiene, não motivo para enfraquecer a suíte;
- runner GitHub-hosted falhando antes de steps: blocker externo de execução, separado de falha de conteúdo;
- runner NODE-01 ocupado por G2-B: não cancelar/interferir.

## Decisões negativas

`state/active-mission.yaml` e `ROADMAP-CHECKLIST.md` continuam `NOT_ADOPTED`; nenhum código funcional G2-B/F1.2c foi importado; nenhuma ação privilegiada/produção/branch cleanup foi executada.

Próximo passo após integração: **retomar as frentes F1.2c e G2-B preservando o HUMAN_GATE de produção**.
