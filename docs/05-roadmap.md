# 05 — Roadmap

| Fase/Etapa | Estado | Evidência |
|---|---|---|
| F0 Orientação e inventário | DONE | baseline e auditorias reconciliadas |
| F1 Acesso/recovery/segurança mínima | DONE | SSH, UFW, fail2ban, sudo, LXD, updates, backup e reboot validados; VNC preservado como validação histórica |
| F2 Cloud Workstation | DONE | XFCE/XRDP sobre túnel SSH e testes reais de produtividade |
| Recovery da missão Codex | DONE | GitHub/VPS/Q1–Q40 reconciliados em `40-mission-acceptance-recovery-report.md` |
| Foundations F1.1 | PARTIAL_CI_PASS_REAL_VPS_NOT_APPLIED | commit `edd2497d` aprovado no run `31972460567`, inclusive integração descartável; próximo passo somente check mode privilegiado humano na VPS |
| Plataforma DEV/lab Q40-D | AUTHORIZED_INCREMENTAL | roadmap detalhado em `45-revised-implementation-roadmap.md` |
| Rotação de credenciais | DEFERRED_BY_HUMAN_DECISION | fora da execução atual |
| Produção | HUMAN_GATE_REQUIRED | promoção não autorizada |

## Resultado técnico da F1

Somente TCP 22 está exposto; SSH aceita apenas `ubuntu`/publickey; UFW/fail2ban estão ativos; sudo exige senha; o caminho root-equivalent do LXD foi removido; VNC e backup proporcional foram validados; zero updates pendem após reboot.

## Resultado técnico da F2

XFCE, LightDM, XRDP em loopback, Firefox DEB, VS Code, terminal e Thunar estão funcionais. Clipboard nos dois sentidos, múltiplas janelas, resolução dinâmica, reconnect, persistência, logout/login e pós-reboot passaram.

Próximo passo: executar somente o check mode F1.1 na VPS com
`--ask-become-pass`, enquanto LEANDRO digita sudo diretamente. Inspecionar e
reconciliar o diff antes de qualquer apply. Apply, segunda reconciliação
`changed=0` e invariance checks reais continuam `NOT_EXECUTED`. A fonte detalhada
é `45-revised-implementation-roadmap.md`; as antigas F3–F10 são históricas.
