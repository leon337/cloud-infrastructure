# 05 — Roadmap

Estados: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `HUMAN_GATE`, `VALIDATING`, `DONE`, `DEFERRED`, `PROVISIONAL`.

| Fase/Etapa | Estado | Evidência/Gate |
|---|---|---|
| 0.1 Modelo mental | DONE | LEANDRO confirmou compreensão |
| 0.2 Repositório canônico | DONE | `cloud-infrastructure` criado, privado e separado do MCF |
| 0.3 Preparação do primeiro acesso | DONE | painel Contabo e credenciais rotacionadas |
| 0.4 Primeiro acesso seguro | DONE | VNC/TigerVNC + SSH + fingerprint validada |
| 0.5 Inventário real | IN_PROGRESS | coleta técnica de SO/kernel/CPU/RAM/disco/filesystems/mounts/rede/uptime/estado básico concluída; falta revisão consolidada e fechamento didático com LEANDRO |
| PUC v1.0 | DONE | teste canônico em novo chat resultou em CONTINUIDADE COMPLETA |
| F1 Base/segurança inicial | PROVISIONAL | após inventário completo e fechamento da Etapa 0.5 |
| F2 Rede/firewall | PROVISIONAL | após acesso alternativo e políticas definidas |
| F3 Armazenamento | PROVISIONAL | decisão somente após inventário e HUMAN_GATE |
| F4 Manutenção/updates | PROVISIONAL | gate futuro |
| F5 Backup/recovery | PROVISIONAL | gate futuro |
| F6 Docker/Compose | PROVISIONAL | somente após base segura e aula |
| F7 Desenvolvimento remoto | PROVISIONAL | gate futuro |
| F8 Observabilidade | PROVISIONAL | gate futuro |
| F9 Plataforma de serviços | PROVISIONAL | gate futuro |
| F10 Cloud Workstation | DEFERRED | avaliar depois da base segura |
| F11 Workloads | PROVISIONAL | implantação gradual |
| F12 Autonomia/reconstrução | PROVISIONAL | maturidade final |

## Gate de continuidade

**PUC v1.0 VALIDADO — CONTINUIDADE COMPLETA.**

Evidência: `governance/CONTINUITY-VALIDATION-2026-08-14.md`.

## Estado da Etapa 0.5

A coleta técnica do inventário foi concluída por comandos somente leitura e está consolidada em `docs/06-inventario.md`.

A etapa permanece `IN_PROGRESS` porque a Definition of Done didática exige revisão/entendimento de LEANDRO antes de marcar `DONE` e avançar para uma fase futura.
