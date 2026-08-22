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

## D7 — Recuperação diagnóstica adicional limitada

Foi preparada uma reprodução diagnóstica restrita à boundary descartável preservada, usando o mesmo candidato e alterando apenas a observabilidade das duas invocações Ansible. O trabalho longo seria executado dentro da VM; o self-hosted runner seria usado somente para ações one-shot.

Nenhum resultado dessa recuperação ficou observável nas evidências disponíveis. Portanto execução e resultado são classificados como `NOT_VERIFIED` e não sustentam nenhuma conclusão técnica. Os workflows temporários foram removidos da árvore final por commits normais.

## D8 — Condição de parada

Como a causa não pôde ser determinada com segurança e não existe lifecycle pós-correção comprovado, a frente retorna `BLOCKED`. Tasks 9/10, escrita G2-B real no NODE-01, HUMAN_GATE e merge permanecem intocados.
