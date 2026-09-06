# PRE-REBOOT CHECKPOINT — NODE-01 — 2026-09-06

Status: `FRESH_READ_ONLY_VERIFIED_OFFHOST_RECOVERY_FRESH`

## Escopo

Checkpoint read-only autorizado por LEANDRO em 06/09/2026.
Nenhum update, reboot, restart, deploy, firewall change ou write foi executado na VPS.
DeepSeek Harness e 9router permaneceram `EXTERNALLY_MANAGED_OBSERVE_ONLY`: nenhum endpoint,
config, processo, supervisor ou sessão desses serviços foi operado.

Base canônica no início: `main@7ce6fff85f66eaed88c7b6e092c4bc2375f5382d`.
Janela principal de coleta: `2026-09-06T13:30:23-03:00` a `13:34:47-03:00`.

## Sistema e reboot

- Host: `vmi3506102`.
- OS: Ubuntu 24.04.4 LTS.
- Kernel em execução: `6.8.0-138-generic`.
- Pacote alvo instalado: `linux-image-6.8.0-139-generic 6.8.0-139.139`.
- `/var/run/reboot-required`: presente.
- Pacotes do reboot: `linux-image-6.8.0-139-generic` e `linux-base`.
- `systemctl --failed`: zero unidades listadas.

## Serviços críticos

Observados `active`:

- `cloud-platform-network-services.service` (`enabled`);
- `systemd-networkd.service` (`enabled`);
- `systemd-networkd-wait-online.service` (`enabled`);
- `docker.service` e `containerd.service` (`enabled`);
- `ufw.service` e `fail2ban.service` (`enabled`);
- `tailscaled.service` (`enabled`);
- `sentinelx-cloud-core.service` (`enabled`);
- `actions.runner.leon337-cloud-infrastructure.node--1-mcf-control.service` (`enabled`);
- `ssh.service` ativo; unit reportada `disabled`, com listeners TCP/22 em IPv4 e IPv6.

Runner:
- MainPID `859398`;
- Listener PID `859415`;
- `ActiveState=active`, `SubState=running`;
- início: `2026-09-05 20:20:44 -03`.

SentinelX:
- MainPID `47653`;
- `ActiveState=active`, `SubState=running`;
- início: `2026-09-01 07:02:28 -03`;
- conectividade persistente ao hub não foi promovida a PASS; causa de intermitência segue `NOT_VERIFIED`.

## Rede, firewall e recursos

- `eth0`: `routable (configured)` e `online`.
- IPv4 público: `169.58.171.192`.
- Gateway: `169.58.128.1`.
- Rota crítica preservada: `169.58.128.1 dev eth0 proto static scope link`.
- Default route: `default via 169.58.128.1 dev eth0 proto static`.
- Tailscale IPv4: `100.71.228.75/32`.
- TCP/22 escutando em `0.0.0.0:22` e `[::]:22`.
- `/etc/ufw/ufw.conf`: `ENABLED=yes`.
- UFW e Fail2Ban: `active`.
- `/`: ext4 290G, 58G usados, 233G disponíveis, 20%.
- RAM: 23 GiB total, ~14 GiB disponíveis no momento da leitura.
- Swap: 0B.

## Workloads Cloud observados sem tocar serviços externos

A contagem inicial por nome exato retornou `squid=0` porque o processo se chama
`squid-gnutls`. A inspeção read-only de processos/cgroups confirmou:

- 2× `coredns`;
- 2× `squid-gnutls`;
- todos os quatro dentro de scopes Docker sob `cloud-platform.slice`.

Não foi feito inventário/probe ativo de DeepSeek Harness ou 9router.

## Backup on-host

Último backup encontrado:

`/var/backups/cloud-infrastructure/cloud-infrastructure-config-20260906T030657Z.tar.gz`

- size: `34567` bytes;
- mtime: `2026-09-06 00:06:59 -03`;
- mode: `640`;
- owner: `root:adm`;
- SHA-256: `ec5d83ddcf8ef72d92d2d52590e6d8a4329fdce6893088ee16520ebb0c5816f4`;
- `tar -tzf`: `PASS`.

Classificação: `FRESH_INTEGRITY_PASS`.

## Recovery off-host

Último recovery completo encontrado no notebook:

`/home/leo/Backups/cloud-infrastructure/recovery/20260905T033111Z`

`SHA256SUMS` foi revalidado: `6/6 PASS`.
Não existe diretório de recovery de 06/09 no momento da coleta.
Nas superfícies verificadas não foi encontrado:

- unit/timer systemd do recovery off-host no escopo do usuário;
- unit/timer systemd correspondente no escopo do sistema;
- entrada no crontab do usuário para esse recovery.

Isso **não prova ausência de outro scheduler**. A causa da falta de recovery de 06/09 é
`NOT_VERIFIED`.

Classificação naquele momento: `NOT_FRESH_FOR_2026_09_06_REBOOT_GATE`.

## Execução autorizada do gate de recovery off-host

LEANDRO autorizou `PRE_REBOOT_OFFHOST_RECOVERY_FRESHNESS_GATE` em 06/09/2026.
Foi executado o script canônico de `main@7ce6fff85f66eaed88c7b6e092c4bc2375f5382d`, usando
`BatchMode=yes`, `StrictHostKeyChecking=yes` e o ssh-agent estável do notebook. Nenhum comando de
update, reboot, restart, deploy, firewall ou mutação de serviço foi executado na VPS.

Resultado:

- recovery: `/home/leo/Backups/cloud-infrastructure/recovery/20260906T185928Z`;
- formato: `RECOVERY-P2-v1`;
- backup raiz: `cloud-infrastructure-config-20260906T030657Z.tar.gz`;
- SHA-256 raiz: `ec5d83ddcf8ef72d92d2d52590e6d8a4329fdce6893088ee16520ebb0c5816f4`;
- `SHA256SUMS`: 6/6 PASS;
- `SECRET_SCAN=PASS`;
- `ARCHIVE_PATH_SAFETY=PASS`;
- `ARCHIVE_LINK_SAFETY=PASS`;
- `RESTORE_SMOKE=PASS`;
- root members: 41;
- runtime overlay members: 11;
- symlink `latest` aponta para `20260906T185928Z`.

Recheck mínimo na mesma janela confirmou `system_state=running`, zero failed units e kernel
`6.8.0-138-generic`; F1.2c, `eth0=routable (configured)`, online state, gateway `/32` e default route
já haviam sido revalidados nesta retomada antes do pull.

A causa de o recovery automático de 06/09 não existir às 13:34 continua `NOT_VERIFIED`; a execução
manual autorizada fecha a lacuna de frescor sem promover hipótese sobre scheduler.

Classificação atual: `FRESH_FOR_2026_09_06_REBOOT_GATE`.

## Decisão atual do checkpoint

- `live_snapshot_fresh=true`.
- `accepted_for_current_reboot=false`.
- `blocking_reason=EXTERNAL_SERVICE_COORDINATION_PENDING`.
- recovery off-host fresco: **PASS**.
- Reboot e updates continuam `NOT_AUTHORIZED_HUMAN_GATE_REQUIRED`.
- DeepSeek Harness e 9router permanecem `EXTERNALLY_MANAGED_OBSERVE_ONLY`.

Próximo gate:

`PRE_REBOOT_EXTERNAL_SERVICE_COORDINATION_GATE`

Nenhuma causa não comprovada foi promovida a fato e nenhum reboot/update foi autorizado.
