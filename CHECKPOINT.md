# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo responde principalmente: **onde estamos agora?** O contexto permanente está distribuído conforme `CONTEXT.md`.

## Gate de continuidade

O PUC v1.0 foi implantado documentalmente. **Não retomar mudanças na VPS até que um novo chat passe no teste de continuidade usando somente o GitHub canônico.**

## Estado atual

- Repositório: `leon337/cloud-infrastructure`.
- Fase: **FASE 0 — ORIENTAÇÃO E INVENTÁRIO**.
- Etapa: **0.5 — Inventário real da VPS**.
- Etapas 0.1 a 0.4: concluídas.
- Etapa 0.5: em andamento.

## Identificadores operacionais

- VPS: Contabo Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Usuário administrativo temporário: `root`.
- Linux Mint local observado: `leo@leo-N43SM`.
- Alias SSH planejado: `contabo-vps`.
- Fingerprint ED25519 validada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

## Inventário já confirmado

- Ubuntu 24.04.4 LTS — Noble Numbat.
- Kernel: `Linux 6.8.0-137-generic`.
- Arquitetura: x86-64.
- Chassis: VM.
- Virtualização: KVM.
- Hardware virtual: QEMU.
- CPU: 8 lógicas, AMD EPYC apresentado à VM, 1 socket, 8 cores/socket, 1 thread/core.
- RAM visível: ~23 GiB.
- RAM usada na medição: ~592 MiB.
- RAM disponível na medição: ~22 GiB.
- Swap: 0 B.

Detalhes permanentes: `docs/06-inventario.md`.

## Primeiro acesso

- senha root inicial foi tratada como comprometida e rotacionada;
- VNC validado com TigerVNC;
- Remmina chegou ao serviço, mas não concluiu a sessão no teste;
- console `tty1` acessado;
- `loadkeys br` corrigiu o layout do teclado no console;
- fingerprint SSH foi verificada via VNC antes da aceitação do host;
- SSH root foi validado.

Detalhes: `docs/01-primeiro-acesso-seguro.md` e `runbooks/acesso-e-recuperacao.md`.

## FND-SSH-001

Sessões SSH sem keepalive ficaram inoperantes após ociosidade, enquanto a VPS continuava alcançável e novas conexões podiam ser abertas.

Teste inválido: keepalive iniciado de dentro da VPS, criando SSH dentro de SSH. Não usar como evidência.

Teste válido, iniciado no Linux Mint local:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 root@169.58.171.192
```

Após ~3 minutos ocioso:

```bash
echo vivo
```

Resultado: `vivo`.

LEANDRO autorizou a configuração permanente no cliente local. Ainda não foi aplicada.

A auditoria de continuidade posterior relatou que `~/.ssh/config` **não existe** no Linux Mint local. Portanto, após o gate do PUC, a criação poderá ser consciente e não uma sobrescrita de arquivo existente.

Detalhes: `findings/FND-SSH-001.md`.

## Próximo passo operacional — somente após continuidade PASS

No Linux Mint LOCAL:

1. revalidar, se necessário, que `~/.ssh/config` continua inexistente;
2. criar o arquivo com permissão apropriada;
3. adicionar:

```sshconfig
Host contabo-vps
    HostName 169.58.171.192
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

4. validar a configuração;
5. conectar com `ssh contabo-vps`;
6. aguardar ~3 minutos;
7. executar `echo vivo`;
8. atualizar finding, inventário, histórico e checkpoint.

Depois continuar inventário de armazenamento, filesystems, mounts, rede e uptime.

## Proibições imediatas

Não executar ainda sem etapa própria e autorização:

- particionamento ou alteração destrutiva de disco;
- firewall;
- desativação de root;
- desativação de senha SSH;
- instalação de Docker;
- desktop gráfico;
- alterações de swap;
- hardening em lote.

## Próxima leitura obrigatória

Qualquer novo chat deve começar em `CONTEXT.md`, não neste arquivo isoladamente.