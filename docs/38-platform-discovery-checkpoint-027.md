# 38 — Platform Discovery Checkpoint 027 — Q39

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q38.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q39 — Acesso ao Management Plane privado

**Escolha de LEANDRO: C — rede privada de administração com identidade de dispositivo/usuário + serviços administrativos não públicos + SSH como fallback + VNC/Rescue como recuperação final.**

### Decisão

O Management Plane da plataforma deve permanecer não publicamente alcançável por padrão. A administração normal deve ocorrer por uma rede privada/overlay de gerenciamento, acessível apenas a identidades de usuário e dispositivos explicitamente autorizados.

A presença na rede privada não substitui autenticação e autorização. O acesso administrativo deve combinar, conforme a tecnologia posteriormente escolhida:

- identidade de dispositivo;
- identidade de usuário;
- autorização por função/capacidade;
- trilha de auditoria;
- revogação de acesso;
- escopo mínimo necessário.

Serviços administrativos como gerenciamento do Capability Core, secret store, observabilidade administrativa, workflow administration, runtime host, backup global e políticas não devem ser publicados diretamente no IP público da VPS.

### Separação entre administração e agentes

Agentes, sandboxes e workloads de projeto **não entram na Management Network**. Eles usam o Agent Gateway e as capacidades mediadas pelo Capability Core.

```text
LEANDRO / DEVICE AUTORIZADO
          |
          v
 PRIVATE MANAGEMENT NETWORK
          |
          v
     MANAGEMENT PLANE

AGENTS / WORKLOADS
          |
          v
    AGENT GATEWAY
          |
          v
    CAPABILITY CORE
```

A regra continua sendo: **publicar capacidades, não autoridade administrativa**.

### Camadas de recuperação

A administração e o recovery devem formar camadas independentes:

```text
NORMAL ADMINISTRATION
Private Management Network
        |
        v
RECOVERY / MAINTENANCE
SSH fortemente protegido
        |
        v
PROVIDER BREAK-GLASS
Contabo VNC / Rescue
```

SSH permanece disponível como caminho controlado de fallback e manutenção, não como única interface administrativa cotidiana. VNC/Rescue do provedor permanece como recuperação de última instância quando os caminhos normais da própria plataforma falharem.

### Compatibilidade com decisões anteriores

- Q21: preserva Management Plane privado + Agent Gateway público e mínimo;
- Q22: aplica identidade individual e autoridade temporária/escopada;
- Q26: permite incluir future execution nodes, inclusive em outros provedores, na rede privada de administração;
- Q31: Cloud Workstation pode acessar interfaces administrativas conforme política, mas a plataforma continua independente da sessão gráfica;
- Q34: mantém isolamento entre redes de projeto/sandbox e rede administrativa.

### Princípios derivados

- management interfaces are private by default;
- device presence on the private network is necessary but not sufficient for authorization;
- agents consume capabilities through gateways rather than administrative networking;
- SSH is controlled fallback, not the primary platform UI;
- provider VNC/Rescue remains final break-glass recovery;
- concrete technology such as WireGuard/Tailscale/Headscale remains unfrozen until Technology Mapping.

## Estado das decisões

```text
Q1–Q38 = preservadas
Q39 = C
```

## Próximo passo

**DISCOVERY_Q40**.
