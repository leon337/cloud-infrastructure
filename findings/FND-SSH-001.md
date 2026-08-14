# FND-SSH-001 — Sessão SSH ociosa fica inoperante

Status: **MITIGAÇÃO TEMPORÁRIA VALIDADA; CORREÇÃO PERMANENTE AUTORIZADA E PENDENTE**.

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

## Teste válido

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

## Conclusão

O keepalive do cliente manteve a sessão funcional no teste realizado.

## Decisão

LEANDRO autorizou persistir no cliente local:

```sshconfig
Host contabo-vps
    HostName 169.58.171.192
    User root
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

O usuário `root` é temporário.

## Estado local mais recente

Auditoria em chat de continuidade relatou inspeção somente leitura e resultado: `~/.ssh/config` ainda não existe.

## Validação permanente exigida

Depois de criar configuração:

1. validar sintaxe/config efetiva;
2. `ssh contabo-vps`;
3. ~3 minutos ocioso;
4. `echo vivo`;
5. somente então marcar `RESOLVED`.

## Recovery

Se configuração causar problema, remover/ajustar somente o bloco local. A VPS não depende desse arquivo para continuar online.