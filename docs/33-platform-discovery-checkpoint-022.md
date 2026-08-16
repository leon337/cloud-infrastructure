# 33 — Platform Discovery Checkpoint 022 — Q34

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q33.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q34 — Rede interna, isolamento e service discovery

**Escolha de LEANDRO: C — redes isoladas por tenant/projeto/sandbox + service discovery por nome/identidade + acesso explícito e auditável aos serviços compartilhados.**

### Decisão

A plataforma deve tratar redes de tenants, projetos e sandboxes como domínios isolados por padrão. Serviços não devem depender de IPs fixos; devem ser encontrados por identidade/nome através de um mecanismo de service discovery. Comunicação lateral entre tenants/projetos/sandboxes é negada por padrão. Acesso a serviços compartilhados da plataforma deve ocorrer somente por caminhos explicitamente autorizados, mediados por políticas/capacidades e auditáveis.

### Modelo conceitual

```text
              PLATFORM SERVICES
              ▲      ▲      ▲
              │ authorized  │
              │    access    │
       ┌──────┘      │      └──────┐
       │             │             │
 PROJECT A       PROJECT B      PROJECT C
 isolated         isolated       isolated
 network          network        network
```

### Regras derivadas

- serviços são referenciados por identidade/nome, não por IP fixo;
- tenants, projetos e sandboxes possuem isolamento de rede por padrão;
- comunicação lateral entre projetos/tenants é negada por padrão;
- serviços compartilhados da plataforma não devem ser expostos indiscriminadamente a todas as redes;
- acesso a serviços compartilhados exige política/capacidade explícita e gera trilha de auditoria;
- sandboxes temporários podem ser criados/destruídos sem alterar contratos de acesso baseados em nomes;
- a arquitetura deve permitir que um serviço mude futuramente de execution node sem alterar a interface consumida pelos agentes;
- a tecnologia concreta de networking/service discovery ainda não está congelada e será escolhida no technology mapping;
- service mesh/mTLS completo não foi escolhido como requisito obrigatório de V1 nesta decisão.

### Compatibilidade com decisões anteriores

Q34-C reforça:

- Q20-C: egress controlado e negação de acesso lateral/administrativo por padrão;
- Q21-C: Management Plane privado e Agent Gateway público mínimo;
- Q24-C: isolamento hierárquico por tenant/workspace, projeto, missão e sandbox;
- Q26-C: single-node first, multi-node ready;
- Q17-C: runtime container-first mediado pelo Capability Core.

### Princípio derivado

`ISOLATED_TENANT_PROJECT_SANDBOX_NETWORKS_SERVICE_DISCOVERY_BY_IDENTITY_EXPLICIT_AUDITABLE_SHARED_SERVICE_ACCESS`

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
```

## Próximo passo

**DISCOVERY_Q35**.

A próxima decisão deve definir objetivos de recuperação e criticidade (RPO/RTO), distinguindo estado irrecuperável/importante de workloads descartáveis e estabelecendo quanto dado e tempo de indisponibilidade são aceitáveis por classe de serviço.