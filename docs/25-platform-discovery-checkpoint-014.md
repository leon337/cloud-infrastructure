# 25 — Platform Discovery Checkpoint 014 — Q26

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q25.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q26 — Portabilidade e evolução de single-node para multi-node

**Escolha de LEANDRO: C — single-node no primeiro release + abstração de execution node + portabilidade por design + evolução futura para multi-node.**

### Decisão

A plataforma será implantada inicialmente em um único nó de execução, a VPS Contabo atual, mas o modelo arquitetônico não deve tratar essa máquina específica como a definição da plataforma.

A VPS atual será considerada o primeiro `execution node`. Workloads, sandboxes, jobs e deployments devem ser modelados como executados em um nó selecionado pelo plano de controle, ainda que no primeiro release exista apenas `node-01`.

Arquitetura conceitual inicial:

```text
PLATFORM
   |
CAPABILITY CORE
   |
NODE LAYER
   |
NODE-01
   |
CONTAINER RUNTIME
```

Evolução futura compatível:

```text
PLATFORM
   |
CAPABILITY CORE
   |
NODE / SCHEDULER LAYER
   +-- NODE-01
   +-- NODE-02
   +-- NODE-03
```

### Regras derivadas

- single-node no primeiro release;
- a VPS Contabo atual é o primeiro nó, não a identidade da plataforma;
- agentes não devem precisar conhecer o host físico de execução;
- Capability Core deve abstrair seleção de nó;
- manifests, artefatos, backups e estado declarativo não devem depender de paths/IPs específicos desnecessariamente;
- a arquitetura deve permitir troca de provedor e reconstrução em nova VPS;
- a Cloud Workstation pode coexistir no primeiro nó, mas não deve ser dependência obrigatória do plano de controle;
- multi-node real, HA e scheduler distribuído ficam para evolução futura, não para o primeiro release;
- Kubernetes ou tecnologia equivalente não é exigido por esta decisão.

### Princípio consolidado

**SINGLE_NODE_FIRST_MULTI_NODE_READY_EXECUTION_NODE_ABSTRACTION_PROVIDER_PORTABLE**

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
```

## Próximo passo

**DISCOVERY_Q27**.

A Discovery continua. Configuração declarativa/reconciliação da plataforma, manutenção/updates, divisão entre workstation local e VPS, estratégia de modelos externos vs inferência local e papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex/TriView ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
