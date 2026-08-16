# Findings

## Resolvidos

- `FND-SSH-001` — keepalive do cliente validado.
- `FND-SSH-002` — SSH endurecido, UFW e fail2ban ativos.
- `FND-SSH-003` — login `ubuntu`/publickey validado.
- `FND-LXD-001` — associação de `ubuntu` removida e LXD desabilitado.
- `FND-SUDO-001` — NOPASSWD removido; sudo autenticado.
- `FND-DOC-001` — deriva documental reconciliada.
- `FND-AUDIT-001` — ativação acidental do LXD recuperada.

## Mitigado e aberto

- `FND-BACKUP-001` — backup proporcional e recovery mínimo validados; backup amplo/reconstrução pendentes.

## A investigar

- `FND-CPU-001` — linha de vulnerabilidade de CPU.
- `FND-CLOUDINIT-001` — cloud-init `degraded done`.
