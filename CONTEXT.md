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
gaps posteriores explicitamente `CONDITIONAL`. O commit de implementação
`edd2497d657cc9bc35952f5dfc71090a18dade53` passou nos jobs estático e de
integração descartável do GitHub Actions run `31972460567`; isso não prova nenhuma
operação privilegiada na VPS real.

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

**SLICE_002C_NODE_01_NETWORK_SERVICES_DESIRED_STATE**.

F1.1 possui artefatos canônicos, desired state Ansible, schema/manifests, policy de
secrets, CI e testes. O run commit-bound `31972460567` passou com 37 testes,
ShellCheck, três syntax-checks Ansible, check mode sem mutação, apply descartável
`changed=7`, segunda reconciliação `changed=0`, quatro recusas fail-closed,
rollback e cleanup. Os resultados anteriores da fixture são somente históricos.
F1.1 foi concluído no NODE-01: check mode sem mutação, backup recente copiado
off-host com hash correspondente, apply `changed=7`, segunda reconciliação
`changed=0` e invariância final passaram. Conta técnica, namespaces, tmpfiles e
slices estão aplicados; SSH/UFW/fail2ban/XRDP/LightDM permaneceram operacionais,
LXD inativo, Docker ausente e nenhum listener de plataforma foi criado.

Em paralelo ao gate real F1.1, F1.2b Docker boundary concluiu desired state,
apply/rollback, pin APT, helper de árvore e harness no desired-state commit
`7015c80759a797bcb141773b79cd9b95f6fbecf1`. A validação local não privilegiada
passou com 63 testes, ShellCheck em seis scripts e syntax-check de seis playbooks.
O commit testado `fa66f1049bac5540a5b12219186a421cc39dcbc0` passou no GitHub
Actions run `31996516019`: check sem mutação, apply `changed=13`, reconciliação e
restart `changed=0`, sete recusas, rollback e cleanup. Depois dessa prova na VM
descartável, o check mode real F1.2b passou sem mutação em
`2026-08-17T08:37:46Z`. A leitura pós-preview confirmou o baseline e liberou o
lifecycle real controlado descrito abaixo.

F1.2b foi concluído depois do preview: backup fresco copiado off-host, apply
`changed=13`, idempotência `changed=0`, restart, nova reconciliação `changed=0` e
invariância final passaram. O runtime permanece vazio e root-only.

O menor avanço independente seguinte criou o contrato repo-only F1.2c em
`platform/network/f1-2c-contract.yaml`, commit
`b4cbeb066605754d538ff5abe2d294f0759d6f59`. Quatro testes específicos e a
suíte integrada de 60 testes/34 YAML passaram. O contrato fixa deny-by-default,
IPv4/IPv6, zonas protegidas, grants, perfis e evidência requerida, mas mantém
DEC-008 aceita o mecanismo `DOCKER-USER`/bridges internas/egress proxy-only. A
base fail-closed IPv4/IPv6 passou no run `32073151044` para `d1da488` e foi
aplicada no NODE-01: `changed=1`, reconciliação `changed=0`, check e 98 testes
passaram. O runtime permanece vazio.

O lifecycle declarativo de redes internas vazias passou no commit `1c0d698`,
run `32075348131`: três scopes foram criados, a reconciliação retornou zero,
uma rede não gerenciada foi recusada e o rollback removeu as três. A prova foi
somente descartável; o NODE-01 permaneceu sem bridge, rede ou workload.

O run `32100527131`, commit `8d5963b`, separou corretamente a prova do runtime
vazio da matriz de serviços e aprovou ambas. DNS por escopo, proxy allowlist,
deny de egress direto, grant explícito, revogação, falha de dependência e cleanup
passaram em VM descartável; o boundary IPv6 permaneceu deny-by-default sem
endereçamento IPv6 de workload. Nada desse incremento foi aplicado no NODE-01.

O próximo passo é converter os serviços validados em desired state bounded para
o NODE-01, com precheck/rollback/evidência. O primeiro workload continua
bloqueado; Management Network, produção e rotação não fazem parte desse passo.
