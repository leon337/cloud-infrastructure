# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-15 após o reboot final. Este arquivo responde: **onde estamos agora?**

## Estado durável

- Repositório: `leon337/cloud-infrastructure`, branch `main`.
- FASE 0 — inventário: `DONE`.
- FASE 1 — acesso, recovery e segurança mínima: `DONE`.
- FASE 2 — Cloud Workstation: `DONE`, `FUNCTIONAL_AND_VALIDATED`.
- Próximo passo exato: `CREDENTIAL_ROTATION`.
- O PUC v1.0 permanece ativo; validações independentes anteriores continuam históricas e um novo teste independente deve ser feito após a publicação deste estado.
- Os artefatos sanitizados implantados e necessários à reconstrução estão versionados em `config/vps/`.

## Segurança e acesso

- `ubuntu`/publickey validado com a chave dedicada; chave anterior preservada.
- SSH efetivo: root login `no`, password `no`, keyboard-interactive `no`, publickey `yes`, `MaxAuthTries 3`, `LoginGraceTime 30`, `AllowUsers ubuntu`.
- UFW ativo: default deny incoming; somente OpenSSH TCP 22 para IPv4/IPv6.
- fail2ban/sshd ativo.
- sudo exige senha; `sudo -n` falha e não há regra `NOPASSWD`; `visudo` passa.
- `ubuntu` não pertence ao grupo `lxd`; LXD daemon/socket estão desabilitados e inativos; zero instâncias foram observadas antes da desativação.
- Root continua existindo para console/recovery, mas não autentica por SSH.

## Recovery e backup

- VNC Contabo revalidado funcionalmente em console `tty1`.
- Rescue disponível, não acionado.
- Snapshots não configurados; backup do provedor não contratado; firewall do provedor não configurado.
- Backup diário sanitizado em `/var/backups/cloud-infrastructure` com timer ativo e criação persistente do diretório por `systemd-tmpfiles`.
- Primeira cópia off-host em `/home/leo/Backups/cloud-infrastructure`; SHA-256 remoto/local idêntico e extração de 24 arquivos validada.
- Backup amplo de dados e reconstrução total ainda não foram testados; `FND-BACKUP-001` permanece mitigado/aberto.

## Cloud Workstation

- Stack: XFCE + LightDM + XRDP/xorgxrdp.
- XRDP escuta somente em `127.0.0.1:3389`; sesman somente em `[::1]:3350`; não há regra pública para RDP.
- Cliente validado por túnel SSH local `127.0.0.1:13389`.
- Passaram: desktop, login gráfico, Firefox, VS Code, terminal, terminal integrado, Thunar, projeto Git, múltiplas janelas, clipboard nos dois sentidos, 1100×700 e 1280×720, reconnect, persistência, logout/login e reboot.
- Firefox Snap incompatível com XRDP foi substituído pelo Firefox DEB oficial da Mozilla.
- Recursos pós-reboot com sessão gráfica ativa: 8 CPUs, ~2,2 GiB/23 GiB RAM, ~7,5 GiB/290 GiB disco.

## Findings

- Resolvidos: `FND-SSH-001`, `FND-SSH-002`, `FND-SSH-003`, `FND-LXD-001`, `FND-SUDO-001`, `FND-DOC-001`, `FND-AUDIT-001`.
- Mitigado e aberto: `FND-BACKUP-001`.
- A investigar: `FND-CPU-001`, `FND-CLOUDINIT-001`.

## Regra de retomada

Rotacionar credenciais temporárias somente com preservação dos canais validados. Novas mudanças estruturais e futuros commits seguem o HUMAN_GATE aplicável. Toda retomada começa em `CONTEXT.md` e verifica a `main` real.
