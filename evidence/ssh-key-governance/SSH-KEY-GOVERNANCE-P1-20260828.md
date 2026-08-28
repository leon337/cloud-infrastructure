# SSH-KEY-GOVERNANCE-P1 — evidência sanitizada

Data: 2026-08-28

## Escopo

Avaliar a chave administrativa irrestrita `dsh-tunnel-leo-N43SM-to-vmi3506102`, determinar provenance/necessidade, comprovar fallback independente e parar em HUMAN_GATE antes de qualquer alteração em `authorized_keys`.

## Inventário live

- `authorized_keys`: 4 entradas, modo `0600`, owner `ubuntu:ubuntu`;
- `dsh-tunnel...`: ED25519, fingerprint `SHA256:ugwguEmoX3yxLEc2YC7+8jLMog7ZeEsFNVfOaoZEkvA`, sem options/restrictions;
- `mcf-ox-display10-20260825`: restrita a loopback + forced command;
- duas chaves administrativas históricas adicionais permanecem presentes.

Nenhum blob de chave privada, passphrase, token ou valor secreto foi coletado/versionado.

## Provenance

- `~/.bash_history` de `ubuntu` contém o comando idempotente que criou/atualizou `authorized_keys` e adicionou a entrada com comment `dsh-tunnel-leo-N43SM-to-vmi3506102`; o blob público foi redigido durante a coleta;
- auth log/journal registra múltiplas autenticações aceitas com o fingerprint da `dsh` em 2026-08-25;
- o endereço de origem observado nesses acessos coincide com o caminho de rede usado pelo fallback administrativo atual; o endereço não é persistido aqui por minimização de dados.

**Classificação:** `CONFIRMED_UBUNTU_HISTORY_AND_AUTH_LOG`.

## Necessidade atual

Na coleta de 2026-08-28:

- nenhum processo SSH tunnel/forward associado foi observado no notebook ou NODE-01;
- nenhuma unit de usuário relacionada a `dsh-tunnel` foi encontrada;
- a chave não estava carregada no agente SSH atual;
- nenhum arquivo `.pub` local atual corresponde ao fingerprint da `dsh`;
- nenhuma referência à comment da chave foi encontrada na configuração SSH atual nem no repositório canônico.

Esses probes sustentavam apenas `dependency_not_observed_by_automated_checks`; eles não eram suficientes para concluir ausência de dependência no fluxo humano. Em 28/08/2026, LEANDRO corrigiu explicitamente esse ponto: a chave é usada para abrir/acessar a VPS pelo notebook. A classificação canônica passa a ser `current_dependency=CONFIRMED_BY_LEANDRO_USER_WORKFLOW`.

## Fallback independente

Uma conexão read-only `BatchMode=yes` + `StrictHostKeyChecking=yes` autenticou com uma chave administrativa distinta, fingerprint `SHA256:/p5jX65s2WyxkD3xooTozV09DSYAmKIAgZKk3Veb1Hg`, e executou um marcador inofensivo com sucesso. A `dsh` não estava no agente durante o teste.

**Classificação:** `PASS_INDEPENDENT_KEY`.

## Boundary e decisão

`authorized_keys` **não foi alterado**. A declaração explícita de LEANDRO confirma que a `dsh-tunnel...` é necessária no fluxo atual notebook→VPS. Portanto a decisão operacional é `KEEP_REQUIRED_FOR_CURRENT_USER_WORKFLOW`. O fallback independente permanece contingência, não justificativa para remoção. Qualquer hardening futuro exige prova de preservação do acesso interativo atual.

Estado: `CURRENT_USER_WORKFLOW_DEPENDENCY_CONFIRMED`.
Próximo passo: `F1_2C_NODE01_ROLLOUT_HUMAN_GATE`.
