# Evidence — SLICE-002C network enforcement

Esta pasta registra o contrato e a base fail-closed de F1.2c. A base foi provada
em VM descartável e aplicada no NODE-01, mas não autoriza workload: bridges
internas, DNS por escopo, egress proxy-only e grants continuam pendentes.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Contrato machine-readable Q20/Q34 | `PASS_LOCAL_COMMIT_B4CBEB0` |
| Testes integrados | `PASS_98` |
| ADR de tecnologia | `ACCEPTED_DEC_008` |
| Chains fail-closed próprias | `PASS_BASE_IPV4_IPV6` |
| Bridges internas vazias | `PASS_RUN_32075348131_APPLY_IDEMPOTENCE_REFUSAL_ROLLBACK` |
| DNS/egress/grants/conectividade | `PENDING` |
| Integração descartável IPv4/IPv6 | `PASS_RUN_32075348131` |
| NODE-01 | `PASS_APPLY_CHANGED_1_IDEMPOTENCE_CHANGED_0` |
| Primeiro workload | `BLOCKED` |

`PASS_BASE` prova instalação, `DOCKER-USER`, IPv4/IPv6, reinício, recusa e
rollback das chains próprias. A prova seguinte cobre somente redes internas
vazias e seu lifecycle; não prova ainda DNS, egress, service discovery, grants
nem a matriz completa de conectividade.

## Próxima evidência necessária

O próximo delta precisa implementar bridges internas, DNS por escopo, egress
proxy-only e grants. Depois, a fixture descartável deve provar toda a matriz
`required_disposable_evidence` em IPv4 e IPv6 antes de reavaliar o primeiro
workload.
