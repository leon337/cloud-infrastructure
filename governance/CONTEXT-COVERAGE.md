# Context Coverage Matrix

Esta matriz impede lacunas silenciosas de memória.

| Categoria obrigatória | Fonte proprietária | Estado atual |
|---|---|---|
| Identidade/finalidade | `docs/02-missao-e-escopo.md` | coberto |
| Regras didáticas | `docs/11-protocolo-didatico.md` | coberto |
| Arquitetura atual/alvo | `docs/03-arquitetura-e-principios.md` | coberto |
| Cloud Workstation | `docs/07-cloud-workstation.md` | coberto |
| Plano mestre | `docs/04-plano-mestre.md` | coberto |
| Roadmap/status | `docs/05-roadmap.md` | coberto |
| Inventário factual | `docs/06-inventario.md` | coberto parcial — etapa 0.5 em andamento |
| Segurança/governança | `docs/08-seguranca-e-governanca.md` | coberto |
| Primeiro acesso | `docs/01-primeiro-acesso-seguro.md` | coberto |
| Painel Contabo | `docs/10-painel-contabo.md` | coberto inicial |
| Glossário | `docs/09-glossario.md` | coberto inicial |
| Decisões | `decisions/` | coberto e expansível |
| Findings | `findings/` | FND-SSH-001 coberto |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md` | esqueleto vivo criado |
| Runbooks | `runbooks/` | acesso/recuperação inicial coberto |
| Histórico de sessões | `history/` | sessão retrospectiva inicial criada |
| Estado imediato | `CHECKPOINT.md` | coberto |
| Estado legível por máquina | `state/current.yaml` | coberto |
| Continuidade universal | `CONTEXT.md` + `governance/PUC-v1.md` | coberto |

## Regra de auditoria

Ao fechar sessão, cada novo fato/decisão deve ser mapeado para uma linha desta matriz. Se não existir categoria apropriada, criar uma e atualizar a matriz.