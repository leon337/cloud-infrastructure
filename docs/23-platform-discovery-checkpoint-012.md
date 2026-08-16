# 23 — Platform Discovery Checkpoint 012 — Q24

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q23.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q24 — Tenancy, ownership e hierarquia de escopo

**Escolha de LEANDRO: C — Workspace/Tenant → Projeto → Missão → Sandbox, com isolamento e políticas em cada nível.**

### Decisão

A plataforma deve possuir uma fronteira explícita de propriedade acima do projeto. Projetos pessoais, da empresa e de clientes não devem coexistir em uma estrutura plana sem contexto de ownership.

Hierarquia conceitual:

```text
PLATAFORMA
   |
   v
WORKSPACE / TENANT
   |
   v
PROJETO
   |
   v
MISSÃO
   |
   v
SANDBOX
```

O nome concreto do nível superior ainda não está congelado; `workspace`, `tenant`, `organization` ou `namespace` permanecem possibilidades terminológicas. A decisão arquitetônica é a existência dessa fronteira de propriedade.

### Escopo e isolamento

A hierarquia deve permitir políticas e isolamento progressivos para recursos como:

- bancos;
- object storage;
- volumes;
- secrets;
- artefatos;
- deployments;
- logs, métricas e auditoria;
- backups;
- quotas e consumo de recursos;
- identidades e capacidades dos agentes.

Uma identidade autorizada para um projeto dentro de um tenant não deve obter, por padrão, acesso a projetos de outros tenants nem a recursos fora do seu escopo.

Exemplo conceitual de identidade contextual:

```text
identity = hermes
tenant   = cliente-alpha
project  = portal
mission  = 73
sandbox  = sb-73-a
```

### Relação com multi-tenancy comercial

A plataforma deve nascer com hierarquia e isolamento compatíveis com múltiplos owners, mas o primeiro release não precisa implementar um SaaS multi-tenant comercial completo com billing, planos, convites, portal de clientes ou RBAC empresarial complexo.

### Princípios derivados

- toda capacidade pertence a um escopo de propriedade antes de pertencer a um projeto;
- tenant/workspace é a fronteira superior de ownership;
- projeto é a unidade principal de desenvolvimento;
- missão e sandbox refinam o escopo operacional temporário;
- dados, secrets, logs, backups e artefatos devem respeitar a hierarquia;
- identidades e autorizações devem carregar contexto de tenant/projeto/missão quando aplicável;
- quotas e consumo devem poder ser agregados por tenant e projeto;
- a arquitetura deve suportar crescimento futuro para clientes/organizações sem exigir redesenho estrutural;
- o primeiro release não precisa incluir billing ou multi-tenancy SaaS comercial completo.

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
```

## Próximo passo

**DISCOVERY_Q25**.

A Discovery continua. Quotas/capacity management, jobs/queues, divisão Linux Mint↔VPS, tecnologias concretas, portabilidade multi-node e papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
