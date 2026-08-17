# Runbook — runner autônomo temporário da Mission 001

Status: **PREPARED — HUMAN_GATE NOT_EXECUTED**

O bootstrap instala uma capability temporária, não sudo geral. O usuário
`ubuntu` recebe `NOPASSWD` somente para seis invocações exatas do runner:
`check`, `apply`, `test`, `reconcile`, `rollback` e `status`. Argumento extra,
operação diferente, shell e comando fornecido pelo chamador são recusados.

O runner usa uma cópia `root:root` em `/opt/codex-mission-001/repository` e não
executa código privilegiado diretamente de `/home/ubuntu`. `test` sempre roda
como `ubuntu`. `apply`/`rollback` só encontram entrypoints fixos, sem argumentos,
em `automation/mission-001/operations/` dentro do snapshot reconciliado.

`reconcile` lê apenas o par fixo
`/var/lib/codex-mission-001/inbox/repository.bundle{,.sig}`, exige assinatura
SSH válida da chave de controlador já registrada (namespace exclusivo da missão),
arquivo regular `ubuntu:ubuntu 0600`, link count 1, máximo 64 MiB, branch exata,
worktree limpa, produção bloqueada e rotação deferred. O snapshot instalado volta a ser
`root:root` e não gravável por grupo/outros.
O diretório-pai de estado é `root:ubuntu 0710`: `ubuntu` pode atravessar apenas
até sua caixa `0700`, mas não listar nem modificar o estado root-owned.

Cada execução registra timestamp, operação, Git SHA e resultado em
`/var/log/codex-mission-001/runner.log` e no journal. Um timer absoluto remove o
sudoers após 12 horas; o próprio runner também recusa e remove a regra ao
detectar prazo vencido.

## Ativação — HUMAN_GATE

Executar somente a partir da raiz da branch revisada:

```bash
git bundle create /tmp/codex-mission-001.bundle codex/mission-001-f1-2c-network-enforcement && rm -f /tmp/codex-mission-001.bundle.sig && ssh-keygen -Y sign -f "$HOME/.ssh/id_ed25519_contabo_vps_ubuntu_20260815.pub" -n codex-mission-001 /tmp/codex-mission-001.bundle && chmod 600 /tmp/codex-mission-001.bundle /tmp/codex-mission-001.bundle.sig && scp scripts/bootstrap_mission_001_autonomous_runner.sh /tmp/codex-mission-001.bundle /tmp/codex-mission-001.bundle.sig contabo-vps:/tmp/ && ssh -t contabo-vps 'chmod 600 /tmp/codex-mission-001.bundle /tmp/codex-mission-001.bundle.sig && sudo /bin/bash /tmp/bootstrap_mission_001_autonomous_runner.sh'
```

A senha sudo é digitada apenas no terminal remoto. Ela não entra em arquivo,
argumento, variável persistente, log, Git ou chat.

## Verificação após ativação

```bash
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner status'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner check'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner test'
```

## Revogação manual imediata

Este comando exige a senha humana e remove imediatamente a autorização:

```bash
ssh -t contabo-vps 'sudo /usr/local/libexec/codex-mission-001-revoke'
```

Depois da revogação, os artefatos root-owned e logs permanecem para auditoria,
mas nenhuma chamada NOPASSWD continua autorizada. SSH, UFW, XRDP, VNC/Rescue,
produção bloqueada e credential rotation deferred não são modificados pelo
bootstrap ou pela revogação.
