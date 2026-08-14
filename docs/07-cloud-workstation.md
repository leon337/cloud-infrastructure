# 07 — Cloud Workstation

Status: **DEFERRED — requisito preservado, implementação ainda não aprovada**.

## Intenção de LEANDRO

Além de servidor, a VPS deve ser avaliada como computador remoto gráfico familiar: navegador, arquivos, VS Code, terminal e ferramentas de trabalho, acessível a partir do Linux Mint físico.

## Modelo pretendido em estudo

```text
Ubuntu da mesma VPS
    +-- camada de serviços: Docker, APIs, bancos, agentes
    +-- camada gráfica: desktop, navegador, editor, terminal
```

Os serviços não ficam "dentro do desktop"; desktop e serviços coexistem no mesmo sistema operacional.

## O que não está decidido

- ambiente gráfico;
- protocolo remoto;
- exposição de rede;
- isolamento;
- consumo máximo aceitável;
- se o desktop ficará sempre ativo;
- se uma segunda VPS seria melhor no futuro.

## Nested virtualization

A intenção original de "ter outro Linux Mint dentro da VPS" foi refinada. Uma VM completa dentro da VPS exigiria nested virtualization. O projeto não dependerá disso sem revalidação explícita da capacidade/política do provedor.

## Avaliação obrigatória antes de instalar

- necessidade real;
- RAM/CPU;
- segurança e superfície de ataque;
- latência;
- protocolo e criptografia;
- experiência de uso;
- diferença entre VS Code Remote SSH e desktop remoto completo;
- impacto em serviços de produção;
- recuperação.

## Possível experiência

Uma interface Cinnamon ou outra solução leve pode ser estudada por familiaridade com Linux Mint, mas isso seria Ubuntu com desktop escolhido, não necessariamente uma VM Linux Mint separada.

## Gate

Não instalar GUI antes de concluir inventário e base segura.