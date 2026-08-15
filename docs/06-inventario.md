# 06 — Inventário Real da VPS

Status: **ETAPA 0.5 CONCLUÍDA — fechamento didático aprovado por LEANDRO em 2026-08-14**.

Baseline histórica: 2026-08-14. Revalidação read-only mais recente: 2026-08-15.

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

### Proveniência cloud-init observada na baseline de 14/08

O arquivo de sudo criado pelo cloud-init para a conta `ubuntu` continha estes metadados de origem:

- `cloud_init_source_comment_version_observed`: `26.1-0ubuntu1~24.04.1`;
- `cloud_init_source_comment_created_at_utc_observed`: `2026-08-13 05:57:21 +0000`.

Esses valores são evidência histórica da baseline, não afirmação sobre a versão ou timestamp atuais.

## Regras derivadas do inventário

- Nenhuma decisão de particionamento/LVM/separação de `/home`, `/var` ou área Docker foi tomada.
- Nenhuma alteração de swap foi realizada.
- Nenhum firewall foi configurado nesta etapa.
- Nenhum serviço foi instalado ou removido para realizar o inventário.

## Fechamento da Etapa 0.5

A coleta técnica foi concluída, o inventário consolidado foi apresentado a LEANDRO e o fechamento recebeu aprovação explícita em 2026-08-14, satisfazendo a Definition of Done didática aplicável a esta etapa.

**Etapa 0.5 — DONE.**

## Fotografia de revalidação — 15/08/2026

Esta fotografia datada complementa, sem apagar, a baseline de 14/08. A coleta terminou em `2026-08-15T11:03:59Z` e foi aprovada por LEANDRO para reconciliação.

### Sistema e recursos

- identidade, Ubuntu 24.04.4, kernel `6.8.0-137-generic`, x86-64 e KVM/QEMU permanecem iguais;
- 8 CPUs lógicas, ~23 GiB RAM e swap 0 B;
- raiz ext4 com ~2,5 GiB usados e ~288 GiB disponíveis;
- aviso `Partition table entries are not in disk order` persiste;
- systemd `running`, 0 unidades failed, NTP sincronizado, timezone `Europe/Berlin`, sem reboot pendente;
- `lscpu` reportou `Spec rstack overflow: Vulnerable: Safe RET, no microcode`; análise pendente em `FND-CPU-001`.

### Rede, listeners e firewall

- `eth0`, endereços, rotas e DNS permanecem consistentes com a baseline;
- somente SSH TCP 22 em IPv4/IPv6 e DNS local em loopback estavam em escuta;
- UFW instalado, porém inativo; nenhuma regra nftables/iptables observada; fail2ban ausente;
- firewall do provedor não confirmado nesta auditoria.

### SSH e atividade observada

- efetivos: `PermitRootLogin yes`, `PasswordAuthentication yes`, `PubkeyAuthentication yes`, `X11Forwarding yes` e `AllowTcpForwarding yes`;
- root por senha validado durante a auditoria;
- desde o boot: 24.447 falhas de senha, 1.676 usuários inválidos, 42 eventos de máximo de autenticações e 3 eventos `MaxStartups`;
- nas 24 horas anteriores: 8.668 falhas de senha e 1.571 usuários inválidos;
- um login histórico por chave para `ubuntu` ocorreu em 14/08/2026;
- dez logins root por senha foram aceitos no período consultado, incluindo a auditoria; suas origens não foram atribuídas independentemente.

Os logs comprovam tentativas automatizadas, não invasão.

### Conta ubuntu e privilégios

- UID/GID 1000, home `/home/ubuntu`, shell `/bin/bash`, senha bloqueada;
- grupos: `ubuntu`, `adm`, `cdrom`, `sudo`, `dip`, `lxd`;
- sudo inclui `(ALL : ALL) ALL` e `(ALL) NOPASSWD: ALL`;
- NOPASSWD vem de `/etc/sudoers.d/90-cloud-init-users`, modo `440`;
- `.ssh` modo `700` e `authorized_keys` modo `600`, ambos de `ubuntu`;
- uma chave ED25519 autorizada, fingerprint `SHA256:FeamXuFKDiA868c9eKVH8AOMXOQMLL1KBNH4Y9DrqMU`, igual à chave pública local dedicada;
- a tentativa atual não concluiu autenticação por chave e caiu para senha; como a senha está bloqueada, o login falhou;
- causa exata não diagnosticada. Estado: **SSH DE ubuntu NÃO VALIDADO**.

### LXD

- snap LXD `5.21.6` instalado;
- 0 instâncias totais e 0 em execução na consulta autorizada;
- `lxc version` ativou o daemon pelo socket;
- recuperação autorizada terminou com daemon `inactive/dead`, processo ausente e socket `active/listening` e habilitado;
- nenhum listener de rede mudou;
- associação de `ubuntu` ao grupo `lxd` está em `FND-LXD-001`.

### Atualizações e integridade

