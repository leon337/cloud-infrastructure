# PUC v1.0 — Protocolo Universal de Continuidade

## Objetivo

Garantir consistência de contexto entre chats, IAs, agentes e períodos de tempo sem depender da memória conversacional.

## Princípio central

**Toda informação necessária para reconstruir estado, intenção, decisões, riscos e próximos passos deve possuir uma casa canônica no GitHub.**

## Tipos de memória

1. **Missão estável** — por que existe e o que pretende alcançar.
2. **Arquitetura** — modelo conceitual e restrições.
3. **Plano/Roadmap** — caminho previsto e estados.
4. **Inventário factual** — o que existe de verdade.
5. **Decisões** — escolhas e motivos.
6. **Findings** — problemas, testes e resultados.
7. **Runbooks/Recovery** — como operar e recuperar.
8. **Histórico** — como o estado evoluiu.
9. **Checkpoint** — onde parar/retomar agora.
10. **State machine-readable** — resumo estruturado.

## Protocolo de abertura de sessão

Antes de agir:

1. consultar `main` real;
2. ler `CONTEXT.md`;
3. ler `CHECKPOINT.md`;
4. ler `state/current.yaml`;
5. ler documentos apontados para a etapa;
6. verificar findings abertos;
7. consultar decisões aplicáveis;
8. verificar estado real do recurso antes de mudança destrutiva/volátil;
9. declarar o ponto de retomada;
10. somente então propor ação.

## Protocolo de trabalho

Cada informação nova deve ser classificada:

- `FACT` — observação validada;
- `DECISION` — escolha autorizada;
- `PROPOSAL` — ainda não aprovada;
- `FINDING` — problema/risco observado;
- `AUTHORIZATION` — gate humano concedido;
- `LESSON` — aprendizado relevante para o tutorial.

Não misturar proposta com decisão nem hipótese com fato.

## Auditoria de Delta obrigatória

Antes de encerrar uma sessão relevante, responder e persistir:

1. O que foi descoberto?
2. O que foi alterado?
3. O que foi validado?
4. O que falhou?
5. Que teste foi inválido e por quê?
6. O que LEANDRO autorizou?
7. Quais decisões foram tomadas?
8. Quais riscos surgiram?
9. O que LEANDRO aprendeu?
10. Quais arquivos canônicos precisam mudar?
11. Qual é o próximo passo exato?
12. Existe algo importante apenas no chat? Se sim, a sessão não pode encerrar.

## Protocolo de fechamento

1. atualizar documentos proprietários do contexto;
2. atualizar findings/decisions pertinentes;
3. criar registro em `history/`;
4. atualizar `state/current.yaml`;
5. atualizar `CHECKPOINT.md` por último;
6. verificar a `main` real;
7. executar teste de continuidade em novo chat quando houver migração de contexto;
8. só retomar operação após `CONTINUIDADE COMPLETA` ou justificativa explícita de LEANDRO.

## Ownership — evitar duplicação divergente

- missão: `docs/02-missao-e-escopo.md`;
- arquitetura: `docs/03-arquitetura-e-principios.md`;
- plano: `docs/04-plano-mestre.md`;
- roadmap/status de fases: `docs/05-roadmap.md`;
- inventário: `docs/06-inventario.md`;
- estado imediato: `CHECKPOINT.md`;
- estado estruturado: `state/current.yaml`;
- decisões: `decisions/`;
- findings: `findings/`;
- histórico: `history/`.

Outros arquivos devem apontar para a fonte proprietária em vez de duplicar detalhes mutáveis sem necessidade.

## Consistência e concorrência

Antes de escrever:

- ler HEAD atual;
- usar conteúdo/SHA atual do arquivo;
- nunca sobrescrever mudanças não lidas;
- se outra IA alterou a `main`, reavaliar o delta;
- preferir commits coerentes por lote lógico;
- verificar o estado final após commit.

## Estado real versus documentação

Documentação pode envelhecer. Para fatos voláteis — IP dinâmico, pacotes, serviços, portas, versões, processos, espaço, firewall — verificar o ambiente real antes de agir. Registrar `last verified` quando útil.

## Política de secrets

Nunca armazenar secrets reais. Usar placeholders para secrets. Identificadores públicos/operacionais conhecidos podem ser canônicos se necessários à operação.

## HUMAN_GATE

Mudança estrutural, destrutiva, de segurança, custo, exposição de rede ou perda potencial de acesso exige autorização explícita de LEANDRO.

## Critério de continuidade completa

Um novo agente deve conseguir responder, sem perguntar a LEANDRO novamente:

- por que o projeto existe;
- o que foi planejado;
- o que foi aprovado;
- o que existe hoje;
- o que já foi feito;
- o que falhou;
- por que decisões foram tomadas;
- quais riscos estão abertos;
- onde exatamente parou;
- qual é o próximo passo;
- quais ações dependem de autorização.

Se não conseguir, a continuidade é parcial e deve ser reparada antes de continuar.