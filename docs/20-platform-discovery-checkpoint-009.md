# 20 — Platform Discovery Checkpoint 009 — Q21

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q20.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q21 — Acesso remoto ao coração da plataforma

**Escolha de LEANDRO: C — dois planos: Management Plane privado + Agent Gateway público, mínimo e fortemente escopado.**

### Decisão

A plataforma deve separar autoridade administrativa de capacidades remotas para agentes e sistemas externos.

Arquitetura conceitual:

```text
                    LEANDRO
                       |
              MANAGEMENT PLANE
                  privado
                       |
                       v
                 CAPABILITY CORE
                       ^
                       |
                AGENT GATEWAY
              público e limitado
                       ^
          +------------+------------+
          |            |            |
       ChatGPT       Hermes       MCF/etc.
```

### Management Plane

O plano administrativo permanece privado e é destinado a operações como configuração da plataforma, políticas globais, firewall, runtime, secret store administrativo, backup global, manutenção e diagnóstico do host.

A tecnologia concreta de acesso privado ainda não está congelada; VPN, WireGuard, Tailscale, SSH/túnel ou equivalente permanecem candidatos para etapa posterior.

### Agent Gateway

Agentes e sistemas externos devem acessar somente capacidades explicitamente publicadas e autorizadas. O gateway deve aplicar autenticação, autorização, escopo e auditoria antes de encaminhar uma operação ao Capability Core.

Exemplos de capacidades potencialmente publicáveis:

- `create_sandbox()`;
- `get_project_status()`;
- `deploy_dev()`;
- `create_preview()`;
- `get_logs()`;
- `destroy_sandbox()`.

Não devem ser publicadas como capacidades normais de agente operações administrativas como shell irrestrito do host, firewall, credenciais do provedor, secret store global ou acesso a outros projetos.

### Separação adicional

O Agent Gateway não deve ser confundido com o Preview Gateway. O primeiro publica capacidades da plataforma; o segundo publica aplicações/previews DEV conforme política.

### Princípios derivados

- publicar capacidades, não autoridade administrativa;
- Management Plane privado;
- Agent Gateway público mínimo e fortemente escopado;
- autenticação, autorização e auditoria antes do Capability Core;
- credenciais comprometidas devem ter raio de impacto limitado por agente/projeto/missão/capacidade;
- MCP deve operar sobre capacidades autorizadas, não como acesso direto ao host;
- Preview Gateway e Agent Gateway são superfícies distintas;
- a tecnologia concreta de acesso privado e gateway ainda não está congelada.

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
```

## Próximo passo

**DISCOVERY_Q22**.

A Discovery continua. Identidade/autenticação dos agentes, tenancy, limites DEV/staging/prod, tecnologias concretas e papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
