# 06 — Inventário Real da VPS

Status: **ETAPA 0.5 CONCLUÍDA — fechamento didático aprovado por LEANDRO em 2026-08-14**.

Última coleta: 2026-08-14.

## Identidade

- Provedor: Contabo.
- Produto: Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Região contratada originalmente: European Union.

## Sistema

- Ubuntu 24.04.4 LTS.
- Noble Numbat (`noble`).
- Kernel `Linux 6.8.0-137-generic`.
- Arquitetura x86-64.

## Virtualização

- Chassis: VM.
- Hypervisor: KVM.
- Hardware virtual apresentado: QEMU.

## CPU

- 8 CPUs lógicas (`0-7`).
- AMD EPYC Processor (with IBPB) apresentado à VM.
- 1 socket virtual.
- 8 cores/socket.
- 1 thread/core.

Uma linha de vulnerabilidade de CPU foi observada no `lscpu`; não foi diagnosticada nesta etapa e deve ser reavaliada durante hardening/kernel, sem conclusões precipitadas.

## Memória

Medição com `free -h`:

- total visível ~23 GiB;
- usada ~592 MiB naquele instante;
- disponível ~22 GiB;
- swap: 0 B.

Swap ausente é fato de inventário, não decisão de que deve permanecer assim.

## Armazenamento e filesystems

### Disco principal

`lsblk` e `fdisk -l /dev/sda` confirmaram:

- disco virtual principal: `/dev/sda`;
- modelo apresentado: `QEMU HARDDISK`;
- capacidade: 300 GiB;
- tabela de partições: GPT;
- setor lógico/físico: 512 bytes.

Partições observadas:

- `/dev/sda1` — ~299G — tipo GPT `Linux filesystem`;
- `/dev/sda14` — 4M — tipo GPT `BIOS boot`;
- `/dev/sda15` — ~106M — tipo GPT `EFI System`;
- `/dev/sda16` — ~913M — tipo GPT `Linux extended boot`.

A mensagem `Partition table entries are not in disk order` foi observada pelo `fdisk`; nesta etapa ela é registrada como observação, sem inferir falha.

### Filesystems e mounts persistentes

`lsblk -f`, `df -hT` e `findmnt` confirmaram:

- `/dev/sda1`:
  - filesystem `ext4`;
  - label `cloudimg-rootfs`;
  - montado em `/`;
  - `df -hT`: ~290G de filesystem, ~2.4G usados, ~288G disponíveis, ~1% de uso no momento da coleta.
- `/dev/sda16`:
  - filesystem `ext4`;
  - label `BOOT`;
  - montado em `/boot`;
  - `df -hT`: ~881M total, ~117M usados, ~703M disponíveis, ~15% de uso.
- `/dev/sda15`:
  - filesystem `vfat`/FAT32;
  - label `UEFI`;
  - montado em `/boot/efi`;
  - `df -hT`: ~105M total, ~6.2M usados, ~99M disponíveis, ~6% de uso.
- `/dev/sda14`:
  - partição `BIOS boot`;
  - sem filesystem ou mountpoint exibido.
- `sr0`:
  - dispositivo ROM virtual de ~4M;
  - filesystem `iso9660`;
  - label `cidata`.

Os `tmpfs`, `proc`, `sysfs`, `devtmpfs`, `cgroup2` e outros mounts virtuais observados são registrados como pseudo-filesystems do sistema, não como partições adicionais do SSD.

## Rede

### Interfaces e endereços

`ip -brief address` confirmou:

- `lo`:
  - `127.0.0.1/8`;
  - `::1/128`.
- `eth0`: estado `UP`;
  - IPv4: `169.58.171.192/17`;
  - IPv6 global: `2a02:c207:2350:6102::1/64`;
  - IPv6 link-local: `fe80::250:56ff:fe66:69ed/64`.

### Rotas IPv4

`ip route` confirmou:

