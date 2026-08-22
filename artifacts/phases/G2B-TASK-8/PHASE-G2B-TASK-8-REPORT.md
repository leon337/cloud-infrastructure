# G2-B Task 8 — Relatório de execução

## Resultado

`BLOCKED`

A Task 8 não recebeu PASS. A falha `apply_g2b exit=2` foi localizada ao estágio de aplicação do playbook, mas a causa técnica interna não pode ser determinada com segurança a partir da evidência preservada.

## Reconciliação viva

O HEAD observado de `codex/control-bridge-g2b` foi:

`fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`

O PR #11 permaneceu draft/aberto. A descrição do PR ainda descrevia a tentativa 3 como em execução, enquanto comentários posteriores registravam a terminação com status 2. A divergência foi registrada e o estado terminal posterior foi usado como evidência.

Branches `ops/g2b-status-output-20260822` e `ops/g2b-cancel-long-waiters-20260822` foram inspecionadas e estavam divergidas do lineage atual; não foram adotadas.

## Tentativa 3 reconstruída

Candidato exato:

`fbef3d407dbd9b7947b6c100a63d098eaebe2b6a`

Evidência terminal:

```text
TASK8_STATUS=2
G2B_DISPOSABLE_TEST_ABORTED stage=apply_g2b exit=2 cleanup=0
RESOURCE_UPDATE_PASS container=control-bridge-g2b-test-20260822115505-4579-6146 cpus=5 memory=8g
TASK8_ACCEPTANCE=FAIL_OR_NOT_TERMINAL
```

O monitor também registrou QEMU ativo, SSH do guest acessível, zero marcadores de aceite, HEAD exato e repositório limpo.

## Processo que retornou exit=2

No harness `scripts/test_control_bridge_g2b_vm.sh`, o estágio `apply_g2b` executa duas vezes:

```text
docker exec --workdir /workspace/cloud-infrastructure/automation/ansible <container> \
  /opt/foundation-test-venv/bin/ansible-playbook \
  --inventory inventory/test-container/hosts.yml \
  playbooks/apply-control-bridge-g2b.yml
```

As duas invocações usam `>/dev/null`.

Logo, está comprovado que uma das duas execuções do playbook terminou não-zero e provocou o abort do harness. A evidência preservada não distingue qual das duas invocações falhou nem qual task Ansible produziu o erro.

## Etapa anterior e etapa seguinte

Anterior comprovada:
- fixture construída e iniciada;
- systemd atingiu `running|degraded`;
- usuário `ubuntu` estava presente ou foi criado;
- watcher aplicou 5 CPUs / 8 GiB ao container.

Seguinte que não ocorreu:
- validações de identidade `mcf-workspace`, entrypoint e workspace;
- marcador `G2B_DISPOSABLE_IDENTITY_PASS`.

Nenhum dos 13 marcadores de aceite foi emitido.

## Stdout/stderr

`run-task8.sh` redirecionou stdout+stderr do harness para `/home/ubuntu/g2b-task8.log`, porém o próprio harness suprimiu stdout das duas chamadas `ansible-playbook` com `>/dev/null`.

O log preservado de 267 bytes contém apenas o aviso do builder Docker e o marcador final de abort. Não contém nome da task Ansible, `fatal`, `FAILED` ou payload diagnóstico suficiente para provar causa raiz.

## Hipóteses verificadas

- `/usr/local/libexec` ausente: era a causa comprovada da tentativa 2 e já estava corrigida no candidato `fbef3d4`; não foi reutilizada como explicação da tentativa 3.
- lock de instalação vazando entre as duas aplicações: descartado pela leitura do role; o bloco `always` remove `/run/lock/mcf-control-bridge-g2b-install`.
- CI commit-bound como fonte de diagnóstico: indisponível; run `32569958931` terminou `action_required` com zero jobs.

Nenhuma dessas verificações prova a causa da tentativa 3.

## Ambiente descartável e resíduos

Auditorias read-only já existentes:
- run `32577551012`;
- run `32577659953`;
- run `32577815107`.

Às 14:09 UTC de 2026-08-22, a QEMU `g2b-disposable-task8-vm3` ainda estava ativa e acessível por SSH local. O cleanup do container interno foi bem-sucedido (`cleanup=0`). O estado atual da QEMU após esse snapshot é `NÃO VERIFICADO`.

## Recuperação adicional

Foi preparada uma reprodução diagnóstica limitada à mesma boundary descartável preservada, com o mesmo `candidate.tar.gz`. A única instrumentação planejada era remover a supressão de stdout das duas chamadas Ansible e marcar separadamente as invocações 1 e 2. O trabalho longo permaneceria dentro da VM e o self-hosted runner seria usado somente em ações one-shot de início/status.

Nenhum resultado dessa reprodução ficou observável nas evidências disponíveis antes do encerramento. Portanto sua execução e seu resultado são `NOT_VERIFIED` e não são usados para inferir causa, correção ou PASS.

Os workflows temporários dessa recuperação foram removidos por commits normais. O diff final do PR #21 voltou a conter somente os 11 arquivos de evidência + PRF.

## Alterações desta frente

Foi preservada a branch isolada `team/g2b-task8-20260822` e o draft PR #21. Foram materializados evidência da tentativa 3, PRF, checkpoint, decisões, validação e mission trace.

Nenhum código funcional do G2-B foi alterado.

## Causa

`NÃO DETERMINADA COM SEGURANÇA`.

A perda de stdout do Ansible é uma causa comprovada de insuficiência de observabilidade, não a causa comprovada da falha funcional do playbook.

## Decisão

Aplicada a condição de parada definida por LEANDRO: não corrigir por hipótese, não declarar PASS sem lifecycle reproduzível e não iniciar Tasks 9/10.
