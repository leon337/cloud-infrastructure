# 31 — Platform Discovery Checkpoint 020 — Q32

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q31.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q32 — Acesso e roteamento de modelos de IA

**Escolha de LEANDRO: C — AI/Model Gateway próprio, com catálogo de modelos, roteamento por política, secrets centralizados, quotas/custos auditáveis, fallback e suporte a provedores externos ou modelos locais como backends substituíveis.**

### Decisão

Os agentes, workflows e executores não devem depender diretamente de um único provedor de IA nem receber credenciais globais de provedores como mecanismo normal de operação.

A plataforma deve possuir uma camada de AI/Model Gateway mediada pelo Capability Core. Agentes devem solicitar uma capacidade de IA dentro de um escopo autorizado; o gateway seleciona um backend compatível segundo política.

Arquitetura conceitual:

```text
MCF / WORKFLOW / EXECUTOR
          |
          v
    CAPABILITY CORE
          |
          v
    AI / MODEL GATEWAY
          |
   POLICY + ROUTING
          |
   +------+------+------+
   |      |      |      |
Provider Provider Router Local
   A      B             Inference
```

### Responsabilidades do AI/Model Gateway

A camada deve suportar conceitualmente:

- catálogo de modelos/backends autorizados;
- roteamento por capacidade requerida;
- seleção por custo, latência, disponibilidade, quota e política;
- fallback entre backends quando permitido;
- isolamento por tenant/projeto/missão;
- quotas e accounting/auditoria de consumo;
- centralização das credenciais no secret store;
- ausência de exposição direta de chaves globais aos agentes;
- suporte futuro a provedores externos e inference local como backends substituíveis;
- observabilidade de chamadas e resultados sem registrar secrets;
- possibilidade de políticas distintas para modelos gratuitos, pagos, locais ou especializados.

### Relação com decisões anteriores

- Q5: o AI/Model Gateway é uma capacidade da plataforma, não um caminho paralelo ao Capability Core;
- Q12: credenciais permanecem centralizadas, escopadas e injetadas apenas quando necessário;
- Q22: identidade e autoridade continuam vinculadas a tenant/projeto/missão/capacidade;
- Q25: quotas de IA devem participar do modelo de resource/accounting da plataforma;
- Q29: o gateway não governa missões e não cria autoridade; ele executa roteamento autorizado;
- Q30: provedores e modelos permanecem substituíveis, preservando desacoplamento.

### Princípios derivados

- agentes solicitam capacidade de IA, não autoridade sobre credenciais globais;
- o backend de IA é substituível;
- escolha de modelo/provedor deve ser uma decisão de política, não acoplamento de código do agente;
- custo, quota, privacidade, disponibilidade e escopo devem ser auditáveis;
- modelos locais podem ser adicionados no futuro sem alterar a interface dos agentes;
- tecnologia concreta do gateway e provedores ainda não está congelada.

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
```

## Próximo passo

**DISCOVERY_Q33**.

A próxima decisão deve definir a política de atualização, vulnerabilidades e supply chain da plataforma: como equilibrar patches automáticos, controle de mudanças, scanning de dependências/imagens e proteção da disponibilidade sem transformar cada atualização rotineira em HUMAN_GATE.