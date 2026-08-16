# Context Coverage Matrix

Esta matriz impede lacunas silenciosas de memória.

| Categoria obrigatória | Fonte proprietária | Estado atual |
|---|---|---|
| Identidade/finalidade | `docs/02-missao-e-escopo.md` | coberto |
| Regras didáticas | `docs/11-protocolo-didatico.md` | coberto |
| Arquitetura atual/alvo | `docs/03-arquitetura-e-principios.md` | coberto |
| Cloud Workstation | `docs/07-cloud-workstation.md` | implementada e validada; arquitetura e testes cobertos |
| Plano mestre | `docs/04-plano-mestre.md` | coberto |
| Roadmap/status | `docs/05-roadmap.md` | coberto |
| Inventário factual | `docs/06-inventario.md` | baseline 14/08 + revalidação 15/08 cobertas |
| Segurança/governança | `docs/08-seguranca-e-governanca.md` | coberto |
| Primeiro acesso | `docs/01-primeiro-acesso-seguro.md` | coberto |
| Painel Contabo | `docs/10-painel-contabo.md` | coberto inicial |
| Glossário | `docs/09-glossario.md` | coberto inicial |
| Decisões | `decisions/` | coberto e expansível |
| Findings | `findings/` | SSH/LXD/sudo resolvidos; backup mitigado/aberto; histórico preservado |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md` | VNC, SSH, XRDP e backup proporcional cobertos; reconstrução ampla pendente |
| Runbooks | `runbooks/` | SSH/publickey, túnel RDP, sudo autenticado, VNC e backup cobertos |
| Histórico de sessões | `history/` | auditorias, Missões 2/2B/4 e implementação F1/F2 preservadas |
| Estado imediato | `CHECKPOINT.md` | coberto |
| Estado legível por máquina | `state/current.yaml` | coberto |
| Evidências visuais | `assets/README.md` | SSH e Cloud Workstation sanitizados, separados de conceitos |
| Continuidade universal | `CONTEXT.md` + `governance/PUC-v1.md` | PUC ativo; validações independentes históricas preservadas; novo estado recuperável e aguardando teste independente |

## Regra de auditoria

Ao fechar sessão, cada novo fato/decisão deve ser mapeado para uma linha desta matriz. Se não existir categoria apropriada, criar uma e atualizar a matriz.
