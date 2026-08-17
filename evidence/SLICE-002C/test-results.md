# SLICE-002C test results

Status: **CONTRACT LOCAL PASS — ADR/DYNAMIC PROOF PENDING — VPS NOT_EXECUTED**

## Resultado corrente

| Verificação | Resultado | Escopo |
|---|---|---|
| Contrato YAML estrito | `PASS` | repo-only |
| Q20/Q34 e threat controls vinculados | `PASS` | teste estático |
| IPv4 + IPv6 obrigatórios | `PASS` | teste estático |
| Deny host/Management/metadata/control/lateral | `PASS` | contrato, não ruleset |
| Sharing por grant e egress por profile | `PASS` | contrato, não conectividade |
| Gate de primeiro workload | `PASS_BLOCKED` | estado declarativo |
| Testes específicos | `PASS_4` | não privilegiado |
| Suíte integrada | `PASS_60` | não privilegiado |
| YAML do repositório | `PASS_34` | parse estrito |
| ADR/mecanismo | `PENDING` | não selecionado |
| Fixture descartável | `PENDING` | não executada |
| NODE-01 | `NOT_EXECUTED` | nenhuma autorização criada |

Os testes verificam o conteúdo do contrato e a separação entre `PASS_LOCAL`,
`PENDING` e `NOT_EXECUTED`. Não foram executados Docker, firewall, network
namespace, probe externo, playbook ou comando privilegiado.
