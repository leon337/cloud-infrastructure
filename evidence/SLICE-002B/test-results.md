# SLICE-002B test results

Status: **LOCAL STATIC PASS — CI PENDING — VPS NOT_EXECUTED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Pins/checksums/fingerprints/licenças documentados | `RECORDED` | decisão e inventário |
| Links Markdown locais | `PASS` | local não privilegiado |
| YAML estrito | `PASS_32` | local não privilegiado |
| State cross-check | `PASS_Q1_Q40_GATES_PRESERVED` | local não privilegiado |
| Secret/history policy | `PASS` | local não privilegiado |
| Diff whitespace | `PASS` | local não privilegiado |
| Unitários/negativos | `PASS_55` | local não privilegiado |
| Sintaxe shell | `PASS_6` | Bash/sh parse local |
| ShellCheck | `PASS_6_V0_11_0` | binário oficial verificado, extraído só em `/tmp` e removido |
| Ansible syntax | `PASS_6_CORE_2_21_3` | wheel oficial verificado, extraído só em `/tmp` e removido |
| GitHub Actions | `PENDING` | nenhum run GitHub commit-bound registrado |
| VM descartável | `PENDING` | nenhuma alegação de apply |
| NODE-01 | `NOT_EXECUTED` | bloqueado por F1.1 |

O código de runtime exercitado corresponde ao desired-state commit
`7015c80759a797bcb141773b79cd9b95f6fbecf1`; a suíte inclui também o gate de
coerência desta camada de checkpoint/estado. Nenhum playbook foi executado
contra inventário/host; somente `--syntax-check`. CI permanecerá `PENDING` até
existir run verde ligado ao mesmo commit publicado.

Os unitários do helper cobrem symlink, hardlink, path extra, open file por
processo, troca de inode após freeze e remoção bottom-up limitada às duas raízes
temporárias. Isso não substitui o lifecycle privilegiado na VM descartável.

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

## Contrato do NODE-01

Nenhuma etapa F1.2b real pode começar enquanto F1.1 não tiver check/apply,
idempotência, invariância e checkpoint reconciliados. Depois de autorizado, o
NODE-01 deve provar baseline/delta de listeners, interfaces, routes, sysctls,
UFW/rulesets, grupos, services e Workstation. Instalação sem workload não prova
Q20/Q34; o primeiro container permanece bloqueado por F1.2c.
