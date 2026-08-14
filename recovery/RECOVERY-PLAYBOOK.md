# Recovery Playbook — versão viva

Objetivo: permitir que LEANDRO recupere a infraestrutura, não apenas saiba instalá-la.

## Cenários

### Perdi acesso SSH

1. confirmar se VPS está em execução no painel;
2. testar alcançabilidade sem assumir que ping prova SSH;
3. consultar `FND-SSH-001` se o problema for sessão ociosa;
4. usar VNC/TigerVNC como console alternativo;
5. se necessário e apropriado, avaliar Rescue System;
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

### Reconstruir VPS

Meta final: reconstrução a partir deste repositório, documentação, decisões, configs sanitizadas e backups apropriados.

## Regra

Cada nova tecnologia instalada deve adicionar seu cenário de falha e recuperação a este playbook.