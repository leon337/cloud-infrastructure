# 22 — Platform Discovery Checkpoint 011 — Q23

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q22.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q23 — Fronteira entre autonomia DEV/staging e promoção para produção

**Escolha de LEANDRO: C — DEV/staging autônomos + HUMAN_GATE único de promoção + execução automatizada e escopada da release aprovada.**

### Decisão

A plataforma deve permitir alta autonomia aos agentes dentro de DEV e staging/pre-production, inclusive para desenvolvimento, testes, builds, previews, diagnóstico, preparação de migrations e validação de release candidates. A promoção para produção exige decisão explícita de LEANDRO por HUMAN_GATE, mas, após a aprovação, a execução operacional da promoção pode ser automatizada por executores autorizados dentro do escopo aprovado.

Fluxo conceitual:

```text
AGENTES
  -> DEV
  -> STAGING / RELEASE CANDIDATE
       -> testes finais
       -> evidências
       -> plano de migration
       -> plano de rollback
  -> HUMAN_GATE de LEANDRO
  -> execução automatizada e escopada
  -> verificação pós-deploy
  -> PRODUÇÃO
```

### Escopo da aprovação de produção

A aprovação não deve conceder autoridade permanente sobre produção. Deve ser vinculada, quando aplicável, a elementos como:

- projeto;
- release/revisão/commit;
- artefato imutável;
- ambiente de destino;
- migration aprovada;
- operações permitidas;
- janela/validade da autorização;
- plano de rollback;
- evidências e health checks esperados.

Ao concluir a promoção, a autoridade temporária de produção deve expirar ou ser revogada conforme a política.

### Operações pós-promoção

Operações somente de observação e diagnóstico previamente autorizadas, como health checks, leitura de logs e consulta de métricas, podem permanecer automáticas quando a política permitir. Novas alterações de produção, deployments, migrations destrutivas, mudanças de domínio, criação de serviços pagos, troca de credenciais principais ou operações equivalentes devem retornar à política protegida e ao HUMAN_GATE apropriado.

### Princípios derivados

- DEV e staging são ambientes de alta autonomia dos agentes dentro do escopo autorizado;
- promoção para produção exige autoridade humana final de LEANDRO;
- HUMAN_GATE aprova a promoção, não obriga LEANDRO a executar manualmente cada clique;
- a execução do release aprovado deve ser automatizável, rastreável e estritamente limitada ao escopo autorizado;
- autorização de produção é temporária e vinculada à release/operação, não permanente;
- evidência, rollback e verificação pós-deploy fazem parte da promoção;
- observabilidade pode continuar automática sem equivaler a autoridade de alteração;
- a arquitetura deve permitir produção externa em serviços gerenciados quando deliberadamente escolhida.

Princípio resumido:

**AUTONOMY_TO_PREPARE_AND_VALIDATE_HUMAN_AUTHORITY_TO_PROMOTE_AUTOMATION_TO_EXECUTE_APPROVED_RELEASE**

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
Q20 = C
Q21 = C
Q22 = C
Q23 = C
```

## Próximo passo

**DISCOVERY_Q24**.

A Discovery continua. Tenancy/ownership de projetos, divisão local-vs-VPS, papéis finais de MCF/Hermes/OpenClaw/Freebuff/Codex, serviços de dados concretos e outras escolhas tecnológicas ainda precisam ser consolidados antes do Infrastructure Blueprint e de qualquer missão pesada para o Codex.
