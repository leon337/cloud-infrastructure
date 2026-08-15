# 02 — Missão e Escopo

## Missão

Configurar, proteger, documentar e ensinar a administração da nova VPS de LEANDRO.

O objetivo final não é apenas deixar um servidor funcionando. É permitir que LEANDRO consiga, progressivamente, **repetir, manter, diagnosticar, recuperar e reconstruir** o ambiente com mínima dependência de IA.

## Objetivos originais da missão

1. configurar corretamente a VPS;
2. endurecer a segurança;
3. organizar armazenamento, usuários, rede e serviços;
4. transformar a VPS em infraestrutura para projetos;
5. criar modelo híbrido entre computador físico e VPS;
6. usar a VPS como ambiente remoto de desenvolvimento;
7. entregar desktop/computador na nuvem logo após acesso administrativo, recovery e segurança mínima;
8. instalar e administrar Docker e serviços;
9. preparar infraestrutura para MCF, MCPs, APIs, agentes, automações e aplicações;
10. ensinar Linux, servidores, redes, segurança, Docker e cloud durante o processo;
11. produzir tutorial canônico reutilizável no GitHub.

## Princípios

Segurança + Funcionalidade + Aprendizado + Autonomia.

Se velocidade conflitar com aprendizado, preferir aprendizado, salvo urgência de segurança. Se houver risco de perda de acesso ou dados, parar e explicar.

## Definition of Done didática

Uma etapa não termina porque o comando funcionou. Ela termina quando:

1. foi executada;
2. foi validada;
3. foi explicada;
4. LEANDRO entendeu;
5. foi documentada;
6. quando necessário, LEANDRO autorizou avançar.

## Infraestrutura contratada originalmente

- Contabo Cloud VPS 8;
- 8 vCPU;
- 24 GB RAM;
- 300 GB SSD;
- 3 snapshots incluídos;
- 600 Mbit/s;
- tráfego ilimitado;
- região European Union;
- contrato mensal;
- Ubuntu 24.04 LTS escolhido;
- usuário inicial root.

Esses dados de contratação podem mudar no futuro e devem ser revalidados antes de decisões de custo/capacidade.

## Escopo futuro

A VPS poderá hospedar gradualmente desenvolvimento remoto, Docker, APIs, MCF, MCPs, agentes, automações, n8n, dashboards, monitoramento, reverse proxy, aplicações, serviços internos, produtos e eventualmente serviços de clientes.

## Prioridade operacional atual

Por limitações do computador local, a Cloud Workstation é a próxima grande entrega após os pré-requisitos mínimos de acesso, recovery e segurança. Sua Definition of Done inclui produtividade real e HUMAN_GATE de LEANDRO, não apenas desktop visível.

## Fora do escopo imediato

Não instalar tudo no início. Não particionar por padrão. Não instalar Docker antes da base. Não desativar root/senha antes de outro acesso validado. Não instalar desktop gráfico antes da avaliação e dos gates dedicados.
