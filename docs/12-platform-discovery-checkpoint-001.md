# 12 — Platform Discovery Checkpoint 001 — Q1–Q8

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Objetivo

Preservar no GitHub o estado atual da nova Discovery de Plataforma para que a continuidade não dependa da memória do chat.

Esta Discovery foi iniciada após a conclusão da Fase 2 — Cloud Workstation. As fases futuras F3–F10 permanecem planejamento anterior/provisional e não devem ser executadas automaticamente antes da consolidação desta Discovery.

A rotação de credenciais permanece **DEFERRED por decisão explícita de LEANDRO** e não é o próximo passo operacional.

## Visão emergente

A VPS não será tratada apenas como servidor de hospedagem. O alvo é uma **plataforma privada de computação, desenvolvimento e execução de agentes**, voltada principalmente a laboratório, desenvolvimento, experimentação, testes, integração e autonomia operacional dos agentes.

Produção poderá continuar usando serviços externos como Vercel, Render, Supabase, Cloudflare ou outros quando a aplicação estiver madura e houver vantagem técnica/econômica. O laboratório próprio deve reduzir HUMAN_GATES operacionais desnecessários durante o desenvolvimento.

Princípios emergentes:

- infraestrutura própria como padrão para desenvolvimento/laboratório;
- serviços externos por escolha para produção ou quando houver vantagem concreta;
- development autonomy first;
- production portability;
- autonomia por escopo, não acesso irrestrito;
- projetos isolados entre si;
- sandboxes temporários para missões/agentes;
- sandboxes com limites explícitos de CPU, RAM, disco e rede;
- núcleo central de capacidades independente de um único cliente de IA;
- MCP como uma interface para agentes, não como a infraestrutura inteira;
- catálogo amplo de capacidades, implementado progressivamente;
- compute descartável; estado importante explicitamente persistente.

## Decisões Q1–Q8

### Q1 — Identidade da infraestrutura

**Escolha: C — plataforma privada de computação, desenvolvimento e execução de agentes.**

A arquitetura deve ser projetada para hospedar capacidades de desenvolvimento, dados, automação, agentes, ferramentas e aplicações, embora a implementação seja progressiva.

### Q2 — Política de dependência de serviços externos

**Escolha: C — infraestrutura própria como padrão, externa quando vantajosa.**

Refinamento explícito de LEANDRO:

- a infraestrutura própria é prioritariamente um **laboratório de desenvolvimento**, não necessariamente o destino final de produção;
- agentes devem conseguir criar bancos, realizar deploys DEV, subir serviços, testar integrações e executar tarefas sem depender da configuração manual de Render/Vercel/Supabase durante o desenvolvimento;
- quando a aplicação estiver madura, poderá haver HUMAN_GATE para promoção/migração para serviços externos adequados à produção.

### Q3 — Isolamento de projetos e ambientes

**Escolha: C — projeto isolado + ambientes temporários para agentes/missões.**

Cada projeto deve possuir isolamento próprio. Além do ambiente DEV principal, a plataforma deve poder criar sandboxes temporários e descartáveis por missão, agente, teste ou mudança.

### Q4 — Autonomia dos agentes

**Escolha: C — autonomia completa dentro de sandbox/projeto, com HUMAN_GATE fora dele.**

Dentro do escopo autorizado, o agente poderá executar operações normais de desenvolvimento sem intervenção humana repetitiva. Operações que alterem infraestrutura-base, afetem outros projetos, produção, custos externos, credenciais ou ações críticas permanecem fora desse escopo e sujeitas a política/HUMAN_GATE.

Princípio: **autonomia por escopo, não por acesso irrestrito.**

### Q5 — Interface de controle da plataforma

**Escolha: D — núcleo de capacidades + API + MCP + CLI, construídos progressivamente.**

Arquitetura-alvo:

```text
Agentes  -> MCP --\
Sistemas -> API ----> CAPABILITY CORE -> infraestrutura
Humanos  -> CLI --/
```

