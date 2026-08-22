# R8 / Task 7 Completion — 2026-08-22

## Identificação e classificação

ID: `R8_TASK7_COMPLETION_2026_08_22`  
Classificação: `SECURITY_CORRECTION_AND_MISSION_TRANSITION`  
Issue: `#10`  
PR principal: `#11` — draft / do not merge

## Contexto anterior

R7 havia preservado Task 7 como `PARTIAL`, com 6/7 testes focados, RED `EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED` e ausência de prova de sintaxe Ansible.

## Evento observado

R8 reproduziu o RED, corrigiu o playbook para exigir o conjunto exato de chaves do grant existente e executou novamente as validações aplicáveis.

## Impacto

Task 7 passou de `PARTIAL` para `COMPLETE`. R8 foi concluída e a missão ativa voltou ao Control Bridge G2-B. Task 8 permaneceu não iniciada.

## Evidência

- candidato: `604e6d0e1fb1feddb7f271c58c9e8baf2cc0b390`;
- focused tests: `7 PASS / 0 FAIL`;
- regressão local: `367` testes PASS e `15` scripts com sintaxe PASS;
- Ansible: `3` syntax-checks PASS no self-hosted runner;
- Issue #10 comment: `R8_TASK7_SELF_HOSTED_VALIDATION=PASS`;
- GitHub-hosted `foundation-ci` run `32548752333`: falha pré-step, zero steps, logs `BlobNotFound`, conteúdo inconclusivo.

## Resposta ou recuperação

Foi usada validação self-hosted limitada a testes e syntax-checks, com Python pinado por `actions/setup-python` e dependências de `requirements-dev.lock`.

## Causa ou lacuna comprovada

O playbook de lifecycle validava apenas campos mínimos de um grant existente, enquanto o contrato canônico do executor exigia schema top-level exato. Isso permitia divergência de política.

A causa da falha GitHub-hosted não foi inferida além da evidência disponível: job falhou antes de steps e logs retornaram `BlobNotFound`.

## Decisões

- exigir schema exato no playbook de grant;
- aceitar Task 7 somente após 7/7 e 3/3 syntax-checks;
- preservar R7 como snapshot histórico;
- retornar a missão ativa para `CONTROL_BRIDGE_G2B`;
- não iniciar Task 8 durante R8.

## Ações corretivas e preventivas

- drift checker atualizado para permitir avanço comprovado sem apagar snapshots históricos;
- entrypoints reconciliados com o estado pós-R8;
- evidência de validação vinculada ao SHA do candidato.

## Riscos residuais

- GitHub-hosted CI continua inconclusivo por falha pré-step;
- Task 8 ainda precisa provar lifecycle completo em boundary descartável;
- NODE-01, grant real, escrita real, produção e merge permanecem fechados.

## Relação com estado atual

Estado atual: `TASK_7_COMPLETE_TASK_8_NOT_STARTED`. Próximo passo: `G2B_TASK8_PROVE_COMPLETE_LIFECYCLE_DISPOSABLE_BOUNDARY`.

## Referências duráveis

- `state/active-mission.yaml`;
- `state/control-bridge-g2b.yaml`;
- `CHECKPOINT.md`;
- `docs/53-repository-continuity-context-recovery-mission.md`;
- `docs/54-control-bridge-g2b-recovery-checkpoint.md`;
- Issue #10;
- PR #11.
