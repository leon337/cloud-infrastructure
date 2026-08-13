# Cloud Infrastructure

Repositório canônico da infraestrutura em nuvem de LEANDRO.

## Objetivo

Documentar, versionar e tornar reproduzível a configuração da infraestrutura da VPS, incluindo segurança, armazenamento, acesso remoto, Docker, serviços, recuperação, observabilidade e evolução futura.

Este repositório é separado do MCF. O repositório `leon337/multiagent-collaboration-framework` permanece independente e não deve receber implementação específica desta VPS sem autorização explícita de LEANDRO.

## Princípios da missão

A infraestrutura deve otimizar simultaneamente:

- segurança;
- funcionalidade;
- aprendizado;
- autonomia.

Uma etapa somente é considerada concluída quando:

1. funcionou;
2. foi validada;
3. foi documentada;
4. LEANDRO entendeu.

## Estado inicial conhecido

- Provedor: Contabo
- Produto: Cloud VPS 8
- Sistema: Ubuntu 24.04 LTS
- Recursos contratados: 8 vCPU, 24 GB RAM, 300 GB SSD
- VPS já provisionada e em execução
- IPv4 público disponível
- Senha root inicial deve ser tratada como comprometida
- Repositório: privado

## Objetivos arquitetônicos

A mesma VPS poderá ser estudada para dois papéis complementares:

1. **Servidor de infraestrutura**
   - Docker
   - APIs
   - bancos de dados
   - MCPs
   - agentes
   - automações
   - aplicações

2. **Cloud Workstation**
   - interface gráfica remota
   - navegador
   - VS Code
   - terminal
   - arquivos e ferramentas de trabalho

A adoção de desktop gráfico ainda não está aprovada; será avaliada depois da base segura e do inventário.

## Política de segurança do repositório

É proibido versionar secrets reais, incluindo:

- senhas;
- chaves SSH privadas;
- tokens;
- API keys;
- códigos 2FA;
- connection strings reais;
- credenciais da Contabo;
- arquivos `.env` com valores reais.

Quando necessário, utilizar placeholders como `<IP_DO_SERVIDOR>`, `<USUARIO>`, `<DOMINIO>` e arquivos de exemplo como `.env.example`.

## Estrutura inicial

- `docs/` — tutorial canônico e visão técnica
- `decisions/` — decisões arquitetônicas
- `recovery/` — recuperação e incidentes
- `scripts/` — automações administrativas futuras
- `docker/` — infraestrutura Docker futura
- `config/` — configurações versionáveis e sanitizadas
- `examples/` — exemplos sem dados sensíveis

## Fase atual

**FASE 0 — ORIENTAÇÃO E INVENTÁRIO**

Nenhuma alteração técnica na VPS deve ocorrer antes do inventário seguro e da compreensão de LEANDRO.
