# 00 — Visão Geral

Este arquivo é um índice introdutório preservado por compatibilidade com o início da missão.

## Missão

Configurar, proteger, documentar e aprender a administrar a infraestrutura VPS, buscando segurança, funcionalidade, aprendizado e autonomia.

A descrição completa está em `02-missao-e-escopo.md`.

## Arquitetura

- Linux Mint físico como estação local;
- Contabo Cloud VPS 8 como infraestrutura remota;
- Ubuntu 24.04.4 LTS confirmado;
- modelo híbrido local/remoto;
- Cloud Workstation como próxima grande entrega após acesso/recovery/segurança mínima.

Detalhes: `03-arquitetura-e-principios.md` e `07-cloud-workstation.md`.

## Estado

FASE 1 — ACESSO ADMINISTRATIVO, RECOVERY E SEGURANÇA MÍNIMA — `IN_PROGRESS`.

FASE 0 e auditoria read-only de 15/08/2026 concluídas. O login atual de `ubuntu` foi validado por nova chave dedicada, exclusivamente via `publickey`; root/senha permanece temporariamente preservado. A revisão read-only de sudo/LXD confirmou dois caminhos equivalentes a root, sem explorá-los ou alterar configuração. O próximo micro-passo é a revisão read-only de recovery proporcional, mediante novo HUMAN_GATE. Cloud Workstation: `PRIORITY_PLANNED`.

Inventário datado: `06-inventario.md`.
Roadmap: `05-roadmap.md`.
Estado imediato: `../CHECKPOINT.md`.

## Continuidade

Qualquer nova IA deve começar por `../CONTEXT.md` e seguir o PUC v1.0. Este arquivo isolado não é suficiente para retomada.
