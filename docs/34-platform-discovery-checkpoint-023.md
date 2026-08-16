# 34 — Platform Discovery Checkpoint 023 — Q35

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q34.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q35 — Classes de criticidade, RPO/RTO e recuperação

**Escolha de LEANDRO: C — classes de criticidade + RPO/RTO diferenciados + restore testado.**

### Decisão

A plataforma não deve aplicar a mesma política de recuperação a todo tipo de estado. Cada classe de estado terá objetivos de recuperação, retenção, frequência de backup e testes de restore proporcionais à sua criticidade.

Modelo arquitetural aprovado:

- **CRITICAL** — estado cuja perda compromete governança, continuidade ou capacidade de recuperação da plataforma;
- **IMPORTANT** — dados persistentes relevantes de projetos, bancos DEV importantes, object storage e evidências;
- **REBUILDABLE** — componentes, serviços, containers, caches e artefatos que podem ser reconstruídos a partir de Git/registry/configuração declarativa;
- **DISPOSABLE** — sandboxes, previews, filesystems temporários e workers cuja recuperação normal é recriação.

Os valores numéricos exatos de RPO e RTO ainda não estão congelados. Eles serão definidos no Infrastructure Blueprint conforme criticidade, custo, tecnologia escolhida, capacidade do ambiente e impacto operacional.

### Regras derivadas

- nem todo estado merece o mesmo nível de proteção;
- backup não é considerado confiável sem restore testado;
- classes CRITICAL e IMPORTANT exigem política explícita de backup, retenção, integridade e restore;
- componentes REBUILDABLE devem ser restauráveis principalmente por reconstrução declarativa;
- componentes DISPOSABLE podem ser recriados em vez de restaurados;
- testes periódicos de restore devem produzir evidência verificável;
- a estratégia permanece compatível com `REBUILDABLE_COMPUTE_OFFHOST_AUTOMATED_BACKUP_TESTED_RESTORE_PROVIDER_PORTABLE` da Q16.

### Princípio derivado

`CRITICALITY_CLASSIFIED_STATE_DIFFERENTIATED_RPO_RTO_BACKUP_RETENTION_AND_TESTED_RESTORE`

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
```

## Próximo passo

**DISCOVERY_Q36**.

A próxima decisão deve definir o modelo de integração interna entre componentes — comandos síncronos versus eventos assíncronos/duráveis — evitando acoplamento ponto a ponto entre MCF, Capability Core, Workflow Engine, observabilidade, TriView e demais componentes.