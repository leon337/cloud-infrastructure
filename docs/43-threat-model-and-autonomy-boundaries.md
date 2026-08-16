# 43 — THREAT_MODEL_AND_AUTONOMY_BOUNDARIES

Status: **BASELINE V1 — DENY BY DEFAULT**
Escopo: DEV/lab single-node

## Ativos protegidos

- autoridade de LEANDRO e decisões/HUMAN_GATEs;
- credenciais humanas, workload identities, tokens e recovery keys;
- SSH, VNC/Rescue e capacidade de reconstrução;
- desired state e provenance de artefatos;
- dados por tenant/project e evidência de auditoria;
- disponibilidade do host, Workstation e control plane;
- isolamento de Management, Core, Data, Project e Sandbox networks;
- orçamento/cotas de modelos e serviços externos.

## Atores e hipóteses

| Ator | Confiança inicial | Tratamento |
|---|---|---|
| LEANDRO autenticado | autoridade humana final | ações críticas ainda exigem contexto/impacto explícitos |
| MCF | governa missão/grant | não executa operação privilegiada diretamente |
| Capability Core | trusted policy enforcement point | código pequeno, auditado e fail-closed |
| Node Agent | altamente privilegiado e local | API mínima, allowlist, nunca acessível ao agente/rede pública |
| Workflow worker | parcialmente confiável | capability temporária por task; sem autoridade administrativa |
| Executor Codex/Hermes | não administrativo | só capabilities emitidas; output é dado não confiável |
| OpenClaw/canal | fronteira pública/não confiável | não traduz texto diretamente em shell/admin |
| Projeto DEV | parcialmente confiável | isolado por project e limites |
| Sandbox/código baixado | não confiável | descartável, egress restrito e sem acesso ao host/core |
| Provedor/Internet/dependência | externo | validar identidade, integridade, disponibilidade e lock-in |

O modelo não assume que prompt, repositório, pacote, imagem ou modelo de IA seja
benigno. Instrução dentro de conteúdo externo é dado, não autorização.

## Fronteiras de autonomia

| Operação | Agente pode preparar | Core pode executar | HUMAN_GATE |
|---|---:|---:|---:|
| Ler estado autorizado e gerar plano | sim | n/a | não |
| Criar/testar sandbox DEV dentro de quota | sim | sim | não |
| Build/test/push de artefato DEV por digest | sim | sim | não, após capability existir |
| Deploy/rollback DEV autorizado | sim | sim | não, dentro do grant |
| Criar/revogar preview DEV no namespace, quota e grant aprovados | sim | sim | não |
| Aumentar quota além do envelope | sim | não | sim |
| Criar novo domínio/namespace, custo ou exposição fora do grant | sim | não | sim |
| Mudar SSH/UFW/Management Network dentro de slice Q40-D | sim | apenas mudança explicitamente escopada | sem nova decisão arquitetônica; `WAITING_FOR_HUMAN_GATE` enquanto sudo, painel ou outra entrada humana for necessária |
| Expandir host/rede além de Q40-D ou operar painel externo | proposta | não | sim |
| Inicializar/unseal secret store | não recebe shares | não sozinho | sim, custódia humana |
| Comprar serviço/mudar plano/provedor | proposta | não | sim |
| Rotacionar credencial adiada | não | não | decisão explícita nova |
| Promover para produção | preparar release/evidência | executar release aprovada | sempre LEANDRO |
| Apagar estado persistente/backup | propor e provar recovery | não sem grant destrutivo | sim |

Capabilities devem conter: sujeito, tenant, project, mission, operação, recurso,
ambiente, limites, expiração, correlation ID e constraints. Ausência ou mismatch
resulta em negação, não em fallback administrativo.

## Ameaças prioritárias e controles

| ID | Ameaça | Controles V1 | Evidência esperada |
|---|---|---|---|
| TM-01 | agente/worker obtém root pelo Docker socket/grupo/Node Agent | Core como caminho obrigatório; Node Agent local revalida capability assinada e curta; grupo `docker` vazio; nenhum socket montado | teste negativo de grupo/socket/API, worker direto e capability expirada/mismatch |
| TM-02 | container alcança host/Management/Data lateralmente | bridges separadas, DOCKER-USER/nft, egress policy, shared-service grants | matriz de conectividade negativa/positiva |
| TM-03 | porta publicada contorna UFW | nenhum `ports:` inicial; bind loopback/private; teste externo v4/v6 | diff de ruleset/listeners e probe externo |
| TM-04 | secret entra em Git/log/prompt/evidence | secret refs, scanner, runtime injection, redaction e `no_log` | scans e teste com fixture sintética |
| TM-05 | prompt injection vira operação administrativa | conteúdo não concede capability; policy valida operação estruturada | tentativa negativa correlacionada |
| TM-06 | token é reutilizado fora de projeto/tempo | audience/scope/expiry/nonce e identidade individual | testes cross-project/expired/replay |
| TM-07 | supply-chain entrega imagem/tag alterada | build por digest, SBOM, scan, assinatura e identity-bound verify | attestation/verify antes do deploy |
| TM-08 | backup cifrado existe mas não restaura | classes/RPO/RTO, off-host, `check`, drill isolado | restore funcional periódico |
| TM-09 | único nó perde control/data/evidence | desired state, registry externo, backup off-host e abstração de node | rebuild drill |
| TM-10 | logs/model gateway exfiltram prompts/secrets | minimização/redaction, policy de logging e egress allowlist | teste de logs e destinos |
| TM-11 | workload esgota RAM/PIDs/disco | slices/cgroups, quotas, admission e high-water alerts | carga controlada e negação |
| TM-12 | canal público chama API administrativa | gateways separados, auth/rate/replay e Core allowlist | scan/listener + chamadas negativas |
| TM-13 | policy/IdP/cofre fail-open | startup dependency e negação quando indisponível | chaos test de dependência |
| TM-14 | mudança manual causa drift perigoso | Git desired state, detecção e reconciliação controlada | diff/report; sem auto-fix crítico cego |
| TM-15 | GUI compartilhada interfere na plataforma | serviços headless, namespaces separados, invariance checks | reboot sem sessão gráfica + health |

## Secrets e bootstrap

- Git contém apenas identificadores simbólicos `secret://...`;
- `.env`, chaves e keystores são bloqueados por path policy;
- systemd credentials poderá transportar material runtime, mas não será a fonte
  canônica nem substituirá recovery do cofre;
- `SetCredential=` literal não será usado para segredo;
- OpenBao será instalado antes de inicializado; inicialização Shamir e custódia
  das shares são HUMAN_GATE;
- o root token inicial serve somente ao bootstrap de auth/policies/audit e deve ser
  revogado assim que credenciais administrativas limitadas existirem; emergência
  usa geração por quorum, não custódia rotineira de token root sem expiração;
- nenhum operador/agente imprime share, token ou connection string para provar
  funcionamento; a evidência é status/redação/fingerprint não reversível.

## Risco residual aceito em DEV/lab

- single-node não é HA;
- Docker/runc não é fronteira equivalente a VM contra kernel exploit;
- SSH 22 permanece público durante onboarding da Management Network;
- observabilidade local pode ser perdida com o nó até exportação off-host;
- cgroup/disco não fornece quota rígida do writable layer no ext4 atual;
- serviços candidatos com AGPL ou rápida cadência de patch exigem revisão antes
  da instalação.

Nenhum risco residual deste documento autoriza produção. Mudança que exceda o
envelope volta para `WAITING_FOR_HUMAN_GATE`.
