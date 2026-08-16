# FND-BACKUP-001 — Backup amplo de dados e reconstrução ainda pendentes

Status: **MITIGATED — OPEN**. Severidade atual: **MEDIUM**.

Na recuperação de 16/08/2026, Restic/pgBackRest e backup amplo continuavam
ausentes. O timer sanitizado de configurações estava ativo e íntegro.

O painel foi verificado durante F1/F2: VNC foi validado, Rescue estava disponível,
snapshots/firewall não estavam configurados e backup do provedor não estava
contratado. A recuperação Codex não reabriu o painel; esses fatos continuam sendo
a última evidência humana, não observação atual dentro do guest.

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

## Limites confirmados na recuperação Codex — 16/08/2026

- dois arquivos remotos passaram checksum e leitura integral do tar;
- somente o primeiro tinha cópia off-host observada com SHA-256 correspondente;
- a extração histórica prova legibilidade, não restore funcional;
- `copy_config()` arquiva todos os arquivos com modo `0640`, inclusive fontes
  originalmente executáveis como `xrdp/startwm.sh`; restore cego pode quebrar
  semântica, owner ou mode;
- o backup é referência proporcional de configuração, não artefato drop-in;
- o script versionado agora possui bit executável, alinhado ao deployment remoto,
  mas a preservação de metadata exige um slice próprio com teste de restore.

## Platform Discovery — Q16 — 16/08/2026

LEANDRO aprovou a estratégia **C — infraestrutura reconstruível + backups automáticos off-host + restore testado**, registrada em `docs/15-platform-discovery-checkpoint-004.md`.

Isso transforma as pendências deste finding em requisitos explícitos da arquitetura-alvo:

- compute e configuração devem ser reconstruíveis a partir de artefatos versionados;
- dados persistentes relevantes devem possuir backup automático;
- deve existir cópia off-host independente da VPS;
- restore deve ser testado e produzir evidência verificável;
- estado descartável não precisa ser tratado como dado permanente;
- a arquitetura deve permitir reconstrução em novo host/provedor sem depender da memória humana.

**O status deste finding não muda por causa da decisão de Discovery.** Ele permanece `MITIGATED — OPEN` até que esses requisitos sejam implementados e validados operacionalmente.
