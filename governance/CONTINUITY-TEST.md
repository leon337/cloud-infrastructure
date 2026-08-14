# Teste de Continuidade Canônica

Objetivo: provar que um novo chat consegue reconstruir o projeto **usando somente o GitHub canônico**, sem depender de memória de conversas anteriores.

## Prompt mínimo recomendado

> Continue a missão `leon337/cloud-infrastructure`. Antes de qualquer ação, consulte a `main` real e siga integralmente `CONTEXT.md`. Não execute mudanças. Faça primeiro o teste de continuidade definido no repositório.

## Perguntas obrigatórias

O novo agente deve conseguir informar, sem pedir novamente a LEANDRO:

1. finalidade da missão;
2. por que o repositório é separado do MCF;
3. quatro objetivos: segurança, funcionalidade, aprendizado e autonomia;
4. fase/etapa atual;
5. etapas concluídas;
6. IP, hostname, sistema, kernel e arquitetura;
7. virtualização KVM/QEMU e posição sobre nested virtualization;
8. inventário de CPU/RAM/swap;
9. canais SSH/VNC/Rescue e estado de cada um;
10. fingerprint SSH validada e por que foi verificada por VNC;
11. FND-SSH-001, papel do ping, teste inválido e teste válido;
12. autorização existente para keepalive permanente;
13. estado relatado de `~/.ssh/config`;
14. alias/bloco SSH planejado;
15. inventário ainda pendente;
16. fases futuras e quais são apenas provisionais;
17. requisito de Cloud Workstation e por que está adiado;
18. regras de secrets e HUMAN_GATE;
19. ponto exato de retomada;
20. documentos canônicos que sustentam cada resposta.

## Critérios

### CONTINUIDADE COMPLETA

- responde todos os itens essenciais a partir do repositório;
- distingue fatos, decisões e propostas;
- não pede IP/hostname/fingerprint já canônicos;
- não inventa estado ausente;
- identifica bloqueio atual e não retoma VPS automaticamente.

### CONTINUIDADE PARCIAL

- consegue operar, mas ainda depende de contexto de chat para motivação, histórico, decisão ou próximo passo.

### CONTINUIDADE INSUFICIENTE

- não consegue reconstruir fase/estado/decisões ou pede novamente dados básicos já documentados.

## Regra pós-teste

A VPS só volta a ser alterada após resultado **CONTINUIDADE COMPLETA**, ou decisão explícita de LEANDRO aceitando uma lacuna conhecida.