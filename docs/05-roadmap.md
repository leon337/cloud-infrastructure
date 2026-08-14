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
| F1 Base/segurança inicial | IN_PROGRESS | LEANDRO determinou continuidade para a próxima fase em 2026-08-14; primeira mudança ainda depende do HUMAN_GATE aplicável |
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

## Início controlado da FASE 1

LEANDRO determinou em 2026-08-14: **“VAMOS PARA A PROXIMA ETAPA”** e reforçou que a missão deve manter continuidade.

Interpretação operacional:

- a **FASE 1 — Base do sistema e segurança inicial** passa a `IN_PROGRESS`;
- isso autoriza a transição de fase e o planejamento do primeiro micro-passo;
- isso **não** autoriza automaticamente mudanças de segurança, upgrade em lote ou operações com risco de lockout;
- o primeiro micro-passo planejado é a **atualização inicial**, começando pela atualização dos índices APT antes de qualquer upgrade;
- antes da primeira mudança operacional relevante, objetivo, risco e recovery devem ser apresentados e o HUMAN_GATE aplicável deve ser obtido.
