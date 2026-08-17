# SLICE-002B test results

Status: **CI/DISPOSABLE + REAL CHECK MODE PASS — APPLY NOT_EXECUTED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Pins/checksums/fingerprints/licenças documentados | `RECORDED` | decisão e inventário |
| Links Markdown locais | `PASS` | local não privilegiado |
| YAML estrito | `PASS_34` | local não privilegiado |
| State cross-check | `PASS_Q1_Q40_GATES_PRESERVED` | local não privilegiado |
| Secret/history policy | `PASS` | local não privilegiado |
| Diff whitespace | `PASS` | local não privilegiado |
| Unitários/negativos | `PASS_66` | local não privilegiado |
| Sintaxe shell | `PASS_6` | Bash/sh parse local |
| ShellCheck | `PASS_6_V0_11_0` | binário oficial verificado, extraído só em `/tmp` e removido |
| Ansible syntax | `PASS_6_CORE_2_21_3` | wheel oficial verificado, extraído só em `/tmp` e removido |
| GitHub Actions | `PASS_32004951916` | commit `83166c37a7fa66abd442a04073c5f6d5a3df00c4` |
| VM descartável | `PASS` | check limpo, apply `changed=13`, reconcilições `changed=0`, sete recusas e rollback limpo |
| NODE-01 | `CHECK_MODE_PASS_NO_MUTATION` | apply ainda `NOT_EXECUTED`; primeiro workload bloqueado por F1.2c |

O desired state nasceu no commit `7015c80759a797bcb141773b79cd9b95f6fbecf1`.
A correção de canonicalização foi exercitada no commit
`83166c37a7fa66abd442a04073c5f6d5a3df00c4`; os runs commit-bound
`32004951916` (Docker) e `32004951955` (Foundation) passaram.

Os unitários do helper cobrem symlink, hardlink, path extra, open file por
processo, troca de inode após freeze e remoção bottom-up limitada às duas raízes
temporárias. A CI complementa esses unitários com o lifecycle privilegiado na
VM descartável; nenhum dos dois substitui prova no NODE-01.

## Contrato do teste descartável

A VM GitHub-hosted Ubuntu 24.04 deve recusar alvo não descartável e executar:

1. preflight/fixture sintética F1.1 exata;
2. check mode sem mutação;
3. install pinado com daemon impedido de autostart antes do config válido;
4. segunda reconciliação `changed=0`;
5. versões, config, socket `root:root 0600`, grupo vazio e negações;
6. zero containers, imagens, volumes, redes customizadas, build cache, swarm e
   portas; restart mantendo o runtime vazio;
7. ausência de bridge/interface/route/forwarding/listener/publicação inesperada;
8. recusas fail-closed por target/extra-var, collision, marker/prestate, grupo,
   objeto, processo, mount e manifesto divergente;
9. rollback vazio por manifesto pré-verificado, limitado a `find -xdev` nos dois
   paths literais, seguido de prova de ausência;
10. cleanup dos recursos nomeados da fixture.

Não é válido usar a Workstation, o NODE-01 ou um container privilegiado local
como substituto da VM descartável. A fixture não prova firewall do host real.

## Preflight real recusado e corrigido

Em `2026-08-17T07:11:25Z`, a primeira tentativa de check mode foi recusada no
controller antes de contato com o NODE-01: `localhost ok=2 changed=0 failed=1`.
A comparação usava o inventário canonicalizado contra um repository root ainda
contendo componentes `..`. Nenhuma autenticação sudo, tarefa remota ou mutação
ocorreu; o log sanitizado tem SHA-256
`c4e9debd48d7b7a1eae77bc2a6e2707e64c0447412c1de42305047bd1464f956`.

A remediação canonicaliza também o repository root com `realpath` antes da
comparação. A suíte local passou com 65 testes e seis syntax-checks; o preflight
DEV exato passou sem sudo com `localhost ok=9 changed=0 failed=0` e `node-01
ok=3 changed=0 failed=0`. A correção passou na CI Docker `32004951916` e na CI
Foundation `32004951955`.

## Preview real recusado por falso positivo do vigia APT

Em `2026-08-17T07:38:16Z`, o preview corrigido chegou aos prechecks remotos e
foi recusado com `changed=0`: `localhost ok=9 failed=0`; `node-01 ok=32
failed=1`. A regra antiga interpretou o processo permanente
`unattended-upgrade-shutdown --wait-for-signal` como uma transação de pacote.
Leitura posterior confirmou zero jobs APT e zero operação de pacote ativa; havia
somente um vigia ocioso. O log sanitizado possui SHA-256
`d778572c0958cbc75e6687feee961f3e14d75b950ce64a0032dfa950b8fce3df`.

A remediação substitui a expressão `pgrep` por classificador `/proc` que ignora
exclusivamente esse vigia ocioso e continua recusando `apt`, `apt-get`, `dpkg`,
`apt.systemd.daily` e `unattended-upgrade` reais. O mesmo guard é usado no apply
e rollback. Teste direto read-only no NODE-01 retornou `active=[]` e
`ignored_idle_shutdown_watchers=1`; a suíte local passou com 66 testes. Novo
preview continuava pendente até CI verde dessa correção.

## Preview real aprovado

O guard corrigido passou na CI Docker `32007871491` e Foundation `32007871496`,
commit `9e9ae2831c18d7887b2e147870e4f700e1ff1a8c`. Em
`2026-08-17T08:37:46Z`, o preview real terminou com `localhost ok=9 changed=0
failed=0` e `node-01 ok=43 changed=1 failed=0 unreachable=0`; o único changed é
a mensagem declarativa de plano do check mode. O log sanitizado tem SHA-256
`425ad91cc3d81b84fe7218bea9064a21efd2b5372c6ebed6e82280b1ffa0ef4b`.

A leitura pós-preview em `2026-08-17T08:38:33Z` confirmou Docker/containerd,
marker e lock ausentes; nenhum listener 2375/2376; serviços SSH/UFW/fail2ban,
XRDP/sesman/LightDM ativos; LXD service/socket inativos. O apply continua
`NOT_EXECUTED` e separado do preview.

## Contrato do NODE-01

F1.1 já possui check/apply, idempotência, invariância e checkpoint reconciliados.
Depois do CI da correção, o NODE-01 pode executar somente check mode e deve provar
baseline/delta de listeners, interfaces, routes, sysctls,
UFW/rulesets, grupos, services e Workstation. Instalação sem workload não prova
Q20/Q34; o primeiro container permanece bloqueado por F1.2c.
