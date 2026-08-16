# 05 — Roadmap

| Fase/Etapa | Estado | Evidência |
|---|---|---|
| F0 Orientação e inventário | DONE | baseline e auditorias reconciliadas |
| F1 Acesso/recovery/segurança mínima | DONE | SSH, VNC, UFW, fail2ban, sudo, LXD, updates, backup e reboot validados |
| F2 Cloud Workstation | DONE | XFCE/XRDP sobre túnel SSH e testes reais de produtividade |
| Rotação de credenciais | NEXT | credenciais temporárias de bootstrap devem ser substituídas |
| F3 Desenvolvimento/estabilização | PROVISIONAL | após rotação |
| F4 Rede/armazenamento/manutenção | PROVISIONAL | gates próprios |
| F5 Backup/recovery amplo | PROVISIONAL | backup completo e reconstrução |
| F6 Docker/Compose | PROVISIONAL | depois da base gráfica segura |
| F7 Observabilidade | PROVISIONAL | gate futuro |
| F8 Plataforma de serviços | PROVISIONAL | gate futuro |
| F9 Workloads | PROVISIONAL | implantação gradual |
| F10 Autonomia/reconstrução | PROVISIONAL | maturidade final |

## Resultado técnico da F1

Somente TCP 22 está exposto; SSH aceita apenas `ubuntu`/publickey; UFW/fail2ban estão ativos; sudo exige senha; o caminho root-equivalent do LXD foi removido; VNC e backup proporcional foram validados; zero updates pendem após reboot.

## Resultado técnico da F2

XFCE, LightDM, XRDP em loopback, Firefox DEB, VS Code, terminal e Thunar estão funcionais. Clipboard nos dois sentidos, múltiplas janelas, resolução dinâmica, reconnect, persistência, logout/login e pós-reboot passaram.

Próximo passo: `CREDENTIAL_ROTATION`, seguido por validação independente do PUC.
