# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado para a reconciliação de 22/08/2026 registrada em `README.md`.

## Estado durável

- Repositório: `leon337/cloud-infrastructure`.
- `main`: painel/documentação integrada; não contém todas as linhagens ativas da plataforma e do Control Bridge.
- F0: `DONE`.
- F1 inicial: `DONE`.
- F2 Cloud Workstation: `DONE / FUNCTIONAL_AND_VALIDATED`.
- S0 Recovery: `DONE`.
- F1.1 Foundations: `DONE`.
- F1.2b Docker Boundary: `DONE`.
- F1.2c Network Enforcement: `PARTIAL`, com trabalho paralelo preservado.
- G1: `PASS_REAL_NODE_01_ROUNDTRIP`.
- G2-A: `PASS_REAL_NODE_01_READ_ONLY`.
- G2-B Tasks 1–7: `COMPLETE` no estado reconciliado do README.
- G2-B Task 8: `FAILED_ATTEMPT_3`, ainda não aceita.
- G2-B Tasks 9–10: `NOT_STARTED`.
- Merge G2-B: `NOT_ELIGIBLE`.
- Produção: `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- Rotação de credenciais: `DEFERRED_BY_HUMAN_DECISION`.

## Ownership e refs críticas

- `main` — ref canônica integrada.
- `mcf/mission-001-control-bridge-g1` — G1/G2-A, protegida.
- `codex/control-bridge-g2b` — G2-B ativo, PR #11 draft, protegida.
- `codex/mission-001-f1-2c-network-enforcement` — frente F1.2c.
- `fix/f1-2c-systemd-runtime-lock` — correções paralelas F1.2c; preservar trabalho local registrado.

Nenhuma sanitização deve reimplementar G2-B, reabrir arquitetura ou descartar trabalho F1.2c.

## Incidentes abertos relevantes

### G2-B Task 8

A terceira tentativa descartável terminou com `apply_g2b exit=2`. O snapshot reconciliado informa que o guest descartável foi preservado para investigação. Não há aceite da Task 8.

Próximo passo registrado:

```text
PRESERVE_G2B_ATTEMPT3_EVIDENCE_THEN_DIAGNOSE_EXIT_2_AND_CLEAN_DISPOSABLE_VM
```

### F1.2c

`cloud-platform-network-services.service` foi observada em `failed`. A próxima ação dessa frente é diagnóstico somente leitura antes de qualquer restart/reapply.

## Guardrails

- LEANDRO é a autoridade humana final.
- Q1–Q39 permanecem vinculantes; Q40-D não foi reaberta.
- Produção externa continua atrás de HUMAN_GATE.
- Secrets reais não podem ser persistidos no Git/evidência.
- G2-B não fornece shell arbitrário, root, sudo genérico ou Docker socket.
- Workflows self-hosted devem ser bounded; runner não é mecanismo de wait/polling.
- `PASS`, `DONE`, `SAFE_TO_DELETE` e equivalentes exigem evidência específica.

## Regra de retomada

1. consultar GitHub live;
2. ler `README.md`, `CONTEXT.md`, este checkpoint e `state/current.yaml`;
3. identificar a branch proprietária da frente;
4. ler state/evidence dessa branch sem promovê-los para `main` por inferência;
5. preservar divergências/worktrees antes de qualquer mutação;
6. respeitar HUMAN_GATEs e limites da frente.

O checkpoint de 18/08 que dizia `MISSION_ACCEPTANCE_AND_RECOVERY_REPORT` e descrevia execução manual por LEANDRO deixou de representar o estado atual e foi substituído por este checkpoint corrente. O histórico continua preservado no Git.
