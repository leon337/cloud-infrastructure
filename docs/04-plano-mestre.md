# 04 — Plano Mestre

Este documento consolida o programa de capacidades.

## FASE 0 — Orientação e inventário — DONE

Arquitetura, primeiro acesso e inventário foram concluídos e revalidados.

## FASE 1 — Acesso administrativo, recovery e segurança mínima — DONE

- `ubuntu`/publickey e sessão independente: validados;
- VNC out-of-band: revalidado; Rescue: disponível;
- SSH endurecido; root e senha desabilitados no SSH;
- UFW ativo somente com OpenSSH e fail2ban ativo;
- sudo NOPASSWD removido e sudo autenticado validado;
- `ubuntu` removido de `lxd`; daemon/socket LXD desabilitados;
- updates aplicados e reboot validado;
- backup sanitizado diário, cópia off-host e extração de recuperação validados.

O backup amplo de dados e reconstrução integral permanecem evolução posterior, sem bloquear a segurança mínima já validada.

## FASE 2 — Cloud Workstation gráfica — DONE

Arquitetura: XFCE + LightDM + XRDP/xorgxrdp sobre túnel SSH. XRDP não é público.

Validações concluídas: login gráfico, navegador, VS Code, terminal, gerenciador de arquivos, projeto Git, múltiplas janelas, clipboard bidirecional, resolução dinâmica, desconexão/reconexão, persistência, logout/login, consumo de recursos e funcionamento após reboot.

## Plataforma privada DEV/lab — AUTHORIZED_INCREMENTAL

Q1–Q39 substituem as fases provisórias como especificação arquitetônica. Q40-D
autoriza Technology Mapping, blueprint e implementação incremental conforme
`CODEX-EXECUTION-MISSION-001.md`.

O plano executável está em:

- `41-consolidated-requirements.md`;
- `42-target-architecture.md`;
- `43-threat-model-and-autonomy-boundaries.md`;
- `44-infrastructure-blueprint-v1.md`;
- `45-revised-implementation-roadmap.md`;
- `46-technology-mapping-v1.md`.

O slice corrente é F1.1. Rotação permanece adiada; produção continua bloqueada.

Cloud Workstation foi antecipada por `DEC-003`; sua arquitetura foi formalizada por `DEC-004`.
