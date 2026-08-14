# 04 — Plano Mestre

Este documento consolida tudo que foi planejado para a implementação. A ordem futura é **provisória** quando ainda não houve HUMAN_GATE específico.

## Programa de capacidades

### FASE 0 — Orientação e Inventário — DONE

Objetivo: compreender arquitetura, acessar com segurança e descobrir o estado real antes de mudanças estruturais.

Inclui: modelo mental, repositório canônico, acesso VNC/SSH, SO, kernel, virtualização, CPU, RAM, armazenamento, filesystems, mounts, rede e uptime.

Fechamento: coleta técnica concluída, inventário consolidado e fechamento didático aprovado por LEANDRO em 2026-08-14.

### FASE 1 — Base do sistema e segurança inicial — IN_PROGRESS

- atualizações iniciais;
- usuário administrativo próprio;
- sudo;
- estratégia de SSH;
- chave SSH;
- validação de acesso por chave;
- política de root;
- política de senha SSH;
- menor privilégio.

LEANDRO determinou o avanço para a próxima fase em 2026-08-14. A FASE 1 foi iniciada de forma controlada.

A sequência permanece gradual: primeiro apresentar e executar um único micro-passo por vez, com explicação prévia, risco/recovery e HUMAN_GATE quando aplicável. O início da fase não autoriza automaticamente mudanças que possam causar lockout ou alterações estruturais em lote.

Primeiro micro-passo planejado: atualização inicial, começando pela atualização dos índices APT antes de qualquer upgrade de pacotes.

### FASE 2 — Rede e firewall — PROVISIONAL

- portas necessárias;
- firewall Contabo;
- firewall Ubuntu/UFW;
- prevenção de bloqueio próprio;
- proteção contra brute force quando pertinente;
- DNS/rede básica.

### FASE 3 — Armazenamento — PROVISIONAL

Antes de alterar: `lsblk`, `df`, filesystems, partições e mounts.

Decidir conscientemente entre layout atual, partição única, múltiplas partições, LVM, separação de `/home`, `/var` ou área Docker. Considerar crescimento, risco de enchimento isolado, recuperação, snapshots e backups.

### FASE 4 — Atualizações e manutenção — PROVISIONAL

Política de atualização, logs, reinicializações, manutenção e verificação.

### FASE 5 — Backup, snapshots e recovery — PROVISIONAL

- distinguir snapshot de backup;
- cópia independente;
- testes de restauração;
- Rescue System;
- Recovery Playbook.

### FASE 6 — Docker e Compose — PROVISIONAL

Antes de instalar, ensinar VM x container, imagem, container, volume, rede, porta, registry, Compose, persistência, restart policy e logs.

### FASE 7 — Desenvolvimento remoto e modelo híbrido — PROVISIONAL

- VS Code Remote SSH;
- Git;
- tmux;
- transferência e sincronização;
- builds remotos;
- ambientes de desenvolvimento.

### FASE 8 — Observabilidade e operação — PROVISIONAL

- saúde do host;
- recursos;
- logs;
- alertas;
- monitoramento de serviços.

### FASE 9 — Plataforma de serviços — PROVISIONAL

- reverse proxy;
- TLS;
- redes de aplicação;
- serviços internos;
- publicação controlada.

### FASE 10 — Cloud Workstation — DEFERRED

Avaliar GUI, consumo, segurança, protocolo, latência, experiência e coexistência com servidor. Não instalar por impulso.

### FASE 11 — Workloads do ecossistema — PROVISIONAL

Implantação gradual de MCF, MCPs, APIs, agentes, automações, n8n, dashboards, aplicações e produtos.

### FASE 12 — Autonomia e reconstrução — PROVISIONAL

Consolidar runbooks, exercícios, recuperação completa e capacidade de LEANDRO reconstruir a infraestrutura a partir do GitHub.

## Regra de mudança de ordem

A ordem pode mudar por segurança, dependências ou decisão de LEANDRO. Qualquer mudança relevante deve atualizar este plano, roadmap e decisão correspondente.
