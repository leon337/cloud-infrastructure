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

## D9 — Local disposable validation is evidence, not production apply
The authorized local host was used only to run the existing disposable Docker/systemd boundary. No real NODE-01 G2-B write was executed.

## D10 — Fix the executor call site, not workspace ownership
The installed pilot boundary now passes the exact reviewed pilot workspace leaf to the executor. Protected parents remain root-owned and non-writable to the service account.

## D11 — Keep the bounded cleanup gate strict
`lsof` was added to the disposable fixture. The rollback continues to fail for command errors outside rc 0/1 and still requires empty stdout. The rc assertion was aligned with proven `lsof` semantics rather than weakening the zero-open-files requirement.

## D12 — Hosted CI billing failure is external
GitHub validate jobs for the published candidate never obtained a runner and executed zero steps. Their check annotations explicitly identify billing/spending-limit failure. They are recorded as NOT_EXECUTED/BLOCKED_BY_BILLING, not as candidate test failures.

## D13 — PASS is technical, merge remains a central decision
Lifecycle 13/13 and repository validation satisfy Task 8 technical acceptance. PR #21 remains draft and unmerged for central MESTRE audit.
