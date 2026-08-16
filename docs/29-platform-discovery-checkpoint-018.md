# 29 — Platform Discovery Checkpoint 018 — Q30

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q29.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q30 — Papéis definitivos de MCF, Capability Core, Workflow Engine, Hermes, Codex, Freebuff, OpenClaw e TriView

**Escolha de LEANDRO: C — ecossistema modular com papéis explícitos e executores substituíveis.**

### Decisão

A plataforma deve evitar um superagente ou uma teia de integrações ponto a ponto. Cada componente ocupa um papel arquitetônico claro e substituível quando aplicável.

### Papéis

- **MCF:** governança de missões, autoridade, HUMAN_GATE, handoffs, evidências esperadas, estado semântico e continuidade.
- **Capability Core:** políticas, autorização técnica, aplicação de escopo e exposição uniforme de capacidades por API/MCP/CLI.
- **Workflow Engine:** execução durável, retries, timeouts, scheduling, resume, etapas dependentes e coordenação de workers.
- **Hermes:** executor autônomo de uso geral, substituível e sempre sujeito ao escopo autorizado.
- **Codex:** executor especializado/pesado para missões complexas, auditorias, refatorações e engenharia de alta complexidade; não deve ser o executor ordinário obrigatório.
- **Freebuff:** ferramenta de desenvolvimento interativa na Cloud Workstation, orientada a uso humano; não é backend autônomo obrigatório da plataforma.
- **OpenClaw:** camada de canais/front door para WhatsApp, Telegram, Discord, Web e canais equivalentes; não é fonte de autoridade.
- **TriView:** cockpit humano para visualização e controle consolidado; apresenta estado canônico de outros sistemas sem substituí-los como fontes de verdade.

### Arquitetura conceitual

```text
                    LEANDRO
                       |
                    TRIVIEW
                       |
                       v
                      MCF
                       |
                CAPABILITY CORE
                       |
                WORKFLOW ENGINE
                       |
            +----------+----------+
            |          |          |
         Hermes      Codex      Outros
```

Entrada alternativa por canais:

```text
CANAIS
  |
OpenClaw
  |
Agent Gateway
  |
MCF / Capability Core
```

Ferramenta humana interativa:

```text
LEANDRO
  |
Cloud Workstation
  |
Freebuff
```

### Princípios derivados

- governança estável; execução substituível; interfaces desacopladas;
- nenhum executor é autoridade da plataforma;
- trocar ou adicionar executores não deve exigir redesenhar MCF, Capability Core ou Workflow Engine;
- OpenClaw é gateway de canais, não orquestrador central;
- TriView é cockpit, não fonte de verdade canônica;
- Freebuff permanece human-interactive e não deve ser pressuposto como backend 24/7;
- seleção futura de executor pode considerar complexidade, custo, disponibilidade, política e capacidades da missão;
- as tecnologias concretas e integrações finais ainda serão selecionadas em etapa posterior.

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
```

## Próximo passo

**DISCOVERY_Q31**.

A próxima decisão deve definir o papel da Cloud Workstation em relação aos serviços headless da plataforma: interface humana opcional versus dependência operacional do Capability Core e dos workloads.