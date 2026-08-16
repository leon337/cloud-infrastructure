# 40 — MISSION ACCEPTANCE + RECOVERY REPORT

Data da recuperação: 2026-08-16 19:46 UTC
Status: **ACCEPTED — BASELINE RECOVERED — SLICE-001 PARTIAL/AWAITING DISPOSABLE VM REVALIDATION**
Autoridade: **LEANDRO / Q40-D**

## GitHub canônico

- repositório: `leon337/cloud-infrastructure`;
- branch recuperada: `main`;
- SHA recuperado e confirmado por fetch/`ls-remote`:
  `987c5359ea948d1903355e98177ae1eb2f1849d5`;
- divergência naquele instante: `0 ahead / 0 behind`;
- worktree/index: limpos;
- branch isolada do primeiro incremento:
  `codex/mission-001-foundations-f1-1`.

Não havia mudança concorrente no GitHub no início do slice. Há sessões humanas e
processos de desenvolvimento ativos na VPS; a ausência de concorrência deve ser
revalidada imediatamente antes de qualquer aplicação privilegiada.

## Estado canônico recuperado

Os 28 checkpoints da Platform Discovery contêm Q1–Q40 sem lacuna ou duplicação.
Todas as escolhas são `C`, exceto Q5=`D`, Q11=`D`, Q28=`D` e Q40=`D`.

Q1–Q39 permanecem requisitos arquitetônicos vinculantes. Q40-D delega seleção
tecnológica e implementação DEV/lab ao Codex. Produção continua bloqueada por
HUMAN_GATE e rotação de credenciais continua `DEFERRED_BY_HUMAN_DECISION`.

O checkpoint operacional recuperado foi:

- F0 orientação/inventário: `DONE`;
- F1 acesso, recovery e segurança mínima: `DONE` no escopo histórico;
- F2 Cloud Workstation: `DONE / FUNCTIONAL_AND_VALIDATED`;
- próximo estado autorizado: Technology Mapping e implementação incremental
  DEV/lab;
- findings abertos: `FND-BACKUP-001`, `FND-CPU-001` e
  `FND-CLOUDINIT-001`.

## Q1–Q40 entendidas

- Q1–Q9: plataforma privada e own-infrastructure-first para DEV/lab, isolamento
  projeto/missão/sandbox, autonomia por escopo, Capability Core, compute
  descartável e manifesto declarativo;
- Q10–Q16: dados DEV persistentes por projeto, storage híbrido, cofre central,
  previews privados por padrão, pipeline DEV rastreável, observabilidade central
  e recuperação off-host testada;
- Q17–Q23: Docker/Compose mediado, registry OCI independente, runners isolados,
  egress controlado, Management/Agent/Preview Gateways separados, identidade e
  autoridade temporária, autonomia DEV/staging e promoção de produção sob
  HUMAN_GATE;
- Q24–Q31: Tenant/Workspace → Project → Mission → Sandbox, quotas e reserva,
  single-node portável, desired state idempotente, workflow durável desde V1,
  MCF/Core/Workflow separados e plataforma headless;
- Q32–Q39: Model Gateway, security/update lifecycle, redes isoladas, classes de
  criticidade/RPO/RTO, Event Backbone, DNS/TLS DEV, Data Service Plane e rede
  administrativa privada;
- Q40-D: o Codex seleciona tecnologias e implementa incrementalmente DEV/lab sem
  reduzir Q1–Q39, promover produção ou rotacionar credenciais adiadas.

## VPS observada

Coleta direta, somente leitura, por SSH com chave dedicada e host key estrita:

| Item | Evidência observada |
|---|---|
| Node | `vmi3506102`, Ubuntu 24.04.4 LTS, kernel `6.8.0-137-generic`, KVM |
| Capacidade | 8 vCPU, 23,5 GiB RAM, sem swap, raiz ext4 de 289,6 GiB |
| Uso no baseline | 6,2 GiB RAM e 10,5 GiB de disco usados; 17,2/279 GiB disponíveis |
| Acesso | `ubuntu`/publickey validado; `sudo -n` negado; host fingerprint conhecido aceito |
| Listeners | público somente TCP 22; XRDP `127.0.0.1:3389`; sesman `[::1]:3350` |
| Segurança | SSH, UFW, fail2ban e unattended-upgrades ativos; zero units falhas |
| Runtime | LXD daemon/socket inativos; Docker/containerd ausentes |
| Workstation | XFCE/LightDM/Firefox/VS Code ativos; múltiplas sessões existentes |
| Backup | timer ativo; dois tars com checksum/listagem válidos; uma cópia off-host observada do archive mais antigo confere; archive mais recente não observado off-host |
| Findings | cloud-init `degraded done`; `spec_rstack_overflow` ainda vulnerável |

O snapshot root do backup confirma SSH efetivo sem root/password/keyboard-
interactive e UFW `INPUT DROP`, `OUTPUT ACCEPT`, somente OpenSSH 22 em IPv4/IPv6.
A verificação externa amostral confirmou 22 acessível e os endpoints gráficos/web
testados fechados ou filtrados.

## Discrepâncias e riscos recuperados

