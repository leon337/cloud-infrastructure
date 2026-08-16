# 16 — Platform Discovery Checkpoint 005 — Q17

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua:

- `docs/12-platform-discovery-checkpoint-001.md` — Q1–Q9;
- `docs/13-platform-discovery-checkpoint-002.md` — Q10–Q13;
- `docs/14-platform-discovery-checkpoint-003.md` — Q14–Q15;
- `docs/15-platform-discovery-checkpoint-004.md` — Q16.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q17 — Runtime de aplicações e sandboxes

**Escolha de LEANDRO: C — arquitetura container-first, com stacks por projeto/sandbox e Docker/Compose inicialmente, mediados pelo Capability Core.**

### Decisão

Aplicações, serviços de projeto e sandboxes deverão ser executados preferencialmente em containers, evitando mistura direta de dependências no host Ubuntu. O host deverá permanecer principalmente como fundação da plataforma e camada operacional protegida.

Docker/Compose é a escolha inicial para o runtime/orquestração de single-host, sem adoção de Kubernetes no primeiro release. A arquitetura deverá preservar uma camada de abstração no Capability Core para que agentes e sistemas não dependam diretamente da API administrativa do runtime.

Fluxo conceitual:

```text
Agente / Sistema
      |
      v
MCP / API / CLI
      |
      v
CAPABILITY CORE
      |
      v
Container Runtime
      |
      +-- Projeto A / DEV
      +-- Projeto A / sandbox missão-42
      +-- Projeto B / DEV
      +-- Projeto C / preview
```

### Regra de autoridade

Agentes não devem receber, por padrão, acesso administrativo bruto ao daemon/socket do Docker nem autoridade equivalente sobre o host. As operações devem ser mediadas por capacidades escopadas, políticas e auditoria do Capability Core.

Princípio: **Docker é mecanismo de execução; não é a interface de autoridade dos agentes.**

### Capacidades desejadas

O Capability Core poderá evoluir para operações como:

- criar stack de projeto;
- criar sandbox containerizado;
- iniciar/parar/recriar serviços;
- aplicar limites de CPU, RAM, disco, rede e processos;
- anexar volumes e redes autorizadas;
- consultar logs/status/health;
- destruir ambientes descartáveis;
- executar deploys a partir de imagens/artefatos rastreáveis.

### Princípios derivados

- container-first para workloads de aplicação e sandboxes;
- host Ubuntu protegido e minimamente contaminado por dependências de projetos;
- Docker/Compose como implementação inicial de single-host;
- sem Kubernetes no primeiro release sem necessidade comprovada;
- agentes não controlam o runtime diretamente;
- runtime deve ficar atrás do Capability Core;
- stacks e sandboxes devem permanecer compatíveis com limites de recursos, observabilidade, secrets, storage e gateway definidos nas Q anteriores;
- arquitetura deve permitir evolução futura para outra camada de orquestração sem reescrever a interface de agentes.

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
```

## Próximo passo

**DISCOVERY_Q18**.

A Discovery continua. A implementação da plataforma permanece bloqueada até consolidação dos requisitos, arquitetura, threat model, blueprint, roadmap e HUMAN_GATE explícito de LEANDRO.
