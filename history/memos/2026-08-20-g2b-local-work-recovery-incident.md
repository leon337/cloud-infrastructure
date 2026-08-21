# Memorando Institucional — Incidente de recuperação do G2-B em 2026-08-20

**Data do evento:** 2026-08-20  
**Classificação:** incidente de continuidade / recuperação de trabalho  
**Escopo:** Control Bridge G2-B / continuidade de missão  
**Autoridade humana:** LEANDRO  
**Missão corretiva:** Issue #10 — Repository Continuity & Context Recovery Hardening  
**Branch associada:** `codex/control-bridge-g2b`

## Resumo executivo

Em 20/08/2026, várias horas de implementação do G2-B existiam apenas em um worktree local. Um reinício inesperado do computador encerrou processos e subagentes temporários. Os commits e arquivos sobreviveram no disco, porém a branch ainda não havia sido publicada no GitHub. Posteriormente, o Codex atingiu limite de mensagens enquanto a Task 7 permanecia parcial.

A recuperação foi possível, mas exigiu reconstrução manual do estado usando múltiplas fontes: histórico de chat, screenshots, worktrees Git, commits locais, reflog, ledger e arquivos não rastreados. O episódio demonstrou que a continuidade operacional dependia excessivamente de memória de sessão e de estado local não publicado.

O incidente não causou perda comprovada do trabalho recuperado, mas revelou uma lacuna de engenharia de continuidade suficientemente relevante para originar uma missão P0 transversal.

## Estado técnico recuperado

O estado preservado e posteriormente publicado foi:

```text
BRANCH=codex/control-bridge-g2b
BASE=mcf/mission-001-control-bridge-g1
RECOVERY_CHECKPOINT_SHA=7205a647f918580d09c87ed44f38b0a433552a51
TASKS_1_6=COMPLETE_MATERIALLY_REVIEWED
TASK_7=PARTIAL
TASK_7_TESTS=6_PASS_1_FAIL
KNOWN_RED=EXISTING_GRANT_EXACT_KEY_SET_NOT_ENFORCED
ANSIBLE_SYNTAX=NOT_EXECUTED_CURRENT_LOCAL_ENVIRONMENT
TASKS_8_10=NOT_STARTED
NODE01_G2B_GATE=CLOSED
REAL_WRITE=NOT_EXECUTED
MERGE=NO
```

O checkpoint preservado nunca foi tratado como aceitação da Task 7.

## Impacto observado

- retomada do trabalho passou a exigir investigação manual em várias superfícies;
- o estado real não podia ser reconstruído com confiança a partir de uma única fonte persistente;
- uma nova IA não teria condições seguras de continuar apenas lendo o repositório remoto daquele momento;
- o trabalho material local acumulou-se por tempo suficiente para ampliar o custo de recuperação;
- o limite posterior de mensagens do Codex tornou mais evidente a dependência de sessão para continuidade.

## O que não foi concluído a partir do incidente

Não existe evidência de que:

- o reinício tenha corrompido commits Git;
- tenha ocorrido comprometimento de segurança da VPS;
- a Task 7 estivesse concluída;
- a escrita real G2-B estivesse autorizada ou executada;
- o problema técnico do grant tenha sido causado pelo reinício.

Essas hipóteses não fazem parte do registro factual.

## Recuperação realizada

A resposta imediata e posterior incluiu:

1. localização do worktree e branch corretos;
2. reconstrução do HEAD local e relação com a base remota;
3. preservação explícita dos artefatos parciais da Task 7 em checkpoint WIP;
4. correção do bloqueio de autenticação GitHub necessário para publicar workflow/branch;
5. publicação de `codex/control-bridge-g2b` no remoto;
6. criação do PR #11 em modo `DRAFT / DO NOT MERGE`;
7. reconciliação de `README.md`, `CONTEXT.md`, `CHECKPOINT.md` e estados estruturados;
8. criação de protocolo obrigatório de startup/recovery;
9. criação de política de persistência para missões longas.

## Lacuna de engenharia comprovada

A lacuna demonstrada foi:

> trabalho material e conhecimento operacional importante podiam permanecer dependentes de uma combinação de estado local e memória de sessão por tempo excessivo, tornando a recuperação cara e potencialmente ambígua.

A correção não é apenas “commitar mais”. O requisito é que o projeto mantenha **checkpoints remotos recuperáveis, estado semântico explícito e fontes canônicas suficientes para reconstrução independente**.

## Decisões corretivas e preventivas

Foram estabelecidas as seguintes decisões permanentes:

- `NO_IMPLEMENTATION_BEFORE_RECOVERY_VERDICT_PASS`;
- `NO_LONG_RUNNING_MISSION_WITHOUT_RECOVERABLE_REMOTE_CHECKPOINTS`;
- máximo de 30 minutos de trabalho material sem checkpoint remoto recuperável quando o remoto estiver disponível;
- checkpoint obrigatório em mudanças materiais de estado, handoffs, HUMAN_GATEs, pausas e slices relevantes;
- WIP remoto não implica `PASS`, aceitação, merge readiness ou autorização de HUMAN_GATE;
- estado de sessão não é estado durável;
- perda de sessão/reboot/rate-limit exige reconstrução pelo protocolo de startup/recovery antes de retomar;
- falha de persistência remota deve gerar blocker explícito e impedir acúmulo de novo trabalho material não relacionado;
- o agente controlador é responsável por tornar duráveis os resultados materiais de subagentes.

## Consequências de longo prazo

O incidente originou a missão `Repository Continuity & Context Recovery Hardening`, organizada em R1–R8.

R1–R4 preservaram estado, reconciliaram entradas canônicas e instituíram protocolos. R5 formaliza esta memória institucional. R6 deve adicionar controles automáticos de consistência/drift. R7 deve provar a recuperação por cold start. Somente R8 pode retomar a correção técnica da Task 7.

## Riscos residuais no momento deste memo

- Task 7 continua `PARTIAL`, com evidência `6 PASS / 1 FAIL`;
- Tasks 8–10 continuam `NOT_STARTED`;
- validação de sintaxe Ansible da Task 7 ainda não foi comprovada no ambiente recuperado;
- NODE-01 G2-B, grant real, escrita real, produção e merge continuam não autorizados;
- a validação de GitHub Actions observada em alguns heads da missão permaneceu inconclusiva quando jobs `validate` falharam sem steps/logs utilizáveis;
- até R6 e R7, os controles de drift e a prova de cold-start ainda não estão concluídos.

## Referências duráveis

- Issue #10 — `Repository Continuity & Context Recovery Hardening`;
- PR #11 — `G2-B — bounded write control bridge (recovered WIP)`;
- `docs/53-repository-continuity-context-recovery-mission.md`;
- `docs/54-control-bridge-g2b-recovery-checkpoint.md`;
- `state/active-mission.yaml`;
- `state/control-bridge-g2b.yaml`;
- `governance/AI-STARTUP-RECOVERY-PROTOCOL.md`;
- `governance/LONG-RUNNING-MISSION-PERSISTENCE-POLICY.md`.

## Regra de preservação deste memo

Este documento é histórico e append-oriented. Se fatos posteriores refinarem a interpretação do incidente, a correção deve ser registrada em novo memo ou adendo relacionado; este registro não deve ser silenciosamente reescrito para simular conhecimento retrospectivo.
