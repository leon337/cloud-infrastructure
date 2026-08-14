# DEC-001 — Protocolo Universal de Continuidade

Status: **ACEITO E IMPLEMENTADO**.

## Contexto

A troca de chats revelou perda progressiva de detalhes: novo chat pediu IP já conhecido e não recuperou integralmente planejamento, raciocínio e histórico.

## Alternativas

1. prompts gigantes a cada novo chat;
2. confiar em memória do produto/chat;
3. checkpoints únicos cada vez maiores;
4. sistema documental canônico distribuído por tipo de contexto.

## Decisão

Adotar o **PUC v1.0**, com `CONTEXT.md` como porta de entrada, checkpoint de estado, state machine-readable, documentos proprietários, decisions, findings, history, runbooks e recovery.

## Motivo

O projeto é longo e não pode depender da memória de LEANDRO nem de uma conversa. Qualquer IA futura deve reconstruir a missão consultando o GitHub.

## Consequências

- fechamento de sessão exige Auditoria de Delta;
- chats deixam de ser fonte canônica;
- documentação passa a ser parte da operação;
- continuidade precisa ser testada;
- há custo de manutenção documental, aceito em troca de consistência.

## Revisão

Revisar o protocolo se ele gerar duplicação excessiva, ficar pesado demais ou falhar em teste de continuidade.