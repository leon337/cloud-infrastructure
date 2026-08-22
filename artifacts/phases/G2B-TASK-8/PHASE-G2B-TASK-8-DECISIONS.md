# G2-B Task 8 — Decisões

## D1 — GitHub vivo prevalece para estado mutável

O PR #11 e o HEAD protegido foram lidos antes de qualquer alteração. A descrição do PR estava defasada em relação ao resultado terminal posterior; a divergência foi registrada.

## D2 — Branch filha obrigatória

A frente nasceu de `fbef3d407dbd9b7947b6c100a63d098eaebe2b6a` em `team/g2b-task8-20260822`. A branch protegida não foi reescrita.

## D3 — Trabalho divergente não foi apropriado

Branches `ops/g2b-*` existentes foram inspecionadas e não pertenciam ao lineage corrente da Task 8. Foram preservadas.

## D4 — `exit=2` não foi tratado como causa

A investigação localizou o processo em uma das duas invocações do playbook `apply-control-bridge-g2b.yml`, mas não uma task/erro raiz.

## D5 — Hipóteses sem prova não viraram correção

A correção de `/usr/local/libexec` já estava no candidato. O lock de instalação é liberado em `always`. Nenhuma outra hipótese recebeu mudança funcional.

## D6 — Não repetir cegamente

A evidência original suprimiu stdout do Ansible. Sem causa comprovada, o lifecycle não foi repetido apenas para obter um resultado diferente.

## D7 — Probe temporário sem execução

Foi criado um workflow read-only e one-shot na branch filha para localizar resíduos da VM preservada. GitHub não gerou run. O probe é removido da árvore final.

## D8 — Condição de parada

Como a causa não pôde ser determinada com segurança, a frente retorna `BLOCKED`. Tasks 9/10, escrita G2-B real no NODE-01, HUMAN_GATE e merge permanecem intocados.
