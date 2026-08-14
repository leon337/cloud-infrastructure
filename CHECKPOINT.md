# CHECKPOINT — IMPLEMENTAÇÃO DA VPS

Atualizado em 2026-08-14.

Este arquivo é o ponto canônico de retomada entre chats. Nenhum secret real deve ser registrado aqui.

## Regra de continuidade

Antes de qualquer ação, o próximo chat deve consultar o estado REAL do repositório e ler integralmente este arquivo, o `README.md`, `docs/00-visao-geral.md` e `docs/01-primeiro-acesso-seguro.md`.

Não pedir novamente informações operacionais já registradas aqui. Não presumir que placeholders substituem dados não secretos já conhecidos.

## Estado da missão

- Projeto: implementação e aprendizado da infraestrutura VPS.
- Repositório canônico: `leon337/cloud-infrastructure`.
- Repositório separado do MCF.
- Fase atual: **FASE 0 — ORIENTAÇÃO E INVENTÁRIO**.
- Etapa atual: **0.5 — inventário real da VPS**.

Etapas concluídas:

- 0.1 — modelo mental da infraestrutura;
- 0.2 — repositório canônico separado do MCF;
- 0.3 — preparação do primeiro acesso;
- 0.4 — primeiro acesso seguro via VNC + SSH.

## Identificadores operacionais já conhecidos — NÃO são secrets

- Provedor: Contabo.
- Produto: Cloud VPS 8.
- IPv4 público da VPS: `169.58.171.192`.
- Hostname atual da VPS: `vmi3506102`.
- Usuário administrativo usado temporariamente nesta fase: `root`.
- Linux Mint local observado: usuário/host `leo@leo-N43SM`.
- Alias SSH planejado: `contabo-vps`.

O IPv4 público e a fingerprint de host são identificadores operacionais, não senhas. Podem ser registrados no repositório privado. Senhas, chaves privadas, tokens e demais secrets continuam proibidos.

## Acesso validado

- SSH funcional.
- VNC funcional com TigerVNC.
- Remmina alcançou o serviço VNC, mas não concluiu a sessão no teste realizado.
- A fingerprint ED25519 do host SSH foi verificada por canal independente via VNC antes de ser aceita no Linux Mint local.
- Fingerprint ED25519 verificada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.
- A chave do host foi registrada conscientemente no `known_hosts` local.
- A senha `root` vigente funciona, mas seu valor NÃO é versionado nem deve ser solicitado no chat.
- Se VNC for necessário novamente, consultar o endpoint atual no painel da Contabo em vez de presumir que uma porta observada anteriormente continua válida.

## Inventário confirmado até agora

### Sistema

- Sistema operacional: Ubuntu 24.04.4 LTS.
- Codinome: Noble Numbat (`noble`).
- Hostname atual: `vmi3506102`.
- Kernel: `Linux 6.8.0-137-generic`.
- Arquitetura: `x86-64`.

### Virtualização

- Chassis: VM.
- Hypervisor: KVM.
- Hardware virtual apresentado por QEMU.

### CPU

- 8 CPUs lógicas visíveis (`0-7`).
- Modelo apresentado à VM: AMD EPYC Processor (with IBPB).
- 1 socket virtual.
- 8 cores por socket.
- 1 thread por core.

### Memória

Observação feita com `free -h`:

- RAM total visível: aproximadamente 23 GiB.
- RAM usada no momento do teste: aproximadamente 592 MiB.
- RAM disponível no momento do teste: aproximadamente 22 GiB.
- Swap: **0 B** — nenhuma swap configurada no momento.

## FND-SSH-001 — sessão SSH ociosa

### Sintoma observado

Sessões SSH normais, iniciadas do Linux Mint local, ficaram aparentemente inoperantes após alguns minutos de ociosidade. A VPS continuou alcançável e novas conexões SSH puderam ser abertas imediatamente.

### Teste inválido que NÃO deve ser repetido

Em uma tentativa anterior, o comando de teste de keepalive foi executado dentro da própria VPS, criando SSH dentro de SSH. Esse teste foi identificado como inválido e não deve ser usado como evidência.

