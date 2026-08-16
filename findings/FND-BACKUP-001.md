# FND-BACKUP-001 — Backup amplo de dados e reconstrução ainda pendentes

Status: **MITIGATED — OPEN**. Severidade atual: **MEDIUM**.

Na VPS não foram encontrados os utilitários comuns `restic`, `borg`, `rclone`, `duplicity` ou `rsnapshot`; apenas o timer de backup do banco do dpkg foi observado.

O estado de snapshots, backups, firewall, VNC e Rescue System do provedor não foi confirmado ao vivo na Fase B. Portanto não se afirma ausência desses recursos: seu estado permanece **UNCONFIRMED**.

Antes de hardening com risco de lockout e antes de considerar a Cloud Workstation pronta, definir e testar caminhos de recuperação proporcionais ao risco.

## Mitigação validada — 15/08/2026

- VNC Contabo revalidado funcionalmente;
- Rescue confirmado disponível;
- timer diário `cloud-infrastructure-config-backup.timer` ativo;
- configurações críticas sanitizadas arquivadas em `/var/backups/cloud-infrastructure`;
- primeira cópia off-host transferida para `/home/leo/Backups/cloud-infrastructure`;
- SHA-256 remoto/local idêntico;
- extração de recuperação validada com 24 arquivos.

O finding permanece aberto porque dados completos de usuário/workloads, retenção off-host automatizada e reconstrução integral ainda não foram testados. Snapshots continuam ausentes e backup do provedor não foi contratado.
