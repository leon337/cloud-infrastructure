# 03 — Arquitetura e Princípios

## Arquitetura física e virtual

```text
Computador físico de LEANDRO — Linux Mint
        |
        | Internet / SSH / ferramentas remotas
        v
Contabo Cloud VPS 8
        |
        | KVM/QEMU
        v
Ubuntu 24.04.4 LTS
```

A VPS é uma máquina virtual. O Ubuntu confirmou `Chassis: vm`, KVM e hardware virtual QEMU.

## Modelo híbrido

O Linux Mint local permanece como interface humana: navegador, teclado, áudio, terminal e ferramentas. A VPS assume processamento, builds, Docker, serviços, agentes, APIs e automações quando fizer sentido.

Ferramentas a estudar: SSH, VS Code Remote SSH, Git, tmux, transferência/sincronização de arquivos, Docker e Docker Compose.

## Latência versus processamento

Latência é tempo de ida e volta entre local e VPS. Capacidade de processamento é quanto a VPS consegue executar depois que a tarefa chega. Uma VPS pode ter maior latência de interação e ainda executar cargas pesadas mais rapidamente que o computador local.

## Virtualização aninhada

A VPS já é guest de um hypervisor. Criar VMs completas dentro dela exigiria nested virtualization e suporte/exposição de extensões pelo provedor.

Durante o planejamento desta sessão, foi decidido **não projetar a solução dependendo de nested virtualization**. A política atual do provedor deve ser revalidada antes de qualquer mudança futura nessa direção.

Containers não são equivalentes a VMs: compartilham o kernel do host e serão estudados em fase Docker.

## Cloud Workstation

A intenção de LEANDRO é também possuir uma experiência gráfica remota familiar, semelhante ao uso cotidiano do Linux Mint, sem necessariamente criar uma segunda VM. A hipótese principal a avaliar é interface gráfica sobre o próprio Ubuntu, coexistindo com serviços.

Essa capacidade está documentada separadamente e permanece adiada até base segura e inventário.

## Camadas arquitetônicas alvo

```text
LEANDRO / Linux Mint local
        |
        +-- SSH / VS Code Remote
        +-- eventual desktop remoto
        v
Ubuntu VPS
        |
        +-- identidade/usuários
        +-- segurança/rede
        +-- armazenamento
        +-- Docker/Compose
        +-- observabilidade
        +-- backup/recovery
        +-- reverse proxy/TLS
        +-- workloads: MCF, MCP, APIs, agentes, n8n, apps
```

## Princípios de arquitetura

- menor privilégio;
- recuperação antes de endurecimento que possa bloquear acesso;
- armazenamento decidido após inventário real;
- persistência explícita para dados;
- isolamento de workloads;
- zero secrets no Git;
- mudanças pequenas, observáveis e reversíveis quando possível;
- documentação é parte da implementação.