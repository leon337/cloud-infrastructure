# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Protocolo

PUC v1.0. As validações independentes existentes continuam históricas e vinculadas aos snapshots em que foram executadas. O estado pós-Cloud Workstation foi reconciliado e validado localmente, mas ainda não passou por novo teste independente em outro chat.

## Regra zero

Antes de agir: verificar a `main` real, ler `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml`, distinguir fatos atuais de baselines históricas, não repetir coleta suficiente, nunca pedir ou versionar secrets e respeitar o HUMAN_GATE aplicável.

Precedência: instrução atual de LEANDRO → infraestrutura verificável → GitHub `main` → CHECKPOINT/state → decisões → docs → findings/runbooks → history → chats.

## Mapa canônico

| Pergunta | Fonte |
|---|---|
| Missão e arquitetura histórica | `docs/02-missao-e-escopo.md`, `docs/03-arquitetura-e-principios.md` |
| Plano e estado anterior | `docs/04-plano-mestre.md`, `docs/05-roadmap.md` |
| Platform Discovery atual | `docs/12-platform-discovery-checkpoint-001.md` |
| Estado corrente | `CHECKPOINT.md`, `state/current.yaml` |
| Infraestrutura observada | `docs/06-inventario.md` |
| Cloud Workstation | `docs/07-cloud-workstation.md`, `DEC-003`, `DEC-004` |
| Segurança e acesso | `docs/08-seguranca-e-governanca.md`, `runbooks/acesso-e-recuperacao.md` |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md`, `findings/FND-BACKUP-001.md` |
| Histórico | `history/SESSION-2026-08-15-012.md` e registros anteriores |
| Evidências visuais | `assets/README.md` |

## Estado operacional atual

- Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, KVM/QEMU, 8 CPUs, ~23 GiB RAM, sem swap.
- F0 `DONE`; F1 `DONE`; F2 Cloud Workstation `DONE` e `FUNCTIONAL_AND_VALIDATED`.
- SSH público somente em TCP 22. Login permitido: `ubuntu` por chave dedicada; `PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`.
- UFW ativo, default deny incoming, somente OpenSSH; fail2ban/sshd ativo.
- sudo autenticado validado; NOPASSWD removido. `ubuntu` não pertence mais a `lxd`; daemon e socket LXD estão desabilitados/inativos.
- Provider VNC `VALIDATED_CURRENTLY`; Rescue `AVAILABLE_CONFIRMED`; snapshots `NOT_CONFIGURED`; backups `NOT_CONTRACTED`; firewall Contabo `NOT_CONFIGURED`.
- Backup diário sanitizado de configurações ativo, cópia off-host validada por SHA-256 e extração de recuperação testada. Backup amplo de dados continua pendente.
- XFCE/LightDM + XRDP somente em loopback; acesso gráfico pelo túnel SSH `127.0.0.1:13389 → VPS 127.0.0.1:3389`.
- Firefox DEB oficial Mozilla, VS Code, terminal XFCE e Thunar validados; clipboard bidirecional, resolução dinâmica, múltiplas janelas, reconnect, logout/login, persistência e reboot passaram.
- Pós-desktop na validação final com sessão ativa: ~2,2 GiB de 23 GiB usados; ~7,5 GiB de 290 GiB usados; zero updates pendentes.

## Nova direção arquitetônica — Platform Discovery

LEANDRO decidiu adiar a rotação de credenciais e interromper a progressão automática pelas antigas F3–F10. Essas fases permanecem `PROVISIONAL` até a nova Discovery consolidar a arquitetura de plataforma.

O objetivo atual é projetar uma **plataforma privada de computação, desenvolvimento e execução de agentes**, priorizando laboratório DEV autônomo e portabilidade posterior para produção externa.

Decisões Q1–Q7 já registradas:

- Q1 `C`: plataforma privada de computação, desenvolvimento e execução de agentes;
- Q2 `C`: infraestrutura própria como padrão de laboratório DEV, externa quando vantajosa/produção;
- Q3 `C`: isolamento por projeto + sandboxes temporários por agente/missão;
- Q4 `C`: autonomia dentro do escopo autorizado, HUMAN_GATE fora dele;
- Q5 `D`: Capability Core + API + MCP + CLI progressivamente;
- Q6 `C`: catálogo completo de capacidades de laboratório, implementado progressivamente;
- Q7 `C`: compute descartável + estado importante explicitamente persistente.

Fonte: `docs/12-platform-discovery-checkpoint-001.md`.

Nenhuma implementação pesada da nova plataforma está autorizada antes da conclusão da Discovery e do HUMAN_GATE correspondente.

## Findings

Resolvidos: `FND-SSH-001`, `FND-SSH-002`, `FND-SSH-003`, `FND-LXD-001`, `FND-SUDO-001`, `FND-DOC-001`, `FND-AUDIT-001`.

`FND-BACKUP-001` está mitigado, mas aberto até existir backup amplo de dados e teste de reconstrução. `FND-CPU-001` e `FND-CLOUDINIT-001` continuam abertos para análise.

## Ponto exato

**DISCOVERY_Q8**.

Continuar a Platform Discovery. Não executar CREDENTIAL_ROTATION agora. Não iniciar implementação pesada da plataforma nem retomar automaticamente F3–F10 antes de requisitos consolidados, arquitetura-alvo, threat model/limites de autonomia, Infrastructure Blueprint v1, roadmap revisado e aprovação explícita de LEANDRO.
