# 21 — Platform Discovery Checkpoint 010 — Q22

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q21.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q22 — Identidade, autenticação e autoridade temporária de agentes/sistemas

**Escolha de LEANDRO: C — identidade individual + credenciais/sessões temporárias e escopadas por projeto, missão e capacidade.**

### Decisão

Cada agente, sistema, cliente MCP, pipeline, CLI ou workload relevante deve possuir identidade distinguível. A identidade pode ser duradoura, mas a autoridade operacional concedida a essa identidade deve ser temporária e limitada ao escopo necessário.

Modelo conceitual:

```text
IDENTIDADE
   +
PROJETO
   +
MISSÃO
   +
CAPACIDADES SOLICITADAS
   +
TEMPO/VALIDADE
      |
      v
POLICY / AUTHORIZATION
      |
      v
SESSÃO OU CREDENCIAL ESCOPADA
      |
      v
AGENT GATEWAY -> CAPABILITY CORE
```

### Princípio central

**Identidade permanente; autoridade temporária e escopada.**

Uma identidade como Hermes, MCF, TriView, Codex Executor, GitHub Pipeline, cliente MCP, CLI de LEANDRO ou serviço interno não deve receber uma master key universal da plataforma. Deve receber somente as capacidades necessárias para o projeto/missão autorizados e, quando tecnicamente possível, por tempo limitado.

### Escopo de autorização

A autorização poderá considerar dimensões como:

- identidade do agente/sistema;
- projeto;
- missão;
- sandbox/workload;
- capacidade solicitada;
- recurso de destino;
- validade temporal;
- classe de risco/política;
- HUMAN_GATE quando aplicável.

Exemplo conceitual:

```text
identity: hermes
project: controle-ponto
mission: M-047
capabilities:
  - create_sandbox
  - deploy_dev
  - get_logs
validity: temporary
```

Essa sessão não deve automaticamente permitir acesso a outros projetos, firewall, host shell irrestrito, credenciais do provedor, secrets globais ou produção.

### Auditoria

A plataforma deve poder registrar ações com contexto suficiente para responder quem fez o quê e em nome de qual missão/escopo, por exemplo:

```text
identity: hermes
project: controle-ponto
mission: M-047
capability: deploy_dev
sandbox: sb-389
result: PASS
```

### Relação com MCF e Capability Core

O MCF poderá declarar missão, autoridade e HUMAN_GATE conforme sua governança, mas a aplicação técnica das permissões continua pertencendo à plataforma/Capability Core/Agent Gateway. O sistema não deve confiar apenas em uma declaração textual de um agente de que possui autorização.

### Direção futura

A arquitetura deve ser compatível com evolução futura para identidade criptográfica de workloads, certificados, mTLS, PKI ou Zero Trust mais completo, mas essas camadas avançadas não são requisito obrigatório do primeiro release.

### Princípios derivados

- identidade individual por agente/sistema relevante;
- nenhuma API key compartilhada universal para todos;
- autoridade operacional temporária e escopada;
- least privilege por projeto/missão/capacidade;
- revogação/expiração quando tecnicamente viável;
- auditoria vinculada à identidade e missão;
- MCF pode governar a missão, mas o Capability Core aplica tecnicamente as permissões;
- credencial comprometida deve ter raio de impacto contido;
- evolução futura para workload identity/PKI/mTLS deve permanecer possível.

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
```

## Próximo passo

**DISCOVERY_Q23**.

A Discovery continua. Tenancy, limites DEV/staging/prod, tecnologias concretas e papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
