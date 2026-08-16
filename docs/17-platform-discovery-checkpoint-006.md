# 17 — Platform Discovery Checkpoint 006 — Q18

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua:

- `docs/12-platform-discovery-checkpoint-001.md` — Q1–Q9;
- `docs/13-platform-discovery-checkpoint-002.md` — Q10–Q13;
- `docs/14-platform-discovery-checkpoint-003.md` — Q14–Q15;
- `docs/15-platform-discovery-checkpoint-004.md` — Q16;
- `docs/16-platform-discovery-checkpoint-005.md` — Q17.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q18 — Registry e armazenamento canônico de imagens/artefatos

**Escolha de LEANDRO: C — registry canônico independente/externo + cache local na VPS.**

### Decisão

Builds que produzam imagens OCI ou artefatos implantáveis devem publicar uma versão canônica e identificável em um registry independente do runtime imediato da VPS. A VPS poderá manter cache local para desempenho, mas esse cache não será a única fonte do artefato.

Princípio: **build once, deploy many.**

Fluxo conceitual:

```text
Git / revisão conhecida
   -> pipeline
   -> build/test
   -> imagem ou artefato imutável
   -> registry canônico
   -> deploy DEV / sandbox / preview / rollback
```

### Proveniência mínima desejada

Cada artefato deverá poder ser relacionado a:

- projeto;
- commit/revisão de origem;
- pipeline/build;
- status de testes/validações relevantes;
- identidade ou missão que acionou o build quando aplicável;
- digest/identificador imutável do artefato;
- data/hora de criação;
- ambientes/deployments que o utilizaram.

### Princípios derivados

- código identifica a origem; artefato identifica exatamente o que será executado;
- rollback deve preferir artefato já produzido e conhecido, não rebuild ad hoc;
- o cache local da VPS é descartável;
- perda da VPS não deve implicar perda dos artefatos canônicos necessários à recuperação;
- o registry deve ser compatível com imagens OCI quando aplicável;
- retenção e limpeza de artefatos devem seguir política explícita;
- segredos de autenticação do registry devem obedecer à decisão Q12;
- a tecnologia/provedor concreto do registry ainda não está congelado.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `publish_artifact()`;
- `list_artifacts()`;
- `get_artifact_provenance()`;
- `deploy_artifact()`;
- `rollback_to_artifact()`;
- `delete_expired_artifact()` conforme política;
- validar digest/imutabilidade antes do deploy.

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
```

## Próximo passo

**DISCOVERY_Q19**.

A Discovery continua. Nenhuma escolha tecnológica final de registry/provedor, banco, object storage, gateway, secret manager, CI/CD, observabilidade, execução de agentes ou desenho detalhado dos servidores MCP deve ser antecipada antes das decisões correspondentes.
