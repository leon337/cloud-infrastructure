# 06 — Inventário Real da VPS

Status: **PARCIAL — Etapa 0.5 em andamento**.

## Identidade

- Provedor: Contabo.
- Produto: Cloud VPS 8.
- IPv4: `169.58.171.192`.
- Hostname: `vmi3506102`.
- Região contratada originalmente: European Union.

## Sistema

- Ubuntu 24.04.4 LTS.
- Noble Numbat (`noble`).
- Kernel `Linux 6.8.0-137-generic`.
- Arquitetura x86-64.

## Virtualização

- Chassis: VM.
- Hypervisor: KVM.
- Hardware virtual apresentado: QEMU.

## CPU

- 8 CPUs lógicas (`0-7`).
- AMD EPYC Processor (with IBPB) apresentado à VM.
- 1 socket virtual.
- 8 cores/socket.
- 1 thread/core.

Uma linha de vulnerabilidade de CPU foi observada no `lscpu`; não foi diagnosticada nesta etapa e deve ser reavaliada durante hardening/kernel, sem conclusões precipitadas.

## Memória

Medição com `free -h`:

- total visível ~23 GiB;
- usada ~592 MiB naquele instante;
- disponível ~22 GiB;
- swap: 0 B.

Swap ausente é fato de inventário, não decisão de que deve permanecer assim.

## Acesso

- SSH validado.
- VNC/TigerVNC validado.
- Remmina: serviço alcançado, sessão não concluída no teste.
- Rescue System: conhecido, não acionado.

## Inventário pendente

### Armazenamento/filesystems

Ainda executar somente leitura e explicar antes:

- `lsblk`;
- `lsblk -f`;
- `df -hT`;
- partições;
- filesystems;
- capacidade real e uso.

### Mounts

Inventariar mounts relevantes e relação com filesystems.

### Rede

Inventariar interfaces, endereços, rotas, DNS e serviços/portas apenas em etapa controlada.

### Estado básico

Uptime, carga, hora/timezone, serviços essenciais e atualizações pendentes quando chegar a etapa.

## Regra de armazenamento

Nenhuma decisão de particionamento/LVM/separação de `/home`, `/var` ou Docker antes do inventário completo, análise de trade-offs e autorização de LEANDRO.