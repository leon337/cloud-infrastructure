# FND-AUDIT-001 — Consulta lxc ativou o daemon durante auditoria

Status: **RESOLVED — RECOVERY VALIDATED**.

Em 15/08/2026, `lxc version`, embora usado com intenção de leitura, acionou `snap.lxd.daemon.service` pelo socket systemd.

Com HUMAN_GATE explícito, confirmou-se primeiro que havia 0 instâncias totais e 0 em execução. O serviço foi então parado. Validação final:

- daemon `inactive/dead`;
- processo LXD ausente;
- socket `active/listening` e habilitado;
- listeners de rede inalterados.

Lição: clientes ligados a socket activation não devem ser classificados como estritamente read-only quanto ao estado operacional do daemon.

