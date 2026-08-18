# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-18 após retomada manual da missão. Este arquivo responde: **onde estamos agora?**

## Estado durável

- Repositório: `leon337/cloud-infrastructure`, branch `main`.
- FASE 0 — inventário: `DONE`.
- FASE 1 — acesso, recovery e segurança mínima: `DONE`.
- FASE 2 — Cloud Workstation: `DONE`, `FUNCTIONAL_AND_VALIDATED`.
- As antigas F3–F10 permanecem históricas/provisórias; a implementação agora segue a arquitetura definida pela Platform Discovery.
- `CREDENTIAL_ROTATION`: `DEFERRED_BY_HUMAN_DECISION`.
- Platform Discovery Q1–Q40 concluída para fins de delegação; Q1–Q39 são requisitos arquitetônicos vinculantes.
- Q40 = `D`: LEANDRO delegou ao Codex a seleção tecnológica e a implementação incremental da plataforma DEV/lab.
- Missão canônica: `docs/CODEX-EXECUTION-MISSION-001.md`.
- Checkpoint da decisão: `docs/39-platform-discovery-checkpoint-028.md`.
- Estado estruturado: `state/platform-discovery.yaml`.
- `implementation_authorized: true` para a plataforma privada DEV/lab dentro dos guardrails.
- `codex_implementation_mission_authorized: true`.
- `production_promotion_authorized: false`; produção continua sujeita a HUMAN_GATE de LEANDRO.

## Contingência de executor — 18/08/2026

- LEANDRO informou que o Codex está indisponível.
- LEANDRO assumiu temporariamente a execução manual das ações na VPS.
- MESTRE assume a orquestração técnica, análise dos resultados, definição de microtarefas, prechecks, rollback, validação e checkpoint.
- A contingência altera apenas o executor atual; não reabre decisões Q1–Q40, não amplia a autorização e não altera os guardrails.
- O contrato incremental de `docs/CODEX-EXECUTION-MISSION-001.md` continua sendo usado como contrato de execução, independentemente do executor.

## Guardrails vigentes

- LEANDRO continua autoridade humana final.
- Q1–Q39 não podem ser reabertas silenciosamente pelo executor.
- Nunca versionar passwords, passphrases, private keys, tokens, API keys, 2FA, connection strings reais ou credenciais do provedor.
- Management Plane não deve ser exposto publicamente.
- Agentes não recebem root/Docker daemon irrestrito.
- Mudanças críticas devem ter precheck, rollback e evidência.
- Cloud Workstation permanece cockpit humano opcional e não deve ser destruída sem plano de recuperação adequado.
- Rotação de credenciais continua adiada por decisão humana.
- Promoção para produção externa continua bloqueada até novo HUMAN_GATE.

## Segurança e acesso atuais

- `ubuntu`/publickey validado com chave dedicada; chave anterior preservada.
- SSH efetivo: root login `no`, password `no`, keyboard-interactive `no`, publickey `yes`, `MaxAuthTries 3`, `LoginGraceTime 30`, `AllowUsers ubuntu`.
- UFW ativo: default deny incoming; somente OpenSSH TCP 22 para IPv4/IPv6.
- fail2ban/sshd ativo.
- sudo exige senha; não há `NOPASSWD`; `visudo` validado.
- `ubuntu` não pertence ao grupo `lxd`; LXD daemon/socket estão desabilitados e inativos.

## Recovery e backup

- VNC Contabo revalidado funcionalmente.
- Rescue disponível, não acionado.
- Snapshots não configurados; backup do provedor não contratado; firewall do provedor não configurado.
- Backup diário sanitizado em `/var/backups/cloud-infrastructure` com timer ativo.
- Primeira cópia off-host em `/home/leo/Backups/cloud-infrastructure`; SHA-256 remoto/local idêntico e extração de 24 arquivos validada.
- Backup amplo de dados e reconstrução total ainda não foram testados; `FND-BACKUP-001` permanece mitigado/aberto.

## Cloud Workstation

- Stack: XFCE + LightDM + XRDP/xorgxrdp.
- XRDP escuta somente em `127.0.0.1:3389`; sesman somente em `[::1]:3350`; não há regra pública para RDP.
- Cliente validado por túnel SSH local `127.0.0.1:13389`.
- Passaram: desktop, login gráfico, Firefox, VS Code, terminal, terminal integrado, Thunar, projeto Git, múltiplas janelas, clipboard nos dois sentidos, 1100×700 e 1280×720, reconnect, persistência, logout/login e reboot.
- Recursos pós-reboot com sessão gráfica ativa: 8 CPUs, ~2,2 GiB/23 GiB RAM, ~7,5 GiB/290 GiB disco.

## Findings

- Resolvidos: `FND-SSH-001`, `FND-SSH-002`, `FND-SSH-003`, `FND-LXD-001`, `FND-SUDO-001`, `FND-DOC-001`, `FND-AUDIT-001`.
- Mitigado e aberto: `FND-BACKUP-001`.
- A investigar: `FND-CPU-001`, `FND-CLOUDINIT-001`.

## Regra de retomada

Toda retomada começa em `CONTEXT.md`, verifica a `main` real, lê `CHECKPOINT.md`, `state/current.yaml`, `state/platform-discovery.yaml`, `docs/39-platform-discovery-checkpoint-028.md` e `docs/CODEX-EXECUTION-MISSION-001.md`.

Próximo passo exato: **MISSION ACCEPTANCE + RECOVERY REPORT**, preservando o mesmo conteúdo exigido pela missão Codex, mas executado temporariamente por LEANDRO sob orquestração do MESTRE.

Antes de qualquer implementação ampla: recuperar GitHub + estado real da VPS, registrar divergências, confirmar riscos, Technology Mapping inicial e primeiro incremento com rollback; depois prosseguir incrementalmente dentro da autorização Q40-D.
