# Off-host recovery — RECOVERY-P2

Este mecanismo roda no computador do operador e **puxa** a evidência da VPS; ele não abre porta no notebook e não adiciona novo privilégio ao servidor.

Camadas:

1. o archive sanitizado root-owned já produzido pela VPS (SSH/UFW/Fail2ban/sudoers/estado);
2. um overlay allowlisted de units e scripts operacionais legíveis, incluindo Cloud Platform, SentinelX service, Hermes wrapper e helpers MCF;
3. metadata de runtime, hashes e `RECOVERY-MANIFEST.txt`.

Exclusões deliberadas: chaves privadas, identidades de provider/SentinelX, tokens, perfis/cookies de navegador, `.env`, dados completos de workloads e dados de usuário. Runtimes externos devem ser reinstalados/re-enrolled a partir de sua fonte oficial e validados contra o manifest.

O pull usa `BatchMode=yes` + `StrictHostKeyChecking=yes` e o ssh-agent do usuário. Se o agent ou a host key validada não estiver disponível, o job falha fechado.

Instalação no notebook:

```bash
install -m 0755 cloud-infrastructure-offhost-recovery ~/.local/bin/
install -m 0644 cloud-infrastructure-offhost-recovery.service ~/.config/systemd/user/
install -m 0644 cloud-infrastructure-offhost-recovery.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cloud-infrastructure-offhost-recovery.timer
```

O timer executa diariamente às 00:30, com persistência quando a máquina estava desligada. Cada execução cria um diretório imutável por timestamp em `~/Backups/cloud-infrastructure/recovery/` e atualiza o symlink `latest`.

O gerador root `/usr/local/sbin/cloud-infrastructure-config-backup` é deliberadamente `0750 root:root` no host live; o pull não tenta burlar essa permissão. Sua implementação é recuperada pela cópia versionada `config/vps/cloud-infrastructure-config-backup`, enquanto o bundle registra metadata do arquivo live.
