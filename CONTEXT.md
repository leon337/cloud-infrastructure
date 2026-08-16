# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Protocolo

PUC v1.0. As validações independentes existentes continuam históricas e vinculadas aos snapshots em que foram executadas. O estado pós-Cloud Workstation foi reconciliado e validado localmente; qualquer executor deve distinguir estado observado atual de baseline histórica.

## Regra zero

Antes de agir: verificar a `main` real, ler `CONTEXT.md`, `CHECKPOINT.md`, `state/current.yaml`, `state/platform-discovery.yaml`, o checkpoint Q40 e a missão Codex; distinguir fatos atuais de baselines históricas; não repetir coleta já suficiente; nunca pedir ou versionar secrets; respeitar HUMAN_GATEs aplicáveis.

Precedência: instrução atual de LEANDRO → infraestrutura verificável → GitHub `main` → CHECKPOINT/state → decisões → docs → findings/runbooks → history → chats.

## Mapa canônico

| Pergunta | Fonte |
|---|---|
| Estado exato de continuidade | `CHECKPOINT.md` |
| Estado operacional estruturado | `state/current.yaml` |
| Decisões Platform Discovery Q1–Q40 | `state/platform-discovery.yaml` |
| Q40 / delegação ao Codex | `docs/39-platform-discovery-checkpoint-028.md` |
| Missão autorizada ao Codex | `docs/CODEX-EXECUTION-MISSION-001.md` |
| Missão e arquitetura histórica | `docs/02-missao-e-escopo.md`, `docs/03-arquitetura-e-principios.md` |
| Plano e estado anterior | `docs/04-plano-mestre.md`, `docs/05-roadmap.md` |
| Infraestrutura observada | `docs/06-inventario.md` |
| Cloud Workstation | `docs/07-cloud-workstation.md`, `DEC-003`, `DEC-004` |
| Segurança e acesso | `docs/08-seguranca-e-governanca.md`, `runbooks/acesso-e-recuperacao.md` |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md`, `findings/FND-BACKUP-001.md` |
| Histórico | `history/` |
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
- Pós-desktop na validação final com sessão ativa: ~2,2 GiB de 23 GiB usados; ~7,5 GiB de 290 GiB usados; zero updates pendentes no snapshot documentado.

## Direção arquitetônica atual

A Platform Discovery definiu Q1–Q39 como arquitetura vinculante da plataforma privada de computação, desenvolvimento e execução de agentes. O estado completo das decisões está em `state/platform-discovery.yaml`.

Q40 = `D` por decisão explícita de LEANDRO:

- o Codex recebe a seleção tecnológica;
- o Codex recebe autorização para implementação incremental da plataforma DEV/lab;
- Q1–Q39 permanecem obrigatórias;
- produção externa continua sujeita a HUMAN_GATE;
- secrets continuam proibidos no Git;
- rotação de credenciais continua `DEFERRED_BY_HUMAN_DECISION`.

A missão vinculante é `docs/CODEX-EXECUTION-MISSION-001.md`.

## Guardrails centrais

- LEANDRO é autoridade humana final.
- MCF governa missões/autoridade; Capability Core autoriza; Workflow Engine executa duravelmente.
- Agentes operam por capacidades escopadas, não por autoridade administrativa irrestrita.
- Management Plane é privado.
- Cloud Workstation é cockpit humano opcional, não dependência da plataforma.
- DEV/staging podem ser automatizados dentro do escopo; promoção para produção exige HUMAN_GATE.
- Mudanças críticas exigem impacto/rollback/evidência.
- Nunca versionar passwords, passphrases, private SSH keys, tokens, API keys, 2FA, real connection strings ou provider credentials.

## Findings

Resolvidos: `FND-SSH-001`, `FND-SSH-002`, `FND-SSH-003`, `FND-LXD-001`, `FND-SUDO-001`, `FND-DOC-001`, `FND-AUDIT-001`.

`FND-BACKUP-001` está mitigado, mas aberto até existir backup amplo de dados e teste de reconstrução. `FND-CPU-001` e `FND-CLOUDINIT-001` continuam abertos para análise.

## Ponto exato

**CODEX_MISSION_ACCEPTANCE_AND_RECOVERY_REPORT**.

O próximo executor deve recuperar o estado real do GitHub e da VPS, confirmar branch/HEAD, divergências, riscos, Technology Mapping inicial e o primeiro incremento com rollback. A partir daí, a implementação autorizada por Q40-D deve avançar em slices pequenos, reversíveis, testados e checkpointados.
