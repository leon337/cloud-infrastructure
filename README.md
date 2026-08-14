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

## Estado confirmado

- Provedor: Contabo
- Produto: Cloud VPS 8
- Sistema observado: Ubuntu 24.04.4 LTS
- Recursos contratados: 8 vCPU, 24 GB RAM, 300 GB SSD
- VPS provisionada e em execução
- Repositório: privado
- senha `root` inicial descartada e rotacionada
- console VNC validado com TigerVNC
- fingerprint SSH ED25519 verificada por canal independente
- primeiro login SSH com `root` validado
- hostname atual: `vmi3506102`
- kernel observado: `Linux 6.8.0-137-generic`
- virtualização confirmada: KVM/QEMU
- 8 CPUs lógicas visíveis
- aproximadamente 23 GiB de RAM visíveis
- swap atualmente ausente (`0 B`)

Checkpoint de continuidade atual: [`CHECKPOINT.md`](CHECKPOINT.md).

Detalhes do primeiro acesso seguro: [`docs/01-primeiro-acesso-seguro.md`](docs/01-primeiro-acesso-seguro.md).

## Achado operacional atual

### FND-SSH-001 — sessão SSH ociosa

Sessões SSH normais ficaram aparentemente inoperantes após alguns minutos de ociosidade. Um teste iniciado corretamente no Linux Mint local com:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 root@<IP_DA_VPS>
```

permaneceu funcional após aproximadamente 3 minutos sem atividade e respondeu a `echo vivo`.

LEANDRO autorizou tornar o keepalive permanente no cliente SSH local. A alteração ainda está pendente e deve ser feita no próximo chat após inspeção de `~/.ssh/config`.

Modelo sanitizado: [`config/ssh_config.example`](config/ssh_config.example).

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

- `CHECKPOINT.md` — estado canônico de retomada entre chats
- `docs/` — tutorial canônico e visão técnica
- `decisions/` — decisões arquitetônicas
- `recovery/` — recuperação e incidentes
- `scripts/` — automações administrativas futuras
- `docker/` — infraestrutura Docker futura
- `config/` — configurações versionáveis e sanitizadas
- `examples/` — exemplos sem dados sensíveis

## Fase atual

**FASE 0 — ORIENTAÇÃO E INVENTÁRIO**

Etapas concluídas:

- 0.1 — modelo mental da infraestrutura;
- 0.2 — repositório canônico separado do MCF;
- 0.3 — preparação do primeiro acesso;
- 0.4 — primeiro acesso seguro via VNC + SSH.

Etapa em andamento:

- **0.5 — inventário real da VPS**.

Próxima ação autorizada:

- aplicar keepalive permanente no `~/.ssh/config` do Linux Mint local;
- validar o alias/conexão;
- continuar inventário de armazenamento, filesystems, mounts, rede e uptime.
