# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `leon337/cloud-infrastructure`.

## Regra de verdade

Hierarquia documental: `README.md` é o painel executivo canônico da missão; `ROADMAP-CHECKLIST.md` é seu checklist operacional detalhado; `state/current.yaml` é a projeção estruturada; este arquivo fornece contexto e entrada.

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

## Estado reconciliado em 22/08/2026 + atualização operacional de 28/08/2026

Baseline deste closeout: `main@ce829067a9a04eceaa6eaefd9553899b2ce14da1` em `DOCUMENTATION_AND_INTEGRATION_DRIFT`; esta branch projeta o estado live F1.2c posterior sem importar a lineage funcional para `main`.

Fatos que não podem ser promovidos além da evidência:

- S0, F1.1 e F1.2b: concluídos conforme a reconciliação integrada;
- F1.2c: `COMPLETE_LIVE_VERIFIED`; candidato `baaf839...` passou static/ShellCheck + KVM `ABSENT`/`EXACT_PRESENT` e o rollout autorizado terminou `RECOVERED` com pós-validação root PASS;
- Control Bridge G1: `PASS_REAL_NODE_01_ROUNDTRIP`;
- Control Bridge G2-A: `PASS_REAL_NODE_01_READ_ONLY`;
- G2-B Tasks 1–7: `COMPLETE`;
- G2-B Task 8: último terminal comprovado `FAILED_ATTEMPT_3_NOT_ACCEPTED`; causa `NOT_VERIFIED`; diagnóstico isolado `IN_PROGRESS_DIAGNOSTIC_REPRODUCTION`;
- G2-B Tasks 9–10: `NOT_STARTED`;
- produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`;
- Repository Hygiene: `REPOSITORY_HYGIENE_REVALIDATED`; a compatibilidade do PR #19 com a toolchain canônica foi comprovada e o blocker histórico de secrets foi resolvido.
- SSH key governance: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`; LEANDRO confirmou uso da `dsh-tunnel...` no acesso notebook→VPS; chave preservada e `authorized_keys` inalterado.
- Runner isolation: `CROSS_JOB_ISOLATION_VERIFIED_GLOBAL_HOOK_RESTART_PENDING`; PoC legado removido, policy/guard canônicos ativos e prova cross-job real PASS; hook global configurado, não carregado até restart autorizado.

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
- ShellCheck;
- policy de isolamento do runner, incluindo recusa de manipulação de `RUNNER_TRACKING_ID` e exigência de guard nos workflows self-hosted.

O executor canônico de integração também preserva o boundary F1.1: GitHub-hosted `ubuntu-24.04`, Python 3.12 e dependências lockadas em `requirements-dev.lock`. O lock neutro contém somente `PyYAML==6.0.3`, pois dependências F1.1 acopladas a Ansible/manifests não pertencem a esta extração.

`.github/workflows/canonical-validation-maintenance-proof.yml` é uma prova alternativa restrita às branches `team/canonical-state-toolchain-*`, `runner/isolation-*` ou disparo manual. Ela usa NODE-01 somente como executor não privilegiado e recusa passwordless sudo ou Docker socket gravável. Não substitui o CI hospedado canônico.

`validate_manifests.py` não é importado porque depende de schemas/manifests da implementação F1.1. A toolchain neutra não enfraquece o secret gate para fabricar resultado verde.

## Modelo de missão ativa

`state/active-mission.yaml` permanece `NOT_ADOPTED`: sua lineage G2-B modela uma missão ativa única, enquanto o projeto possui frentes isoladas paralelas.

`ROADMAP-CHECKLIST.md` está `ADOPTED` como checklist operacional detalhado da missão **IMPLEMENTAÇÃO DA VPS**, subordinado ao `README.md`. O README permanece o painel executivo canônico e consolidado; o checklist não constitui uma autoridade concorrente nem se estende ao MCF como projeto separado. `state/active-mission.yaml` permanece separado e `NOT_ADOPTED`.

## Guardrails

- LEANDRO é autoridade humana final.
- MESTRE orquestra a missão.
- conclusão F1.2c não autoriza merge funcional automático, produção, escrita real G2-B, reboot ou novo reapply;
- a operação privilegiada F1.2c autorizada foi concluída e consumida; novas operações privilegiadas exigem seus próprios gates;
- branches G2-B/F1.2c permanecem isoladas;
- secrets nunca são versionados.

## Próximo passo exato

**NETWORK_CONVERGENCE_P2**. F1.2c foi concluído no NODE-01 com evidência live; o próximo passo começa read-only e deve fechar `systemd-networkd` / `wait-online` antes de qualquer reboot. `SSH_KEY_GOVERNANCE_P1` continua preservando a `dsh-tunnel...`; o hardening de hooks globais do runner permanece pendente até restart autorizado do serviço.
