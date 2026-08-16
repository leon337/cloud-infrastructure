# 24 — Platform Discovery Checkpoint 013 — Q25

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q24.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q25 — Quotas, limites e capacidade compartilhada

**Escolha de LEANDRO: C — reserva da plataforma + quotas hierárquicas + limites por workload + burst controlado + fila quando faltar capacidade.**

### Decisão

A VPS deve preservar uma reserva operacional para o sistema e os componentes críticos da plataforma, impedindo que workloads de projetos, agentes, builds, sandboxes ou tenants consumam recursos suficientes para tornar o laboratório inadministrável.

A capacidade destinada a workloads deve ser governada hierarquicamente por tenant/workspace, projeto, missão e sandbox, com limites individuais, quotas agregadas e políticas de prioridade.

Estrutura conceitual:

```text
                VPS
                 |
       +---------+---------+
       |                   |
PLATFORM RESERVE      WORKLOAD POOL
                           |
                    QUOTA / SCHEDULER
                           |
               +-----------+-----------+
               |           |           |
            Tenant A    Tenant B    Tenant C
               |
             Project
               |
             Mission
               |
             Sandbox
```

### Reserva da plataforma

Devem permanecer protegidos recursos suficientes para manter operacionais, conforme aplicável:

- sistema operacional;
- SSH/acesso de recuperação;
- Capability Core;
- Management Plane e Agent Gateway;
- observabilidade;
- backup/recovery;
- componentes essenciais de controle e segurança.

Workloads de aplicação e agentes não devem consumir essa reserva por operação normal.

### Quotas e limites

A arquitetura deve suportar, de forma progressiva:

- limites máximos por sandbox/job/workload;
- quotas agregadas por projeto;
- quotas agregadas por tenant/workspace;
- limites de CPU, RAM, disco, processos e concorrência quando tecnicamente aplicável;
- limites para quantidade de sandboxes/jobs simultâneos;
- quotas de storage e outros recursos persistentes;
- políticas diferenciadas por classe de workload.

Os valores concretos não são congelados nesta decisão e deverão ser definidos a partir da capacidade real, medições e testes.

### Burst controlado

Recursos ociosos poderão ser utilizados de forma temporária quando a política permitir, desde que isso não comprometa a reserva da plataforma nem garantias de workloads de maior prioridade.

### Fila e admissão

Quando não houver capacidade segura para iniciar novo trabalho, a plataforma deve preferir fila/admission control em vez de iniciar todos os workloads e degradar a VPS.

Resultados conceituais de uma solicitação de recursos:

- `GRANTED`;
- `QUEUED`;
- `DENIED_BY_POLICY`.

### Prioridade

A arquitetura deve permitir classes de prioridade para preservar a plataforma e favorecer trabalho relevante. A taxonomia exata será definida posteriormente, mas a infraestrutura crítica deve sempre prevalecer sobre workloads descartáveis ou de background.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `get_capacity()`;
- `get_usage()`;
- `get_project_quota()`;
- `request_resources()`;
- `release_resources()`;
- `queue_job()`;
- `cancel_job()`;
- `get_queue()`;
- aplicar quotas e prioridades segundo política.

### Princípios derivados

- nenhum workload pode consumir recursos suficientes para tornar a plataforma inadministrável;
- a própria plataforma possui reserva operacional protegida;
- recursos são limitados por workload e orçados hierarquicamente por tenant/projeto/missão/sandbox;
- capacidade livre pode ser compartilhada/burst apenas de forma controlada;
- falta de capacidade deve gerar fila ou negação por política, não oversubscription descontrolada;
- observabilidade deve alimentar decisões de capacidade;
- valores concretos de quotas e tecnologias de scheduling ainda não estão congelados;
- a arquitetura deve permanecer compatível com evolução futura para múltiplos nós sem exigir scheduler distribuído no primeiro release.

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
```

## Próximo passo

**DISCOVERY_Q26**.

A Discovery continua. Portabilidade/multi-node, divisão de responsabilidades entre workstation local e VPS, lifecycle/patching, tecnologias concretas e papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
