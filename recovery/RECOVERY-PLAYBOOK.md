# Recovery Playbook — versão viva

Objetivo: permitir que LEANDRO recupere a infraestrutura, não apenas saiba instalá-la.

## Cenários

### Perdi acesso SSH

1. confirmar se VPS está em execução no painel;
2. testar alcançabilidade sem assumir que ping prova SSH;
3. consultar `FND-SSH-001` se o problema for sessão ociosa;
4. consultar no painel se VNC/TigerVNC está realmente disponível; a validação é histórica e não foi repetida em 15/08;
5. confirmar e avaliar Rescue System; seu estado atual não foi revalidado;
6. não reinstalar por impulso.

### Host key SSH mudou

Parar. Não aceitar automaticamente. Verificar se houve reinstalação/migração legítima ou risco de identidade incorreta. Conferir por canal independente.

### Firewall bloqueou acesso

Procedimento detalhado será preenchido quando firewall for implementado. Pré-requisito: manter caminho alternativo de recuperação.

### Disco cheio

Procedimento será preenchido após inventário/arquitetura de armazenamento.

### Container/serviço caiu

Será preenchido após Docker/serviços.

### Atualização quebrou sistema

Será preenchido após política de atualização.

### Restaurar backup/snapshot

Será preenchido após estratégia de backup. Snapshot não substitui backup independente.

Em 15/08/2026 nenhum backup independente comum foi encontrado no guest. Snapshots e backups do provedor não foram confirmados ao vivo. Este caminho ainda não é recovery validado.

### LXD ativado por uma consulta

Antes de parar o daemon, confirmar se há instâncias e se alguma está em execução. Na recuperação de 15/08 havia 0 instâncias; com HUMAN_GATE, somente `snap.lxd.daemon.service` foi parado, preservando `snap.lxd.daemon.unix.socket`. Revalidar processo, units e listeners.

### Reconstruir VPS

Meta final: reconstrução a partir deste repositório, documentação, decisões, configs sanitizadas e backups apropriados.

## Regra

Cada nova tecnologia instalada deve adicionar seu cenário de falha e recuperação a este playbook.
