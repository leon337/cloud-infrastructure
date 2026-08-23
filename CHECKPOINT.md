# CHECKPOINT — State + Toolchain canônicos

Atualizado em 22/08/2026 após autorização explícita de LEANDRO para uma extração mainline-neutral de state + validação.

## Estado da frente

- Repositório: `leon337/cloud-infrastructure`.
- Base: `main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b`.
- Branch isolada: `team/canonical-state-toolchain-20260822`.
- PR: `#22`, draft, sem autorização de merge final.
- HUMAN_GATE: resolvido por LEANDRO com autorização da extração neutra.
- Estado atual: `HARDENED_CANONICAL_VALIDATION_PENDING`.

## State canônico

`state/current.yaml` foi reconciliado a partir de evidência ao vivo e separa estado atual de snapshots históricos.

Fatos principais:

- integração de `main`: `DOCUMENTATION_AND_INTEGRATION_DRIFT`;
- F1.2c: `REQUIRES_REVIEW`, recovery candidate estático verde, KVM acceptance não executado por falha externa pré-step, NODE-01 sem reapply autorizado;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: `FAILED_ATTEMPT_3_NOT_ACCEPTED`, causa `NOT_VERIFIED`, diagnóstico isolado `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: não autorizada;
- Repository Hygiene: `REPOSITORY_HYGIENE_BLOCKED` até a suíte canônica executar e os blockers reais de higiene serem tratados.

## Toolchain canônica

Entry point: `scripts/test.sh`.

Origem comprovada do contrato: commit `edd2497d657cc9bc35952f5dfc71090a18dade53`, lineage `codex/mission-001-foundations-f1-1`, PR #2.

A extração neutra preserva os gates genéricos separáveis:

- `git diff --check`;
- scanner de secrets da árvore atual e de todos os blobs Git alcançáveis;
- links Markdown locais;
- YAML estrito, incluindo recusa de chaves duplicadas;
- state e consistência documental;
- unit tests do contrato;
- sintaxe Python/shell e ShellCheck.

`validate_manifests.py` não é importado porque exige schemas/manifests da implementação F1.1. O scanner histórico de secrets foi preservado deliberadamente; remover esse gate apenas para obter PASS seria não canônico e impediria Repository Hygiene de detectar seu próprio blocker.

## Evidência de validação

Primeiro candidato neutro: `55cbbf0be25daa9fef5ca4ac231f6bd4f74c8ea6`.
Run `32609819790`, job `97120890824`:

- checkout exato: PASS;
- boundary não privilegiado: PASS;
- ShellCheck pin/hash: PASS;
- workspace limpo: PASS;
- suíte: FAIL no primeiro `git diff --check`, por quatro trailing spaces desta frente.

As quatro ocorrências foram corrigidas. Antes de aceitar a segunda tentativa, a auditoria de canonicidade também restaurou o scanner histórico, Markdown links e YAML estrito, produzindo um novo candidato endurecido que deve ser validado do zero.

## Decisões negativas explícitas

- `state/active-mission.yaml`: **NÃO ADOTADO**; modelo single-active não comprovado para as frentes paralelas atuais.
- `ROADMAP-CHECKLIST.md`: **NÃO ADOTADO**; origem específica G2-B Task 8.
- código funcional G2-B: não importado.
- código funcional F1.2c: não importado.
- operação privilegiada NODE-01: não executada.
- produção: não promovida.
- branch cleanup: não executado.

## Gate de conclusão

A frente precisa executar o candidato endurecido em SHA exato. Um eventual `SECRET_POLICY_FAIL` originado em histórico preexistente será classificado como **blocker real de Repository Hygiene**, não como motivo para enfraquecer a toolchain.

Próximo passo: **EXECUTE_HARDENED_CANONICAL_VALIDATION**.
