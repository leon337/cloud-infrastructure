# DEC-007 — Docker runtime rootful com fronteira vazia e root-only

Status: **ACCEPTED — DONE EMPTY RUNTIME — WORKLOAD BLOCKED BY F1.2c**

## Contexto

Q17 fixa Docker/Compose como runtime inicial, mas proíbe entregar o daemon
diretamente aos agentes. Q20/Q34 exigem isolamento, egress e service discovery
que ainda pertencem a F1.2c. Instalar o runtime com defaults criaria bridge,
forwarding e uma superfície de publicação capaz de contornar a expectativa do
UFW antes que essa policy fosse provada.

F1.1 e F1.2b foram concluídos no NODE-01. O runtime vazio passou CI descartável,
check mode, backup off-host, apply, reconciliação `changed=0`, restart e
invariância. F1.2c ainda bloqueia qualquer workload.

## Alternativas

1. Docker do arquivo Ubuntu (`docker.io`);
2. script de conveniência `get.docker.com` ou pacotes sem versão fixa;
3. Docker rootless;
4. Docker CE rootful do repositório oficial com grupo e socket defaults;
5. Docker CE rootful do repositório oficial, pinado, sem bridge/workload e com
   socket apenas para root.

O pacote Ubuntu não é a distribuição selecionada pelo contrato de F1.2b; o
script de conveniência não fornece a provenance/reconciliação exigida. Rootless
não elimina a necessidade de policy de rede e introduz trade-offs de AppArmor e
operação que não são justificados para o daemon host inicial. O grupo `docker`
equivale a uma fronteira root e não pode ser entregue a operadores ou agentes.

## Decisão

Usar os pacotes Docker CE oficiais para Ubuntu Noble `amd64`, sem recommends e
com versões APT exatas:

| Pacote | Versão | SHA-256 do `.deb` no índice oficial |
|---|---|---|
| `docker-ce` | `5:29.7.2-1~ubuntu.24.04~noble` | `8243f97d569a0fa33ea32417e399e9f524e7d75d3898fa9d24e0eadaa486af68` |
| `docker-ce-cli` | `5:29.7.2-1~ubuntu.24.04~noble` | `920a5fa031f33f2dd5b56b4a9bc4c725bc9549d6007004a6610a469873ec69fe` |
| `containerd.io` | `2.3.3-1~ubuntu.24.04~noble` | `3a2c59a92b4c57d247f26ea37c6f1913aefee9e6f8d64815c47505e6de0033db` |
| `docker-buildx-plugin` | `0.36.1-1~ubuntu.24.04~noble` | `405be4bdbd70052880583da5d181c8e1c06e61f1a5b230ad2ad124e04318def2` |
| `docker-compose-plugin` | `5.4.0-1~ubuntu.24.04~noble` | `f7890c92ea2d356bc7ea7ac351a854bde8d7c446da6102126a9d9fac9ea0583c` |

A chave pública oficial é material público, não secret, e fica versionada para
eliminar download mutável durante o reconcile. O arquivo aceito possui SHA-256
`1500c1f56fa9e26b9b8f42452a553675796ade0807cdce11975eb98170b3a570`,
fingerprint primária `9DC858229FC7DD38854AE2D88D81803C0EBFCD88` e subchave de
assinatura `D3306A018370199E527AE7997EA0A9C3F273FCD8`. A source APT é
somente `stable`, `noble`, `amd64`, com `signed-by` dedicado. O playbook valida
checksum, fingerprints e os digests publicados no índice antes de instalar.

Docker Engine/Moby, Docker CLI, containerd, Buildx e Compose são projetos
Apache-2.0. Docker Desktop não é instalado e seus termos comerciais não fazem
parte desta escolha. Não há serviço pago selecionado por esta decisão.

O daemon é rootful, com as seguintes fronteiras obrigatórias:

- socket Unix `root:root 0600`, daemon `group=root` e grupo `docker` vazio;
- nenhuma API TCP, listener de métricas, workload, volume, imagem ou porta;
- `firewall-backend=iptables`, usando o frontend `iptables-nft` suportado em
  Noble; não selecionar o backend nftables experimental e nunca usar
  `iptables=false`;
- bridge default desabilitada (`bridge=none`), IPv4 forwarding e masquerade
  desabilitados, IPv6 do daemon desabilitado;
- `iptables=true` e `ip6tables=true` permanecem explícitos para não criar uma
  falsa promessa de isolamento por desligamento da integração do daemon;
