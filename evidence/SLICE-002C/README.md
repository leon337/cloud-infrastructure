# Evidence — SLICE-002C network enforcement

Esta pasta registra o contrato e a base fail-closed de F1.2c. A base foi provada
em VM descartável e aplicada no NODE-01. Bridges internas, DNS por escopo,
egress proxy-only, grant explícito, revogação e falha fechada passaram no run
descartável `32100527131`. O lifecycle NODE-01 completo passou no commit
`f771cfd`, run `32131461110`; esses serviços ainda não foram aplicados no NODE-01.

## Cadeia corrente

| Etapa | Estado |
|---|---|
| Contrato machine-readable Q20/Q34 | `PASS_LOCAL_COMMIT_B4CBEB0` |
| Testes integrados | `PASS_123` |
| ADR de tecnologia | `ACCEPTED_DEC_008` |
| Chains fail-closed próprias | `PASS_BASE_IPV4_IPV6` |
| Bridges internas vazias | `PASS_RUN_32075348131_APPLY_IDEMPOTENCE_REFUSAL_ROLLBACK` |
| DNS/egress/grants/conectividade | `PASS_RUN_32100527131_DISPOSABLE_ONLY` |
| Integração descartável IPv4/IPv6 boundary | `PASS_RUN_32100527131` |
| Desired state NODE-01 | `PASS_RUN_32131461110_COMMIT_F771CFD` |
| NODE-01 | `PASS_APPLY_CHANGED_1_IDEMPOTENCE_CHANGED_0` |
| Primeiro workload | `BLOCKED` |

`PASS_BASE` prova instalação, `DOCKER-USER`, IPv4/IPv6, reinício, recusa e
rollback das chains próprias. A prova mais recente cobre redes internas,
descoberta DNS, perfis de proxy, bloqueio de egress direto, grant/revogação e
falha de dependência, sem habilitar IPv6 nos workloads e sem tocar o NODE-01.

## Próxima evidência necessária

O próximo passo verifica o runner temporário e aplica o desired state já provado
no NODE-01, com precheck, reconciliação e evidência. O primeiro workload continua
bloqueado por esse apply e pelos gates restantes de quota/admission.
