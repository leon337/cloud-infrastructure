# SLICE-002C test results

Status: **BASE ENFORCEMENT PASS — FULL F1.2c POLICY PENDING — FIRST WORKLOAD BLOCKED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Contrato YAML estrito | `PASS` | desired state |
| Q20/Q34 e threat controls vinculados | `PASS` | teste estático |
| IPv4 + IPv6 obrigatórios | `PASS` | teste estático |
| Deny host/Management/metadata/control/lateral | `PASS_BASE` | chains próprias; política completa pendente |
| Sharing por grant e egress por profile | `PASS` | contrato, não conectividade |
| Gate de primeiro workload | `PASS_BLOCKED` | estado declarativo |
| Testes específicos | `PASS` | contrato, compilador, runtime base e lifecycle de redes |
| Suíte integrada | `PASS_100` | local; snapshot VPS anterior permanece 98 |
| YAML do repositório | `PASS_36` | parse estrito |
| Base IPv4/IPv6 | `PASS` | apply, check, reinício e rollback em VM descartável |
| ADR/mecanismo | `ACCEPTED_DEC_008` | `DOCKER-USER`, bridges internas e egress proxy-only |
| Fixture descartável | `PASS` | run `32073151044`, commit `d1da488` |
| Redes internas vazias | `PASS` | 3 scopes; apply 3, idempotência 0, recusa e rollback 3; run `32075348131` |
| NODE-01 apply | `PASS_CHANGED_1` | `2026-08-17T21:58:36Z` |
| NODE-01 idempotência | `PASS_CHANGED_0` | `2026-08-17T21:58:57Z` |
| NODE-01 check/test | `PASS` | check + 98 testes; runtime vazio |

No NODE-01, o incremento instala somente chains fail-closed próprias para
interfaces futuras `cp*`, reaplicadas após restart do Docker; nenhuma bridge ou
rede foi criada ali. Na VM descartável, o lifecycle criou três redes internas
vazias com identidade/sub-rede/bridge determinísticas, recusou rede não
gerenciada e removeu tudo. DNS por escopo, egress proxy-only, grants e a matriz
com workloads continuam pendentes; o resultado não autoriza o primeiro workload
nem satisfaz integralmente Q20/Q34.
