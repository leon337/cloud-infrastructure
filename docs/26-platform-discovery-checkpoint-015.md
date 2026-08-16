# 26 — Platform Discovery Checkpoint 015 — Q27

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q26.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q27 — Estado desejado, idempotência e controle de drift

**Escolha de LEANDRO: C — estado declarativo versionado + automação idempotente + detecção/reconciliação controlada de drift.**

### Decisão

A plataforma não deve depender da configuração artesanal acumulada na VPS como fonte de verdade operacional. O estado desejado da infraestrutura e dos componentes da plataforma deve ser representado de forma versionada e auditável, preferencialmente em Git, enquanto mecanismos idempotentes devem convergir o estado real para o estado aprovado.

Fluxo conceitual:

```text
GIT / DESIRED STATE
        |
        v
RECONCILIATION / DIFF
        |
        v
POLICY + HUMAN_GATE QUANDO EXIGIDO
        |
        v
EXECUTION NODE / ACTUAL STATE
```

### Idempotência

Aplicar novamente uma definição já satisfeita não deve gerar alterações desnecessárias, duplicação ou degradação. Quando o estado real estiver divergente, a automação deve detectar o drift e produzir evidência suficiente para correção controlada.

### Limite de autonomia

Declaratividade não equivale a autorização irrestrita. Mudanças em projetos e DEV podem ser reconciliadas automaticamente quando permitidas pela política. Mudanças de infraestrutura-base, segurança, firewall, SSH, secret store administrativo, backup global, runtime do host e outras operações protegidas continuam sujeitas às políticas e HUMAN_GATES definidos na Discovery.

### Relação com recovery e portabilidade

Esta decisão complementa Q16 e Q26: uma nova VPS/nó deve poder receber bootstrap mínimo, recuperar a definição versionada, aplicar configuração idempotente, restaurar estado persistente, baixar artefatos e validar a convergência sem depender da memória humana.

### Princípios derivados

- Git/versionamento representa o estado desejado aprovado, não o estado acidental da máquina;
- automação de infraestrutura deve ser idempotente sempre que tecnicamente possível;
- drift deve ser detectável e auditável;
- reconciliação automática depende de política e escopo;
- infraestrutura-base protegida não deve mudar apenas porque um arquivo foi alterado;
- rebuild deve derivar de definição versionada + automação + dados persistentes restauráveis;
- a tecnologia concreta de IaC/reconciliação ainda não está congelada.

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
```

## Próximo passo

**DISCOVERY_Q28**.

A Discovery continua. Jobs duráveis/background, atualização e vulnerability management, divisão local/VPS, serviços de modelos externos, papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex e o technology mapping ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
