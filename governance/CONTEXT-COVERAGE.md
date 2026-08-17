# Context Coverage Matrix

Esta matriz impede lacunas silenciosas de memória.

| Categoria obrigatória | Fonte proprietária | Estado atual |
|---|---|---|
| Identidade/finalidade | `docs/02-missao-e-escopo.md` | coberto |
| Regras didáticas | `docs/11-protocolo-didatico.md` | coberto |
| Requisitos Q1–Q40 | `docs/41-consolidated-requirements.md` + checkpoints | baseline vinculante coberta |
| Arquitetura atual/alvo | `docs/03-arquitetura-e-principios.md` + `docs/42-target-architecture.md` | histórico e target V1 cobertos |
| Threat/autonomy model | `docs/43-threat-model-and-autonomy-boundaries.md` | baseline deny-by-default coberta |
| Cloud Workstation | `docs/07-cloud-workstation.md` | implementada e validada; arquitetura e testes cobertos |
| Plano/blueprint | `docs/04-plano-mestre.md` + `docs/44-infrastructure-blueprint-v1.md` | blueprint executável V1 coberto |
| Roadmap/status | `docs/05-roadmap.md` + `docs/45-revised-implementation-roadmap.md` | slices Q40-D cobertos |
| Technology Mapping | `docs/46-technology-mapping-v1.md` + DEC-005/006 | seleção/lifecycle V1 cobertos |
| Inventário factual | `docs/06-inventario.md` + `state/components.yaml` | baseline histórica + componentes 16/08 cobertos |
| Segurança/governança | `docs/08-seguranca-e-governanca.md` | coberto |
| Primeiro acesso | `docs/01-primeiro-acesso-seguro.md` | coberto |
| Painel Contabo | `docs/10-painel-contabo.md` | coberto inicial |
| Glossário | `docs/09-glossario.md` | coberto inicial |
| Decisões | `decisions/` | coberto e expansível |
| Findings | `findings/` | SSH/LXD/sudo resolvidos; backup mitigado/aberto; histórico preservado |
| Recovery | `recovery/RECOVERY-PLAYBOOK.md` | VNC, SSH, XRDP e backup proporcional cobertos; reconstrução ampla pendente |
| Runbooks | `runbooks/` | acesso/recovery e Foundations F1.1 cobertos |
| Evidência de implementação | `evidence/` | F1.1 real DONE com backup/apply/idempotência/invariância; F1.2b pronto somente para preview real |
| Histórico de sessões | `history/` | auditorias, F1/F2 e Mission Acceptance/F1.1 preservadas |
| Estado imediato | `CHECKPOINT.md` | coberto |
| Estado legível por máquina | `state/current.yaml` | coberto |
| Evidências visuais | `assets/README.md` | SSH e Cloud Workstation sanitizados, separados de conceitos |
| Continuidade universal | `CONTEXT.md` + `governance/PUC-v1.md` + `governance/CONTINUITY-VALIDATION-2026-08-16-MISSION-001.md` | PUC ativo; estado recuperável, preview real registrado e apply humano ainda aberto |

## Regra de auditoria

Ao fechar sessão, cada novo fato/decisão deve ser mapeado para uma linha desta matriz. Se não existir categoria apropriada, criar uma e atualizar a matriz.
