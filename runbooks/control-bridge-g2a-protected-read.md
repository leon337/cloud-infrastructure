# Control Bridge G2-A Protected Read — Runbook

Este runbook cobre somente a instalação, validação e rollback do reader protegido G2-A.
Ele não concede autoridade de escrita e não altera grant, state ou revogações do G2-B.

## Sequência obrigatória

1. **read-only precheck** do NODE-01 e dos boundaries G2-B existentes.
2. Qualificar o SHA em **exact-head CI**.
3. Executar Ansible `--check` sem mutação no NODE-01.
4. Manter uma segunda sessão **recovery SSH** já autenticada.
5. Abrir HUMAN_GATE explícito de **LEANDRO** antes de qualquer apply live.
6. Executar **apply 1** do protected reader.
7. Executar **apply 2** e exigir `changed=0`, `unreachable=0`, `failed=0`.
8. Sem grant G2-B ativo, provar `workspace.stat=PASS` e `workspace.read=NOT_FOUND`.
9. Parar novamente antes de qualquer grant, **reissue** ou write G2-B.

## Cross-lifecycle posterior

Após novo gate humano separado para G2-B:

1. reissue temporário e bounded write seguro;
2. observar o mesmo `G2B-PILOT.txt` via G2-A protegido;
3. exigir hash G2-A igual ao `after.sha256` do G2-B;
4. executar rollback do write G2-B;
5. exigir G2-A `NOT_FOUND` novamente;
6. opcionalmente executar rollback do protected reader.

## Proibições durante implementação e validação

Até o gate live, é proibido:

- **package install** ou alteração de dependências no NODE-01;
- **permission relaxation** no workspace protegido;
- grant/reissue G2-B, write real ou rollback real;
- execução do apply/rollback G2-A contra NODE-01;
- alteração de sudoers, conta `mcf-workspace`, Docker socket ou rede live;
- promover ou mesclar a PR #56 como efeito desta missão.

Falha em identity, marker, hash, ownership/mode, CI, syntax ou check-mode encerra a tentativa em fail-closed. Nunca contornar uma falha de leitura elevando permissões, copiando o arquivo protegido ou usando shell root.
