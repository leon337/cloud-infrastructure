# 00 — Visão Geral

## Objetivo

Registrar a visão da infraestrutura, o plano de aprendizado da missão e o estado validado da Fase 0.

## Arquitetura conhecida

- Computador local: Linux Mint em hardware físico.
- Infraestrutura remota: Contabo Cloud VPS 8.
- Sistema remoto observado: Ubuntu 24.04.4 LTS.
- Uso futuro em estudo: servidor de infraestrutura e Cloud Workstation gráfica.

## Modelo híbrido

O computador local poderá ser usado como interface de trabalho, enquanto a VPS executa processamento, serviços, ambientes de desenvolvimento e aplicações remotas.

## Acesso validado

Foram validados dois canais independentes de acesso:

- SSH para administração normal;
- VNC/TigerVNC para console alternativo e recuperação.

A fingerprint ED25519 apresentada pelo SSH foi confirmada diretamente na VPS através do console VNC antes de ser aceita no cliente local.

O detalhamento está em [`01-primeiro-acesso-seguro.md`](01-primeiro-acesso-seguro.md).

## Fase atual

**FASE 0 — ORIENTAÇÃO E INVENTÁRIO**

O primeiro acesso seguro foi concluído.

A etapa atual é:

**0.5 — Inventário real da VPS.**

O objetivo agora é inventariar sistema, hostname, kernel, CPU, memória, armazenamento, filesystems, mounts, rede e uptime por comandos somente de leitura antes de qualquer mudança estrutural.

## Regra de conclusão

Uma etapa só é concluída quando funcionou, foi validada, foi documentada e LEANDRO entendeu.