- RAM/disco aumentaram em relação ao snapshot documentado por causa da sessão de
  trabalho ativa; isso é estado dinâmico, não evidência de vazamento.
- O backup atual é configuração de referência: checksum e extração passaram,
  mas restore/rebuild funcional não foi provado.
- O script de backup normaliza arquivos arquivados para `0640`; restore cego pode
  quebrar executáveis ou arquivos com modos especiais.
- O arquivo remoto mais recente ainda não tinha cópia off-host observada.
- Não há snapshot, backup contratado ou firewall do provedor.
- Não existe Management Network privada; SSH 22 permanece fallback público.
- Docker poderá alterar o ruleset e exige baseline/rollback próprios.
- O host não possui swap e divide o mesmo failure domain com a Workstation.
- Documentos legados ainda apontavam rotação como `NEXT`; a fonte canônica atual
  a mantém adiada.

VNC/Rescue e opções do provedor não podem ser revalidados de dentro do guest; as
últimas evidências continuam históricas até nova inspeção humana do painel.

## Plano de Technology Mapping

O mapping usa Q1–Q39 e os treze critérios da missão. Uma seleção arquitetônica
não prova instalação nem `DONE`. A ordem é:

1. registrar candidatos, versão/release observada, licença, custo e fonte oficial;
2. comparar recursos do nó, privilégios, recovery, portabilidade, multi-node,
   interfaces, auditoria, lock-in e rollback;
3. classificar cada item como `SELECTED`, `CONDITIONAL` ou `CANDIDATE`;
4. resolver no precheck do slice digest/versão e incompatibilidades ainda abertas;
5. instalar somente por slice reversível e promover a `VALIDATED` apenas com os
   critérios de DONE aplicáveis.

O baseline detalhado está em `docs/46-technology-mapping-v1.md`. Enforcement de
rede/egress, quota de disco, runner isolation, DNS e escolhas condicionais devem
ser fechados em ADR/precheck próprio antes da capability correspondente; não são
inferidos como prontos.

## Primeiro incremento autorizado

`SLICE-001 — Foundations F1.1 declarativa` cria apenas desired state, identidade
técnica bloqueada, namespaces, tmpfiles e slices de accounting. Não instala
runtime, não cria listener, não muda SSH/UFW/XRDP e não manipula credenciais.

A revisão de safety encontrou gaps de provenance/TOCTOU no rollback, adoção de
objetos, check mode e proteção do target. A remediação candidata e a suíte estática
passaram no worktree local, ainda sem vínculo a commit; check mode, apply,
idempotência e rollback aguardam prova em VM GitHub descartável. Na VPS essas
operações continuam bloqueadas. Quando um checkpoint posterior as liberar, a
aplicação ainda requer autenticação sudo digitada por LEANDRO fora de logs.

## Rollback do primeiro incremento

- executar somente o playbook de rollback versionado do slice, com confirmação
  explícita e depois de validar a proveniência dos objetos;
- recusar remoção quando conta/processo, marker, ownership, conteúdo ou diretório
  não corresponder exatamente ao estado gerenciado;
- remover apenas units, tmpfiles, conta/grupo e namespaces criados por F1.1;
- nunca remover recursivamente estado persistente ou runtime não vazio;
- executar `systemctl daemon-reload` quando aplicável e repetir os checks de SSH,
  UFW, listeners, XRDP, LXD, units e Workstation;
- o rollback não altera pacotes, Docker, rede, firewall, SSH, credenciais ou dados
  preexistentes.

Esses são requisitos do rollback, não uma afirmação de que a implementação atual
já os satisfaz dinamicamente. O playbook atual não pode ser executado na VPS até
provar fail-closed em VM descartável os controles de provenance/TOCTOU, adoção e
target. O resultado anterior da fixture é histórico e requer revalidação após a
revisão; o rollback na VPS real continua `NOT_EXECUTED`.

## HUMAN_GATEs conhecidos

- senha sudo existente digitada diretamente por LEANDRO, nunca enviada ao agente;
- onboarding/identidade/plano/policy da Management Network externa;
- inicialização, unseal e custódia humana das shares do secret store;
- permissão/OIDC/token escopado do registry externo;
- domínio, zona DNS e credencial escopada; depois desse bootstrap, previews DEV
  dentro do namespace/grant aprovado não exigem gate repetitivo;
- destino/custo/retention e custódia da chave de backup off-host;
- uso/licença/custo de componente que exija aceitação humana ou serviço pago;
- operações do painel Contabo, como snapshot, backup contratado, firewall, VNC ou
  Rescue;
- qualquer expansão fora de Q40-D e toda promoção para produção.

Mudanças reversíveis de host/rede dentro de Q40-D continuam autorizadas quando
precheck, impacto, backup/checkpoint, rollback e evidência forem satisfeitos; elas
não criam automaticamente um novo HUMAN_GATE arquitetônico. Rotação de
credenciais permanece fora da missão.

## Evidência e limite da recuperação

O snapshot sanitizado está em `evidence/SLICE-001/baseline.yaml`. Ele preserva o
estado observado sem secrets, mas não substitui nova inspeção imediatamente antes
de apply. Claims do painel do provedor permanecem históricos, e a cópia off-host
validada refere-se ao archive observado, não ao archive remoto mais recente.
