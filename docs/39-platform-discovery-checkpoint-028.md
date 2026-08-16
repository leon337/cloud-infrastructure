# 39 — Platform Discovery Checkpoint 028 — Q40

Data: 2026-08-16
Status: **CODEX_HANDOFF_AUTHORIZED**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q39.

## Q40 — Transição da Discovery para seleção tecnológica e implementação

**Escolha de LEANDRO: D — entregar ao Codex a seleção das tecnologias e a implementação.**

### Efeito da decisão

LEANDRO exerce HUMAN_GATE explícito para delegar ao Codex:

1. inspeção do estado canônico do repositório e do estado real da VPS;
2. seleção das tecnologias concretas que implementam as capacidades definidas em Q1–Q39;
3. documentação das decisões tecnológicas e dos trade-offs;
4. elaboração do blueprint técnico executável e roadmap incremental;
5. implementação progressiva e verificável da plataforma na VPS, respeitando os limites abaixo.

Esta escolha substitui o Technology Mapping manual conduzido pergunta por pergunta. O Codex passa a executar o Technology Mapping como parte da própria missão, mas **não recebe autoridade para reabrir ou contrariar Q1–Q39**.

## Guardrails obrigatórios

Q1–Q39 são requisitos arquitetônicos vinculantes e constituem a especificação de alto nível.

A autorização NÃO inclui:

- promoção de workloads para produção externa;
- alteração da autoridade final de LEANDRO;
- remoção de HUMAN_GATEs definidos nas decisões anteriores;
- versionamento de senhas, tokens, chaves privadas, API keys, 2FA ou connection strings reais;
- exposição direta do Management Plane à Internet;
- concessão de Docker daemon/root irrestrito a agentes;
- destruição da Cloud Workstation existente sem plano de rollback e autorização específica quando houver impacto humano relevante;
- rotação das credenciais atualmente marcadas como `DEFERRED_BY_HUMAN_DECISION`;
- alteração silenciosa das decisões Q1–Q39.

### Produção continua separada

A autorização é para construir a plataforma privada de desenvolvimento/laboratório e suas capacidades DEV/staging/sandbox.

A promoção para produção continua sujeita ao modelo estabelecido em Q23:

```text
DEV / STAGING
    -> autonomia dentro do escopo autorizado

PRODUCTION PROMOTION
    -> HUMAN_GATE de LEANDRO
```

## Modo de execução do Codex

O Codex deve trabalhar em incrementos pequenos, reversíveis e verificáveis:

```text
INSPECT
  -> SELECT TECHNOLOGY
  -> DOCUMENT DECISION
  -> IMPLEMENT SMALL SLICE
  -> TEST
  -> COLLECT EVIDENCE
  -> CHECKPOINT
  -> NEXT SLICE
```

Para mudanças críticas do host, rede, SSH, firewall, secret store, backup/recovery ou Management Plane, aplicar análise de impacto, rollback e evidência antes de prosseguir.

## Fonte de verdade

- GitHub `leon337/cloud-infrastructure` = estado desejado, decisões, documentação e checkpoints.
- VPS real = estado operacional a ser inspecionado antes de qualquer alteração.
- Q1–Q39 = arquitetura vinculante.
- LEANDRO = autoridade humana final.

## Estado das decisões

```text
Q1  = C
Q2  = C
Q3  = C
Q4  = C
Q5  = D
Q6  = C
Q7  = C
Q8  = C
Q9  = C
Q10 = C
Q11 = D
Q12 = C
Q13 = C
Q14 = C
Q15 = C
Q16 = C
Q17 = C
Q18 = C
Q19 = C
Q20 = C
Q21 = C
Q22 = C
Q23 = C
Q24 = C
Q25 = C
Q26 = C
Q27 = C
Q28 = D
Q29 = C
Q30 = C
Q31 = C
Q32 = C
Q33 = C
Q34 = C
Q35 = C
Q36 = C
Q37 = C
Q38 = C
Q39 = C
Q40 = D
```

## Próximo passo

Preparar e entregar a missão canônica `CODEX-EXECUTION-MISSION-001`, na qual o Codex recebe a delegação para Technology Mapping + blueprint técnico + implementação incremental da plataforma, mantendo todos os guardrails deste checkpoint.

Atualização de continuidade em 16/08/2026: a missão foi criada e aceita; o
MISSION ACCEPTANCE + RECOVERY REPORT está em
`40-mission-acceptance-recovery-report.md` e o slice F1.1 foi iniciado. A revisão
de safety posterior rebaixou o desired state; a remediação foi vinculada ao commit
`edd2497d657cc9bc35952f5dfc71090a18dade53` e passou no GitHub Actions run
`31972460567`, inclusive check mode, apply, `changed=0`, recusas fail-closed,
rollback e cleanup na VM descartável. Nenhuma operação privilegiada ocorreu na
VPS real. O próximo passo é somente check mode privilegiado no NODE-01, com sudo
digitado diretamente por LEANDRO; apply depende da reconciliação desse preview.
Essa atualização operacional não reabre Q1–Q40.
