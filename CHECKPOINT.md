# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-16 durante a nova Platform Discovery. Este arquivo responde: **onde estamos agora?**

## Estado durável

- Repositório: `leon337/cloud-infrastructure`, branch `main`.
- FASE 0 — inventário: `DONE`.
- FASE 1 — acesso, recovery e segurança mínima: `DONE`.
- FASE 2 — Cloud Workstation: `DONE`, `FUNCTIONAL_AND_VALIDATED`.
- As antigas F3–F10 permanecem `PROVISIONAL_PENDING_PLATFORM_DISCOVERY`.
- `CREDENTIAL_ROTATION`: `DEFERRED_BY_HUMAN_DECISION`.
- Próximo passo exato: `DISCOVERY_Q8`.
- Checkpoint da Discovery: `docs/12-platform-discovery-checkpoint-001.md`.
- Nenhuma implementação pesada da nova plataforma está autorizada antes do fechamento da Discovery e de HUMAN_GATE explícito de LEANDRO.
- O PUC v1.0 permanece ativo; validações independentes anteriores continuam históricas.

## Segurança e acesso

- `ubuntu`/publickey validado com a chave dedicada; chave anterior preservada.
- SSH efetivo: root login `no`, password `no`, keyboard-interactive `no`, publickey `yes`, `MaxAuthTries 3`, `LoginGraceTime 30`, `AllowUsers ubuntu`.
- UFW ativo: default deny incoming; somente OpenSSH TCP 22 para IPv4/IPv6.
- fail2ban/sshd ativo.
- sudo exige senha; não há `NOPASSWD`; `visudo` validado.
- `ubuntu` não pertence ao grupo `lxd`; LXD daemon/socket estão desabilitados e inativos.
- Root continua existindo para console/recovery, mas não autentica por SSH.

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

## Platform Discovery — Q1–Q7

Estado: `IN_PROGRESS`.

Decisões registradas:

1. Q1 `C` — plataforma privada de computação, desenvolvimento e execução de agentes;
2. Q2 `C` — infraestrutura própria como padrão para laboratório DEV, externa quando vantajosa/produção;
3. Q3 `C` — projeto isolado + sandboxes temporários por missão/agente;
4. Q4 `C` — autonomia dentro de sandbox/projeto, HUMAN_GATE fora do escopo;
5. Q5 `D` — Capability Core + API + MCP + CLI, progressivamente;
6. Q6 `C` — laboratório completo de desenvolvimento, implementado progressivamente;
7. Q7 `C` — ambientes descartáveis, dados importantes explicitamente persistentes.

Princípios consolidados até aqui:

- development autonomy first;
- production portability;
- autonomia por escopo, não acesso irrestrito;
- isolamento entre projetos;
- sandboxes temporários;
- compute descartável;
- estado importante explicitamente persistente;
- MCP como interface para agentes, não como núcleo único da infraestrutura.

## Findings

- Resolvidos: `FND-SSH-001`, `FND-SSH-002`, `FND-SSH-003`, `FND-LXD-001`, `FND-SUDO-001`, `FND-DOC-001`, `FND-AUDIT-001`.
- Mitigado e aberto: `FND-BACKUP-001`.
- A investigar: `FND-CPU-001`, `FND-CLOUDINIT-001`.

## Regra de retomada

Toda retomada começa em `CONTEXT.md`, verifica a `main` real, lê `CHECKPOINT.md`, `state/current.yaml` e `docs/12-platform-discovery-checkpoint-001.md`.

Próximo passo: **DISCOVERY_Q8**.

Não executar rotação de credenciais agora. Não iniciar implementação pesada ou entregar missão de implementação ao Codex até que a Discovery produza requisitos consolidados, arquitetura-alvo, limites de autonomia/threat model, Infrastructure Blueprint v1, roadmap revisado e HUMAN_GATE explícito de LEANDRO.
