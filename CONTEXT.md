# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada operacional para qualquer IA, agente ou humano que assuma `leon337/cloud-infrastructure`.

## Ordem de recuperação

1. consultar o GitHub real e confirmar `main` e a branch que será trabalhada;
2. ler `README.md` como painel executivo consolidado;
3. ler este `CONTEXT.md` e `CHECKPOINT.md`;
4. ler `state/current.yaml` como estado estruturado da linha canônica;
5. para uma frente ativa, ler também o state/checkpoint existente **na branch proprietária**, sem promover WIP para `main` por inferência;
6. confrontar PRs/issues/evidências live antes de declarar `PASS`, `DONE`, autorização ou próximo passo.

Precedência: instrução atual de LEANDRO → infraestrutura/GitHub verificáveis → estado canônico corrente → decisões e requisitos aprovados → documentação histórica.

## Snapshot reconciliado corrente

Fonte: `README.md`, reconciliado em 22/08/2026 a partir de GitHub, worktrees e probes read-only no NODE-01.

- VPS/NODE-01: `OPERATIONAL_WITH_OPEN_INCIDENTS`.
- Plataforma: `IMPLEMENTATION_IN_PROGRESS`.
- S0, F1.1 e F1.2b: concluídos.
- F1.2c: parcial; a linha ativa permanece separada e não deve ser alterada por trabalhos transversais sem ownership explícito.
- Control Bridge G1: `PASS_REAL_NODE_01_ROUNDTRIP`.
- Control Bridge G2-A: `PASS_REAL_NODE_01_READ_ONLY`.
- Control Bridge G2-B: Tasks 1–7 concluídas; Task 8 em `FAILED_ATTEMPT_3`; Tasks 9–10 não iniciadas; PR #11 draft, não elegível para merge.
- produção externa: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- rotação de credenciais: `DEFERRED_BY_HUMAN_DECISION`.

## Linhas estruturais protegidas

- `main` — estado canônico integrado/documental;
- `mcf/mission-001-control-bridge-g1` — G1/G2-A e base do bridge;
- `codex/control-bridge-g2b` — trabalho G2-B em andamento.

A frente F1.2c continua paralela em `codex/mission-001-f1-2c-network-enforcement` e `fix/f1-2c-systemd-runtime-lock`. Não descartar worktrees ou commits dessa frente como efeito colateral de higiene.

## Incidentes atuais que afetam retomada

### G2-B Task 8

A tentativa descartável 3 terminou com `EXIT_2` em `apply_g2b`. A VM descartável ainda estava preservada no snapshot do README para investigação. Isso **não** é aceite da Task 8 e não autoriza Tasks 9–10.

Próxima ação registrada no painel executivo:

```text
PRESERVE_G2B_ATTEMPT3_EVIDENCE_THEN_DIAGNOSE_EXIT_2_AND_CLEAN_DISPOSABLE_VM
```

### F1.2c

`cloud-platform-network-services.service` foi observada em `failed`. O tratamento correto é diagnóstico somente leitura antes de restart/reapply. A sanitização do repositório não autoriza operação privilegiada no NODE-01.

## Guardrails invariantes

- LEANDRO é a autoridade humana final.
- Q1–Q39 permanecem requisitos arquitetônicos vinculantes; Q40-D continua sendo a autorização de implementação incremental DEV/lab já existente.
- nenhum trabalho transversal reabre arquitetura aprovada silenciosamente;
- produção continua sujeita a HUMAN_GATE;
- secrets reais não podem ser versionados ou publicados em evidência;
- agentes/runners não recebem root, shell administrativo irrestrito ou Docker socket por conveniência;
- claims de estado exigem evidência adequada ao snapshot/commit;
- histórico deve ser preservado como histórico, não apresentado como estado atual.

## Mapa de fontes

| Pergunta | Fonte primária |
|---|---|
| Estado executivo corrente | `README.md` |
| Ponto de retomada | `CHECKPOINT.md` |
| Estado estruturado canônico | `state/current.yaml` |
| Decisões Q1–Q40 | `state/platform-discovery.yaml` e checkpoints associados |
| Roadmap vigente | `docs/45-revised-implementation-roadmap.md` na linha de implementação pertinente |
| G2-B corrente | branch `codex/control-bridge-g2b`, PR #11 e evidência G2-B |
| F1.2c corrente | branches/PRs da frente F1.2c |
| Evidência histórica | `history/**`, `evidence/**`, PRs/issues concluídos |

## Regra de retomada

Nunca iniciar implementação a partir de um texto histórico isolado. Recuperar refs e PRs live, confirmar ownership e branch, identificar o último estado **comprovado**, preservar qualquer trabalho divergente e só então executar a próxima ação autorizada.
