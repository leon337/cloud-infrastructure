# 13 — Platform Discovery Checkpoint 002 — Q10

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua `docs/12-platform-discovery-checkpoint-001.md`, que preserva integralmente as decisões Q1–Q9.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q10 — Estratégia de dados por projeto e sandbox

**Escolha de LEANDRO: C — banco DEV persistente por projeto + bancos temporários por sandbox.**

### Decisão

Cada projeto poderá possuir um banco DEV persistente quando necessário. Missões, testes e agentes devem poder receber bancos temporários isolados, preferencialmente clonados ou reconstruídos a partir de estado conhecido, para permitir experimentação sem comprometer o banco DEV principal.

Estrutura conceitual:

```text
Projeto A
|
+-- Banco DEV persistente
|
+-- Sandbox missão 001
|   +-- banco temporário
|
+-- Sandbox missão 002
|   +-- banco temporário
|
+-- Sandbox teste
    +-- banco temporário
```

Ao destruir um sandbox, seu banco temporário pode ser destruído junto, salvo decisão explícita de preservar evidência ou estado relevante.

### Capacidades desejadas

O futuro Capability Core deverá ser capaz de evoluir para operações como:

- criar banco persistente de projeto;
- criar/clone/reconstruir banco temporário para sandbox;
- executar migrations;
- resetar banco de sandbox;
- fazer backup e restore;
- destruir banco temporário de forma segura;
- fornecer credenciais temporárias e escopadas ao ambiente autorizado.

### Princípios derivados

- isolamento de dados por projeto;
- dados de sandbox são descartáveis por padrão;
- dados DEV importantes são persistentes por decisão explícita;
- experimentos e migrations de agentes não devem comprometer o banco DEV principal;
- a arquitetura deve favorecer portabilidade futura para serviços externos de produção;
- a tecnologia concreta da camada de dados ainda não está congelada.

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
```

## Próximo passo

**DISCOVERY_Q11**.

A Discovery continua. Nenhuma escolha tecnológica final de banco, runtime, storage, reverse proxy, secret manager, CI/CD, observabilidade, Hermes/OpenClaw/Freebuff/OpenHands ou desenho detalhado de MCP deve ser antecipada antes das decisões correspondentes.
