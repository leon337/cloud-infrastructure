# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `leon337/cloud-infrastructure`.

## Regra de verdade

Use esta precedência para qualquer decisão operacional:

1. instrução explícita atual de LEANDRO;
2. GitHub e infraestrutura verificáveis ao vivo;
3. testes/evidências executáveis vinculados a SHA;
4. `state/current.yaml` e este checkpoint;
5. documentação canônica;
6. histórico.

Nunca transforme estado desejado em estado observado.

## Mapa canônico atual

| Pergunta | Fonte |
|---|---|
| Estado estruturado reconciliado | `state/current.yaml` |
| Checkpoint de continuidade | `CHECKPOINT.md` |
| Painel executivo | `README.md` |
| Decisões Platform Discovery Q1–Q40 | `state/platform-discovery.yaml` |
| Contrato de execução histórico/vinculante | `docs/CODEX-EXECUTION-MISSION-001.md` |
| Validação canônica do repositório | `scripts/test.sh` + `.github/workflows/canonical-validation.yml` |

## Estado reconciliado em 22/08/2026

`main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b` está em `DOCUMENTATION_AND_INTEGRATION_DRIFT`.

Fatos que não podem ser promovidos além da evidência:

- S0, F1.1 e F1.2b: concluídos conforme a reconciliação integrada;
- F1.2c: `REQUIRES_REVIEW`; recovery candidate estático verde, mas KVM acceptance não executado e NODE-01 sem reapply;
- Control Bridge G1: `PASS_REAL_NODE_01_ROUNDTRIP`;
- Control Bridge G2-A: `PASS_REAL_NODE_01_READ_ONLY`;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: último terminal comprovado `FAILED_ATTEMPT_3_NOT_ACCEPTED`; causa `NOT_VERIFIED`; diagnóstico isolado `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`;
- Repository Hygiene: `REPOSITORY_HYGIENE_BLOCKED` até state/toolchain executarem e os blockers reais de higiene serem tratados.

## Toolchain canônica

`scripts/test.sh` é o entrypoint canônico. A extração mainline-neutral preserva os gates genéricos separáveis do contrato F1.1:

- `git diff --check` contra a base de integração;
- secret policy na árvore atual e em todos os blobs Git alcançáveis;
- links Markdown locais;
- YAML estrito com rejeição de chaves duplicadas;
- invariantes de `state/current.yaml`;
- consistência README/CONTEXT/CHECKPOINT/state;
- testes unitários;
- sintaxe Python/shell;
- ShellCheck.

O executor canônico de integração também preserva o boundary F1.1: GitHub-hosted `ubuntu-24.04`, Python 3.12 e dependências lockadas em `requirements-dev.lock`. O lock neutro contém somente `PyYAML==6.0.3`, pois dependências F1.1 acopladas a Ansible/manifests não pertencem a esta extração.

`.github/workflows/canonical-validation-maintenance-proof.yml` é uma prova alternativa restrita às branches `team/canonical-state-toolchain-*` ou disparo manual. Ela usa NODE-01 somente como executor não privilegiado e recusa passwordless sudo ou Docker socket gravável. Não substitui o CI hospedado canônico.

`validate_manifests.py` não é importado porque depende de schemas/manifests da implementação F1.1. A toolchain neutra não enfraquece o secret gate para fabricar resultado verde.

## Modelo de missão ativa

`state/active-mission.yaml` permanece `NOT_ADOPTED`: sua lineage G2-B modela uma missão ativa única, enquanto o projeto possui frentes isoladas paralelas.

`ROADMAP-CHECKLIST.md` permanece `NOT_ADOPTED`: sua origem comprovada é um checkpoint específico da Task 8 G2-B. `README.md` permanece a projeção executiva.

## Guardrails

- LEANDRO é autoridade humana final.
- MESTRE orquestra a missão.
- nenhuma conclusão autoriza merge final, produção, escrita real G2-B ou reapply F1.2c;
- nenhuma operação privilegiada no NODE-01 pertence a esta frente;
- branches G2-B/F1.2c permanecem isoladas;
- secrets nunca são versionados.

## Próximo passo exato

**EXECUTE_HOSTED_CANONICAL_CI_AND_MAINTENANCE_PROOF_THEN_HANDOFF_HYGIENE_FINDINGS**.
