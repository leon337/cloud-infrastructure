# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Protocolo

PUC v1.0. A reconciliação de 15/08 foi publicada no commit `be52e36962159fa7a42ba93a0e96a028daabb67a` e seu estado foi reconstruído em novo chat a partir do GitHub canônico, sem depender de recapitulação conversacional, com resultado **CONTINUIDADE COMPLETA**. Evidência: `governance/CONTINUITY-VALIDATION-INDEPENDENT-2026-08-15.md`. A validação anterior, feita antes da publicação, permanece preservada em `governance/CONTINUITY-VALIDATION-2026-08-15.md`. O protocolo continua aplicável a futuras mudanças e migrações de contexto.

## Regra zero

Antes de qualquer ação operacional:

1. consultar `main` real no GitHub;
2. ler este arquivo, `CHECKPOINT.md` e `state/current.yaml`;
3. ler os documentos canônicos pertinentes;
4. distinguir baseline histórica, fotografia datada e fato volátil;
5. não repetir coleta já suficientemente evidenciada;
6. não pedir secrets pelo chat;
7. não executar mudança sem HUMAN_GATE aplicável.

Precedência: instrução atual de LEANDRO → infraestrutura verificável → GitHub `main` → CHECKPOINT/state → decisões → docs → findings/runbooks → history → chats.

## Mapa canônico

| Pergunta | Fonte |
|---|---|
| Missão e arquitetura | `docs/02-missao-e-escopo.md`, `docs/03-arquitetura-e-principios.md` |
| Plano e estado | `docs/04-plano-mestre.md`, `docs/05-roadmap.md`, `CHECKPOINT.md` |
| Infraestrutura observada | `docs/06-inventario.md` |
| Cloud Workstation | `docs/07-cloud-workstation.md`, `decisions/DEC-003-cloud-workstation-prioridade-operacional.md` |
| Segurança e didática | `docs/08-seguranca-e-governanca.md`, `docs/11-protocolo-didatico.md` |
| Auditoria Fase B | `governance/AUDIT-FASE-B-2026-08-15.md`, `history/SESSION-2026-08-15-009.md` |
| Achados e recovery | `findings/`, `runbooks/`, `recovery/` |
| Evidências visuais | `assets/README.md` |

## Estado operacional

- Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, KVM/QEMU, 8 CPUs, ~23 GiB RAM, sem swap.
- F0: `DONE`. Auditoria Fase B: `DONE` e aprovada para reconciliação.
- F1 acesso/recovery/segurança mínima: `IN_PROGRESS`.
- Root/senha é o acesso validado atual. Não restringir antes da alternativa.
- `ubuntu` possui sudo/NOPASSWD e chave compatível, mas login atual por chave não foi validado; pertence ao grupo `lxd`.
- SSH público em TCP 22; UFW inativo; ataques automatizados confirmados.
- LXD daemon recuperado inactive/dead; socket ativo; 0 instâncias na auditoria.
- Cinco updates Krb5 seguem adiados por phasing; nenhum upgrade forçado.
- Provider VNC/Rescue/firewall/snapshots/backups: `UNCONFIRMED` na coleta de 15/08.
- Cloud Workstation: `PRIORITY_PLANNED`, após validação dos pré-requisitos mínimos.

## Ponto exato

A reconciliação de 15/08 está versionada e publicada. Em 15/08/2026 foi confirmado que HEAD local, `main`, `origin/main` e GitHub `main` apontavam para `be52e36962159fa7a42ba93a0e96a028daabb67a`. O fechamento pós-push/pós-PUC está documentado no estado canônico.

Próximo micro-passo: aguardar HUMAN_GATE operacional de LEANDRO para iniciar a MISSÃO 2 — diagnóstico mínimo read-only da autenticação SSH por chave de `ubuntu`. Nenhuma conexão ou mudança na VPS está autorizada antes desse gate. Futuros commits também continuam sujeitos a HUMAN_GATE.
