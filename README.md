# Cloud Infrastructure

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Nova IA/agente? Comece por [`CONTEXT.md`](CONTEXT.md).

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO aprende a administrar, diagnosticar, recuperar e reconstruir o ambiente com mínima dependência de IA. O projeto é separado do MCF; a VPS poderá hospedar o framework e outros sistemas, mas a infraestrutura não pertence estruturalmente a ele.

## Continuidade

O repositório implementa o PUC v1.0. `CONTEXT.md`, `CHECKPOINT.md` e `state/current.yaml` são as portas de entrada; `docs/`, `decisions/`, `findings/`, `history/`, `runbooks/`, `recovery/`, `assets/` e `governance/` preservam o contexto por tipo. Chats são temporários; o GitHub é a memória canônica após validação e publicação.

## Regra operacional — acesso à VPS e self-hosted runner

> **IMPORTANTE PARA QUALQUER IA/AGENTE:** o self-hosted runner da VPS/NODE-01 é um transporte curto e serializado. Ele **não deve ser usado como mecanismo de espera, monitoramento contínuo ou polling prolongado**.

Em 22/08/2026 foi identificado um incidente operacional causado por workflows temporários de observação que mantinham o único self-hosted runner ocupado com `sleep`, loops de polling e timeouts longos (10/15/60/75 minutos). A fila resultante criou uma latência artificial próxima de 25 minutos para novas operações e deu a falsa impressão de que o acesso à VPS ou o ChatGPT possuíam esse limite específico.

Regras vinculantes para trabalhos futuros na VPS:

- **NÃO** criar jobs self-hosted que fiquem aguardando um processo terminar por vários minutos.
- **NÃO** usar `sleep`, loops de polling ou `timeout-minutes` elevado como mecanismo de acompanhamento de lifecycle.
- **NÃO** ocupar o único runner apenas para observar logs ou estado.
- Operações longas devem ser disparadas de forma **desacoplada na própria VPS**, persistindo PID/status/logs/checkpoints fora da sessão de controle.
- O MESTRE/ChatGPT ou qualquer outro agente deve consultar o estado por **probes curtos e independentes**, retornar imediatamente e repetir uma nova consulta somente quando necessário.
- Workflows temporários de transporte/observação devem ser mínimos, fail-closed e removidos após o uso.
- Antes de usar o self-hosted runner, verificar se não há job antigo `queued`/`in_progress` ocupando ou bloqueando a fila.
- Nunca interpretar uma fila causada pelo runner como limitação intrínseca da VPS ou como evidência de falha do processo remoto.

A correção aplicada no incidente foi remover/reverter os workflows de espera longa da branch operacional. Esta regra evita recriar o gargalo; ela **não altera nem promete remover limites próprios da plataforma ChatGPT ou de ferramentas externas**.

## Estado operacional — 18/08/2026

- FASE 0, FASE 1 e FASE 2: **DONE**.
- Cloud Workstation: **FUNCTIONAL_AND_VALIDATED**.
- `ubuntu`/publickey é o único login SSH permitido; root e autenticação SSH por senha estão desabilitados pela política efetiva.
- UFW está ativo com `deny incoming` e somente OpenSSH em TCP 22; fail2ban protege o SSH.
- sudo exige senha; não existe regra `NOPASSWD`; `ubuntu` saiu do grupo `lxd` e o LXD está desabilitado/inativo.
- VNC do provedor foi revalidado como console out-of-band; Rescue está disponível, snapshots não estão configurados, backup do provedor não está contratado e firewall do provedor não está configurado.
- backup diário sanitizado de configurações está ativo; a primeira cópia off-host teve hash validado e passou em extração de recuperação.
- zero atualizações APT pendentes no último snapshot documentado após upgrade e reboot final.
- `CREDENTIAL_ROTATION`: **DEFERRED_BY_HUMAN_DECISION**.
- Platform Discovery Q1–Q40 concluída; Q1–Q39 permanecem requisitos arquitetônicos vinculantes.
- Q40-D autorizou seleção tecnológica e implementação incremental da plataforma privada DEV/lab dentro dos guardrails documentados.
- Promoção para produção externa continua bloqueada até HUMAN_GATE de LEANDRO.

## Cloud Workstation

A Cloud Workstation está **FUNCTIONAL_AND_VALIDATED**: XFCE + LightDM, XRDP restrito a `127.0.0.1:3389` e acesso somente por túnel SSH. Firefox oficial em pacote DEB, VS Code, terminal, Thunar, múltiplas janelas, clipboard bidirecional, resolução dinâmica, logout/login, desconexão/reconexão, persistência e reboot foram testados.

Recursos na validação final com sessão gráfica ativa: 8 CPUs, 23 GiB de RAM total (~2,2 GiB usada), raiz de 290 GiB (~7,5 GiB usada).

## Execução atual

A delegação Q40-D ao Codex continua registrada como decisão arquitetônica e autorização histórica. Em 18/08/2026, LEANDRO informou indisponibilidade do Codex e assumiu temporariamente a execução manual na VPS, sob orquestração técnica do MESTRE.

Essa contingência muda o executor, não reabre Q1–Q40 e não amplia o escopo autorizado.

## Próximo passo exato

Executar o **MISSION ACCEPTANCE + RECOVERY REPORT** previsto em `docs/CODEX-EXECUTION-MISSION-001.md`, agora em modo manual LEANDRO + MESTRE: recuperar GitHub e estado real da VPS, verificar drift, riscos, Technology Mapping inicial e primeiro incremento com rollback antes de qualquer implementação ampla.

Nunca versionar passwords, passphrases, chaves privadas, tokens, API keys, 2FA, connection strings reais ou credenciais do provedor.
