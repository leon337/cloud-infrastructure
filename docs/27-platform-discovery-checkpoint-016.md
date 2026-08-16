# 27 — Platform Discovery Checkpoint 016 — Q28

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q27.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q28 — Jobs duráveis, tarefas longas, scheduling e workflows

**Escolha de LEANDRO: D — workflow engine durável/distribuído completo desde o primeiro release.**

### Decisão

A plataforma não deve limitar a primeira versão a processos síncronos, cron/timers ou apenas uma fila simples de jobs. A camada de execução assíncrona deve nascer apoiada em um workflow engine com semântica de execução durável, preparado para workflows longos e distribuídos.

A tecnologia concreta ainda não está congelada. A decisão é arquitetural e exige, desde o primeiro release, suporte conceitual a:

- execução durável;
- persistência de estado do workflow;
- retries controlados;
- idempotência;
- scheduling;
- cancelamento;
- timeouts;
- etapas dependentes;
- compensação/rollback quando aplicável;
- status consultável;
- logs, eventos e evidências;
- associação a tenant, projeto, missão e identidade solicitante;
- workers isolados e sujeitos às políticas do Capability Core;
- futura distribuição entre múltiplos workers/nós sem alterar a interface dos agentes.

### Compatibilidade com Q26

Q28-D **não substitui nem contradiz Q26-C**.

O primeiro release continua **single-node first** no plano físico. O workflow engine pode ser executado inicialmente no `NODE-01`, mas sua arquitetura e modelo operacional devem suportar múltiplos workers e futura distribuição entre execution nodes.

Portanto:

```text
PHYSICAL DEPLOYMENT V1
= SINGLE NODE

WORKFLOW EXECUTION MODEL V1
= DURABLE / DISTRIBUTED-CAPABLE
```

### Relação com Capability Core

O workflow engine não se torna autoridade administrativa. Ele executa trabalho autorizado e mediado pelas políticas da plataforma.

Fluxo conceitual:

```text
AGENT / MCF / PIPELINE
        |
        v
AGENT GATEWAY / CAPABILITY CORE
        |
     POLICY
        |
        v
DURABLE WORKFLOW ENGINE
        |
        v
ISOLATED WORKERS / SANDBOXES
        |
        v
RESULT + EVIDENCE
```

Workers não devem receber acesso irrestrito ao host ou ao Docker daemon. Credenciais e capacidades continuam temporárias, escopadas e auditáveis conforme decisões anteriores.

### Princípios derivados

- o estado do trabalho é durável mesmo quando processos/containers são descartáveis;
- falha de worker, processo ou reboot não deve fazer a plataforma esquecer uma missão em andamento;
- retries devem ser idempotentes e controlados;
- workflows devem carregar provenance e escopo de tenant/projeto/missão;
- execução física V1 permanece single-node, mas o workflow model nasce distribuído-capable;
- o workflow engine é mecanismo de execução, não fonte de autoridade;
- tecnologia/vendor do workflow engine ainda será selecionado posteriormente.

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
```

## Próximo passo

**DISCOVERY_Q29**.

A próxima decisão deve separar claramente a responsabilidade de governança/orquestração do MCF da responsabilidade de execução durável do workflow engine, evitando dois orquestradores concorrentes como fontes de verdade.