# 10 — Painel Contabo: recovery atual

Coleta read-only e validação de 15/08/2026:

| Recurso | Estado |
|---|---|
| Controle VNC | `VALIDATED_CURRENTLY` — habilitado/configurado e console `tty1` revalidado |
| Sistema de Resgate | `AVAILABLE_CONFIRMED` — disponível, não acionado |
| Snapshots | `NOT_CONFIGURED` — nenhum snapshot existente |
| Auto Backup | `NOT_CONTRACTED` |
| Firewall Contabo | `NOT_CONFIGURED` |
| Reinstalação/imagens | disponível, mas destrutivo e não validado como recovery |

VNC é console, não o desktop XRDP. Rescue muda temporariamente o boot e exigiria mutação para validação. Snapshot não substitui backup independente. Firewall do provedor é separado do UFW do Ubuntu.

Não clicar em confirmar, criar, restaurar, contratar, reiniciar, reinstalar, redefinir credenciais ou alterar firewall sem HUMAN_GATE próprio.
