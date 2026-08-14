# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo responde principalmente: **onde estamos agora?** O contexto permanente está distribuído conforme `CONTEXT.md`.

## Gate de continuidade

O PUC v1.0 foi implantado e validado em novo chat usando somente o GitHub canônico.

**Resultado: CONTINUIDADE COMPLETA.**

Evidência: `governance/CONTINUITY-VALIDATION-2026-08-14.md`.

A retomada operacional está liberada, respeitando HUMAN_GATEs e autorizações já registrados.

## Estado atual

- Repositório: `leon337/cloud-infrastructure`.
- **FASE 0 — ORIENTAÇÃO E INVENTÁRIO: DONE.**
- Etapas 0.1 a 0.5: `DONE`.
- PUC v1.0: `DONE`.
- **FASE 1 — Base do sistema e segurança inicial: IN_PROGRESS.**
- Item `atualizações iniciais`: baseline concluída sem forçar updates adiados por phasing.
- `HG-F1-APT-UPDATE-001`: **AUTORIZADO E EXECUTADO COM SUCESSO**.
- `apt update`: executado com sucesso; índices APT atualizados; nenhum upgrade instalado.
- `apt list --upgradable`: 5 pacotes Krb5 permaneceram disponíveis, todos de `1.20.1-6ubuntu2.7` para `1.20.1-6ubuntu2.8`.
- `apt-get -s upgrade`: simulação concluída; `0 upgraded, 0 newly installed, 0 to remove and 5 not upgraded`.
- Motivo informado pelo APT: `The following upgrades have been deferred due to phasing`.
- Não foi executado contorno de phased updates e nenhum pacote foi forçado.
- Próximo item da FASE 1: **usuário administrativo próprio**, começando por inspeção somente leitura das contas atuais.

## Escopo da FASE 1

Conforme o Plano Mestre:

1. atualizações iniciais — baseline atual concluída com phased updates respeitados;
2. usuário administrativo próprio — próximo item;
3. sudo;
4. estratégia de SSH;
5. chave SSH;
6. validação de acesso por chave;
7. política de root;
8. política de senha SSH;
9. menor privilégio.

A sequência será executada em pequenos passos. Não desativar acesso existente antes de validar a alternativa correspondente.

## Identificadores operacionais

- VPS: Contabo Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Usuário administrativo temporário: `root`.
- Linux Mint local observado: `leo@leo-N43SM`.
- Alias SSH: `contabo-vps`.
- Fingerprint ED25519 validada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

## Atualizações APT observadas

Pacotes ainda listados como atualizáveis após `apt update`:

- `krb5-locales`;
- `libgssapi-krb5-2`;
- `libk5crypto3`;
- `libkrb5-3`;
- `libkrb5support0`.

Versão instalada observada: `1.20.1-6ubuntu2.7`.
Versão candidata observada: `1.20.1-6ubuntu2.8`.

A simulação padrão não selecionou nenhum deles para instalação porque o APT os adiou por phasing. Não forçar esse mecanismo sem decisão explícita e justificativa própria.

## Base técnica herdada da FASE 0

- Ubuntu 24.04.4 LTS — Noble Numbat.
- Kernel: `Linux 6.8.0-137-generic`.
- Arquitetura: x86-64.
- Virtualização KVM com hardware virtual QEMU.
- CPU: 8 lógicas.
- RAM visível: ~23 GiB.
- Swap: 0 B.
- Disco principal: `/dev/sda`, 300 GiB, GPT.
- Raiz: ext4 em `/dev/sda1`, ~2.4G usados e ~288G disponíveis na medição.
- Interface principal: `eth0`, `UP`.
- IPv4: `169.58.171.192/17`.
- IPv6 global: `2a02:c207:2350:6102::1/64`.
- `sshd` em TCP 22 para IPv4 e IPv6.
- `systemd`: `running`, 0 unidades failed na medição.
- Timezone observado: `Europe/Berlin`.
- NTP ativo e relógio sincronizado.

Detalhes permanentes: `docs/06-inventario.md`.

## Acesso e recovery conhecidos

- SSH root validado.
- Alias `contabo-vps` validado.
- Keepalive permanente aplicado e validado.
- `FND-SSH-001`: **RESOLVED**.
- VNC/TigerVNC validado.
- Rescue System conhecido, não acionado.

Princípio: nenhuma melhoria de segurança deve criar risco maior de perda de acesso sem caminho de recuperação validado.

## Ponto exato de retomada

**FASE 1 em andamento. Atualizações iniciais avaliadas; nenhum upgrade foi instalado porque os 5 candidatos foram adiados pelo phasing padrão do APT.**

Próximo passo operacional é somente leitura: inspecionar quais contas locais de usuário humano já existem antes de decidir qualquer criação de usuário administrativo.

Depois dessa inspeção, qualquer criação de usuário ou alteração de `sudo` exigirá explicação e HUMAN_GATE próprio.

## Proibições imediatas

Não executar ainda sem etapa própria e autorização:

- forçar phased updates;
- `apt upgrade` com override de phasing;
- criação/alteração de usuário administrativo;
- mudança de sudo;
- política de root;
- desativação de senha SSH;
- firewall;
- particionamento ou alteração destrutiva de disco;
- alterações de swap;
- instalação de Docker;
- desktop gráfico;
- hardening em lote.

## Próxima leitura obrigatória

Qualquer novo chat deve começar em `CONTEXT.md`, não neste arquivo isoladamente.
