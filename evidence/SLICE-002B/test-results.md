# SLICE-002B test results

Status: **PREPARATION — CI PENDING — VPS NOT_EXECUTED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Pins/checksums/fingerprints/licenças documentados | `RECORDED` | decisão e inventário |
| Links Markdown locais | `PENDING_FINAL_DELTA` | local, não CI |
| YAML estrito | `PENDING_FINAL_DELTA` | local, não CI |
| State cross-check | `PENDING_FINAL_DELTA` | local, não CI |
| Secret/history policy | `PENDING_FINAL_DELTA` | local, não CI |
| Diff whitespace | `PENDING_FINAL_DELTA` | local, não CI |
| Ansible syntax/static guards | `PENDING` | implementação em andamento |
| GitHub Actions | `PENDING` | nenhum run/commit registrado |
| VM descartável | `PENDING` | nenhuma alegação de apply |
| NODE-01 | `NOT_EXECUTED` | bloqueado por F1.1 |

Resultados locais serão atualizados somente depois de executar o delta integrado.
CI permanecerá `PENDING` até existir run verde ligado ao commit publicado.

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

