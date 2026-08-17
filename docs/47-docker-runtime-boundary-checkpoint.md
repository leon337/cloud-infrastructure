# 47 — Docker runtime boundary F1.2b checkpoint

Data: 2026-08-17
Status: **REPO DESIRED STATE + DISPOSABLE CI PASS — REAL VPS NOT_EXECUTED**
Ambiente autorizado: **DEV/lab somente**

## Objetivo

Preparar Docker Engine/Compose como runtime host vazio, pinado, root-only e
reversível. Este slice implementa apenas a fronteira do daemon; não instala
serviço de plataforma, não cria workload e não satisfaz Q20/Q34.

## Estado recuperado e dependências

- base da branch: `e4503af12bf81806e8c2508eb108c4dc4c264784`;
- o último baseline real registrou Docker/containerd ausentes;
- F1.1 passou em VM descartável, mas check mode privilegiado, apply, segunda
  reconciliação e invariância no NODE-01 permanecem `NOT_EXECUTED`;
- por isso F1.2b pode avançar em código/CI, mas check/apply real está bloqueado;
- F1.2c network enforcement bloqueia o primeiro container no NODE-01.

O desired state nasceu no commit
`7015c80759a797bcb141773b79cd9b95f6fbecf1`. Apply/rollback, role, preflight,
pin APT, helper de árvore, harness e CI foram exercitados no commit publicado
`fa66f1049bac5540a5b12219186a421cc39dcbc0`, run `31996516019`.

Nenhuma inspeção nova ou mutação foi executada na VPS para produzir este
checkpoint.

## Seleção congelada

DEC-007 seleciona o repositório oficial Docker `stable/noble/amd64` e fixa:

| Pacote | Versão exata | SHA-256 `.deb` |
|---|---|---|
| `docker-ce` | `5:29.7.2-1~ubuntu.24.04~noble` | `8243f97d569a0fa33ea32417e399e9f524e7d75d3898fa9d24e0eadaa486af68` |
| `docker-ce-cli` | `5:29.7.2-1~ubuntu.24.04~noble` | `920a5fa031f33f2dd5b56b4a9bc4c725bc9549d6007004a6610a469873ec69fe` |
| `containerd.io` | `2.3.3-1~ubuntu.24.04~noble` | `3a2c59a92b4c57d247f26ea37c6f1913aefee9e6f8d64815c47505e6de0033db` |
| `docker-buildx-plugin` | `0.36.1-1~ubuntu.24.04~noble` | `405be4bdbd70052880583da5d181c8e1c06e61f1a5b230ad2ad124e04318def2` |
| `docker-compose-plugin` | `5.4.0-1~ubuntu.24.04~noble` | `f7890c92ea2d356bc7ea7ac351a854bde8d7c446da6102126a9d9fac9ea0583c` |

A chave pública versionada é aceita somente com SHA-256
`1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570`,
fingerprint primária `9DC858229FC7DD38854AE2D88D81803C0EBFCD88` e subchave
`D3306A018370199E527AE7997EA0A9C3F273FCD8`. Chave pública não é secret.
Os cinco projetos upstream registram Apache-2.0; Docker Desktop não é instalado.

## Boundary desired state

- daemon rootful; socket Unix `root:root 0600`; `group=root` e grupo `docker`
  sem membros;
- API TCP 2375/2376 e endpoint de métricas ausentes;
- `firewall-backend=iptables` pelo iptables-nft do Noble, nunca backend nftables
  experimental e nunca `iptables=false`;
- `bridge=none`, `ip-forward=false`, `ip-masq=false`, IPv6 do daemon false;
- `iptables=true`/`ip6tables=true`, sem criar falsa garantia por desligar a
  integração suportada;
- nenhuma interface `docker0`/`br-*`, rota, forwarding, DNAT ou porta;
- cgroup driver systemd; daemon/containerd em `cloud-platform.slice`; parent de
  futuros workloads em `cloud-workloads.slice`;
- zero containers, imagens, volumes, redes customizadas, build cache e swarm;
- marker `/etc/cloud-platform-docker-runtime.managed` `root:root 0600`, lock
  exclusivo e prestate/sentinel persistente fora das raízes Docker;
- pin APT dedicado com prioridade `1001`; índice autenticado deve fornecer
  versão/path/SHA-256 exatos antes da instalação;
- `policy_rc_d=101`, com recusa de policy host-wide preexistente, impede start
  por package script antes de config/digest/unit validation.

## Rollback definido antes do apply

Rollback exige marker/prestate exatos, versões/provenance exatas e runtime
comprovadamente vazio. O apply congela um baseline exato depois de provar roots
inicialmente ausentes. Dentro do lock, `find -xdev` é executado separadamente
apenas nos literais `/var/lib/docker` e `/var/lib/containerd`; a árvore corrente
precisa coincidir com o baseline antes de congelar device/inode no manifesto de
remoção. Symlinks, hardlinks, mounts, processo com path aberto, drift ou escape
recusam antes da mutação.

A remoção consome somente paths exatos do manifesto, revalida cada entrada,
remove bottom-up e termina com `rmdir` das raízes. `rm -rf`, glob, busca em pai
amplo e `apt autoremove` são proibidos. Arquivos/packages com provenance exata
saem antes do daemon-reload; o marker é o último objeto removido.

## Evidence matrix

| Gate | Estado |
|---|---|
| Decisão, pins e boundary | `RECORDED` |
| Desired state integrado | `PASS_LOCAL_COMMIT_7015C80` |
| Local static/fail-closed suite final | `PASS_63_TESTS_6_SHELLCHECK_6_ANSIBLE_SYNTAX` |
| CI GitHub commit-bound | `PASS_RUN_31996516019_COMMIT_FA66F10` |
| Disposable check/apply/changed=0/restart/rollback | `PASS` |
| NODE-01 check/apply/changed=0/invariância | `NOT_EXECUTED` |
| Q20/Q34 network enforcement | `BLOCKED_BY_F1_2C` |

`PENDING`/`NOT_EXECUTED` não são `PASS`. VM descartável não prova firewall do
host real, e instalação vazia não prova isolamento de workload.

## Próximo passo exato

1. preservar a evidência commit-bound `fa66f10`/run `31996516019`;
2. manter NODE-01 bloqueado até F1.1 ser aplicado/reconciliado/checkpointed;
3. executar somente o preview real F1.2b após novo checkpoint/human sudo;
4. usar o contrato F1.2c `b4cbeb0` para selecionar o mecanismo em ADR e provar a
   matriz dinâmica antes do primeiro container.

Nenhum item deste checkpoint autoriza produção, rotação de credenciais ou acesso
Docker irrestrito a agentes.
