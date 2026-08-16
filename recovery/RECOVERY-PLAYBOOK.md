# Recovery Playbook — versão viva

## Perdi acesso SSH

1. confirmar no painel se a VPS está em execução;
2. confirmar a fingerprint sem aceitá-la automaticamente;
3. usar VNC Contabo validado para observar console/boot;
4. conferir `sshd`, UFW e rede pelo console;
5. se o sistema não iniciar, avaliar Rescue disponível;
6. não reinstalar nem restaurar sem gate explícito.

## Cloud Workstation não conecta

1. validar primeiro `ssh contabo-vps`;
2. iniciar o túnel `ssh -N contabo-vps-rdp`;
3. confirmar localmente `127.0.0.1:13389`;
4. na VPS, XRDP deve estar somente em `127.0.0.1:3389` e sesman em `[::1]:3350`;
5. verificar `xrdp`, `xrdp-sesman`, `lightdm` e logs sem publicar RDP;
6. se a sessão estiver corrompida, encerrar somente a sessão gráfica afetada e reconectar.

## Firewall bloqueou acesso

Pelo VNC, revisar UFW. Estado esperado: ativo, default deny incoming e somente OpenSSH 22 permitido. Fazer rollback pequeno; não desativar permanentemente a proteção.

## Restaurar configurações

1. escolher um arquivo em `/var/backups/cloud-infrastructure` ou na cópia off-host;
2. validar SHA-256 e listar/extrair em diretório temporário;
3. comparar o arquivo necessário;
4. restaurar somente o componente afetado;
5. validar sintaxe antes de recarregar serviço.

A extração de recuperação foi testada com 24 arquivos, mas um restore real não foi necessário. Dados de usuário/workloads não estão cobertos por esse backup.

## LXD

Estado esperado: `ubuntu` fora do grupo `lxd`, daemon/socket desabilitados e inativos. Antes de qualquer reativação, confirmar necessidade e risco root-equivalent.

## Atualização/reboot

Antes: validar SSH/VNC, backup e ausência de operação crítica. Depois: validar SSH, UFW, fail2ban, XRDP, LightDM, LXD inativo e login gráfico.

## Reconstrução

Meta posterior: reconstruir a VPS a partir do repositório, backups e runbooks. Esta validação ampla ainda está pendente.
