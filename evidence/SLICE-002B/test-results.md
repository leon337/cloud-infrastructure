# SLICE-002B test results

Status: **CI/DISPOSABLE PASS — VPS NOT_EXECUTED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Pins/checksums/fingerprints/licenças documentados | `RECORDED` | decisão e inventário |
| Links Markdown locais | `PASS` | local não privilegiado |
| YAML estrito | `PASS_34` | local não privilegiado |
| State cross-check | `PASS_Q1_Q40_GATES_PRESERVED` | local não privilegiado |
| Secret/history policy | `PASS` | local não privilegiado |
| Diff whitespace | `PASS` | local não privilegiado |
| Unitários/negativos | `PASS_63` | local não privilegiado |
| Sintaxe shell | `PASS_6` | Bash/sh parse local |
| ShellCheck | `PASS_6_V0_11_0` | binário oficial verificado, extraído só em `/tmp` e removido |
| Ansible syntax | `PASS_6_CORE_2_21_3` | wheel oficial verificado, extraído só em `/tmp` e removido |
| GitHub Actions | `PASS_31996516019` | commit `fa66f1049bac5540a5b12219186a421cc39dcbc0` |
| VM descartável | `PASS` | check limpo, apply `changed=13`, reconcilições `changed=0`, sete recusas e rollback limpo |
| NODE-01 | `NOT_EXECUTED` | F1.1 DONE; check mode liberado, apply ainda bloqueado pelo review do preview |

O desired state nasceu no commit `7015c80759a797bcb141773b79cd9b95f6fbecf1` e
o delta final exercitado corresponde ao commit `fa66f1049bac5540a5b12219186a421cc39dcbc0`.
O run commit-bound `31996516019` passou. A primeira tentativa real posterior foi
recusada no controller antes de contato com o NODE-01, conforme seção abaixo.

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
ok=3 changed=0 failed=0`. O check mode privilegiado continua `NOT_EXECUTED` até
CI verde do commit da correção.

## Contrato do NODE-01

F1.1 já possui check/apply, idempotência, invariância e checkpoint reconciliados.
Depois do CI da correção, o NODE-01 pode executar somente check mode e deve provar
baseline/delta de listeners, interfaces, routes, sysctls,
UFW/rulesets, grupos, services e Workstation. Instalação sem workload não prova
Q20/Q34; o primeiro container permanece bloqueado por F1.2c.
