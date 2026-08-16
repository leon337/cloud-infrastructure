# DEC-004 — XFCE e XRDP sobre túnel SSH

Status: **ACCEPTED — IMPLEMENTED AND VALIDATED**.

## Contexto

A Cloud Workstation precisava ser estável em Ubuntu 24.04, econômica em recursos e não ampliar desnecessariamente a superfície pública.

## Decisão

Usar XFCE + LightDM + XRDP/xorgxrdp. O XRDP escuta somente em `127.0.0.1:3389`; o cliente local acessa esse endpoint por túnel SSH autenticado com a chave de `ubuntu`.

## Consequências

- nenhuma porta RDP pública ou regra UFW adicional;
- clipboard e resolução dinâmica fornecidos pelo RDP;
- desconexão pode preservar sessão;
- VNC Contabo permanece console de recovery, não transporte primário do desktop;
- `AllowTcpForwarding yes` continua necessário no SSH;
- credencial do XRDP deve ser rotacionada depois do bootstrap.

## Validação

Desktop, Firefox, VS Code, terminal, Thunar, múltiplas janelas, clipboard bidirecional, 1100×700/1280×720, reconnect, persistência, logout/login e reboot passaram em 15/08/2026.
