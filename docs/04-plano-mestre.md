# 04 — Plano Mestre

Este documento consolida o programa de capacidades.

## FASE 0 — Orientação e inventário — DONE

Arquitetura, primeiro acesso e inventário foram concluídos e revalidados.

## FASE 1 — Acesso administrativo, recovery e segurança mínima — DONE

- `ubuntu`/publickey e sessão independente: validados;
- VNC out-of-band: revalidado; Rescue: disponível;
- SSH endurecido; root e senha desabilitados no SSH;
- UFW ativo somente com OpenSSH e fail2ban ativo;
- sudo NOPASSWD removido e sudo autenticado validado;
- `ubuntu` removido de `lxd`; daemon/socket LXD desabilitados;
- updates aplicados e reboot validado;
- backup sanitizado diário, cópia off-host e extração de recuperação validados.

O backup amplo de dados e reconstrução integral permanecem evolução posterior, sem bloquear a segurança mínima já validada.

## FASE 2 — Cloud Workstation gráfica — DONE

Arquitetura: XFCE + LightDM + XRDP/xorgxrdp sobre túnel SSH. XRDP não é público.

Validações concluídas: login gráfico, navegador, VS Code, terminal, gerenciador de arquivos, projeto Git, múltiplas janelas, clipboard bidirecional, resolução dinâmica, desconexão/reconexão, persistência, logout/login, consumo de recursos e funcionamento após reboot.

## Próxima operação — rotação de credenciais

Rotacionar credenciais temporárias de bootstrap preservando `ubuntu`/publickey, VNC e acesso gráfico. Depois executar novo teste independente do PUC.

## Fases futuras — PROVISIONAL

3. desenvolvimento remoto e estabilização;
4. rede, armazenamento e manutenção;
5. backup/recovery amplo;
6. Docker/Compose;
7. observabilidade;
8. plataforma de serviços;
9. workloads;
10. autonomia e reconstrução.

Cloud Workstation foi antecipada por `DEC-003`; sua arquitetura foi formalizada por `DEC-004`.
