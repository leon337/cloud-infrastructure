# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo é o ponto canônico de retomada entre chats. Nenhum secret real deve ser registrado aqui.

## Estado da missão

- Projeto: implementação e aprendizado da infraestrutura VPS.
- Repositório canônico: `leon337/cloud-infrastructure`.
- Repositório separado do MCF.
- Fase atual: **FASE 0 — ORIENTAÇÃO E INVENTÁRIO**.
- Etapa atual: **0.5 — inventário real da VPS**.

Etapas concluídas:

- 0.1 — modelo mental da infraestrutura;
- 0.2 — repositório canônico separado do MCF;
- 0.3 — preparação do primeiro acesso;
- 0.4 — primeiro acesso seguro via VNC + SSH.

## Acesso validado

- SSH funcional.
- VNC funcional com TigerVNC.
- Remmina alcançou o serviço VNC, mas não concluiu a sessão no teste realizado.
- A fingerprint ED25519 do host SSH foi verificada por canal independente via VNC antes de ser aceita no Linux Mint local.
- A chave do host foi registrada conscientemente no `known_hosts` local.
- A senha `root` vigente funciona, mas seu valor não é versionado.

## Inventário confirmado até agora

### Sistema

- Sistema operacional: Ubuntu 24.04.4 LTS.
- Codinome: Noble Numbat (`noble`).
- Hostname atual: `vmi3506102`.
- Kernel: `Linux 6.8.0-137-generic`.
- Arquitetura: `x86-64`.

### Virtualização

- Chassis: VM.
- Hypervisor: KVM.
- Hardware virtual apresentado por QEMU.

### CPU

- 8 CPUs lógicas visíveis (`0-7`).
- Modelo apresentado à VM: AMD EPYC Processor (with IBPB).
- 1 socket virtual.
- 8 cores por socket.
- 1 thread por core.

### Memória

Observação feita com `free -h`:

- RAM total visível: aproximadamente 23 GiB.
- RAM usada no momento do teste: aproximadamente 592 MiB.
- RAM disponível no momento do teste: aproximadamente 22 GiB.
- Swap: **0 B** — nenhuma swap configurada no momento.

## FND-SSH-001 — sessão SSH ociosa

### Sintoma observado

Sessões SSH normais, iniciadas do Linux Mint local, ficaram aparentemente inoperantes após alguns minutos de ociosidade. A VPS continuou alcançável e novas conexões SSH puderam ser abertas imediatamente.

### Teste válido realizado

A partir do **Linux Mint local**, foi aberta uma sessão com:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 root@<IP_DA_VPS>
```

Após aproximadamente 3 minutos sem atividade manual, foi executado:

```bash
echo vivo
```

Resultado:

```text
vivo
```

Conclusão operacional provisória: o keepalive do cliente SSH evitou o travamento observado no teste curto.

### Decisão autorizada e ainda pendente

LEANDRO autorizou tornar o keepalive permanente no Linux Mint local usando `~/.ssh/config`.

**IMPORTANTE:** a configuração permanente ainda NÃO foi aplicada neste checkpoint. O próximo chat deve começar por inspecionar o arquivo `~/.ssh/config` local antes de editá-lo e então aplicar a configuração de forma segura.

Configuração pretendida:

```sshconfig
Host contabo-vps
    HostName <IP_DA_VPS>
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

O usuário `root` é temporário e deverá ser substituído posteriormente por um usuário administrativo próprio.

Modelo versionado: `config/ssh_config.example`.

## Pendências imediatas

1. Aplicar e validar o keepalive permanente no `~/.ssh/config` do Linux Mint local.
2. Continuar a Etapa 0.5 com inventário de armazenamento e filesystems.
3. Inventariar mounts.
4. Inventariar rede.
5. Inventariar uptime e estado básico.
6. Registrar o inventário completo antes de qualquer hardening estrutural.

## Pendências posteriores de segurança

Ainda não executar sem etapa própria e autorização:

- criar usuário administrativo próprio;
- configurar `sudo`;
- configurar autenticação SSH por chave;
- decidir política para login direto de `root`;
- configurar firewall;
- decidir política permanente para VNC;
- decidir política de swap;
- estruturar backup, snapshots e recovery playbook;
- avaliar desktop gráfico / Cloud Workstation somente depois da base segura.

## Regra de retomada no próximo chat

Antes de afirmar estado atual, ler este `CHECKPOINT.md`, o `README.md` e os documentos canônicos relevantes do repositório.

Retomar exatamente em:

**FASE 0 → ETAPA 0.5 → aplicar keepalive permanente no Linux Mint local e continuar o inventário.**
