# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo responde principalmente: **onde estamos agora?** O contexto permanente está distribuído conforme `CONTEXT.md`.

## Gate de continuidade

O PUC v1.0 foi implantado e validado em novo chat usando somente o GitHub canônico.

**Resultado: CONTINUIDADE COMPLETA.**

Evidência: `governance/CONTINUITY-VALIDATION-2026-08-14.md`.

A retomada operacional da VPS está liberada, respeitando HUMAN_GATEs e autorizações já registrados.

## Estado atual

- Repositório: `leon337/cloud-infrastructure`.
- Fase: **FASE 0 — ORIENTAÇÃO E INVENTÁRIO**.
- Etapa: **0.5 — Inventário real da VPS**.
- Etapas 0.1 a 0.4: concluídas.
- Etapa 0.5: em andamento.
- PUC v1.0: `DONE`.

## Identificadores operacionais

- VPS: Contabo Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Usuário administrativo temporário: `root`.
- Linux Mint local observado: `leo@leo-N43SM`.
- Alias SSH: `contabo-vps`.
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

## FND-SSH-001 — RESOLVED

Sessões SSH sem keepalive ficavam inoperantes após ociosidade, enquanto a VPS continuava alcançável e novas conexões podiam ser abertas.

O teste temporário com `ServerAliveInterval=30` e `ServerAliveCountMax=3` já havia sido validado.

LEANDRO autorizou tornar a configuração permanente no cliente SSH do Linux Mint local.

### Aplicação permanente concluída

No Linux Mint LOCAL:

1. foi revalidado que `~/.ssh/config` não existia;
2. o arquivo foi criado conscientemente;
3. a permissão foi definida como `600`;
4. foi adicionado o bloco:

```sshconfig
Host contabo-vps
    HostName 169.58.171.192
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

5. `ssh -G contabo-vps` confirmou a configuração efetiva esperada;
6. `ssh contabo-vps` abriu corretamente `root@vmi3506102`;
7. após aproximadamente 3 minutos de ociosidade, `echo vivo` respondeu `vivo`.

**Resultado:** keepalive permanente aplicado e validado. `FND-SSH-001` marcado como `RESOLVED`.

Detalhes: `findings/FND-SSH-001.md`.

## Próximo passo operacional

Continuar a **Etapa 0.5 — Inventário real da VPS**, começando por armazenamento/filesystems com comandos somente leitura e explicação prévia.

Sequência pendente:

1. armazenamento/filesystems;
2. mounts;
3. rede;
4. uptime/estado básico.

Nenhuma decisão de particionamento, LVM ou reorganização de disco deve ser tomada antes do inventário completo, análise e HUMAN_GATE de LEANDRO.

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
