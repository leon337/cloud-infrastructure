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
| Validação canônica do repositório | `scripts/test.sh` |

## Estado reconciliado em 22/08/2026

`main@f2e01dfa1247d648a4c6e2ecf5ecc0f57ce0db8b` está em `DOCUMENTATION_AND_INTEGRATION_DRIFT`: o README consolidou evidência posterior às antigas projeções de `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml`.

Fatos que não podem ser promovidos além da evidência:

- S0, F1.1 e F1.2b: concluídos conforme a reconciliação integrada;
- F1.2c: `REQUIRES_REVIEW`; existe recovery candidate com validação estática verde, mas a aceitação KVM continua não executada por falha externa pré-step do runner e NODE-01 não recebeu reapply;
- Control Bridge G1: `PASS_REAL_NODE_01_ROUNDTRIP`;
- Control Bridge G2-A: `PASS_REAL_NODE_01_READ_ONLY`;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: último resultado terminal comprovado `FAILED_ATTEMPT_3_NOT_ACCEPTED`; a causa do `exit=2` continua `NOT_VERIFIED` e há uma reprodução diagnóstica isolada `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`;
- Repository Hygiene: `REPOSITORY_HYGIENE_BLOCKED` até state + toolchain canônicos terem evidência executável e os próprios gates de higiene serem satisfeitos.

## Toolchain canônica

`scripts/test.sh` é o entrypoint canônico, preservando o contrato estabelecido originalmente na lineage F1.1. A implementação atual é uma extração mainline-neutral: valida somente contratos que pertencem ao `main` atual e não importa implementação funcional de G2-B ou F1.2c.

A suíte preserva os gates genéricos separáveis do contrato original:

- `git diff --check` contra a base de integração;
- secret policy na árvore atual **e em todos os blobs Git alcançáveis**;
- links Markdown locais;
- YAML estrito com rejeição de chaves duplicadas;
- invariantes de `state/current.yaml`;
- consistência entre README, CONTEXT, CHECKPOINT e state;
- testes unitários do contrato;
- sintaxe Python e shell;
- ShellCheck obrigatório no CI.

O validador de manifests F1.1 não foi importado porque depende de schemas/manifests da implementação da plataforma. A toolchain neutra não enfraquece o secret gate para fabricar um resultado verde: se o histórico do repositório violar a política, a suíte deve falhar e entregar esse blocker à Repository Hygiene.

## Modelo de missão ativa

`state/active-mission.yaml` não faz parte do pacote mainline-neutral neste checkpoint. O arquivo recuperado surgiu na continuidade G2-B e modela uma missão ativa única, enquanto o projeto possui frentes isoladas paralelas. Adotá-lo agora exigiria inventar governança não formalizada.

`ROADMAP-CHECKLIST.md` também não é promovido: sua origem comprovada é um checkpoint específico da Task 8 G2-B. O `README.md` permanece a projeção executiva.

## Guardrails

- LEANDRO é autoridade humana final.
- MESTRE orquestra a missão.
- nenhuma conclusão desta reconciliação autoriza merge final, produção ou escrita real G2-B;
- nenhuma conclusão autoriza reapply F1.2c no NODE-01;
- nenhuma operação privilegiada no NODE-01 pertence a esta frente;
- branches G2-B/F1.2c permanecem isoladas;
- secrets nunca são versionados.

## Próximo passo exato

**EXECUTE_HARDENED_CANONICAL_VALIDATION_THEN_HANDOFF_REPOSITORY_HYGIENE_RESULTS**.
