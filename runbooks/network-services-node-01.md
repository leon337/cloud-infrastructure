# Runbook — F1.2c network services no NODE-01

Status: **DESIRED STATE PREPARED — CI AND REAL APPLY PENDING**

Este incremento instala somente quatro componentes privados de plataforma:
CoreDNS e Squid para os escopos `development-default` e `restricted`. Não há
`ports:`, listener público, workload de usuário, Management Network, produção,
secret ou rotação de credencial.

As configurações são `root:root 0644` porque CoreDNS e Squid executam sem root e
precisam ler os bind mounts. Elas não contêm segredos; o marker de proveniência
e a autorização temporária permanecem privados em `0600`.

## Gates antes do apply

1. commit exato publicado e os quatro jobs da workflow Docker verdes;
2. runner temporário atualizado, ativo e com expiração futura;
3. SSH público, UFW, fail2ban, XRDP, Docker, containerd e enforcement base ativos;
4. LXD daemon/socket inativos; zero unit falha;
5. zero containers, imagens, volumes e redes customizadas não gerenciados;
6. rotas sem colisão com `10.240.0.0/16` e `10.240.254.0/24`;
7. backup de configuração fresco executado pelo entrypoint;
8. segunda sessão SSH disponível e VNC/Rescue preservados.

O runner e os scripts falham fechados diante de qualquer divergência. Não usar
clientes `lxc` na coleta, pois eles podem ativar o daemon por socket.

## Sequência controlada

```bash
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner status'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner test'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner apply'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner apply'
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner check'
```

A primeira execução deve registrar mudança somente na camada de serviços; a
segunda deve ser idempotente. O check exige quatro containers exatos, três
bridges internas `cp*`, uma bridge `cpeg0001`, socket Docker `root:root 0600`,
IPv6 forwarding zero, nenhum bind público 53/3128/2375/2376 e serviços humanos
inalterados.

## Falha e rollback

O rollback remove primeiro somente a camada de serviços e preserva a base
F1.2c. Ele recusa container/rede desconhecido, drift de marker/configuração ou
estado parcial não classificado.

```bash
ssh contabo-vps 'sudo -n /usr/local/sbin/codex-mission-001-runner rollback'
```

Depois, `status` deve permanecer verde para Foundation, Docker vazio e base de
enforcement. Não remover SSH, UFW, XRDP, backup, chave ativa ou marker de uma
camada anterior. Qualquer falha em restaurar o baseline preserva o marker e vira
HUMAN recovery gate; não repetir cegamente.
