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
| Mission Acceptance / recovery | `docs/40-mission-acceptance-recovery-report.md` |
| Requisitos consolidados | `docs/41-consolidated-requirements.md` |
| Arquitetura e threat model | `docs/42-target-architecture.md`, `docs/43-threat-model-and-autonomy-boundaries.md` |
| Blueprint e roadmap corrente | `docs/44-infrastructure-blueprint-v1.md`, `docs/45-revised-implementation-roadmap.md` |
| Technology Mapping | `docs/46-technology-mapping-v1.md`, `DEC-006` |
| Componentes/versões | `state/components.yaml` |
| Automação Foundations | `automation/ansible/`, `runbooks/platform-foundation.md` |
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
- Provider VNC `VALIDATED_HISTORICAL_2026_08_15_NOT_RECHECKABLE_FROM_GUEST`;
  Rescue historicamente confirmado; snapshots `NOT_CONFIGURED`, backups
  `NOT_CONTRACTED` e firewall Contabo `NOT_CONFIGURED` no último registro humano.
- Backup diário sanitizado de configurações ativo. Uma cópia off-host observada
  conferiu por SHA-256; o archive remoto mais recente não foi observado off-host.
  Houve extração histórica, não restore/rebuild funcional, e os archives atuais
  normalizam modes para `0640`. Backup amplo de dados continua pendente.
- XFCE/LightDM + XRDP somente em loopback; acesso gráfico pelo túnel SSH `127.0.0.1:13389 → VPS 127.0.0.1:3389`.
- Firefox DEB oficial Mozilla, VS Code, terminal XFCE e Thunar validados; clipboard bidirecional, resolução dinâmica, múltiplas janelas, reconnect, logout/login, persistência e reboot passaram.
- Recuperação read-only de 16/08/2026 19:46 UTC: ~6,2 GiB de 23,5 GiB
  usados e ~10,5 GiB de 289,6 GiB usados, com Firefox/VS Code/Codex e múltiplas
  sessões ativos; zero units falhas. Os números 2,2/7,5 GiB permanecem baseline
  histórica pós-desktop.

## Direção arquitetônica atual

A Platform Discovery definiu Q1–Q39 como arquitetura vinculante da plataforma privada de computação, desenvolvimento e execução de agentes. O estado completo das decisões está em `state/platform-discovery.yaml`.

Q40 = `D` por decisão explícita de LEANDRO:

- o Codex recebe a seleção tecnológica;
- o Codex recebe autorização para implementação incremental da plataforma DEV/lab;
- Q1–Q39 permanecem obrigatórias;
- produção externa continua sujeita a HUMAN_GATE;
- secrets continuam proibidos no Git;
- rotação de credenciais continua `DEFERRED_BY_HUMAN_DECISION`.

A missão vinculante é `docs/CODEX-EXECUTION-MISSION-001.md`. Mission Acceptance e
Q1–Q40 foram persistidos. O Technology Mapping é suficiente para F1.1, mas mantém
gaps posteriores explicitamente `CONDITIONAL`; a remediação candidata do primeiro
slice aguarda revalidação em VM GitHub descartável.

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

**SLICE_001_REVALIDATE_IN_DISPOSABLE_GITHUB_VM_AFTER_SAFETY_REMEDIATION**.

F1.1 possui artefatos canônicos, desired state Ansible, schema/manifests, policy de
secrets, CI e testes. A remediação candidata dos gaps de safety foi materializada no
worktree; suíte estática, unit tests, syntax-checks Ansible e ShellCheck nos quatro
scripts passaram localmente, ainda sem vínculo a commit; as contagens ficam no
test report. Os resultados
anteriores da fixture Ubuntu (`changed=7`, depois `changed=0` e cleanup) são
históricos. Nada foi aplicado à VPS real.

O próximo executor deve rodar na VM GitHub descartável o check mode, primeiro
apply, segunda reconciliação e rollback, incluindo as recusas de
provenance/TOCTOU, adoção e target guard. Só um checkpoint novo após esse rerun
pode liberar check mode/apply na VPS. Quando isso ocorrer, LEANDRO digita a senha
sudo diretamente no prompt interativo; ela nunca é enviada ao agente ou
registrada. Docker, Management Network, produção e rotação não fazem parte desse
apply.
