# CONTEXT — Porta de entrada canônica

Este arquivo é a porta de entrada obrigatória para qualquer IA, agente ou humano que assuma a missão `cloud-infrastructure`.

## Protocolo ativo

**PUC v1.0 — Protocolo Universal de Continuidade**.

Objetivo: permitir continuidade segura entre chats, modelos, agentes, dias, meses ou anos sem depender da memória de uma conversa.

Status do protocolo: **VALIDADO — CONTINUIDADE COMPLETA**.

Evidência: `governance/CONTINUITY-VALIDATION-2026-08-14.md`.

## Regra zero

Antes de qualquer ação operacional:

1. consultar o estado REAL da branch `main` no GitHub;
2. ler este arquivo;
3. ler `CHECKPOINT.md`;
4. ler `state/current.yaml`;
5. ler os documentos canônicos pertinentes à etapa atual;
6. verificar a infraestrutura real antes de afirmar estado volátil;
7. não pedir novamente dados já registrados, salvo se houver motivo para revalidá-los;
8. não executar mudança estrutural sem `HUMAN_GATE` de LEANDRO.

## Ordem de precedência

Em caso de conflito:

1. instrução explícita atual de LEANDRO;
2. estado real verificável da infraestrutura;
3. estado real da branch `main`;
4. `CHECKPOINT.md` e `state/current.yaml`;
5. decisões canônicas em `decisions/`;
6. inventário e documentação canônica em `docs/`;
7. findings e runbooks;
8. histórico de sessões;
9. memória de chats.

Chats nunca são fonte canônica de longo prazo.

## Mapa da memória do projeto

| Pergunta | Fonte canônica |
|---|---|
| Por que o projeto existe? | `docs/02-missao-e-escopo.md` |
| Como a arquitetura deve evoluir? | `docs/03-arquitetura-e-principios.md` |
| Qual é o plano completo? | `docs/04-plano-mestre.md` |
| Onde estamos no plano? | `docs/05-roadmap.md` + `CHECKPOINT.md` |
| O que existe de fato hoje? | `docs/06-inventario.md` |
| Como será a Cloud Workstation? | `docs/07-cloud-workstation.md` |
| Quais regras de segurança/governança? | `docs/08-seguranca-e-governanca.md` |
| Quais termos já foram aprendidos? | `docs/09-glossario.md` |
| Como funciona o painel Contabo? | `docs/10-painel-contabo.md` |
| Como ensinar/avançar com LEANDRO? | `docs/11-protocolo-didatico.md` |
| Como manter continuidade entre chats? | `governance/PUC-v1.md` |
| O PUC foi validado? | `governance/CONTINUITY-VALIDATION-2026-08-14.md` |
| Quais riscos do próprio protocolo? | `governance/RC-001-PUC-v1.md` |
| Qual cobertura de contexto é obrigatória? | `governance/CONTEXT-COVERAGE.md` |
| Qual decisão foi tomada? | `decisions/` |
| Qual problema técnico foi encontrado? | `findings/` |
| O que ocorreu em uma sessão? | `history/` |
| Como executar/recuperar uma operação? | `runbooks/` e `recovery/` |
| Qual é o estado resumido para máquinas? | `state/current.yaml` |

## Estado operacional resumido

- Provedor: Contabo.
- Produto: Cloud VPS 8.
- VPS: Ubuntu 24.04.4 LTS.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Linux Mint local: `leo@leo-N43SM`.
- Fase atual: FASE 0 — ORIENTAÇÃO E INVENTÁRIO.
- Etapa atual: 0.5 — Inventário real da VPS.
- PUC v1.0: validado com `CONTINUIDADE COMPLETA`.
- Retomada operacional: permitida conforme `state/current.yaml`.
- `FND-SSH-001`: **RESOLVED**.
- Keepalive permanente: aplicado e validado no Linux Mint local.
- Alias SSH `contabo-vps`: validado.
- Próximo passo: continuar inventário de armazenamento/filesystems, seguido por mounts, rede e uptime/estado básico.

## Regra de fechamento de sessão

Nenhuma sessão relevante está corretamente encerrada enquanto descobertas, decisões, autorizações, mudanças, riscos ou próximos passos existirem apenas no chat.

Antes de trocar de chat, executar a Auditoria de Delta definida no PUC, persistir as mudanças, atualizar `CHECKPOINT.md` e `state/current.yaml`, registrar a sessão em `history/`, verificar a `main` e realizar teste de continuidade quando houver migração relevante de contexto.
