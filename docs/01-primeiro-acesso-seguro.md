# 01 — Primeiro Acesso Seguro

## Status

Checkpoint concluído em 2026-08-13.

A VPS foi acessada e validada por dois canais independentes:

- SSH — acesso administrativo normal;
- VNC/TigerVNC — console alternativo e caminho de recuperação.

Nenhuma senha, token, chave privada ou outra credencial real deve ser registrada neste documento.

## Ambiente confirmado

- Provedor: Contabo
- Produto: Cloud VPS 8
- Sistema observado no console: Ubuntu 24.04.4 LTS
- Identificação observada: `vmi3506102`
- Usuário inicial: `root`
- IPv4 público: conhecido e mantido fora deste documento operacional

## Credencial root

A senha `root` inicial foi tratada como comprometida e rotacionada pelo Customer Panel da Contabo.

Durante o processo, uma credencial antiga foi deliberadamente exposta e posteriormente descartada. Ela não deve ser reutilizada.

A senha `root` vigente foi validada com sucesso, mas seu valor NÃO é versionado.

## VNC

O VNC da Contabo estava habilitado.

### Cliente local

No Linux Mint local foram instalados para diagnóstico:

- Remmina;
- `remmina-plugin-vnc`;
- TigerVNC Viewer.

O Remmina alcançou o serviço VNC, mas não concluiu a sessão neste teste. O TigerVNC Viewer concluiu a autenticação e abriu o console da VPS com sucesso.

Isso não estabelece que o Remmina seja incompatível em geral; registra somente o comportamento observado neste ambiente e nesta data.

### Credencial VNC

A senha VNC é independente da senha `root`.

A Contabo exigiu exatamente 8 caracteres alfanuméricos para essa credencial no fluxo observado.

O valor da senha VNC NÃO é versionado.

### Console

O TigerVNC abriu o console `tty1` do Ubuntu. O layout de teclado inicial não correspondia ao teclado brasileiro do computador local.

O comando abaixo ajustou o mapa do console para o teste atual:

```bash
loadkeys br
```

Esse ajuste foi usado para permitir digitação correta de caracteres como `/` no console.

## Verificação independente da identidade SSH

Na primeira tentativa SSH, o cliente local apresentou uma chave de host ED25519 ainda desconhecida.

A conexão foi cancelada antes da aceitação automática.

Em seguida, pelo console VNC já autenticado, foi executado:

```bash
ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub
```

Fingerprint verificada em 2026-08-13:

```text
SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4
```

A fingerprint obtida diretamente na VPS por VNC coincidiu exatamente com a fingerprint apresentada pelo SSH no Linux Mint.

Somente depois dessa comparação a chave de host foi aceita no cliente SSH local e registrada em `~/.ssh/known_hosts`.

## Primeiro login SSH validado

O primeiro login SSH foi concluído com sucesso usando o usuário inicial `root` e a senha já rotacionada.

Fluxo validado:

```text
Linux Mint local
    |
    | SSH
    v
VPS Contabo
    |
    v
Ubuntu 24.04.4 LTS
    |
    v
root@vmi3506102
```

## Canais de acesso e recuperação conhecidos

### SSH

Canal administrativo normal. Validado.

### VNC

Console alternativo fornecido pela Contabo. Validado com TigerVNC.

### Rescue System

Conhecido conceitualmente e disponível no Customer Panel, mas ainda não acionado. Deve ser usado como ambiente temporário de recuperação quando o sistema principal não inicia ou o acesso normal está indisponível.

## Estado de segurança

O acesso inicial funciona, mas a VPS ainda NÃO deve ser considerada endurecida para produção.

Fotografia atual de 15/08/2026:

- inventário técnico concluído e revalidado;
- `ubuntu` existe e possui sudo, inclusive NOPASSWD por cloud-init;
- uma nova chave ED25519 dedicada foi criada localmente e sua chave pública foi adicionada sem remover a chave antiga;
- autenticação atual de `ubuntu` foi validada exclusivamente por `publickey`, confirmando UID 1000 e hostname `vmi3506102`;
- root/senha permanece operacional, validado e temporariamente preservado;
- política SSH, sudo, firewall e LXD não foram alterados pela validação;
- UFW está inativo;
- backup independente e recovery do provedor não foram validados.

## Próxima etapa

**FASE 1 — acesso administrativo, recovery e segurança mínima.**

Próximo micro-passo recomendado: revisão read-only de sudo e do privilégio equivalente a root via LXD, somente após novo HUMAN_GATE. Esta seção substitui apenas o estado atual; o restante do documento preserva a história do primeiro acesso.
