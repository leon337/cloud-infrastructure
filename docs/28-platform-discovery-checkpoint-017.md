# 28 — Platform Discovery Checkpoint 017 — Q29

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q28.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q29 — Divisão de responsabilidade entre MCF, Capability Core e Workflow Engine

**Escolha de LEANDRO: C — MCF governa missões/autoridade; Capability Core aplica políticas; Workflow Engine executa workflows duráveis; cada domínio mantém sua própria fonte de verdade.**

### Decisão

A plataforma deve usar orquestração em camadas, sem transformar MCF e Workflow Engine em dois orquestradores concorrentes sobre o mesmo domínio.

Arquitetura conceitual:

```text
                 LEANDRO
                    |
                    v
                   MCF
          GOVERNANÇA DA MISSÃO
                    |
                    v
             CAPABILITY CORE
        AUTORIZAÇÃO + POLÍTICAS
                    |
                    v
            WORKFLOW ENGINE
          EXECUÇÃO DURÁVEL
                    |
             +------+------+ 
             |      |      |
          Worker  Worker  Worker
             |
          Sandboxes
```

### Fontes de verdade por domínio

A divisão canônica deve ser:

```text
Git
= estado desejado/configuração declarativa

MCF
= missão, governança, autoridade, HUMAN_GATE e estado semântico

Capability Core
= políticas, escopo e capacidades efetivamente permitidas

Workflow Engine
= estado operacional e durável da execução

Observabilidade
= logs, métricas, eventos e evidências
```

Nenhum desses componentes deve silenciosamente substituir a autoridade de outro domínio.

### Papel do MCF

O MCF deve responder principalmente:

- qual é a missão;
- qual é o objetivo;
- quem possui autoridade;
- qual agente/executor está designado;
- qual escopo foi aprovado;
- quais HUMAN_GATES existem;
- qual é o estado semântico da missão;
- quais evidências são necessárias para considerar a missão concluída.

O MCF não precisa reimplementar retry, timeout, durable execution, worker scheduling ou recuperação de processo já fornecidos pelo Workflow Engine.

### Papel do Capability Core

O Capability Core deve continuar sendo o ponto técnico de enforcement das políticas.

Uma declaração de missão ou ordem de um agente não é, por si só, autorização técnica suficiente. Antes de executar uma capacidade, a plataforma deve validar identidade, tenant, projeto, missão, capability, ambiente e demais políticas aplicáveis.

### Papel do Workflow Engine

O Workflow Engine deve responder principalmente:

- qual workflow está em execução;
- quais etapas passaram, falharam ou aguardam;
- retries, timeouts e scheduling;
- estado durável da execução;
- recuperação/resume após falha;
- distribuição entre workers quando aplicável;
- emissão de resultados e evidências operacionais.

Ele executa trabalho autorizado, mas não cria autoridade própria.

### HUMAN_GATE

O HUMAN_GATE pertence exclusivamente a LEANDRO e permanece no domínio de governança do MCF/políticas da plataforma.

O Workflow Engine pode chegar a um estado como `WAITING_FOR_AUTHORIZATION`, mas não deve autoaprovar a operação protegida.

Fluxo conceitual:

```text
WORKFLOW
   |
RELEASE_CANDIDATE_READY
   |
   v
MCF / GOVERNANCE
   |
HUMAN_GATE: LEANDRO
   |
APPROVED
   |
   v
CAPABILITY CORE
   |
   v
WORKFLOW CONTINUES
```

### Princípios derivados

- MCF governa;
- Capability Core autoriza e aplica políticas;
- Workflow Engine executa de forma durável;
- fontes de verdade são separadas por domínio;
- HUMAN_GATE não pertence ao Workflow Engine;
- estado operacional do workflow não substitui estado semântico da missão;
- MCF não deve ficar fortemente acoplado a um vendor específico de workflow engine;
- Hermes, Codex e outros executores podem permanecer substituíveis sob essa arquitetura.

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
```

## Próximo passo

**DISCOVERY_Q30**.

A próxima decisão deve consolidar o papel arquitetônico dos executores e interfaces já considerados — especialmente Hermes, Codex, Freebuff, OpenClaw e TriView — evitando sobreposição de autoridade e acoplamento indevido ao Capability Core.