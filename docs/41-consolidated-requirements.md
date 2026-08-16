# 41 — CONSOLIDATED_REQUIREMENTS

Status: **CANONICAL DERIVATIVE BASELINE V1 — Q1–Q40 REMAIN BINDING**
Fonte: Platform Discovery Q1–Q40
Autoridade: LEANDRO

Este documento transforma as decisões arquitetônicas em requisitos verificáveis.
Ele não substitui os checkpoints: detalhes e exceções registrados neles continuam
vinculantes.

## Requisitos Q1–Q40

| ID | Q | Requisito verificável |
|---|---:|---|
| CR-001 | Q1 | A plataforma deve fornecer compute, desenvolvimento e execução privada de agentes. |
| CR-002 | Q2 | DEV/lab deve preferir infraestrutura própria; serviço externo exige vantagem e decisão registradas. |
| CR-003 | Q3 | Projetos devem ser isolados e missões devem poder obter sandboxes temporários. |
| CR-004 | Q4 | Automação só pode agir dentro de escopo pré-autorizado; fora dele deve falhar em `WAITING_FOR_HUMAN_GATE`. |
| CR-005 | Q5 | Capability Core deve ser a fronteira de capacidades/policy, evoluindo por API, MCP e CLI. |
| CR-006 | Q6 | O catálogo deve cobrir progressivamente Projects, Sandboxes, Compute, Databases, Storage, Deploy DEV, Preview, Network, Logs, Metrics/Observability, Backup/Restore e Diagnosis, sem exigir big-bang. |
| CR-007 | Q7 | Compute deve ser descartável; estado importante deve ser declarado e persistido explicitamente. |
| CR-008 | Q8 | Cada sandbox deve ter limites de CPU, RAM, PIDs, disco, filesystem e rede. |
| CR-009 | Q9 | Projetos devem possuir manifesto versionado, schema estrito e operações idempotentes. |
| CR-010 | Q10 | Cada projeto pode ter banco DEV persistente; banco de sandbox deve ser temporário. |
| CR-011 | Q11 | Storage deve combinar Git, filesystem temporário, object storage e volumes somente quando necessários. |
| CR-012 | Q12 | Secrets devem residir em cofre central; a autoridade/injeção deve ser escopada e temporária, e credenciais temporárias devem ser preferidas quando tecnicamente viáveis, sem forçar rotação das credenciais atualmente adiadas. |
| CR-013 | Q13 | Serviços são privados por padrão; previews exigem gateway controlado e HTTPS automático. |
| CR-014 | Q14 | Build/test/deploy DEV deve partir de Git, ser acionável, rastreável, testado e rollback-capable. |
| CR-015 | Q15 | Logs, métricas, eventos, auditoria e correlação devem ser centrais; não há DONE sem evidência. |
| CR-016 | Q16 | Compute deve ser reconstruível; backup off-host automático e restore funcional devem ser testados. |
| CR-017 | Q17 | O runtime inicial deve ser Docker/Compose, container-first e mediado; agentes nunca recebem daemon/socket. |
| CR-018 | Q18 | Registry OCI canônico deve sobreviver à perda do nó; cache local é descartável; deploy usa digest/provenance. |
| CR-019 | Q19 | Pipelines devem usar control plane híbrido e runners isolados, efêmeros e mediados. |
| CR-020 | Q20 | Egress útil deve ser permitido por policy; lateral, admin e private são negados por padrão. |
| CR-021 | Q21 | Management Plane privado, Agent Gateway público mínimo e Preview Gateway devem ser fronteiras distintas. |
| CR-022 | Q22 | Toda ação deve ter identidade distinguível e autoridade curta por tenant/project/mission/capability. |
| CR-023 | Q23 | DEV/staging podem automatizar; produção exige gate de LEANDRO preso à release/artefato/rollback. |
| CR-024 | Q24 | Ownership deve seguir Tenant/Workspace → Project → Mission → Sandbox. |
| CR-025 | Q25 | Deve haver reserva do host, quotas hierárquicas, limites, burst controlado e fila/admission sob pressão. |
| CR-026 | Q26 | V1 é single-node, mas todo executor deve usar abstração de node e preservar portabilidade/multi-node. |
| CR-027 | Q27 | Desired state deve ser versionado, idempotente, detectar drift e reconciliar apenas conforme policy. |
| CR-028 | Q28 | V1 deve incluir workflow engine durável e distributed-capable, mesmo implantado em um nó. |
| CR-029 | Q29 | MCF governa; Capability Core autoriza; Workflow Engine executa; cada domínio mantém sua fonte de verdade. |
| CR-030 | Q30 | TriView/OpenClaw/Hermes/Codex/Freebuff devem integrar por interfaces explícitas e continuar substituíveis. |
| CR-031 | Q31 | A plataforma deve ser headless; XFCE/XRDP é cockpit humano opcional. |
| CR-032 | Q32 | Model Gateway deve centralizar policy, routing, quotas/custos, fallback e backends substituíveis. |
| CR-033 | Q33 | Host, dependências, IaC, imagens e artefatos devem ter scanning, classificação, update e rollback por policy. |
| CR-034 | Q34 | Redes devem isolar tenant/project/sandbox; service discovery é nominal/identitário e sharing é explícito. |
| CR-035 | Q35 | Estado deve ser classificado como critical/important/rebuildable/disposable, com RPO/RTO/retention próprios. |
| CR-036 | Q36 | Comandos síncronos passam pelo Core; eventos duráveis usam backbone com identidade e correlação. |
| CR-037 | Q37 | A plataforma deve administrar namespace DNS, URLs e TLS de previews, separando rigidamente DEV/PROD. |
| CR-038 | Q38 | Data Service Plane deve oferecer banco, cache, object storage e mensageria/queues/topics, isolar logicamente tenant/project e criar recursos descartáveis para sandbox. |
| CR-039 | Q39 | Administração deve usar rede privada e identidade de usuário/dispositivo; SSH é fallback; VNC/Rescue break-glass. |
| CR-040 | Q40 | Codex pode selecionar/implementar DEV/lab sem reabrir Q1–Q39, promover produção ou rotacionar credenciais. |

