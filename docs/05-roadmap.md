# 05 — Roadmap

Estados: `NOT_STARTED`, `IN_PROGRESS`, `BLOCKED`, `HUMAN_GATE`, `VALIDATING`, `DONE`, `PRIORITY_PLANNED`, `PROVISIONAL`.

| Fase/Etapa | Estado | Evidência/Gate |
|---|---|---|
| 0.1 Modelo mental | DONE | LEANDRO confirmou compreensão |
| 0.2 Repositório canônico | DONE | repositório separado do MCF |
| 0.3 Preparação do primeiro acesso | DONE | painel e credenciais iniciais tratados |
| 0.4 Primeiro acesso seguro | DONE | VNC/TigerVNC, SSH e fingerprint validados historicamente |
| 0.5 Inventário real | DONE | baseline de 14/08 e revalidação de 15/08 documentadas |
| PUC v1.0 | DONE | estado reconciliado de 15/08 publicado em `be52e369...` e validado com CONTINUIDADE COMPLETA; protocolo permanece aplicável a novos estados |
| Auditoria Fase B | DONE | fotografia read-only de 15/08 aprovada para reconciliação |
| F1 Acesso/recovery/segurança mínima | IN_PROGRESS | `ubuntu`/publickey validado; sudo/LXD, recovery e segurança mínima ainda pendentes |
| F2 Cloud Workstation | PRIORITY_PLANNED | próxima grande entrega após pré-requisitos da F1; conclusão exige HUMAN_GATE de produtividade |
| F3 Desenvolvimento/estabilização | PROVISIONAL | após implantação gráfica funcional |
| F4 Rede/armazenamento/manutenção | PROVISIONAL | gates próprios |
| F5 Backup/recovery amplo | PROVISIONAL | gate futuro |
| F6 Docker/Compose | PROVISIONAL | depois da entrega gráfica e base segura |
| F7 Observabilidade | PROVISIONAL | gate futuro |
| F8 Plataforma de serviços | PROVISIONAL | gate futuro |
| F9 Workloads | PROVISIONAL | implantação gradual |
| F10 Autonomia/reconstrução | PROVISIONAL | maturidade final |

## Estado da FASE 1

- baseline APT feita em 14/08; cinco updates Krb5 continuaram adiados por phasing em 15/08;
- `ubuntu` possui login atual validado exclusivamente por nova chave `publickey`; a chave anterior e root/senha foram preservados;
- UFW está inativo e o SSH público recebe alto volume de tentativas automatizadas;
- LXD oferece risco de privilégio equivalente a root para `ubuntu`;
- backup independente e recursos de recovery do provedor não foram validados.

Próximo micro-passo recomendado: revisão read-only de sudo e do privilégio equivalente a root via LXD, após novo HUMAN_GATE. Depois, validar recovery proporcional e segurança mínima de SSH/firewall sem lockout. Nenhuma política root/senha/firewall deve mudar antes desses controles.

## Mudança de prioridade

Por `DEC-003`, a Cloud Workstation deixou de estar `DEFERRED`. Ela antecede Docker, observabilidade e a plataforma ampla de serviços.
