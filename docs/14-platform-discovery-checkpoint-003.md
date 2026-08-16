# 14 — Platform Discovery Checkpoint 003 — Q14–Q15

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua:

- `docs/12-platform-discovery-checkpoint-001.md` — Q1–Q9;
- `docs/13-platform-discovery-checkpoint-002.md` — Q10–Q13.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q14 — Transformação do código em ambiente executável

**Escolha de LEANDRO: C — Git + pipeline automático de build/test/deploy DEV, acionável pelos agentes.**

### Decisão

O código versionado em Git deve ser a referência para builds e deploys DEV reproduzíveis. Agentes poderão acionar autonomamente pipelines de desenvolvimento dentro do escopo autorizado, mas cada execução deverá manter rastreabilidade suficiente para responder qual revisão está rodando, quais validações foram executadas e como retornar a uma revisão anterior.

Fluxo conceitual:

```text
Agente
  -> altera código
  -> testes locais quando aplicável
  -> branch/commit
  -> pipeline DEV
       -> valida manifesto
       -> resolve dependências
       -> build
       -> testes/validações
       -> produz imagem/artefato quando aplicável
       -> prepara sandbox/ambiente
       -> deploy da revisão
       -> health check
       -> registra evidências
       -> entrega status/URL/logs
```

### Rastreabilidade mínima desejada

Cada deployment deve poder ser relacionado a informações como:

- projeto;
- branch/revisão/commit;
- missão/sandbox quando aplicável;
- pipeline/build que o produziu;
- status de testes e validações relevantes;
- artefato ou imagem resultante quando aplicável;
- ambiente de destino;
- status/health check;
- logs/evidências;
- revisão anterior elegível para rollback.

### Autonomia

Agentes autorizados poderão, dentro do laboratório e do seu escopo:

- disparar build;
- disparar testes;
- solicitar deploy DEV;
- criar preview associado a branch/missão/revisão;
- consultar logs e status;
- solicitar rollback permitido;
- destruir deployment/sandbox descartável quando a política permitir.

Produção não é automaticamente incluída nessa autonomia. Promoção para produção externa permanece sujeita às políticas e HUMAN_GATES que ainda serão definidos pela Discovery.

### Princípios derivados

- todo deploy DEV deve ser reproduzível e rastreável;
- deployments devem estar associados a uma revisão conhecida do código;
- Git é referência versionada, não autorização irrestrita para alterar toda a plataforma;
- agentes podem acionar pipelines DEV sem intervenção humana repetitiva quando dentro do escopo autorizado;
- build/test/deploy deve produzir evidência operacional suficiente;
- rollback deve ser suportado quando tecnicamente aplicável;
- previews temporários devem poder ser associados a branch, missão ou revisão;
- GitOps completo de toda a plataforma não é exigido no primeiro release, mas a arquitetura não deve impedir evolução futura nessa direção;
- a tecnologia concreta de CI/CD, registry, builder e runtime ainda não está congelada.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `build_project()`;
- `run_tests()`;
- `deploy_revision()`;
- `deploy_branch()`;
- `create_preview()`;
- `get_deployment_status()`;
- `get_build_logs()`;
- `rollback_deployment()`;
- `destroy_deployment()`;
- registrar proveniência/evidências do deployment.

## Q15 — Observabilidade e diagnóstico para agentes

**Escolha de LEANDRO: C — logs + métricas + eventos + auditoria centralizados.**

### Decisão

A plataforma deve oferecer observabilidade central suficiente para que agentes possam verificar resultados, diagnosticar falhas e entender o estado de projetos, sandboxes, deployments e recursos sem depender de investigação manual recorrente de LEANDRO.

A observabilidade inicial deve combinar quatro classes principais:

- **logs** — mensagens e erros produzidos por aplicações e serviços;
- **métricas** — CPU, RAM, disco, latência, requests, erros, uso de banco e consumo por projeto/sandbox;
- **eventos** — criação/destruição de sandbox, deploy iniciado/concluído/falhado, preview publicado/revogado, backup/restore e outras mudanças relevantes;
- **auditoria** — identidade/agente, projeto, missão, sandbox, ação, resultado e momento da operação.

### Princípio operacional

Um agente não deve marcar uma tarefa como concluída apenas porque executou uma ação. A plataforma deve fornecer evidência suficiente para verificar se o resultado esperado realmente ocorreu.

Fluxo conceitual:

```text
AÇÃO
  -> logs + métricas + eventos + status
  -> evidência
  -> verificação
  -> DONE ou diagnóstico/correção
```

### Relação com limites de recursos

A observabilidade deve permitir identificar quando um sandbox ou projeto se aproxima ou excede limites definidos de CPU, RAM, disco, rede ou processos. A política futura poderá então alertar, limitar, pausar ou encerrar workloads conforme regras explícitas, sem permitir que um agente descontrolado comprometa todo o laboratório.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `get_logs()`;
- `get_metrics()`;
- `get_events()`;
- `get_health()`;
- `get_resource_usage()`;
- `get_deployment_status()`;
- `diagnose_project()`;
- `diagnose_sandbox()`;
- consultar trilha de auditoria;
- detectar anomalias futuramente.

### Direção futura

Tracing distribuído deve permanecer compatível como evolução futura, mas não será requisito obrigatório do primeiro release.

### Princípios derivados

- observabilidade central, não dependência de inspeção manual serviço por serviço;
- evidência antes de considerar uma ação concluída;
- logs, métricas, eventos e auditoria como capacidades de primeira classe;
- isolamento de visibilidade por projeto/missão quando necessário;
- agentes devem poder diagnosticar problemas dentro do escopo autorizado;
- ações relevantes do Capability Core devem deixar trilha auditável;
- a tecnologia concreta de observabilidade ainda não está congelada.

## Estado das decisões

```text
Q1  = C
Q2  = C
Q3  = C
Q4  = C
Q5  = D
Q6  = C
Q7  = C
Q8  = C
Q9  = C
Q10 = C
Q11 = D
Q12 = C
Q13 = C
Q14 = C
Q15 = C
```

## Próximo passo

**DISCOVERY_Q16**.

A Discovery continua. Nenhuma escolha tecnológica final de runtime, banco, object storage, gateway, secret manager, CI/CD, registry, observabilidade, backup/recovery, Hermes/OpenClaw/Freebuff/OpenHands ou desenho detalhado de MCP deve ser antecipada antes das decisões correspondentes.
