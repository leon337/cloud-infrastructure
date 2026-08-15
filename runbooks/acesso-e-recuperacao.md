# Runbook — Acesso e Recuperação Inicial

## Canais conhecidos

### SSH — principal

Endpoint operacional: `root@169.58.171.192` durante fase inicial.

Host fingerprint validada: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

Em 15/08/2026, root por senha permanecia como acesso operacional validado. É temporário e não deve ser restringido antes de alternativa e recovery validados.

### Conta ubuntu — ainda não usar como único canal

A conta existe, possui sudo e chave autorizada compatível com a chave pública local, mas o teste atual não concluiu autenticação por chave. O cliente caiu para senha e a senha da conta está bloqueada. Diagnosticar somente com novo HUMAN_GATE; não remover root antes da validação.

### VNC — console alternativo

TigerVNC foi validado historicamente. O estado atual não foi revalidado em 15/08; consultar endpoint/porta no painel antes de usar. Senha VNC é secret e não pertence ao repositório.

O console observado foi `tty1`. Se o teclado brasileiro estiver incorreto:

```bash
loadkeys br
```

### Rescue System — emergência

Conhecido conceitualmente como ambiente Linux temporário. Sua disponibilidade e uso real não foram revalidados na auditoria de 15/08 e permanecem `UNCONFIRMED`.

### LXD — estado recuperado

Após ativação acidental pelo socket durante a auditoria, confirmou-se 0 instâncias. O daemon foi parado com autorização e ficou `inactive/dead`; o socket permaneceu `active/listening`. Não usar `lxc` em auditoria estritamente passiva sem considerar socket activation.

## Verificação de host SSH

Se host key mudar inesperadamente, não aceitar automaticamente. Investigar causa. Em primeiro acesso, a fingerprint foi verificada pelo VNC antes do `yes`.

## Sessão SSH ociosa

Ver `findings/FND-SSH-001.md`.

## Não fazer

- não divulgar senhas;
- não remover acesso atual antes de alternativa validada;
- não mexer no firewall durante recuperação sem entender impacto;
- não usar reinstalação como ferramenta de diagnóstico inicial.
