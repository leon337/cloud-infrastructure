# Runbook — GitHub Self-Hosted Runner Bootstrap para NODE-01

Status: EXECUTED — HANDSHAKE PASS
Missão: CODEX-EXECUTION-MISSION-001 / G1 Control Bridge
Branch: mcf/mission-001-control-bridge-g1
Data de execução: 2026-08-18

## Objetivo

Registrar um GitHub Actions self-hosted runner no NODE-01 apenas para o bootstrap do Control Bridge G1. O runner é o transporte GitHub -> VPS para o primeiro handshake remoto read-only.

Este runbook não autoriza merge, produção, rotação de credenciais, Docker socket, sudo irrestrito ou operações mutantes na VPS.
