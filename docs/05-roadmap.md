# 05 — Roadmap

Estados: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `HUMAN_GATE`, `VALIDATING`, `DONE`, `DEFERRED`, `PROVISIONAL`.

| Fase/Etapa | Estado | Evidência/Gate |
|---|---|---|
| 0.1 Modelo mental | DONE | LEANDRO confirmou compreensão |
| 0.2 Repositório canônico | DONE | `cloud-infrastructure` criado, privado e separado do MCF |
| 0.3 Preparação do primeiro acesso | DONE | painel Contabo e credenciais rotacionadas |
| 0.4 Primeiro acesso seguro | DONE | VNC/TigerVNC + SSH + fingerprint validada |
| 0.5 Inventário real | IN_PROGRESS | SO/kernel/CPU/RAM feitos; disco/rede/mounts/uptime pendentes |
| PUC v1.0 | VALIDATING | estrutura implantada; exige teste de novo chat |
| F1 Base/segurança inicial | PROVISIONAL | após inventário completo |
| F2 Rede/firewall | PROVISIONAL | após acesso alternativo e políticas definidas |
| F3 Armazenamento | PROVISIONAL | decisão somente após inventário |
| F4 Manutenção/updates | PROVISIONAL | gate futuro |
| F5 Backup/recovery | PROVISIONAL | gate futuro |
| F6 Docker/Compose | PROVISIONAL | somente após base segura e aula |
| F7 Desenvolvimento remoto | PROVISIONAL | gate futuro |
| F8 Observabilidade | PROVISIONAL | gate futuro |
| F9 Plataforma de serviços | PROVISIONAL | gate futuro |
| F10 Cloud Workstation | DEFERRED | avaliar depois da base segura |
| F11 Workloads | PROVISIONAL | implantação gradual |
| F12 Autonomia/reconstrução | PROVISIONAL | maturidade final |

## Bloqueio atual

Não retomar operação na VPS até o PUC v1.0 passar em teste de continuidade canônica.