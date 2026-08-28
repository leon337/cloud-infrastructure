# Runbook — F1.2c network services no NODE-01

Status: **DESIRED STATE PREPARED — CI AND REAL APPLY PENDING**

Este incremento instala somente quatro componentes privados de plataforma:
CoreDNS e Squid para os escopos `development-default` e `restricted`. Não há
`ports:`, listener público, workload de usuário, Management Network, produção,
secret ou rotação de credencial.

As configurações são `root:root 0644` porque CoreDNS e Squid executam sem root e
precisam ler os bind mounts. Elas não contêm segredos; o marker de proveniência
e a autorização temporária permanecem privados em `0600`.

## Recovery do estado parcial observado em 28/08/2026

O NODE-01 não está mais no estado de primeira aplicação limpa descrito na sequência
histórica abaixo. A evidência read-only de 28/08 confirmou uma aplicação parcial:

- `cloud-platform-network-services.service` permanece `failed` com o erro histórico
  `/run/lock/cloud-platform-network-services.lock: Read-only file system`;
- o marker `SLICE-002C-NODE-01-SERVICES-V1` está presente;
- helper e unit instalados correspondem aos hashes históricos
  `06d0f016...` e `dfe10b0e...`;
- `/etc/cloud-platform/network-services` está ausente;
- não foram observadas interfaces `cp*`/`cpeg*`;
- base enforcement e serviços humanos permanecem ativos;
- `systemd-networkd-wait-online.service` continua como incidente separado.

Por isso, **não executar** o `apply` ou `rollback` normais contra esse estado. Ambos são
fail-closed para uma superfície já marcada e divergente, e devem recusar em vez de
reparar.

O recovery dedicado é:

```text
automation/mission-001/operations/recover-network-services-partial
```

Ele aceita somente `precheck`, `apply`, `check` e `rollback`. No NODE-01 exige:

1. hostname e machine-id exatos;
2. candidato Git exato descendente da lineage validada
   `80a1579bf6525029be8085fa1d1cbdec602ddfbd`;
3. repositório fonte `root:root`, limpo e com o HEAD igual ao SHA explicitamente
   fornecido em `F1_2C_RECOVERY_CANDIDATE_SHA`;
4. hashes antigos exatos da unit/helper e hashes exatos de todas as fontes novas;
5. markers Foundation/Docker/F1.2c e base enforcement sem drift;
6. service config tree ausente, runtime privado ausente e legacy lock conhecido;
7. zero containers, imagens, volumes e redes Docker customizadas;
8. nenhuma interface `cp*`/`cpeg*`, rota `10.240.*` ou listener público gerenciado;
9. SSH, UFW, fail2ban, XRDP, Docker, containerd e base enforcement ativos.

`precheck` não corrige divergência: qualquer diferença gera `RECOVERY_REFUSED` antes da
primeira mutação.

### Checkpoint e apply

O `apply` repete o precheck, cria um checkpoint root-owned dos helper/unit históricos,
executa o backup de configuração existente e só então instala a superfície candidata.
O serviço é iniciado apenas depois de hashes e configs instalados serem verificados.

Se o start/check falhar depois de a mutação de rede ter começado, o recovery registra
`RECOVERY_HUMAN_GATE_REQUIRED` e **não executa limpeza destrutiva best-effort**. O
checkpoint e o estado ficam preservados para recuperação humana.

### Rollback do recovery

`rollback` só é aceito a partir de um estado candidato completamente saudável e
verificado. Ele usa o helper novo para desmontar os recursos gerenciados, remove apenas
a configuração candidata, restaura helper/unit do checkpoint, preserva marker/sysctl e
a base enforcement, e exige Docker/runtime vazio ao final.

O rollback restaura um baseline parcial seguro com a unit histórica habilitada porém
sem iniciar deliberadamente a falha antiga.

### Gate operacional

A preparação, os testes e o KVM descartável podem avançar sem tocar o NODE-01. Para o
host real, staging root-owned, `precheck` privilegiado e `apply` pertencem ao mesmo
rollout controlado e **não estão autorizados até HUMAN_GATE explícito de LEANDRO**.
A chave usada no fluxo interativo notebook→VPS deve ser preservada.

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
