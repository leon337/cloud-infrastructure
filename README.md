# Cloud Infrastructure

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Nova IA/agente? Comece por [`CONTEXT.md`](CONTEXT.md).

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO aprende a administrar, diagnosticar, recuperar e reconstruir o ambiente com mínima dependência de IA. O projeto é separado do MCF; a VPS poderá hospedar o framework e outros sistemas, mas a infraestrutura não pertence estruturalmente a ele.

## Continuidade

O repositório implementa o PUC v1.0. `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml` são as portas de entrada; `docs/`, `decisions/`, `findings/`, `history/`, `runbooks/`, `recovery/`, `assets/` e `governance/` preservam o contexto por tipo. Chats são temporários; o GitHub é a memória canônica após validação e publicação.

## Estado operacional — baseline reconciliada em 16/08/2026

- FASE 0, FASE 1 e FASE 2: **DONE**.
- `ubuntu`/publickey é o único login SSH permitido; root e autenticação SSH por senha estão desabilitados pela política efetiva.
- UFW está ativo com `deny incoming` e somente OpenSSH em TCP 22; fail2ban protege o SSH.
- sudo exige senha; não existe regra `NOPASSWD`; `ubuntu` saiu do grupo `lxd` e o LXD está desabilitado/inativo.
- VNC do provedor foi revalidado como console out-of-band; Rescue está disponível, snapshots não estão configurados, backup do provedor não está contratado e firewall do provedor não está configurado.
- backup diário sanitizado de configurações está ativo; a primeira cópia off-host teve hash validado e passou em extração de recuperação.
- zero atualizações APT pendentes após upgrade e reboot final.

## Cloud Workstation

A Cloud Workstation está **FUNCTIONAL_AND_VALIDATED**: XFCE + LightDM, XRDP restrito a `127.0.0.1:3389` e acesso somente por túnel SSH. Firefox oficial em pacote DEB, VS Code, terminal, Thunar, múltiplas janelas, clipboard bidirecional, resolução dinâmica, logout/login, desconexão/reconexão, persistência e reboot foram testados.

Recursos são fatos voláteis. A recuperação da missão observou 8 CPUs, 23 GiB de
RAM total, sem swap e raiz de 290 GiB; uso atual deve ser medido antes de cada
slice. Os números de ~2,2 GiB RAM/~7,5 GiB disco pertencem ao snapshot histórico
da validação final da Workstation.

## Implementação atual

Q1–Q39 definem a arquitetura vinculante e Q40-D autoriza o Codex a selecionar as
tecnologias e implementar incrementalmente a plataforma DEV/lab. A missão está em
[`docs/CODEX-EXECUTION-MISSION-001.md`](docs/CODEX-EXECUTION-MISSION-001.md) e o
roadmap corrente em
[`docs/45-revised-implementation-roadmap.md`](docs/45-revised-implementation-roadmap.md).

Próximo passo exato: concluir `SLICE-001 — Foundations F1.1`, atualmente com
desired state em validação e aplicação privilegiada pendente. Produção não está
autorizada e rotação de credenciais permanece `DEFERRED_BY_HUMAN_DECISION`.
