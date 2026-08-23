# Memória Institucional

Esta pasta contém registros históricos permanentes de eventos materiais do projeto que precisam sobreviver a chats, sessões, agentes e mudanças de estado corrente.

## Finalidade

Um checkpoint responde **onde retomar**. Um memo institucional responde **o que aconteceu, por que importou, o que foi decidido e quais consequências permaneceram**.

Memos são apropriados para:

- incidentes e interrupções relevantes;
- mudanças materiais de objetivo ou escopo;
- descobertas significativas;
- decisões arquiteturais ou processuais de alto impacto;
- eventos de recuperação;
- mudanças materiais de risco;
- lições que alterem controles, políticas ou operação futura.

## Regra append-oriented

Memos são evidência histórica do que era conhecido e decidido naquele momento.

- não reescrever silenciosamente um memo para fazê-lo parecer compatível com entendimento posterior;
- correções materiais devem gerar novo memo ou adendo explicitamente relacionado;
- estado corrente continua em `state/`, `CHECKPOINT.md` e documentos da missão ativa;
- quando memória e estado corrente diferirem, isso não é automaticamente erro: memória explica o passado, estado explica o presente;
- divergência inexplicada entre fontes atuais continua sujeita ao protocolo de recuperação fail-closed.

## Convenção de nome

```text
history/memos/YYYY-MM-DD-<slug>.md
```

## Estrutura mínima

Cada memo deve registrar, quando aplicável:

1. identificação e classificação;
2. contexto anterior;
3. evento observado;
4. impacto;
5. evidências disponíveis;
6. recuperação/resposta;
7. causa ou lacuna comprovada — sem inventar causa não evidenciada;
8. decisões tomadas;
9. ações corretivas e preventivas;
10. riscos residuais;
11. relação com estado atual e próximos controles;
12. referências duráveis.

## Índice machine-readable

O contrato e índice atual ficam em:

`state/institutional-memory.yaml`

Esse arquivo pode apontar para memos, mas não substitui o conteúdo histórico deles.
