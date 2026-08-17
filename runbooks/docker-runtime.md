# Runbook — Docker runtime boundary F1.2b

Escopo: instalar Docker CE/CLI, containerd, Buildx e Compose em DEV/lab, sem
workload, imagem, volume, bridge, porta publicada ou acesso não-root ao socket.
Não inclui F1.2c, Management Network nem produção.

Status operacional: **IMPLEMENTING; CI PENDING; NODE-01 NOT_EXECUTED**.

## Gates e guardrails

- F1.1 precisa estar aplicado, reconciliado com `changed=0`, documentado e com
  invariância aprovada antes de qualquer check/apply F1.2b no NODE-01;
- o primeiro workload, inclusive fixture no NODE-01, depende de F1.2c;
- executar somente no alvo DEV `node-01`, com segunda sessão SSH funcional;
- autenticação sudo é digitada diretamente por LEANDRO; nunca usar senha em
  variável, arquivo, linha de comando ou log;
- não usar `get.docker.com`, `docker.io`, pacote sem pin, `--extra-vars` para
  sobrepor identidade/versão/boundary, `lxc`, Docker Desktop ou `apt autoremove`;
- não adicionar membros ao grupo `docker` e não abrir API TCP/porta pública;
- não alterar SSH, UFW policy, XRDP/LightDM, backup ou credenciais;
- abortar diante de package manager/reconcile concorrente, unit falha, lock,
  objeto Docker preexistente ou collision em config/source/key/marker.

O teste privilegiado completo só pode rodar em VM Ubuntu 24.04 descartável
identificada pelo harness. Nunca o execute na Workstation física ou na VPS.

## Pacotes e chave fixados

As versões, SHA-256 dos `.deb`, checksum/fingerprints da chave pública e licenças
estão em `DEC-007-docker-runtime-boundary.md` e no inventário estruturado. O
playbook deve falhar se o índice oficial não apresentar exatamente esses
artefatos. A chave pública versionada não é credencial e não concede acesso.

## Precheck read-only

Antes de qualquer operação privilegiada:

1. confirmar branch/commit, worktree limpo e CI aplicável ao mesmo SHA;
2. confirmar o checkpoint real de F1.1, marker/conteúdo, conta/grupo, paths e
   units esperados; `NOT_EXECUTED` bloqueia F1.2b;
3. validar identidade exata do NODE-01, SSH estrito e segunda sessão;
4. capturar boot ID, failed units, listeners IPv4/IPv6, interfaces, routes,
   sysctls de forwarding, UFW e rulesets iptables/nftables;
5. confirmar Docker/containerd/pacotes/source/key/config/units/marker ausentes;
6. confirmar grupos `ubuntu` e `platform-core` e que `docker` está ausente ou
   vazio, sem membro suplementar;
7. confirmar inexistência de `docker0`, `br-*`, 2375/2376 e processos/mounts nas
   raízes de runtime;
8. confirmar que `/var/lib/docker` e `/var/lib/containerd` não existem; conteúdo
   preexistente não é adotado;
9. confirmar lock ausente e ausência de Ansible/apt/dpkg/unattended-upgrade
   concorrente;
10. executar suíte estática e syntax check.

O prestate sanitizado registra apenas metadados, hashes e enumerações necessárias;
nunca conteúdo secreto de config do host.

## Preview e apply no NODE-01

Enquanto F1.1 não estiver concluído, estes comandos são referência bloqueada e
não devem ser executados. Depois do checkpoint e de CI verde no mesmo commit:

```bash
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/docker-runtime.yml \
  --ask-become-pass --check --diff
```

Reconciliar o preview sanitizado antes de autorizar apply. Check mode não prova
download, post-install suppression, daemon start ou ruleset real.

```bash
../../.venv/bin/ansible-playbook playbooks/docker-runtime.yml \
  --ask-become-pass --diff
```

Não encadear preview e apply automaticamente. Se um package post-install iniciar
o daemon antes da validação do config, parar e executar rollback; esse caminho é
falha do slice.

## Verificação após apply

1. validar versões exatas dos cinco pacotes e `docker compose version`;
2. validar config do daemon, unit/drop-ins e marker por hash/mode/owner;
3. confirmar Docker socket `root:root 0600`, grupo `docker` vazio e negação para
   `ubuntu`/`platform-core`;
4. confirmar daemon/containerd em `cloud-platform.slice` e cgroup driver
   `systemd`; nenhum processo em `cloud-workloads.slice`;
5. confirmar zero containers, imagens, volumes, build cache, swarm e redes
   customizadas; redes builtin não são workload;
6. confirmar ausência de `docker0`, `br-*`, ports/bindings e listeners novos;
7. comparar interfaces, routes, sysctls, UFW e rulesets: somente delta Docker
   vazio explicitamente classificado pode existir;
8. confirmar nenhum DNAT/publicação e nenhum listener 2375/2376/metrics;
9. reiniciar somente Docker/containerd, repetir todos os checks e validar logs;
10. executar segunda reconciliação; resultado esperado `changed=0`;
11. confirmar SSH/UFW/fail2ban/XRDP/LightDM/LXD, failed units e Workstation
    invariantes.

Não criar um container “só para testar” no NODE-01: o teste de workload pertence
a F1.2c. A integração descartável comprova o ciclo F1.2b sem transformar a VPS
em fixture.

## Rollback vazio e fail-closed

O comando permanece bloqueado até haver desired state e CI verde no mesmo
commit. Requer confirmação explícita própria do playbook:

```bash
cd automation/ansible
../../.venv/bin/ansible-playbook playbooks/rollback-docker-runtime.yml \
  --ask-become-pass \
  -e platform_docker_runtime_rollback_confirm=true --diff
```

O rollback precisa recusar, sem mutação, diante de marker/prestate adulterado,
versão diferente, membro no grupo, qualquer objeto Docker, swarm, build cache,
processo, mount ou conteúdo não atribuível ao runtime vazio.

Sob lock exclusivo, o preflight congela e valida o manifesto retornado por
`find -xdev` separadamente nos literais `/var/lib/docker` e
`/var/lib/containerd`. São recusados symlink, hardlink, mountpoint, device/inode
alterado e path fora dessas raízes. A remoção usa somente as entradas exatas do
manifesto, revalidadas e em ordem bottom-up; as raízes são removidas com
`rmdir`. Nunca usar `rm -rf`, glob, raiz/pai genérico ou autoremove.

Depois de provar ausência do runtime, remover apenas pacotes e arquivos com
provenance exata, executar daemon-reload e remover o marker por último. Restaurar
somente o prestate exato; não “limpar” recursos que não pertencem ao slice.

## Lock obsoleto

O diretório `/run/lock/cloud-platform-docker-runtime-operation` deve ser removido
pelo bloco `always` em sucesso/falha normal. Se persistir após queda abrupta,
todo novo reconcile falha fechado. Em segunda sessão, confirmar zero processo,
package manager ou operação concorrente e comparar marker/prestate/objetos. Só
então LEANDRO pode usar `sudo rmdir` no caminho literal vazio; conteúdo exige
investigação, nunca remoção recursiva.

## Evidência

Persistir resultados sanitizados em `evidence/SLICE-002B/`: SHA, pin/digest,
timestamp, contagens, hashes, invariantes, deltas classificados e PASS/FAIL por
etapa. `PENDING` e `NOT_EXECUTED` nunca equivalem a `PASS`.

