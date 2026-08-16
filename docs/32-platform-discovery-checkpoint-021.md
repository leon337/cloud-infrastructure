# 32 — Platform Discovery Checkpoint 021 — Q33

Data: 2026-08-16
Status: **DISCOVERY_IN_PROGRESS**
Autoridade humana final: **LEANDRO**

## Continuidade

Este checkpoint continua a lineage da Platform Discovery preservada nos checkpoints anteriores até Q32.

A implementação pesada da plataforma e a missão de implementação para o Codex continuam **NÃO AUTORIZADAS** enquanto a Discovery não atingir maturidade suficiente e não houver HUMAN_GATE explícito de LEANDRO.

A rotação de credenciais permanece **DEFERRED_BY_HUMAN_DECISION**.

## Q33 — Atualizações, vulnerabilidades e software supply chain

**Escolha de LEANDRO: C — scanning contínuo + classificação de risco + atualização automatizada por política + testes/rollback + HUMAN_GATE apenas quando o risco ultrapassar o escopo autorizado.**

### Decisão

A plataforma deve separar detecção, avaliação de risco e aplicação de correções. Atualizações não devem ser totalmente manuais nem aplicadas indiscriminadamente assim que uma nova versão surgir.

A arquitetura deve prever:

- scanning contínuo de host, dependências, imagens e artefatos;
- identificação de versões vulneráveis ou obsoletas;
- classificação de risco e impacto;
- automação de correções rotineiras e reversíveis dentro do escopo autorizado;
- build, testes, security checks, health checks e evidências antes de promover uma atualização;
- plano de rollback/checkpoint para alterações relevantes;
- elevação para fluxo controlado/HUMAN_GATE quando uma alteração ultrapassar o escopo autorizado ou afetar componentes críticos;
- rastreabilidade entre source, dependency, build, image, registry e deploy;
- capacidade de identificar projetos afetados por uma vulnerabilidade e criar remediation jobs/workflows;
- tratamento separado para atualização da própria plataforma.

### Classes conceituais

Atualizações rotineiras e de baixo risco podem seguir fluxo automatizado de detecção, build, teste, scan e deploy DEV.

Mudanças críticas, como kernel, SSH, firewall, networking, secret store, Capability Core, backup engine ou workflow engine, devem passar por análise de impacto, backup/checkpoint e rollback plan, com gate quando exigido pela política.

### Compatibilidade com decisões anteriores

Q33 complementa:

- Q15: observabilidade, eventos, auditoria e evidência antes de DONE;
- Q18: artefatos imutáveis e provenance;
- Q23: promoção para produção sob autoridade humana;
- Q27: estado declarativo, idempotência e reconciliação controlada;
- Q28: remediation e patching podem ser executados como workflows duráveis;
- Q32: dependências de AI/model backends também permanecem sujeitas a política e auditoria.

### Princípios derivados

- detectar continuamente;
- automatizar correções rotineiras e reversíveis dentro do escopo autorizado;
- não atualizar componentes críticos sem validação, checkpoint e rollback;
- elevar mudanças quando o risco ultrapassar o escopo autorizado;
- supply-chain provenance deve acompanhar source, dependency, build, artifact e deploy;
- correção automática não elimina governança nem HUMAN_GATE quando necessário;
- tecnologia concreta de scanners, SBOM, signing e policy engines será selecionada posteriormente.

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
Q24 = C
Q25 = C
Q26 = C
Q27 = C
Q28 = D
Q29 = C
Q30 = C
Q31 = C
Q32 = C
Q33 = C
```

## Próximo passo

**DISCOVERY_Q34**.

A próxima decisão deve tratar da arquitetura de rede interna e descoberta de serviços: como workloads encontram serviços autorizados sem depender de IPs fixos, sem abrir portas desnecessárias e preservando isolamento entre tenants/projetos.