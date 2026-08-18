# 49 — CONTROL BRIDGE G1

Status: **HANDSHAKE_PASS — RUNNER_ACTIVE — PR_DRAFT**
Data: 2026-08-18
Missão: `CODEX-EXECUTION-MISSION-001` / continuidade MCF
Branch: `mcf/mission-001-control-bridge-g1`
Base: `codex/mission-001-f1-2c-network-enforcement`
PR: `#3` — OPEN / DRAFT / NOT MERGED

## Objetivo

Criar a ponte mínima para que ChatGPT/agentes possam solicitar execução na VPS por GitHub sem depender de LEANDRO como transportador manual de comandos, preservando o trabalho já implementado na Mission 001.

G1 não substitui o Capability Core, Node Agent, F5.0 runner isolation ou MCP final. Ele é o bootstrap operacional que permite construir e validar essas camadas com acesso remoto observável.
