# DEC-008 — Enforcement por DOCKER-USER e egress proxy-only

Status: **ACCEPTED — IMPLEMENTAÇÃO E PROVA DESCARTÁVEL PENDENTES**

## Contexto

Q20 exige egress útil por política, bloqueio lateral/administrativo e exceções
escopadas. Q34 exige redes isoladas por tenant/projeto/sandbox, descoberta por
nome/identidade e compartilhamento somente explícito. F1.2b instalou Docker
29.7.2 vazio com backend `iptables`, bridge default ausente, forwarding zero e
socket root-only. Nenhum workload está autorizado.

O mecanismo precisa coexistir com UFW, preservar SSH/XRDP e impedir que uma
porta Docker publicada contorne a expectativa do firewall do host. Também deve
ser reversível e comprovável em IPv4 e IPv6 antes do primeiro container real.

## Alternativas

1. backend nftables nativo do Docker 29;
2. firewall nftables independente modificando tabelas do Docker;
3. `iptables=false` e regras integralmente próprias;
4. Kubernetes/CNI/eBPF já no V1;
5. backend Docker `iptables-nft`, policy própria em `DOCKER-USER`, redes bridge
   internas por sandbox e saída somente por proxies controlados.

O backend nftables nativo continua experimental no Docker 29 e não fornece a
cadeia `DOCKER-USER`. Modificar tabelas de propriedade do Docker é instável.
Desligar `iptables` tende a quebrar networking e transfere toda a semântica NAT
para a plataforma. Kubernetes/CNI/eBPF aumenta o control plane e contraria a
escolha container-first Docker/Compose inicial de Q17.

## Decisão

Selecionar a alternativa 5:

- Docker permanece com `firewall-backend=iptables`, usando `iptables-nft` do
  Ubuntu Noble; não usar o backend nftables experimental;
- uma cadeia versionada `CLOUD-PLATFORM-FWD` é chamada no início de
  `DOCKER-USER`; nenhuma regra altera diretamente chains pertencentes ao Docker;
- cada sandbox recebe bridge determinística própria, nunca rede compartilhada
  implícita; somente gateways de plataforma podem participar de mais de uma
  rede, sob grant explícito e auditável;
- bridges de workload nascem `internal`; não há forwarding/NAT direto para a
  Internet e nenhuma porta pode ser publicada pelo executor;
- `none` não recebe DNS nem proxy; `restricted` recebe DNS controlado e proxy
  com destinos explícitos; `development-default` recebe DNS controlado e proxy
  HTTP(S) com policy versionada;
- tráfego para host, Management, metadata, control plane, endereços privados e
  outras bridges é negado antes de qualquer allow de egress;
- respostas `ESTABLISHED,RELATED` são aceitas somente para fluxos iniciados por
  uma autorização válida; grants vencidos ou ausentes compilam para deny;
- IPv6 permanece sem endereço/rota/forwarding no primeiro incremento. A matriz
  deve provar fail-closed e ausência de exposição IPv6; habilitar egress IPv6
  direto exige revisão desta decisão;
- descoberta usa nomes emitidos pelo Core e uma visão DNS por sandbox/projeto.
  Nome ou IP Docker isolado não constitui autorização; o source bridge e o
  grant compilado vinculam a identidade operacional;
- o Preview Gateway será a única futura origem permitida para ingress de
  workloads. `ports:`, host network, macvlan/ipvlan, privileged e attach manual
  de redes permanecem recusados pelo Core/Node Agent.

O pool candidato DEV é `10.240.0.0/16`; ele não é aplicado até precheck de
colisão com interfaces, rotas, VPN/Management e redes Docker. A faixa IPv6
reservada para futura revisão é `fd42:434c:4f55::/48`, igualmente condicionada a
collision check.

## Modelo operacional

O Core compila manifesto e grants para um plano imutável. O Node Agent valida
novamente o plano, cria a bridge com nome/CIDR fixos e reconcilia uma transação
de firewall. Agentes e workloads nunca recebem Docker socket nem autoridade
para editar rede. Falha do compilador, DNS, proxy ou policy remove o allow e
mantém deny.

O ruleset é aplicado atomicamente por `iptables-restore --noflush` e
`ip6tables-restore --noflush`, sob lock exclusivo e com hash/provenance. A
reconciliação deve verificar o jump único, ordem das regras, ausência de broad
allow e identidade de cada interface. Rollback remove somente chain/jump/redes
marcados pelo slice, depois de provar zero workload e zero processo dependente.

## Evidência obrigatória

Antes do NODE-01:

- VM Ubuntu 24.04 descartável com Docker 29.7.2/F1.2b;
- baseline e pós-ruleset IPv4/IPv6, check mode, apply, `changed=0`, restart e
  rollback limpo;
- probes negativos para host, Management, metadata, control, lateral,
  cross-sandbox e ingress externo v4/v6;
- perfis `none`, `restricted` e `development-default`, incluindo falha de DNS e
  proxy;
- grant compartilhado positivo e sua revogação/expiração negativa;
- ausência de publicação, host networking, socket, forwarding irrestrito e
  acesso ao plano administrativo.

## Consequências

- egress arbitrário TCP/UDP direto não faz parte do perfil DEV inicial;
- ferramentas devem respeitar `HTTP_PROXY` e `HTTPS_PROXY`; TLS não é
  interceptado por padrão;
- protocolos não HTTP precisam de capability/perfil específico e nova prova;
- DNS/proxy tornam-se componentes de disponibilidade, mas falham fechados;
- o primeiro workload continua bloqueado até integração descartável completa e
  checkpoint explícito;
- produção, Management Network e rotação de credenciais continuam fora do
  escopo.

## Fontes primárias

- [Docker packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
- [Docker with nftables](https://docs.docker.com/engine/network/firewall-nftables/)
- [Docker networking overview](https://docs.docker.com/engine/network/)
- [Netfilter bridge filtering](https://wiki.netfilter.org/wiki-nftables/index.php/Bridge_filtering)

## Revisão

Revisar para Docker major upgrade, backend nftables estável, multi-node,
Swarm/Kubernetes, egress não HTTP, IPv6 direto ou mudança do modelo de proxy.
