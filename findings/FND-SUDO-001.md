# FND-SUDO-001 — Conta ubuntu possui elevação direta a root sem senha

Status: **CONFIRMED — OPEN**. Severidade: **HIGH**.

## Evidência — Missão 4 em 15/08/2026

- `sudo -n -l` terminou com exit code `0`;
- a política efetiva listou `(ALL : ALL) ALL` e `(ALL) NOPASSWD: ALL` para `ubuntu`;
- a regra ativa observada foi `ubuntu ALL=(ALL) NOPASSWD:ALL`;
- `sudo -n -u root id -u` confirmou UID `0` sem solicitar senha;
- `sudo -n -u root id -un` confirmou usuário `root` sem solicitar senha;
- a origem observada foi `/etc/sudoers.d/90-cloud-init-users`, proprietário `root:root`, modo `440`;
- o mesmo arquivo também continha `root ALL=(ALL) NOPASSWD:ALL`;
- `visudo -cf /etc/sudoers` terminou com resultado `PASS`.

## Avaliação

`ubuntu` possui caminho direto e não interativo para autoridade root. Isso pode ser aceitável temporariamente durante bootstrap ou recovery, mas é incompatível com o princípio de menor privilégio em um estado endurecido.

Este finding não autoriza alterar sudo, remover a regra ou mudar acessos. Qualquer mitigação exige análise de recovery, desenho da política administrativa e HUMAN_GATE próprio.
