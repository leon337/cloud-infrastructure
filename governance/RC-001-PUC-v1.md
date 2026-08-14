# RC-001 — Revisão Crítica do PUC v1.0

Status: **IMPLEMENTADO COM CONTROLES**.

## Problema original

Checkpoints resumidos estavam sofrendo compressão sucessiva de contexto. O risco era cada novo chat herdar menos intenção, histórico e decisões, gerando perguntas repetidas e ações inconsistentes.

## Riscos encontrados e controles

### R1 — Checkpoint virar depósito de toda a memória

**Risco:** arquivo gigante, difícil de manter e propenso a inconsistência.

**Controle:** separar missão, arquitetura, plano, inventário, decisões, findings, histórico e runbooks. Checkpoint aponta para essas fontes.

### R2 — Duplicação divergente

**Risco:** IP, fase ou decisão aparecem diferentes em vários arquivos.

**Controle:** matriz de ownership e `CONTEXT-COVERAGE`; cada categoria possui fonte proprietária.

### R3 — Documentação vencer realidade

**Risco:** agir sobre informação antiga.

**Controle:** precedência explícita do estado real sobre documentação e regra de revalidação de fatos voláteis.

### R4 — IA ignorar contexto

**Risco:** novo chat começa executando comandos.

**Controle:** `CONTEXT.md` como porta de entrada e startup gate obrigatório.

### R5 — Continuidade depender de prompt gigante

**Risco:** prompt manual fica desatualizado.

**Controle:** prompt de handoff deve apenas apontar para o protocolo do repositório; o conteúdo vive no GitHub.

### R6 — Informação importante ficar só no chat

**Risco:** perda na troca de conversa.

**Controle:** Auditoria de Delta e proibição de encerrar sessão enquanto houver delta não persistido.

### R7 — Proposta virar decisão

**Risco:** IA tratar hipótese como aprovação.

**Controle:** classificação FACT/DECISION/PROPOSAL/FINDING/AUTHORIZATION.

### R8 — Autorização humana desaparecer

**Risco:** repetir gate ou executar algo não autorizado.

**Controle:** autorizações ativas em `state/current.yaml`, checkpoint e, quando estrutural, decision log.

### R9 — Escrita concorrente por múltiplas IAs

**Risco:** sobrescrever documentação recente.

**Controle:** ler HEAD/arquivo antes de escrever, usar SHA atual e reavaliar se a branch mudou.

### R10 — Secrets contaminarem a memória

**Risco:** preservar contexto copiando credenciais.

**Controle:** política explícita de zero secrets e distinção entre secret e identificador operacional.

### R11 — Histórico crescer sem limite e inviabilizar leitura

**Risco:** toda IA ter de ler anos de sessões.

**Controle:** `CONTEXT.md` aponta leituras mínimas; histórico é consultado apenas quando causalidade/decisão exigir.

### R12 — Machine state e human docs divergirem

**Risco:** `state/current.yaml` ficar atrasado.

**Controle:** atualização do state é item obrigatório do fechamento e deve refletir o checkpoint.

### R13 — Roadmap criar falsa sensação de aprovação

**Risco:** fases futuras propostas serem tratadas como decisões fechadas.

**Controle:** roadmap marca explicitamente `PROVISIONAL` e gates de decisão.

### R14 — Continuidade ser declarada sem teste

**Risco:** estrutura parecer boa, mas novo chat continuar pedindo contexto.

**Controle:** teste de continuidade obrigatório após grandes mudanças de governança ou migração de chat.

## Lacunas retrospectivas identificadas nesta sessão

Foram recuperadas e agora ganham casa canônica:

- missão didática e operacional original;
- arquitetura híbrida local/VPS;
- intenção de Cloud Workstation;
- discussão KVM/QEMU e nested virtualization;
- planejamento de armazenamento antes de particionar;
- estratégia de segurança gradual;
- roadmap de Docker/desenvolvimento/backup/monitoramento/serviços;
- protocolo didático;
- conceitos do painel Contabo;
- FND-SSH-001 com ping, teste inválido e teste válido;
- inspeção relatada de `~/.ssh/config` inexistente.

## Veredito

O PUC v1.0 resolve o problema estrutural se for aplicado como processo, não apenas como conjunto de arquivos. O maior risco residual é **disciplina de atualização**. Por isso a retomada da VPS fica bloqueada até um teste de continuidade provar que um novo chat consegue reconstruir o estado somente a partir do repositório.