O Capability Core deve concentrar regras e capacidades reais. MCP será uma interface para agentes; API permitirá integração com outros sistemas; CLI permitirá operação humana e automação independente de um cliente específico.

### Q6 — Catálogo inicial de capacidades

**Escolha: C — laboratório completo de desenvolvimento, implementado progressivamente.**

Categorias previstas no blueprint:

- Projects;
- Sandboxes;
- Compute;
- Databases;
- Storage;
- Deploy DEV;
- Preview;
- Network;
- Logs;
- Metrics/observabilidade;
- Backup/Restore;
- Diagnóstico.

Regra: catálogo amplo no desenho, implementação por necessidade e por releases incrementais.

### Q7 — Persistência e descarte

**Escolha: C — ambientes descartáveis, dados importantes explicitamente persistentes.**

A arquitetura deve separar claramente:

```text
PERSISTENTE
- banco DEV principal quando necessário
- storage importante
- artefatos/evidências
- backups
- estado necessário do projeto

DESCARTÁVEL
- sandbox de agente
- sandbox de missão
- preview temporário
- serviços/processos de teste
```

Princípio: **compute é descartável; estado importante é explicitamente persistente.**

Direção futura possível, ainda não decidida: aumentar gradualmente a capacidade de reconstrução automática a partir de Git, manifests, migrations, fixtures e backups.

### Q8 — Nível de isolamento do sandbox

**Escolha: C — projeto isolado + sandbox por missão com limites de recursos.**

Cada projeto deve possuir um ambiente principal isolado e a plataforma deve ser capaz de criar sandboxes adicionais para missões, agentes ou testes. Esses sandboxes devem poder receber limites e políticas próprias de:

- CPU;
- RAM;
- disco;
- rede;
- processos;
- filesystem temporário;
- variáveis e serviços;
- banco temporário quando necessário.

Princípio: **um agente descontrolado não deve conseguir consumir todos os recursos do laboratório nem interferir em outro projeto ou na infraestrutura-base.**

A tecnologia de isolamento ainda não está decidida; containers são candidatos naturais, mas Docker/Podman/Kubernetes ou outra solução permanecem para decisão posterior.

## Arquitetura conceitual emergente

```text
                         LEANDRO
                            |
                    ChatGPT / TriView
                            |
                           MCF
                   governança/políticas
                            |
                      agentes/executores
                            |
                 MCP / API / CLI clients
                            |
                    CAPABILITY CORE
                            |
       +--------------------+--------------------+
       |          |          |        |          |
    Projects   Sandboxes   Compute   Data      Deploy
       |          |          |        |          |
       +----------+----------+--------+----------+
                            |
                        CONTABO VPS
                            |
                     LABORATÓRIO DEV
                            |
                     aplicação madura
                            |
                        HUMAN_GATE
                            |
                  PRODUÇÃO EXTERNA/ALVO
```

## Não decidido ainda

Nenhuma escolha tecnológica específica está congelada por estas Q1–Q8. Em particular, ainda não está decidido de forma final:

- Docker/Podman/Kubernetes ou outra estratégia de runtime;
- PostgreSQL/Supabase self-hosted ou outra camada de dados;
- Redis/filas/cache;
- object storage;
- reverse proxy e publicação de previews;
- secret manager;
- CI/CD;
- observabilidade;
- Hermes/OpenClaw/Freebuff/OpenHands e seus papéis finais;
- desenho detalhado dos servidores MCP;
- política final de autenticação/autorização entre agentes e Capability Core;
- estratégia completa de backup/recovery;
- arquitetura de promoção DEV -> produção externa.

Esses itens devem ser resolvidos pela continuação da Discovery, não por instalação antecipada.

## Próximo passo

**DISCOVERY_Q9**.

Continuar o questionário até existir maturidade suficiente para produzir:

1. requisitos consolidados;
2. arquitetura-alvo;
3. threat model e limites de autonomia;
4. Infrastructure Blueprint v1;
5. roadmap de implementação revisado;
6. missão executável para o Codex;
7. HUMAN_GATE de aprovação antes da implementação pesada.
