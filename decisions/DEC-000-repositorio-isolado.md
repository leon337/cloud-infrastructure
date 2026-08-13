# DEC-000 — Repositório isolado para a infraestrutura

## Contexto

A nova VPS será usada como infraestrutura para múltiplos projetos e não deve contaminar o repositório do MCF.

## Decisão

Usar `leon337/cloud-infrastructure` como repositório canônico e separado para documentação, decisões e artefatos da infraestrutura.

## Consequências

- O MCF permanece independente.
- A VPS poderá hospedar MCF e outros projetos sem pertencer estruturalmente ao MCF.
- Configurações e documentação específicas da VPS ficam centralizadas neste repositório.
- O repositório será mantido privado nesta fase inicial.
- Nenhum secret real deverá ser versionado.

## Revisão futura

A decisão pode ser revisada se a infraestrutura crescer a ponto de exigir separação por ambientes, provedores ou produtos.
