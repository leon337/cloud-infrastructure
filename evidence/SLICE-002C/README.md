# Evidence — SLICE-002C network enforcement contract

Esta pasta registra o avanço repo-only de F1.2c. O contrato fixa os resultados
de segurança e DEC-008 seleciona o mecanismo, mas ainda não há ruleset aplicável,
prova dinâmica ou autorização de workload.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Contrato machine-readable Q20/Q34 | `PASS_LOCAL_COMMIT_B4CBEB0` |
| Testes de contrato + compilador | `PASS_8` |
| Suíte integrada do repositório | `PASS_70` |
| ADR de tecnologia | `ACCEPTED_DEC_008` |
| Compilador fail-closed | `PASS_LOCAL_EXAMPLE_ONLY` |
| Apply/DNS/egress implementation | `NOT_IMPLEMENTED` |
| Integração descartável IPv4/IPv6 | `PENDING` |
| NODE-01 | `NOT_EXECUTED` |
| Primeiro workload | `BLOCKED` |

`PASS_LOCAL` prova apenas que o contrato preserva deny-by-default, escopos,
grants e gates esperados. Não prova nftables, `DOCKER-USER`, DNS, egress,
service discovery, firewall, Docker ou conectividade real.

## Próxima evidência necessária

O próximo delta precisa implementar apply/rollback fail-closed. Depois, uma
fixture descartável precisa provar toda a matriz
`required_disposable_evidence` em IPv4 e IPv6. Somente essa cadeia, mais as
dependências F1.1/F1.2b aplicáveis, poderá reavaliar o gate do primeiro workload.
