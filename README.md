# Cloud Infrastructure

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Nova IA/agente? Comece por [`CONTEXT.md`](CONTEXT.md).

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a infraestrutura da VPS, enquanto LEANDRO aprende progressivamente a administrar, diagnosticar, recuperar e reconstruir o ambiente com o mínimo possível de dependência de IA.

O projeto é separado do MCF. A VPS poderá servir MCF e outros sistemas, mas a infraestrutura não pertence estruturalmente ao framework.

## Quatro objetivos simultâneos

- segurança;
- funcionalidade;
- aprendizado;
- autonomia.

Uma etapa só termina quando **funcionou + foi validada + foi documentada + LEANDRO entendeu**.

## Continuidade entre chats

O repositório implementa o **PUC v1.0 — Protocolo Universal de Continuidade**.

- `CONTEXT.md` — porta de entrada universal;
- `CHECKPOINT.md` — estado atual;
- `state/current.yaml` — estado resumido legível por máquinas;
- `governance/` — protocolo, cobertura e revisão crítica;
- `docs/` — missão, arquitetura, plano, roadmap, inventário e tutorial;
- `decisions/` — decisões persistentes;
- `findings/` — problemas/achados técnicos;
- `history/` — histórico resumido de sessões;
- `runbooks/` — procedimentos operacionais;
- `recovery/` — recuperação;
- `config/` — exemplos versionáveis sem secrets.

Chats são sessões temporárias; o GitHub é a memória canônica.

## Estado resumido

- Provedor: Contabo.
- Produto: Cloud VPS 8.
- Contratação original: 8 vCPU, 24 GB RAM, 300 GB SSD, 3 snapshots incluídos, 600 Mbit/s, tráfego ilimitado, região EU, contrato mensal.
- Sistema confirmado: Ubuntu 24.04.4 LTS.
- Fase atual: FASE 0 — ORIENTAÇÃO E INVENTÁRIO.
- Etapa atual: 0.5 — Inventário real da VPS.
- Primeiro acesso seguro: validado por SSH e VNC/TigerVNC.
- Finding ativo: `FND-SSH-001`.
- Keepalive permanente: autorizado, ainda pendente.

## Objetivos de longo prazo

A VPS deverá ser preparada gradualmente para:

- desenvolvimento remoto;
- Docker e Docker Compose;
- APIs e aplicações;
- MCF;
- servidores MCP;
- agentes e automações;
- n8n;
- dashboards;
- reverse proxy/TLS;
- observabilidade;
- serviços internos e futuros produtos;
- eventual Cloud Workstation gráfica, após avaliação específica.

## Segurança

Nunca versionar senhas, chaves privadas, tokens, API keys, 2FA, connection strings reais ou credenciais sensíveis. IP público, hostname, alias e fingerprint de host SSH são identificadores operacionais e podem ser documentados.

## Retomada

Não continue a missão a partir deste README isoladamente. Leia [`CONTEXT.md`](CONTEXT.md) e siga a ordem canônica.