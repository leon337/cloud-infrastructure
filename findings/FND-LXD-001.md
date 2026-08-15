# FND-LXD-001 — Conta ubuntu possui acesso potencialmente root-equivalent via LXD

Status: **CONFIRMED — OPEN**. Severidade: **HIGH**.

## Evidência de 15/08/2026

- LXD snap `5.21.6` instalado;
- `ubuntu` pertence ao grupo `lxd`;
- socket `/var/snap/lxd/common/lxd/unix.socket` pertence a `root:lxd` e tem modo `660`;
- o socket permanece ativo, listening e habilitado;
- nenhuma instância LXD existia na consulta autorizada.

Pertencer ao grupo `lxd` normalmente concede capacidade equivalente a root por meio do daemon. Isso deve ser avaliado na política de menor privilégio antes de considerar a conta administrativa segura.

O daemon ficou `inactive/dead` após recuperação autorizada; o socket foi intencionalmente mantido ativo.

