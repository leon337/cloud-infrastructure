# 05 — Roadmap

Estados: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `HUMAN_GATE`, `VALIDATING`, `DONE`, `DEFERRED`, `PROVISIONAL`.

| Fase/Etapa | Estado | Evidência/Gate |
|---|---|---|
| 0.1 Modelo mental | DONE | LEANDRO confirmou compreensão |
| 0.2 Repositório canônico | DONE | `cloud-infrastructure` criado, privado e separado do MCF |
| 0.3 Preparação do primeiro acesso | DONE | painel Contabo e credenciais rotacionadas |
| 0.4 Primeiro acesso seguro | DONE | VNC/TigerVNC + SSH + fingerprint validada |
| 0.5 Inventário real | DONE | coleta técnica concluída, inventário consolidado e fechamento didático aprovado por LEANDRO em 2026-08-14 |
| PUC v1.0 | DONE | teste canônico em novo chat resultou em CONTINUIDADE COMPLETA |
| F1 Base/segurança inicial | PROVISIONAL | próxima fase; ainda não iniciada e sujeita aos HUMAN_GATEs aplicáveis |
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

## Fechamento da FASE 0

As etapas 0.1 a 0.5 estão `DONE`.

A Etapa 0.5 teve sua coleta técnica concluída, foi revisada de forma consolidada com LEANDRO e recebeu HUMAN_GATE explícito de fechamento em 2026-08-14.

**FASE 0 — ORIENTAÇÃO E INVENTÁRIO: CONCLUÍDA.**

A FASE 1 permanece `PROVISIONAL` e **não foi iniciada** por este fechamento. Antes de qualquer mudança operacional na VPS, o escopo imediato da FASE 1 deve ser apresentado e os HUMAN_GATEs pertinentes respeitados.
