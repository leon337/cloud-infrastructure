# Runbook — Acesso e Recuperação Inicial

## Canais conhecidos

### SSH — principal

Endpoint operacional: `root@169.58.171.192` durante fase inicial.

Host fingerprint validada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

O `root` é temporário e deverá ser substituído por usuário administrativo próprio em fase posterior.

### VNC — console alternativo

TigerVNC foi validado. Consultar endpoint/porta atuais no painel Contabo antes de usar novamente. Senha VNC é secret e não pertence ao repositório.

O console observado foi `tty1`. Se o teclado brasileiro estiver incorreto:

```bash
loadkeys br
```

### Rescue System — emergência

Conhecido como ambiente Linux temporário para reparar/acessar o disco quando sistema normal não inicia ou acesso normal falha. Ainda não foi acionado nesta missão.

## Verificação de host SSH

Se host key mudar inesperadamente, não aceitar automaticamente. Investigar causa. Em primeiro acesso, a fingerprint foi verificada pelo VNC antes do `yes`.

## Sessão SSH ociosa

Ver `findings/FND-SSH-001.md`.

## Não fazer

- não divulgar senhas;
- não remover acesso atual antes de alternativa validada;
- não mexer no firewall durante recuperação sem entender impacto;
- não usar reinstalação como ferramenta de diagnóstico inicial.