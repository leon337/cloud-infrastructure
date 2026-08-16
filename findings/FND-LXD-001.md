# FND-LXD-001 — Conta ubuntu possui caminho de privilégio equivalente a root via LXD

Status: **RESOLVED em 15/08/2026**. Severidade histórica: **HIGH**.

## Evidência de 15/08/2026

- LXD snap `5.21.6` instalado;
- `ubuntu` pertence ao grupo `lxd`;
- socket `/var/snap/lxd/common/lxd/unix.socket` pertence a `root:lxd` e tem modo `660`;
- o socket permanece ativo, listening e habilitado;
- nenhuma instância LXD existia na consulta autorizada.

Pertencer ao grupo `lxd` normalmente concede capacidade equivalente a root por meio do daemon. Isso deve ser avaliado na política de menor privilégio antes de considerar a conta administrativa segura.

O daemon ficou `inactive/dead` após recuperação autorizada; o socket foi intencionalmente mantido ativo.

## Evidência adicional — Missão 4 em 15/08/2026

A auditoria read-only confirmou diretamente:

- `ubuntu` continuava no grupo `lxd`;
- o socket Unix existia, pertencia a `root:lxd` e tinha modo `660`;
- o processo autenticado como `ubuntu` podia escrever no socket;
- o daemon permaneceu `inactive/dead` antes e depois;
- a socket unit permaneceu `active/listening/enabled` antes e depois;
- os hashes dos listeners antes e depois foram idênticos;
- nenhum comando `lxc`, exploração ou chamada à API LXD foi executado.

Essa combinação confirma o **caminho de privilégio equivalente a root** disponível para `ubuntu` por meio do socket LXD, sem alegar que ele foi explorado. O finding permanece aberto e exige decisão explícita de menor privilégio; nenhuma correção automática foi autorizada.

## Resolução — 15/08/2026

Após confirmar novamente zero instâncias, `ubuntu` foi removido do grupo `lxd`. O snap LXD foi parado e desabilitado; daemon, socket de sistema e user-daemon permaneceram `inactive` após reboot. O grupo `lxd` ficou sem membros.

O caminho root-equivalent anteriormente comprovado não está mais disponível à conta `ubuntu`. Nenhuma instância foi removida.
