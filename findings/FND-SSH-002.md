# FND-SSH-002 — Exposição SSH com ataques automatizados e controles mínimos ausentes

Status: **CONFIRMED — OPEN**. Severidade: **HIGH**.

## Evidência de 15/08/2026

- SSH escutando publicamente em TCP 22 para IPv4 e IPv6;
- `PermitRootLogin yes` e `PasswordAuthentication yes` efetivos;
- UFW instalado, porém inativo, sem regras nftables/iptables observadas;
- fail2ban ausente;
- desde o boot: 24.447 falhas de senha, 1.676 tentativas com usuários inválidos, 42 eventos de máximo de autenticações e 3 eventos de limitação `MaxStartups`;
- nas 24 horas anteriores à coleta: 8.668 falhas de senha e 1.571 usuários inválidos.

Os números comprovam tráfego automatizado hostil, mas não comprovam invasão. Os logins aceitos observados não foram atribuídos independentemente a pessoas específicas.

## Correção necessária

Validar primeiro acesso administrativo por chave e recovery. Depois, mediante HUMAN_GATE próprio, definir defesa em profundidade: política de root/senha, firewall do host e provedor, limitação de tentativas e monitoramento.

