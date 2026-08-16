# Configuração sanitizada implantada

Artefatos de referência para reconstrução:

- `00-cloud-workstation-hardening.conf` → `/etc/ssh/sshd_config.d/`;
- `cloud-workstation-sshd.local` → `/etc/fail2ban/jail.d/`;
- `ubuntu.xsession` → `/home/ubuntu/.xsession`;
- `light-locker.desktop` → `/home/ubuntu/.config/autostart/`;
- `cloud-infrastructure-config-backup` → `/usr/local/sbin/`;
- unidades systemd → `/etc/systemd/system/`;
- `cloud-infrastructure-backup.conf` → `/etc/tmpfiles.d/`.

O `xrdp.ini` de pacote foi preservado, alterando somente o `port=` da seção `[Globals]` para `tcp://127.0.0.1:3389`. Os ports dos backends `[Xorg]` e `[Xvnc]` permanecem `-1`.

Estes arquivos não contêm credenciais, chaves privadas ou conteúdo de `authorized_keys`. Aplicação em outro host exige revisão, backup e validação própria.
