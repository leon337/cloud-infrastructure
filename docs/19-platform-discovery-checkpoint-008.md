# 19 — Platform Discovery Checkpoint 008 — Q20

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery e registra a decisão Q20.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q20 — Política de egress dos sandboxes

**Escolha de LEANDRO: C — egress controlado por política: Internet útil permitida, recursos sensíveis/privados bloqueados, exceções escopadas.**

### Decisão

Sandboxes de projeto, missão, agente e jobs de CI não devem possuir acesso irrestrito à rede interna ou à infraestrutura-base. O tráfego de saída necessário ao desenvolvimento pode ser permitido por política, enquanto movimento lateral, acesso administrativo e acesso a recursos de outros projetos permanecem bloqueados por padrão.

Princípio:

> **Permitir o necessário para desenvolver; bloquear por padrão acesso lateral e administrativo.**

Estrutura conceitual:

```text
SANDBOX
   |
   v
EGRESS POLICY
   |
   +-- GitHub / registries / APIs declaradas -> permitido conforme política
   +-- Internet geral -> permitido ou limitado conforme perfil
   +-- recursos do próprio projeto -> somente quando explicitamente autorizado
   +-- outros projetos -> bloqueado
   +-- host administrativo -> bloqueado
   +-- SSH/serviços de infraestrutura-base -> bloqueado
   +-- control plane administrativo -> bloqueado
```

### Relação com o manifesto

O manifesto do projeto poderá declarar necessidades de conectividade de saída sem conter credenciais ou conceder autoridade por si só. O Capability Core deverá interpretar a necessidade declarada e aplicar a política correspondente.

Exemplo conceitual:

```text
project manifest
  -> requires github/package-registry/external-api
  -> Capability Core valida escopo
  -> policy engine concede egress necessário
  -> sandbox recebe apenas a conectividade autorizada
```

### Princípios derivados

- Internet útil ao desenvolvimento não deve exigir HUMAN_GATE repetitivo para cada acesso comum;
- movimento lateral entre projetos deve ser bloqueado por padrão;
- sandboxes não devem acessar o host administrativo nem serviços de infraestrutura-base sem capacidade explícita;
- acessos externos mais sensíveis, pagos ou privilegiados podem exigir política adicional ou HUMAN_GATE;
- política de rede deve ser associável a projeto, missão, sandbox e classe de workload;
- eventos relevantes de rede devem poder produzir auditoria compatível com a observabilidade definida na Q15;
- a arquitetura deve permitir evolução futura para controles Zero Trust mais avançados, sem exigir service mesh completo no primeiro release;
- a tecnologia concreta de enforcement de rede ainda não está congelada.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `request_network_access()`;
- `grant_scoped_egress()`;
- `revoke_egress()`;
- `list_network_policy()`;
- `audit_network_access()`;
- aplicar perfis de egress por projeto/sandbox/job;
- negar automaticamente acesso lateral e administrativo não autorizado.

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
```

## Próximo passo

**DISCOVERY_Q21**.

A Discovery continua. Nenhuma implementação pesada da plataforma está autorizada ainda.