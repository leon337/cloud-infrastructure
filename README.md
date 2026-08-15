# Cloud Infrastructure

Repositório canônico da missão **IMPLEMENTAÇÃO DA VPS**.

> Nova IA/agente? Comece por [`CONTEXT.md`](CONTEXT.md).

## Finalidade

Configurar, proteger, documentar e tornar reproduzível a VPS enquanto LEANDRO aprende a administrar, diagnosticar, recuperar e reconstruir o ambiente com mínima dependência de IA.

O projeto é separado do MCF. A VPS poderá servir MCF e outros sistemas, mas a infraestrutura não pertence estruturalmente ao framework.

Os quatro objetivos simultâneos são segurança, funcionalidade, aprendizado e autonomia. Uma etapa só termina quando funcionou, foi validada, documentada, explicada e recebeu o gate aplicável.

## Continuidade

O repositório implementa o PUC v1.0:

- `CONTEXT.md` — porta de entrada;
- `CHECKPOINT.md` — estado imediato;
- `state/current.yaml` — resumo legível por máquinas;
- `docs/` — missão, arquitetura, plano, roadmap e inventário;
- `decisions/`, `findings/`, `history/` — decisões, achados e causalidade;
- `runbooks/` e `recovery/` — operação e recuperação;
- `assets/` — evidências visuais e imagens conceituais segregadas;
- `governance/` — protocolo, cobertura, auditoria e validações.

Chats são temporários; o GitHub é a memória canônica após revisão e commit.

## Estado reconciliado em 15/08/2026

- Fase 0 e auditoria read-only Fase B: concluídas.
- Fase atual: **F1 — acesso administrativo, recovery e segurança mínima**.
- Root por senha: acesso operacional validado, ainda temporário.
- `ubuntu`: UID 1000 e login atual **VALIDATED** por nova chave dedicada, exclusivamente via `publickey`; a Missão 4 confirmou elevação direta a root por sudo/NOPASSWD e caminho equivalente a root pelo socket LXD.
- A chave antiga de `ubuntu` foi preservada; root/senha continua validado, temporário e ainda não deve ser restringido.
- UFW: instalado e inativo; tentativas automatizadas contra SSH confirmadas.
- LXD: 0 instâncias na auditoria; daemon `inactive/dead`; socket `root:lxd` modo `660`, ativo e gravável por `ubuntu`; `FND-LXD-001` permanece aberto/high.
- Updates: cinco pacotes Krb5 adiados por phasing; nenhum upgrade forçado.
- Backup/recovery do provedor: não confirmado na Fase B.
- Cloud Workstation: **PRIORITY_PLANNED**, próxima grande entrega após os pré-requisitos da F1.

## Cloud Workstation

A solução gráfica será validada como ferramenta de produtividade: navegador, VS Code, terminal, gerenciador de arquivos, múltiplas janelas, copiar/colar, resolução, estabilidade, reconexão, latência percebida e recursos. Somente HUMAN_GATE de LEANDRO conclui essa entrega.

## Segurança

Nunca versionar senhas, passphrases, chaves privadas, tokens, API keys, 2FA ou credenciais. O próximo micro-passo é a revisão read-only de recovery proporcional e dos caminhos de recuperação, somente após novo HUMAN_GATE.