- gateway padrão IPv4: `169.58.128.1` via `eth0`;
- rota observada para `169.58.128.0/17` via `169.58.128.1` em `eth0`.

### Rotas IPv6

`ip -6 route` confirmou:

- prefixo global `2a02:c207:2350:6102::/64` em `eth0`;
- prefixo link-local `fe80::/64` em `eth0`;
- gateway padrão IPv6: `fe80::1` via `eth0`.

### DNS

`resolvectl status` confirmou:

- `systemd-resolved` em modo `stub`;
- DNS atual: `195.179.224.53`;
- servidores DNS listados:
  - `195.179.224.53`;
  - `209.126.15.53`;
- LLMNR desativado;
- mDNS desativado;
- DNS-over-TLS desativado;
- DNSSEC reportado como `no/unsupported`.

Esses itens são fatos de inventário, não decisões de política DNS.

### Portas/processos em escuta

`ss -lntup` confirmou:

- SSH (`sshd`):
  - TCP `0.0.0.0:22`;
  - TCP `[::]:22`.
- `systemd-resolved`:
  - TCP/UDP em `127.0.0.53:53` e `127.0.0.54:53`.

O fato de `sshd` ouvir em todas as interfaces locais não prova sozinho alcançabilidade externa irrestrita; firewall do host/provedor e demais políticas devem ser avaliados separadamente.

Nenhuma porta VNC foi observada dentro do Ubuntu; o VNC já validado pertence à infraestrutura de console da Contabo, não a um servidor VNC instalado nesta VPS.

## Estado básico

### Uptime e carga

`uptime` observado:

- uptime ~5h37 no momento da medição;
- 2 sessões/usuários contabilizados;
- load average: `0.00`, `0.03`, `0.00` para 1, 5 e 15 minutos.

### Hora e sincronização

`timedatectl` confirmou:

- timezone: `Europe/Berlin`;
- horário local observado em CEST (`UTC+2`);
- relógio do sistema sincronizado: `yes`;
- serviço NTP: `active`;
- RTC em UTC (`RTC in local TZ: no`).

Timezone atual é fato de inventário; nenhuma decisão de alteração foi tomada nesta etapa.

### Estado do systemd

- `systemctl --failed --no-pager`: `0 loaded units listed`;
- `systemctl is-system-running`: `running`.

### Atualizações pendentes segundo os índices atuais

`apt list --upgradable` listou cinco pacotes Kerberos/Krb5 como atualizáveis:

- `krb5-locales`;
- `libgssapi-krb5-2`;
- `libk5crypto3`;
- `libkrb5-3`;
- `libkrb5support0`.

Versão disponível observada: `1.20.1-6ubuntu2.8`, a partir de `1.20.1-6ubuntu2.7`.

Importante: nenhum `apt update` foi executado nesta etapa; portanto a lista reflete os índices APT já presentes na VPS naquele momento e não deve ser tratada como fotografia garantidamente atual dos repositórios externos.

## Acesso

- SSH validado.
- Alias local `contabo-vps` validado.
- Keepalive permanente do cliente SSH local aplicado e validado.
- `FND-SSH-001`: `RESOLVED`.
- VNC/TigerVNC validado.
- Remmina: serviço alcançado, sessão não concluída no teste.
- Rescue System: conhecido, não acionado.

## Regras derivadas do inventário

- Nenhuma decisão de particionamento/LVM/separação de `/home`, `/var` ou área Docker foi tomada.
- Nenhuma alteração de swap foi realizada.
- Nenhum firewall foi configurado nesta etapa.
- Nenhum serviço foi instalado ou removido para realizar o inventário.

## Fechamento da Etapa 0.5

A coleta técnica foi concluída, o inventário consolidado foi apresentado a LEANDRO e o fechamento recebeu aprovação explícita em 2026-08-14, satisfazendo a Definition of Done didática aplicável a esta etapa.

**Etapa 0.5 — DONE.**
