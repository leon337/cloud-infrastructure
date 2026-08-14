# FND-SSH-001 — Sessão SSH ociosa fica inoperante

Status: **RESOLVED — KEEPALIVE PERMANENTE VALIDADO NO CLIENTE SSH LOCAL**.

## Sintoma

Sessões SSH normais iniciadas do Linux Mint ficavam aparentemente travadas após alguns minutos sem interação. O prompt permanecia visível, mas não respondia normalmente.

## Evidências contra "VPS inteira travou"

- novas conexões SSH podiam ser abertas imediatamente;
- a VPS continuava alcançável;
- durante diagnóstico, ping ao IPv4 continuou respondendo enquanto uma sessão antiga estava inoperante.

O ping prova alcançabilidade ICMP, não saúde da sessão TCP/SSH específica.

## Hipótese

Estado da conexão SSH ociosa era perdido/invalidado em alguma camada do caminho. Não foi identificado de forma conclusiva se NAT, firewall, roteador, ISP ou outro intermediário era o responsável.

## Teste inválido

O comando de keepalive foi inicialmente executado quando o prompt já era `root@vmi3506102`, isto é, de dentro da VPS. Isso criou SSH dentro de SSH e não testou o caminho Linux Mint → VPS. O resultado foi descartado.

## Teste válido temporário

Origem confirmada: Linux Mint local, prompt `leo@leo-N43SM`.

```bash
ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 root@169.58.171.192
```

A sessão ficou ~3 minutos ociosa. Depois:

```bash
echo vivo
```

Resultado:

```text
vivo
```

Conclusão: o keepalive do cliente manteve a sessão funcional no teste temporário.

## Decisão autorizada

LEANDRO autorizou persistir no cliente local:

```sshconfig
Host contabo-vps
    HostName 169.58.171.192
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

O usuário `root` é temporário.

## Aplicação permanente

No Linux Mint local foi revalidado que `~/.ssh/config` não existia. Em seguida:

1. o arquivo foi criado conscientemente;
2. a permissão foi definida como `600` (`rw-------`);
3. o bloco `Host contabo-vps` foi adicionado;
4. a configuração efetiva foi validada com `ssh -G contabo-vps`;
5. foram confirmados `user root`, `hostname 169.58.171.192`, `serveraliveinterval 30` e `serveralivecountmax 3`.

## Validação permanente

A conexão foi iniciada a partir do Linux Mint local com:

```bash
ssh contabo-vps
```

O alias abriu corretamente a sessão remota `root@vmi3506102`.

Após aproximadamente 3 minutos de ociosidade, na mesma sessão foi executado:

```bash
echo vivo
```

Resultado:

```text
vivo
```

Conclusão: a configuração permanente do keepalive foi validada no cenário que reproduzia o finding.

## Estado final

- mitigação temporária: validada;
- configuração permanente: aplicada no Linux Mint local;
- alias `contabo-vps`: validado;
- teste de ociosidade permanente: validado;
- finding: **RESOLVED**.

## Recovery

Se a configuração local causar problema no futuro, remover ou ajustar somente o bloco `Host contabo-vps`. A VPS não depende de `~/.ssh/config` do Linux Mint para continuar online.
