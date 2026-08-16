# 18 — Platform Discovery Checkpoint 007 — Q19

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a linhagem de Discovery já registrada em:

- `docs/12-platform-discovery-checkpoint-001.md` — Q1–Q9;
- `docs/13-platform-discovery-checkpoint-002.md` — Q10–Q13;
- `docs/14-platform-discovery-checkpoint-003.md` — Q14–Q15;
- `docs/15-platform-discovery-checkpoint-004.md` — Q16;
- `docs/16-platform-discovery-checkpoint-005.md` — Q17;
- `docs/17-platform-discovery-checkpoint-006.md` — Q18.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q19 — Execução de jobs de build, teste e deploy

**Escolha de LEANDRO: C — pipeline híbrido: GitHub/control plane + job runners isolados e descartáveis mediados pelo Capability Core.**

### Decisão

O pipeline pode solicitar execução de jobs, mas não deve receber autoridade administrativa irrestrita sobre o host. Builds, testes e outras tarefas automatizadas devem ser tratados como workloads descartáveis e isolados, executados sob políticas do Capability Core.

Arquitetura conceitual:

```text
GitHub / MCF / CLI / outros control planes
                  |
                  v
            Capability Core
                  |
                  v
             Job Runner
                  |
                  v
        Sandbox isolado do job
```

### Propriedades desejadas do job sandbox

Cada job deve poder receber:

- limite de CPU;
- limite de RAM;
- limite de disco;
- filesystem temporário;
- rede controlada;
- credenciais escopadas e preferencialmente temporárias;
- timeout/duração máxima;
- identidade/proveniência do projeto, missão, revisão e pipeline;
- logs, métricas, eventos e auditoria centralizados.

Ao término do job:

- artefatos aprovados podem ser publicados no registry canônico;
- logs/evidências são preservados conforme política;
- estado temporário deve ser destruído por padrão.

### Princípios derivados

- pipeline pode solicitar execução; não controla diretamente o host;
- self-hosted runner genérico e privilegiado não deve se tornar uma porta lateral para contornar o Capability Core;
- jobs de CI devem reutilizar o mesmo modelo de isolamento de sandboxes da plataforma;
- build/test são workloads descartáveis;
- acesso a recursos internos deve ser mínimo, escopado e autorizado;
- GitHub Actions poderá atuar como control plane/dispatcher quando fizer sentido, sem receber autoridade administrativa ampla na VPS;
- a arquitetura deve permitir que MCF, Hermes, CLI, TriView ou outros clientes usem o mesmo mecanismo de jobs futuramente;
- scheduler/queue totalmente internos poderão ser evoluções futuras sem serem obrigatórios no primeiro release.

### Capacidades desejadas

O futuro Capability Core poderá evoluir para operações como:

- `create_job_sandbox()`;
- `run_build_job()`;
- `run_test_job()`;
- `get_job_status()`;
- `get_job_logs()`;
- `cancel_job()`;
- `publish_artifact()`;
- `destroy_job_sandbox()`.

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
Q16 = C
Q17 = C
Q18 = C
Q19 = C
```

## Próximo passo

**DISCOVERY_Q20**.

A Discovery continua. Nenhuma decisão tecnológica adicional deve ser antecipada antes das perguntas correspondentes, e nenhuma implementação pesada foi autorizada.