### Teste válido realizado

A partir do **Linux Mint local**, com prompt semelhante a `leo@leo-N43SM:~$`, foi aberta uma sessão com:

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 root@169.58.171.192
```

Após aproximadamente 3 minutos sem atividade manual, foi executado:

```bash
echo vivo
```

Resultado:

```text
vivo
```

Conclusão operacional: o keepalive do cliente SSH manteve funcional a sessão no teste de ociosidade realizado.

## Decisão autorizada — keepalive permanente

LEANDRO já autorizou tornar o keepalive permanente no **Linux Mint local** usando `~/.ssh/config`.

**A configuração permanente ainda NÃO foi aplicada.**

### Primeira ação obrigatória no próximo chat

Antes de editar qualquer arquivo, confirmar que o terminal é LOCAL (`leo@leo-N43SM:~$`) e inspecionar de forma somente leitura o estado atual de `~/.ssh/config`.

Sugestão de primeira verificação, executada no Linux Mint LOCAL:

```bash
test -f "$HOME/.ssh/config" && sed -n '1,220p' "$HOME/.ssh/config" || echo "~/.ssh/config ainda não existe"
```

Depois, analisar o resultado junto com LEANDRO.

### Regra crítica de edição

**NÃO usar `cat > ~/.ssh/config` nem qualquer comando que sobrescreva o arquivo inteiro sem antes inspecioná-lo.**

Se o arquivo já existir, preservar todas as entradas existentes e adicionar/atualizar somente o bloco desta VPS. Se não existir, criar conscientemente o arquivo. Depois definir permissão `600` e validar a configuração antes do uso.

Configuração já definida para esta VPS:

```sshconfig
Host contabo-vps
    HostName 169.58.171.192
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

O usuário `root` é temporário e deverá ser substituído posteriormente por um usuário administrativo próprio.

Modelo versionado: `config/ssh_config.example`.

### Validação esperada após aplicação

1. Validar sintaxe/configuração do cliente SSH.
2. Conectar a partir do Linux Mint local com:

```bash
ssh contabo-vps
```

3. Deixar a sessão ociosa por aproximadamente 3 minutos.
4. Executar `echo vivo`.
5. Somente considerar a correção permanente validada se a sessão responder normalmente.

## Pendências imediatas

1. Inspecionar e aplicar com segurança o keepalive permanente no `~/.ssh/config` do Linux Mint local.
2. Validar `ssh contabo-vps` após o período de ociosidade.
3. Continuar a Etapa 0.5 com inventário de armazenamento e filesystems.
4. Inventariar mounts.
5. Inventariar rede.
6. Inventariar uptime e estado básico.
7. Registrar o inventário completo antes de qualquer hardening estrutural.

## Pendências posteriores de segurança

Ainda não executar sem etapa própria e autorização:

- criar usuário administrativo próprio;
- configurar `sudo`;
- configurar autenticação SSH por chave;
- decidir política para login direto de `root`;
- configurar firewall;
- decidir política permanente para VNC;
- decidir política de swap;
- estruturar backup, snapshots e recovery playbook;
- avaliar desktop gráfico / Cloud Workstation somente depois da base segura.

## Regras de interação para continuidade

- Explicar antes de alterar.
- Uma etapa por vez.
- Diferenciar explicitamente **Linux Mint LOCAL** de **VPS REMOTA** em todos os comandos importantes.
- Não presumir conhecimento prévio de LEANDRO.
- Não pedir novamente IP, hostname ou fingerprint já registrados neste checkpoint.
- Não registrar secrets reais.
- Não fazer alteração estrutural sem autorização de LEANDRO.
- Quando um teste falhar, diagnosticar antes de trocar múltiplas variáveis.

## Ponto exato de retomada

**FASE 0 → ETAPA 0.5 → no Linux Mint LOCAL, inspecionar `~/.ssh/config`; depois aplicar o bloco `Host contabo-vps` com `HostName 169.58.171.192`, validar keepalive permanente e então continuar o inventário.**