- binding default de redes bridge futuras em `127.0.0.1` como defesa adicional,
  sem autorizar criar essa rede em F1.2b;
- cgroup driver `systemd`, daemon/containerd em `cloud-platform.slice`, futuro
  cgroup parent em `cloud-workloads.slice` e namespace cgroup privado;
- `no-new-privileges`, logging local limitado e live restore desabilitado;
- package post-install não pode iniciar o daemon antes de a configuração ser
  validada; o start ocorre apenas depois dos prechecks.

O pin APT versionado fixa os cinco candidatos com prioridade `1001`; o apply
também confere no índice autenticado a versão, o path Noble/stable e o SHA-256
de cada `.deb` antes da instalação. `policy_rc_d=101` impede autostart de package
scripts, e a execução recusa uma policy host-wide preexistente em vez de
sobrescrevê-la.

O marker de provenance fica fora das árvores removíveis em
`/etc/cloud-platform-docker-runtime.managed`, `root:root 0600`, com conteúdo
exato do slice. Lock e prestate/sentinel ficam respectivamente em
`/run/lock/cloud-platform-docker-runtime-operation` e
`/var/lib/cloud-platform/runtime-boundaries/docker/`.

## Fronteira de rede

F1.2b mede e preserva listeners, interfaces, routes, sysctls, UFW e rulesets
não-Docker. Aceita apenas o delta mínimo documentado de chains criado pelo
runtime vazio. Qualquer `docker0`/`br-*`, forwarding habilitado, rota nova,
DNAT/publicação, listener 2375/2376, tabela nftables nativa `docker-bridges` ou
regra não atribuível ao runtime é falha.

Essa instalação não satisfaz Q20/Q34. F1.2c deve selecionar e provar
isolamento/egress/service discovery IPv4/IPv6 antes do primeiro container, ainda
que ele não publique portas.

## Consequências

- Docker e Compose ficam disponíveis somente para operação root mediada;
- `ubuntu`, `platform-core`, runners, workers, sandboxes e agentes não recebem o
  grupo nem o socket;
- o runtime vazio é `Rebuildable`, sem backup de `/var/lib/docker` ou
  `/var/lib/containerd`;
- o daemon não pode ser usado para “adiantar” serviços antes de F1.2c;
- versões novas exigem novo pin, checksum, reexecução completa e revisão desta
  decisão diante de mudança de backend/licença;
- produção e rotação de credenciais continuam fora do escopo.

## Rollback

Rollback só é permitido quando a provenance e o prestate provarem que as raízes
de runtime não existiam antes de F1.2b e quando não houver containers, imagens,
volumes, redes customizadas, build cache, swarm, membros no grupo, processos,
mounts ou arquivos não atribuíveis ao runtime vazio.

Após o primeiro start vazio e com os serviços parados, o apply congela um
baseline exato de paths/tipos/owners/modes que só pode ter surgido das raízes
comprovadamente ausentes no prestate. Dentro do lock exclusivo, o rollback
invoca `find -xdev` separadamente apenas nos caminhos literais
`/var/lib/docker` e `/var/lib/containerd`, compara a árvore ao baseline e cria
um manifesto imutável de remoção com device/inode correntes. Ele recusa
symlinks, hardlinks, mountpoints, processo com path aberto, troca de
device/inode, path fora das raízes e qualquer entrada fora do baseline. A fase
mutante consome somente esse manifesto, reconfere tipo/inode e remove folhas
exatas em ordem bottom-up; as raízes saem por `rmdir`. É proibido `rm -rf`,
glob, `find` sobre pai amplo ou `apt autoremove`.

Um sentinel de apply incompleto não é retomado nem apagado automaticamente. O
playbook de rollback corrente aceita somente deployment completo com baseline
íntegro; estado transacional parcial exige classificação explícita antes de uma
extensão de recovery, preservando fail-closed.

Depois, removem-se apenas os cinco pacotes e arquivos de config/source/key/drop-in
com provenance exata, recarrega-se systemd e remove-se o marker por último.
Qualquer drift aborta antes da primeira remoção.

## Revisão

Revisar antes do primeiro workload, major upgrade, troca do backend do firewall,
mudança de cgroup/systemd, introdução de nó adicional ou necessidade comprovada
de runtime rootless. A revisão não pode reduzir Q17/Q20/Q34 sem decisão humana.
