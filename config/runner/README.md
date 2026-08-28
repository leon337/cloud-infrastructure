# Runner isolation guard

Este diretório contém o guard de isolamento do self-hosted GitHub Actions runner do NODE-01.

## Objetivo

Retirar e impedir a recorrência do PoC legado `mcf-mission2-terminal.py`, que historicamente desabilitou o tracking normal do runner e sobreviveu entre jobs.

## Artefato

`cloud-infrastructure-runner-isolation-guard` encerra somente o daemon legado quando a identidade do processo corresponde ao caminho esperado e remove o socket/PID residuais. O script não mata processos genéricos.

Instalação live esperada:

```text
~/.local/libexec/cloud-infrastructure-runner-isolation-guard
```

## Hooks oficiais

O runner deve apontar os hooks de início e conclusão para o guard no arquivo `~/actions-runner/.env`:

```text
ACTIONS_RUNNER_HOOK_JOB_STARTED=/home/ubuntu/.local/libexec/cloud-infrastructure-runner-isolation-guard
ACTIONS_RUNNER_HOOK_JOB_COMPLETED=/home/ubuntu/.local/libexec/cloud-infrastructure-runner-isolation-guard
```

Alterar `.env` não ativa os hooks no processo já em execução. O GitHub Actions runner precisa de **restart** para recarregar essas variáveis. O restart deve ocorrer somente com runner idle e por um caminho autorizado; não contornar systemd, sudo ou HUMAN_GATE.

Estados permitidos:

- `CONFIGURED_NOT_ACTIVE`: arquivo `.env` e guard instalados, mas processo atual ainda não foi reiniciado/provado;
- `ACTIVE_VERIFIED`: novo Listener contém os nomes das duas variáveis e um job real mostra o guard no início/fim;
- `BLOCKED_PRIVILEGE`: restart recusado pela política do host; manter o runner ativo e não improvisar outro supervisor.

## Defesa enquanto o hook global não está ativo

Todo workflow self-hosted versionado no `main` deve chamar o guard explicitamente. `scripts/check_runner_isolation.py` rejeita:

1. qualquer referência a `RUNNER_TRACKING_ID` em workflows;
2. qualquer workflow self-hosted sem o token `cloud-infrastructure-runner-isolation-guard`.

A prova `runner-isolation-proof.yml` usa dois jobs para confirmar que um processo benigno iniciado com `nohup + setsid`, mas sem bypass de tracking, não atravessa a fronteira entre jobs.