## Invariantes transversais

| ID | Invariante |
|---|---|
| INV-001 | Nenhuma senha, passphrase, chave privada, token, API key, 2FA, connection string real ou credencial de provedor entra no Git/log/evidência. |
| INV-002 | Nenhum agente, runner, canal ou workload recebe root, sudo irrestrito, grupo `docker` ou socket do daemon. |
| INV-003 | Management Plane e interfaces administrativas não escutam em endereço público. |
| INV-004 | Produção permanece desabilitada em manifests/policies e exige HUMAN_GATE explícito de LEANDRO. |
| INV-005 | Cloud Workstation não é dependência e não pode ser quebrada por reconciliação da plataforma. |
| INV-006 | Mudança crítica exige precheck, impacto, backup, rollback, teste e evidência. |
| INV-007 | Capacidade não comprovada permanece `PROPOSED`/`PARTIAL`, nunca `DONE`. |
| INV-008 | Worker, executor ou sandbox parcialmente confiável não alcança diretamente o Node Agent; toda operação privilegiada é autorizada pelo Core e revalidada na fronteira local. |
| INV-009 | Depois do bootstrap humano de domínio/DNS, previews DEV dentro de namespace, quota e grant aprovados não exigem HUMAN_GATE repetitivo; novo domínio, custo, produção ou expansão de escopo exigem. |

## Evidência mínima por capability

Uma capability só pode mudar para `DONE` quando houver, conforme aplicável:

1. desired state versionado e schema/policy correspondente;
2. aplicação e segunda reconciliação com `changed=0`;
3. health/status e restart/reboot verificados;
4. acesso autorizado e negações relevantes testados;
5. isolamento e limites medidos;
6. logs, métricas, eventos, auditoria e correlação visíveis;
7. backup/rebuild/restore testado segundo a classe;
8. rollback executável e evidência preservada;
9. inventário, runbook, state e checkpoint atualizados.
