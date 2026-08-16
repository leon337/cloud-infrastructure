# 35 — Platform Discovery Checkpoint 024 — Q36

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q35.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q36 — Comunicação entre componentes: comandos e eventos

**Escolha de LEANDRO: C — comandos síncronos via API/Capability Core + eventos assíncronos duráveis em um Event Backbone, com identidade, correlação e entrega confiável.**

### Decisão

A plataforma deve separar explicitamente dois modelos de comunicação:

1. **Comandos** — pedidos direcionados para que uma operação seja executada, usando API/MCP/CLI e passando pelo Capability Core quando houver autoridade/capacidade envolvida.
2. **Eventos** — fatos imutáveis de que algo aconteceu, publicados em um backbone assíncrono e durável para consumo desacoplado por MCF, TriView, observabilidade e outros componentes autorizados.

Fluxo conceitual:

```text
COMMAND
AGENT / MCF / SYSTEM
        |
        v
API / MCP / CLI
        |
        v
CAPABILITY CORE
        |
        v
WORKFLOW / SERVICE

EVENT
WORKFLOW / SERVICE
        |
        v
DURABLE EVENT BACKBONE
     /      |       \
    v       v        v
   MCF   TRIVIEW   OBSERVABILITY
```

### Requisitos derivados

Eventos devem carregar identidade e contexto suficientes para rastreabilidade, incluindo quando aplicável:

- `event_id`;
- `event_type`;
- `tenant_id`;
- `project_id`;
- `mission_id`;
- `source`;
- `timestamp`;
- `correlation_id`;
- payload versionado.

A entrega deve ser confiável o suficiente para que consumidores temporariamente indisponíveis possam recuperar eventos pendentes conforme sua política de retenção/consumo.

A tecnologia concreta do backbone ainda não está congelada. Não fica decidido nesta etapa se será NATS, RabbitMQ, Redis Streams, Kafka, mecanismo do workflow engine ou outra implementação.

### Relação com decisões anteriores

- **Q5**: comandos continuam expostos por Capability Core + API/MCP/CLI.
- **Q15**: eventos alimentam evidência, auditoria e observabilidade.
- **Q22/Q24**: identidade, tenant, projeto e missão acompanham a comunicação.
- **Q28**: o workflow engine mantém execução durável, mas não precisa chamar diretamente cada consumidor.
- **Q29**: MCF e Workflow Engine permanecem desacoplados por domínio; eventos comunicam mudanças sem fundir fontes de verdade.
- **Q30**: o ecossistema modular evita uma teia de integrações ponto a ponto.

### Princípios derivados

- comandos dizem **o que deve acontecer**;
- eventos registram **o que aconteceu**;
- produtores de eventos não precisam conhecer todos os consumidores;
- operações interativas e consultas simples não devem ser artificialmente transformadas em eventos;
- não fica adotado event sourcing completo para toda a plataforma nesta decisão.

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
```

## Próximo passo

**DISCOVERY_Q37**.

A próxima decisão deve definir o modelo de ingress público, namespaces de domínio, URLs de preview e TLS automático sem expor serviços internos nem misturar DEV com produção.