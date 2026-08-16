# DEC-002 — Preservar arquitetura híbrida e requisito de Cloud Workstation

Status: **DIREÇÃO ACEITA; SEQUENCIAMENTO SUPERSEDED POR DEC-003/DEC-004**.

## Contexto

LEANDRO quer usar o Linux Mint físico como estação local e deslocar processamento/serviços para a VPS. Também quer futuramente uma experiência gráfica remota semelhante a um computador próprio.

## Alternativas discutidas

- servidor Ubuntu puro com acesso remoto;
- Ubuntu com desktop gráfico na mesma VPS;
- workspace/container gráfico;
- VM Linux Mint aninhada;
- segunda VPS dedicada a desktop.

## Decisão atual

1. preservar modelo híbrido local + VPS;
2. não depender de nested virtualization;
3. estudar Cloud Workstation sobre a mesma VPS apenas depois do inventário e base segura;
4. não instalar GUI imediatamente.

O item 4 registra a sequência decidida naquele snapshot. DEC-003 autorizou a
antecipação e DEC-004 registra a implementação XFCE/XRDP validada.

## Consequências

- prioridade atual continua segurança/inventário;
- requisito gráfico não será esquecido;
- escolha de desktop/protocolo permanece HUMAN_GATE futuro;
- VPS poderá futuramente combinar serviços e experiência gráfica, desde que segurança e recursos permitam.
