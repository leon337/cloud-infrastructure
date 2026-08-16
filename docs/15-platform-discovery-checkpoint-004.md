# 15 — Platform Discovery Checkpoint 004 — Q16

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua:

- `docs/12-platform-discovery-checkpoint-001.md` — Q1–Q9;
- `docs/13-platform-discovery-checkpoint-002.md` — Q10–Q13;
- `docs/14-platform-discovery-checkpoint-003.md` — Q14–Q15.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q16 — Recuperação diante da perda completa da VPS

**Escolha de LEANDRO: C — infraestrutura reconstruível + backups automáticos off-host + restore testado.**

### Decisão

A plataforma não deve depender da sobrevivência física da VPS atual. A arquitetura deve separar claramente:

1. **estado reconstruível** — código, manifests, automações, configuração versionável, documentação e definições da plataforma;
2. **estado que exige backup** — bancos persistentes, object storage importante, volumes persistentes, estado necessário da plataforma e segredos protegidos;
3. **estado descartável** — sandboxes temporários, previews, caches, builds e filesystem temporário.

A perda completa da VPS não deve significar perda do projeto nem exigir reconstrução artesanal baseada na memória de LEANDRO.

### Backup e recovery

A política-alvo deve prever:

- backups automáticos dos dados persistentes relevantes;
- cópia off-host independente da VPS;
- retenção apropriada;
- integridade verificável;
- testes reais de restore;
- capacidade progressiva de reconstruir projetos e, posteriormente, a própria plataforma a partir de Git + manifests/configuração + backups.

Backup somente local na mesma VPS não satisfaz a estratégia de proteção contra perda total do host.

### Restore testado

Uma execução de backup não deve ser considerada evidência suficiente de recuperabilidade. A arquitetura deve prever restauração em ambiente controlado e verificação de integridade/funcionalidade quando tecnicamente aplicável.

Fluxo conceitual:

```text
BACKUP
  -> cópia off-host
  -> restore em ambiente controlado
  -> verificação
  -> PASS/FAIL auditável
```

### Autonomia e HUMAN_GATE

Operações de baixo risco, como backup automático e restore de banco temporário de sandbox, poderão ser automatizadas conforme política.

Operações de maior impacto, como restore de dados persistentes principais, exclusão de backups, reconstrução global da VPS ou mudanças que afetem recovery da plataforma, deverão respeitar níveis superiores de autorização e HUMAN_GATE conforme threat model futuro.

### Relação com FND-BACKUP-001

Esta decisão transforma a lacuna já registrada em `findings/FND-BACKUP-001.md` em requisito arquitetônico explícito da Platform Discovery. O finding continua **MITIGATED — OPEN** até que backup amplo de workloads/dados, retenção off-host automatizada e reconstrução/restore suficiente sejam implementados e testados.

### Princípios derivados

- compute deve ser reconstruível;
- dados importantes devem ser recuperáveis;
- backup off-host é requisito para proteção contra perda total do host;
- backup só é confiável quando o restore é testado;
- estado descartável não deve inflar desnecessariamente a estratégia de backup;
- reconstrução deve depender de artefatos versionados e evidências, não da memória humana;
- arquitetura deve preservar portabilidade para outro host/provedor;
- alta disponibilidade multi-host não é exigida no primeiro release, mas a arquitetura não deve impedir evolução futura.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `backup_database()`;
- `restore_database()`;
- `backup_storage()`;
- `verify_backup()`;
- `snapshot_project_state()` quando aplicável;
- `restore_project_state()`;
- `rebuild_project()`;
- `rebuild_platform()` em estágio posterior;
- registrar evidências de backup, restore e verificação.

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
```

## Próximo passo

**DISCOVERY_Q17**.

A Discovery continua. Nenhuma implementação pesada nem missão de implementação para o Codex está autorizada neste ponto.
