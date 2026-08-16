# 37 — Platform Discovery Checkpoint 026 — Q38

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q37.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q38 — Data Service Plane para bancos, cache, object storage e mensageria

**Escolha de LEANDRO: C — Data Service Plane compartilhado + isolamento lógico por tenant/projeto + sandboxes descartáveis + instâncias dedicadas somente quando requisitos exigirem.**

### Decisão

A plataforma deve oferecer capacidades persistentes de dados por meio de um plano compartilhado de serviços, evitando tanto a duplicação permanente de motores por projeto quanto o compartilhamento sem isolamento.

Princípio operacional:

> **Compartilhar o motor não significa compartilhar autoridade, namespace ou credenciais.**

O modelo prevê:

- motores de dados compartilhados por padrão quando tecnicamente adequado;
- isolamento lógico por tenant/workspace e projeto;
- credenciais independentes e escopadas;
- bancos, schemas, buckets, prefixes, cache namespaces, filas/topics e políticas segregados;
- quotas e classificação de backup/criticidade por escopo;
- recursos temporários descartáveis para missão/sandbox;
- instâncias dedicadas quando versão, extensão, carga, sensibilidade, requisitos de cliente ou isolamento justificarem;
- ausência de dependência obrigatória de clones completos de plataformas SaaS.

### Compatibilidade com decisões anteriores

A decisão mantém compatibilidade com:

- Q7: compute descartável e estado importante explicitamente persistente;
- Q10: banco DEV persistente por projeto + bancos temporários de sandbox;
- Q11: armazenamento híbrido;
- Q12: secrets centralizados e credenciais escopadas;
- Q24: hierarquia Tenant/Workspace → Project → Mission → Sandbox;
- Q25: quotas hierárquicas e controle de capacidade;
- Q34: redes isoladas e acesso explícito a serviços compartilhados;
- Q35: criticidade e RPO/RTO diferenciados.

### Fluxo conceitual

```text
TENANT / PROJECT
       |
       v
CAPABILITY CORE
       |
       v
DATA SERVICE PLANE
  |       |       |
DB     STORAGE   CACHE/QUEUE
  |       |       |
logical isolation per tenant/project
```

Sandboxes podem solicitar recursos temporários, que são destruídos no encerramento da missão quando não houver requisito de persistência.

### Princípio derivado

`SHARED_DATA_SERVICE_PLANE_LOGICAL_TENANT_PROJECT_ISOLATION_DEDICATED_WHEN_REQUIRED_DISPOSABLE_SANDBOX_RESOURCES`

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
```

## Próximo passo

**DISCOVERY_Q39**.

A próxima decisão deve definir a tecnologia conceitual de acesso ao **Management Plane privado**, preservando o Agent Gateway público e mínimo definido em Q21, sem expor interfaces administrativas diretamente à Internet.