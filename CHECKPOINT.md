# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo responde principalmente: **onde estamos agora?** O contexto permanente está distribuído conforme `CONTEXT.md`.

## Gate de continuidade

O PUC v1.0 foi implantado e validado em novo chat usando somente o GitHub canônico.

**Resultado: CONTINUIDADE COMPLETA.**

Evidência: `governance/CONTINUITY-VALIDATION-2026-08-14.md`.

A retomada operacional está liberada, respeitando HUMAN_GATEs e autorizações já registrados.

## Estado atual

- Repositório: `leon337/cloud-infrastructure`.
- Fase: **FASE 0 — ORIENTAÇÃO E INVENTÁRIO**.
- Etapa: **0.5 — Inventário real da VPS**.
- Etapas 0.1 a 0.4: concluídas.
- Etapa 0.5: `IN_PROGRESS`.
- Coleta técnica da Etapa 0.5: **CONCLUÍDA**.
- Fechamento da Etapa 0.5: **pendente de revisão consolidada e confirmação de entendimento de LEANDRO**.
- PUC v1.0: `DONE`.

## Identificadores operacionais

- VPS: Contabo Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Usuário administrativo temporário: `root`.
- Linux Mint local observado: `leo@leo-N43SM`.
- Alias SSH: `contabo-vps`.
- Fingerprint ED25519 validada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

## Inventário confirmado

### Sistema e virtualização

- Ubuntu 24.04.4 LTS — Noble Numbat.
- Kernel: `Linux 6.8.0-137-generic`.
- Arquitetura: x86-64.
- Chassis: VM.
- Virtualização: KVM.
- Hardware virtual: QEMU.

### CPU e memória

- CPU: 8 lógicas, AMD EPYC apresentado à VM, 1 socket, 8 cores/socket, 1 thread/core.
- RAM visível: ~23 GiB.
- RAM usada na medição inicial: ~592 MiB.
- RAM disponível na medição inicial: ~22 GiB.
- Swap: 0 B.

### Armazenamento/filesystems

- disco principal `/dev/sda`: QEMU HARDDISK, 300 GiB, GPT;
- `/dev/sda1`: ~299G, ext4, label `cloudimg-rootfs`, montado em `/`;
- `df -hT` da raiz: ~290G total, ~2.4G usados, ~288G disponíveis, ~1% de uso;
- `/dev/sda14`: 4M, `BIOS boot`, sem filesystem/mountpoint exibido;
- `/dev/sda15`: ~106M, vfat/FAT32, `EFI System`, montado em `/boot/efi`;
- `/dev/sda16`: ~913M, ext4, montado em `/boot`;
- `sr0`: ROM virtual ~4M, iso9660, label `cidata`.

### Rede

- interface principal: `eth0`, `UP`;
- IPv4: `169.58.171.192/17`;
- gateway IPv4: `169.58.128.1`;
- IPv6 global: `2a02:c207:2350:6102::1/64`;
- gateway IPv6: `fe80::1`;
- DNS via `systemd-resolved` stub;
- servidores DNS observados: `195.179.224.53` e `209.126.15.53`;
- `sshd` em TCP `0.0.0.0:22` e `[::]:22`;
- `systemd-resolved` ouvindo localmente em `127.0.0.53:53` e `127.0.0.54:53`.

### Estado básico

- uptime observado: ~5h37;
- load average observado: `0.00 0.03 0.00`;
- timezone: `Europe/Berlin` (`CEST`, UTC+2 no momento observado);
- NTP: ativo;
- relógio sincronizado: sim;
- unidades `systemd` em falha: 0;
- `systemctl is-system-running`: `running`;
- `apt list --upgradable`: 5 pacotes krb5 observados como atualizáveis segundo os índices APT existentes;
- nenhum `apt update` foi executado durante o inventário, portanto esse último dado não é uma fotografia garantidamente atual dos repositórios externos.

Detalhes permanentes: `docs/06-inventario.md`.

## Acesso e FND-SSH-001

- SSH root validado.
- Alias `contabo-vps` validado.
- Keepalive permanente aplicado no Linux Mint LOCAL e validado após ~3 minutos de ociosidade com `echo vivo`.
- `FND-SSH-001`: **RESOLVED**.
- VNC/TigerVNC validado.
- Remmina chegou ao serviço, mas não concluiu a sessão no teste.
- Rescue System conhecido, não acionado.

Detalhes: `findings/FND-SSH-001.md`, `docs/01-primeiro-acesso-seguro.md` e `runbooks/acesso-e-recuperacao.md`.

## Ponto exato de retomada

**NÃO iniciar a FASE 1 ainda.**

A coleta técnica da Etapa 0.5 terminou. O próximo passo é apresentar/revisar com LEANDRO o inventário consolidado, confirmar entendimento conforme a Definition of Done didática e somente então marcar a Etapa 0.5 como `DONE`.

Depois disso, qualquer avanço para FASE 1 deve respeitar o plano provisório e os HUMAN_GATEs aplicáveis.

## Proibições imediatas

Não executar ainda sem etapa própria e autorização:

- particionamento ou alteração destrutiva de disco;
- firewall;
- desativação de root;
- desativação de senha SSH;
- instalação de Docker;
- desktop gráfico;
- alterações de swap;
- hardening em lote;
- atualização/upgrade em lote.

## Próxima leitura obrigatória

Qualquer novo chat deve começar em `CONTEXT.md`, não neste arquivo isoladamente.
