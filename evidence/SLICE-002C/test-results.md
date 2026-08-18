# SLICE-002C test results

Status: **NODE-01 DESIRED STATE CI PASS — REAL APPLY PENDING — FIRST WORKLOAD BLOCKED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Contrato YAML estrito | `PASS` | desired state |
| Q20/Q34 e threat controls vinculados | `PASS` | teste estático |
| IPv4 + IPv6 obrigatórios | `PASS` | teste estático |
| Deny host/Management/metadata/control/lateral | `PASS_BASE` | chains próprias; política completa pendente |
| Sharing por grant e egress por profile | `PASS` | conectividade descartável + revogação |
| Gate de primeiro workload | `PASS_BLOCKED` | estado declarativo |
| Testes específicos | `PASS` | contrato, compilador, runtime, redes e serviços |
| Suíte integrada | `PASS_123` | CI; snapshot VPS anterior permanece 98 |
| YAML do repositório | `PASS_39` | parse estrito |
| Base IPv4/IPv6 | `PASS` | apply, check, reinício e rollback em VM descartável |
| ADR/mecanismo | `ACCEPTED_DEC_008` | `DOCKER-USER`, bridges internas e egress proxy-only |
| Fixture descartável | `PASS` | run `32073151044`, commit `d1da488` |
| Redes internas vazias | `PASS` | 3 scopes; apply 3, idempotência 0, recusa e rollback 3; run `32075348131` |
| DNS/proxy/grants/fail-closed | `PASS` | run `32100527131`, commit `8d5963b` |
| NODE-01 services desired state | `PASS_RUN_32131461110_COMMIT_F771CFD` | apply 1, idempotência 0, DNS, proxy, direct deny, restart e rollback limpo |
| NODE-01 apply | `PASS_CHANGED_1` | `2026-08-17T21:58:36Z` |
| NODE-01 idempotência | `PASS_CHANGED_0` | `2026-08-17T21:58:57Z` |
| NODE-01 check/test | `PASS` | check + 98 testes; runtime vazio |

No NODE-01, o incremento instala somente chains fail-closed próprias para
interfaces futuras `cp*`, reaplicadas após restart do Docker; nenhuma bridge ou
rede foi criada ali. Na VM descartável, o lifecycle criou três redes internas
determinísticas, recusou rede não gerenciada e removeu tudo. Uma VM separada
provou DNS por escopo, proxy allowlist, deny de egress direto, grant explícito,
revogação e falha fechada. O NODE-01 continua somente com a base. O desired
state NODE-01 passou integralmente no run `32131461110`; o apply real permanece
pendente e o resultado não autoriza o
primeiro workload nem declara Q20/Q34 integralmente operacionais no host real.
