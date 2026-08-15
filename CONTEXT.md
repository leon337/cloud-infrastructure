# CONTEXT — Porta de entrada canônica

Este arquivo é a entrada obrigatória para qualquer IA, agente ou humano que assuma `cloud-infrastructure`.

## Protocolo

PUC v1.0. A reconciliação de 15/08 foi publicada no commit `be52e36962159fa7a42ba93a0e96a028daabb67a`; o fechamento pós-push/pós-PUC foi publicado em `27e6f8223a12ad65da253a1b5364472ce1f764e8`. Aquele snapshot foi reconstruído em novo chat a partir do GitHub canônico, sem depender de recapitulação conversacional, com resultado **CONTINUIDADE COMPLETA**. Evidência histórica: `governance/CONTINUITY-VALIDATION-INDEPENDENT-2026-08-15.md`. A validação pré-publicação permanece em `governance/CONTINUITY-VALIDATION-2026-08-15.md`. Nenhum novo teste independente foi executado para o estado posterior à Missão 2/2B; o protocolo continua aplicável.

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
| Auditoria, acesso e privilégios | `governance/AUDIT-FASE-B-2026-08-15.md`, `history/SESSION-2026-08-15-009.md`, `history/SESSION-2026-08-15-010.md`, `history/SESSION-2026-08-15-011.md` |
| Achados e recovery | `findings/`, `runbooks/`, `recovery/` |
| Evidências visuais | `assets/README.md` |

## Estado operacional

- Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, KVM/QEMU, 8 CPUs, ~23 GiB RAM, sem swap.
- F0: `DONE`. Auditoria Fase B: `DONE` e aprovada para reconciliação.
- F1 acesso/recovery/segurança mínima: `IN_PROGRESS`.
- Root/senha permanece validado, temporário e preservado; ainda não restringir antes de recovery proporcional e decisões explícitas sobre sudo/LXD.
- `ubuntu` tem login atual `VALIDATED` exclusivamente por nova chave `publickey`; a chave anterior foi preservada. A Missão 4 confirmou UID/GID 1000, grupos `ubuntu adm cdrom sudo dip lxd`, elevação sem senha a UID 0 por sudo/NOPASSWD e escrita no socket LXD.
- SSH público em TCP 22; UFW inativo; ataques automatizados confirmados.
- LXD daemon permaneceu inactive/dead e o socket `root:lxd` modo `660` permaneceu active/listening; o caminho equivalente a root foi confirmado sem exploração ou execução de `lxc`.
- Cinco updates Krb5 seguem adiados por phasing; nenhum upgrade forçado.
- Provider VNC/Rescue/firewall/snapshots/backups: `UNCONFIRMED` na coleta de 15/08.
- Cloud Workstation: `PRIORITY_PLANNED`, após validação dos pré-requisitos mínimos.

## Ponto exato

A reconciliação e o fechamento pós-push/pós-PUC estão versionados. A validação independente preservada corresponde ao snapshot anterior à Missão 2/2B e não deve ser reinterpretada como validação independente do estado atual.

Próximo micro-passo: aguardar HUMAN_GATE operacional de LEANDRO para revisão read-only de recovery proporcional e validação dos caminhos de recuperação. Os findings `FND-SUDO-001` e `FND-LXD-001` permanecem abertos/high; segurança mínima de SSH/firewall continua pendente. Nenhuma nova conexão ou mudança na VPS está autorizada sem gate próprio; futuros commits também continuam sujeitos a HUMAN_GATE.
