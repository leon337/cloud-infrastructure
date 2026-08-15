# Findings

Achados técnicos persistentes.

Cada finding deve registrar sintoma, evidências, hipóteses, testes válidos/inválidos, mitigação, correção, validação e status.

- `FND-SSH-001.md` — sessão SSH ociosa; resolvido com keepalive permanente validado.
- `FND-SSH-002.md` — ataques automatizados contra SSH e controles mínimos ausentes; aberto, high.
- `FND-SSH-003.md` — login atual da conta `ubuntu` não validado; aberto, high.
- `FND-LXD-001.md` — grupo/socket LXD concede privilégio potencialmente equivalente a root; aberto, high.
- `FND-DOC-001.md` — deriva documental encontrada e reconciliada em 15/08/2026.
- `FND-CPU-001.md` — relato de Spec rstack overflow; análise pendente.
- `FND-CLOUDINIT-001.md` — cloud-init em `degraded done`; aberto.
- `FND-BACKUP-001.md` — backup independente e recovery não validados; aberto, high.
- `FND-AUDIT-001.md` — ativação involuntária do LXD durante auditoria; recuperado e resolvido.