- índice APT local mais recente: `2026-08-14 20:53:48`;
- os mesmos cinco pacotes Krb5 permaneciam candidatos de `.7` para `.8`, adiados por phasing;
- simulação: 0 upgraded, 0 newly installed, 0 removed, 5 not upgraded;
- auditoria dpkg limpa; unattended-upgrades e timers habilitados.

### Workstation, containers e recovery

- Docker e containerd não instalados;
- nenhum display manager, xrdp, servidor VNC guest ou desktop testável confirmado;
- `graphical.target` como default não prova presença de desktop;
- nenhum backup independente comum encontrado no guest;
- VNC, Rescue, snapshots, backups e firewall do provedor não foram revalidados ao vivo e permanecem **UNCONFIRMED**.

### Cloud-init

Cloud-init `26.1` terminou `degraded done` por chaves depreciadas; a lista de erros estava vazia. Ver `FND-CLOUDINIT-001`.

## Evento pós-auditoria — acesso SSH de ubuntu em 15/08/2026

Este evento complementa a fotografia anterior sem reescrevê-la. Na auditoria, o login atual de `ubuntu` ainda estava não validado; a Missão 2/2B resolveu esse bloqueio depois da coleta.

- a chave privada antiga estava protegida por passphrase desconhecida por LEANDRO e não estava disponível em `ssh-agent`/keyring;
- nenhuma tentativa de recuperar, extrair ou quebrar essa passphrase foi realizada;
- uma nova chave ED25519 dedicada foi criada localmente em `~/.ssh/id_ed25519_contabo_vps_ubuntu_20260815`;
- fingerprint pública validada: `SHA256:/p5jX65s2WyxkD3xooTozV09DSYAmKIAgZKk3Veb1Hg`;
- a nova chave pública foi adicionada a `/home/ubuntu/.ssh/authorized_keys` exatamente uma vez, sem substituir ou remover a chave anterior;
- `authorized_keys` permaneceu com proprietário `ubuntu:ubuntu` e modo `600`;
- root por senha foi revalidado no diagnóstico autorizado, com UID remoto `0` e exit code `0`, e permaneceu inalterado;
- login de `ubuntu` com a nova chave foi validado exclusivamente por `publickey`, com fallback para senha desativado;
- o teste confirmou usuário `ubuntu`, UID `1000` e hostname `vmi3506102`;
- o teste final executou somente identificação read-only e não alterou estado operacional;
- `sshd_config`, root, sudo, firewall e LXD não foram alterados.

Estado resultante: `FND-SSH-003` **RESOLVED**. A associação de `ubuntu` a sudo/NOPASSWD e ao grupo `lxd` permanece conforme a fotografia anterior e será revisada separadamente, mediante novo HUMAN_GATE.

## Evento pós-auditoria — revisão read-only de sudo/LXD em 15/08/2026

A Missão 4 complementa as fotografias anteriores. Houve uma tentativa de autenticação malsucedida antes da coleta bem-sucedida, sem efeito operacional. A sessão que produziu a evidência foi autenticada como `ubuntu` e confirmou usuário `ubuntu`, UID/GID `1000`, home `/home/ubuntu`, hostname `vmi3506102` e grupos `ubuntu adm cdrom sudo dip lxd`.

### Sudo/NOPASSWD

- `sudo -n -l` terminou com exit code `0` e confirmou as regras efetivas `(ALL : ALL) ALL` e `(ALL) NOPASSWD: ALL`;
- `sudo -n` confirmou elevação sem senha a UID `0` e usuário `root`;
- a origem observada foi `/etc/sudoers.d/90-cloud-init-users`, proprietário `root:root`, modo `440`;
- as regras ativas observadas foram `ubuntu ALL=(ALL) NOPASSWD:ALL` e `root ALL=(ALL) NOPASSWD:ALL`;
- `visudo -cf /etc/sudoers` terminou com validação `PASS`.

Resultado: caminho direto de elevação a root sem senha confirmado em `FND-SUDO-001`. Nenhuma política sudo foi alterada.

### Privilégio LXD

- snap LXD `5.21.6-78b046a`, revisão `40361`;
- socket existente, proprietário `root:lxd`, modo `660` e gravável pelo usuário autenticado `ubuntu`;
- combinação de associação ao grupo `lxd` e escrita no socket confirmou um caminho equivalente a root, sem exploração;
- daemon antes/depois: `inactive/dead`; socket unit antes/depois: `active/listening/enabled`;
- hash dos listeners antes/depois: `bbda5db2de8957b27e25815cd797a72b67a5e11fe14bbe4a06ff7272f362383b`;
- nenhum comando `lxc` foi executado.

Resultado: `FND-LXD-001` permanece **OPEN/HIGH**, agora sustentado por evidência direta de acesso ao socket. A coleta não executou escrita de configuração, mudança de serviço, alteração de firewall ou qualquer outra mudança operacional.

Próximo micro-passo proposto: revisão read-only de recovery proporcional e validação dos caminhos de recuperação, somente após novo HUMAN_GATE.
