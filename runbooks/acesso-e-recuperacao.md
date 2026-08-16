# Runbook — Acesso e recuperação

## SSH administrativo

Canal atual: `ubuntu@169.58.171.192` por chave dedicada. Fingerprint do host: `SHA256:sb3hPt85xBueteG/kVVVXZs1Wf/KCO3DSeY25fvGkj4`.

O servidor não aceita root, senha ou keyboard-interactive por SSH. Não alterar `known_hosts` diante de fingerprint inesperada.

## Cloud Workstation

Exemplo usando `config/ssh_config.example`:

```bash
ssh -N contabo-vps-rdp
```

Com o túnel ativo, abrir Remmina/FreeRDP em `127.0.0.1:13389`, protocolo RDP, usuário `ubuntu`. Não publicar 3389 nem criar regra UFW para RDP.

Fechar o cliente preserva a sessão; logout cria uma sessão limpa no próximo login. Clipboard e resolução dinâmica foram validados.

## Sudo

`ubuntu` pertence a `sudo`, mas exige senha. `sudo -n` deve falhar. Não reintroduzir `NOPASSWD:ALL`.

## VNC/Rescue

- VNC Contabo: console out-of-band validado; sua credencial é independente e nunca deve ser versionada.
- Rescue: disponível no painel, não acionado. Usar somente em incidente real com gate próprio.

## Backup proporcional

- timer: `cloud-infrastructure-config-backup.timer`;
- cópias remotas: `/var/backups/cloud-infrastructure`;
- cópia off-host inicial: `/home/leo/Backups/cloud-infrastructure`;
- retenção remota: sete arquivos;
- conteúdo: configurações sanitizadas e estado técnico, sem chaves privadas ou senhas.

Verificar timer, arquivo e hash antes de depender do backup. O backup atual não cobre dados completos de usuários/workloads.

## Não fazer

- não expor RDP à Internet;
- não remover a chave validada antes de testar uma substituta;
- não reativar LXD/NOPASSWD sem decisão;
- não aceitar host key alterada automaticamente;
- não registrar senhas, passphrases ou chaves privadas.
